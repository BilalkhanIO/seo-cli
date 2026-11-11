#!/usr/bin/env python3
"""Run repeatable on-page SEO checks against a local HTML file or live URL."""
import html
import re
import sys
import urllib.request
import json
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


class ArticleExtractor(HTMLParser):
    """Capture Blogger post-body or schema.org articleBody, excluding site chrome."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.depth = 0
        self.parts = []
        self.found = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.depth and ("post-body" in attrs.get("class", "").split() or attrs.get("itemprop") == "articleBody"):
            self.depth = 1
            self.found = True
            return
        if self.depth:
            self.parts.append(self.get_starttag_text())
            if tag not in {"img", "br", "hr", "input", "meta", "link", "source", "wbr", "area", "base", "embed", "param", "track", "col"}:
                self.depth += 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1
            if self.depth:
                self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

    def handle_entityref(self, name):
        if self.depth: self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if self.depth: self.parts.append(f"&#{name};")

    def handle_startendtag(self, tag, attrs):
        if self.depth: self.parts.append(self.get_starttag_text())


def fetch(target):
    if target.startswith("http"):
        req = urllib.request.Request(target, headers={"User-Agent": "StudentsTime-SEOGate/1.0"})
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    return open(target, encoding="utf-8").read()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python seo_pipeline_check.py <local.html|https://url>")
    target = sys.argv[1]
    raw = fetch(target)
    extractor = ArticleExtractor()
    extractor.feed(raw)
    article = "".join(extractor.parts) if extractor.found else raw
    text = re.sub(r"\s+", " ", re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<[^>]+>", " ", article, flags=re.S | re.I)).strip()
    words = len(re.findall(r"\b[\w’'-]+\b", html.unescape(text)))
    title = re.search(r"<title[^>]*>(.*?)</title>", raw, re.S | re.I)
    h1 = re.findall(r"<h1\b[^>]*>(.*?)</h1>", raw, re.S | re.I)
    h2 = re.findall(r"<h2\b[^>]*>(.*?)</h2>", raw, re.S | re.I)
    canonical = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', raw, re.I)
    if not canonical:
        canonical = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', raw, re.I)
    imgs = re.findall(r"<img\b[^>]*>", article, re.S | re.I)
    missing_alt = [x for x in imgs if not re.search(r'''\balt=["']''', x, re.I)]
    internal = 0
    external = 0
    links = re.findall(r'<a\b[^>]+href=["\']([^"\']+)', article, re.I)
    host = urlparse(target).netloc if target.startswith("http") else "studenttimepk.blogspot.com"
    for link in links:
        if not link.startswith(("http://", "https://", "/")):
            continue
        if link.startswith("/") or host == urlparse(urljoin(target, link)).netloc:
            internal += 1
        elif link.startswith("http"):
            external += 1
    checks = {
        "measurement_scope": "article body" if extractor.found else "HTML fragment or full document (no article container found)",
        "words": words,
        "title": html.unescape(title.group(1).strip()) if title else "MISSING",
        "h1_count": len(h1),
        "h2_count": len(h2),
        "canonical": canonical.group(1) if canonical else "MISSING",
        "images": len(imgs),
        "images_missing_alt": len(missing_alt),
        "internal_links": internal,
        "external_links": external,
        "faq_schema": '"FAQPage"' in raw or "'FAQPage'" in raw,
        "article_schema": '"Article"' in raw or '"BlogPosting"' in raw,
        "noindex": bool(re.search(r"<meta[^>]+robots[^>]+noindex", raw, re.I)),
    }
    print("SEO PIPELINE GATE")
    for key, value in checks.items():
        print(f"{key}: {value}")
    errors = []
    live = target.startswith("http")
    if live and not title: errors.append("missing title")
    if len(h1) > 1: errors.append("multiple H1 tags")
    if live and not canonical: errors.append("missing canonical")
    if checks["noindex"]: errors.append("noindex present")
    if missing_alt: errors.append("image missing alt text")
    if not imgs: errors.append("missing article image")
    if internal < 3: errors.append("fewer than 3 internal links")
    if external < 1: errors.append("no external source links")
    if not checks["article_schema"]: errors.append("missing Article/BlogPosting schema")
    for block in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', raw, re.S | re.I):
        try:
            json.loads(block)
        except json.JSONDecodeError:
            errors.append("invalid JSON-LD")
    print("EDITORIAL REVIEW: verify search intent, sources, image relevance and useful examples; word count is informational")
    print("RESULT:", "PASS" if not errors else "FAIL")
    if errors:
        print("Issues:", "; ".join(errors))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
