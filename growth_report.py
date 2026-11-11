#!/usr/bin/env python3
"""Read-only growth audit: GSC periods, GA4 referrals, live links and Ahrefs CSVs.

Run: python3 growth_report.py [--skip-crawl]
No posts are changed and no paid API is used.
"""
import argparse
import csv
import io
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse, quote, unquote, urlsplit, urlunsplit, parse_qsl, urlencode
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from weekly_report import creds, BLOGS
from seo_pipeline_check import ArticleExtractor

BASE = Path(__file__).resolve().parent
REPORTS = BASE / "reports"
UA = {"User-Agent": "StudentsTime-growth-audit/1.0"}


def clean_url(url):
    p = urlsplit(url)
    return urlunsplit((p.scheme,p.netloc,unquote(p.path),urlencode([(k,v) for k,v in parse_qsl(p.query) if k != "m"]),""))


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.images, self.canonicals, self.robots = [], [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"): self.links.append(a["href"])
        if tag == "img": self.images.append(a)
        if tag == "link" and "canonical" in a.get("rel", "").split(): self.canonicals.append(a.get("href"))
        if tag == "meta" and a.get("name", "").lower() in ("robots", "googlebot"):
            self.robots.append(a.get("content", ""))


def get_url(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(quote(url, safe=":/?&=%#@+;"), headers=UA), timeout=15) as r:
            kind = r.headers.get("Content-Type", "")
            return {"status": r.status, "final": r.url, "type": kind,
                    "html": r.read(2_000_000).decode("utf-8", "replace") if "html" in kind else ""}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": "HTTP response"}
    except Exception as e:
        return {"status": None, "error": type(e).__name__}


def search_rows(sc, site, start, end, dimensions):
    out = []
    offset = 0
    while True:
        rows = sc.searchanalytics().query(siteUrl=site, body={
            "startDate": str(start), "endDate": str(end), "dimensions": dimensions,
            "dataState": "final", "rowLimit": 25000, "startRow": offset,
        }).execute().get("rows", [])
        out.extend(rows)
        if len(rows) < 25000: return out
        offset += len(rows)


def prioritize(rows, previous):
    def combine(items):
        result = {}
        for row in items:
            url = clean_url(row["keys"][0])
            if url not in result:
                result[url] = dict(row, keys=[url])
                continue
            r = result[url]
            total = r["impressions"] + row["impressions"]
            r["position"] = (r["position"]*r["impressions"] + row["position"]*row["impressions"])/total if total else 0
            r["impressions"] = total; r["clicks"] += row["clicks"]
        return list(result.values())
    rows, previous = combine(rows), combine(previous)
    old = {r["keys"][0]: r for r in previous}
    result = []
    for r in rows:
        url = r["keys"][0]
        prior = old.get(url, {})
        imp = r["impressions"]
        pos = r["position"]
        decline = max(0, prior.get("impressions", 0) - imp)
        score = imp * (3 if 8 <= pos <= 20 else 2 if 20 < pos <= 50 else 1) + decline
        reason = "Improve intent and contextual links"
        if 8 <= pos <= 20: reason = "Near page one; review missing answers and title"
        elif pos < 8: reason = "Protect ranking; review snippet and reader experience"
        elif decline: reason = "Investigate lost impressions and query changes"
        result.append(dict(url=url, impressions=imp, clicks=r["clicks"], position=pos,
                           previous_impressions=prior.get("impressions", 0), score=score, action=reason))
    return sorted(result, key=lambda r: -r["score"])[:5]


def ahrefs_csvs():
    folder = BASE / "ahrefs_exports"
    summaries = []
    for path in sorted(folder.glob("*.csv")):
        try:
            data = path.read_bytes()
            text = data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
            dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
            rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
            fields = list(rows[0]) if rows else []
            source = next((f for f in fields if f.lower() in ("referring page url", "referring page", "url_from")), None)
            domains = {urlparse(r.get(source, "")).netloc for r in rows} - {""} if source else set()
            domain_counts = Counter(urlparse(r.get(source, "")).netloc for r in rows) if source else Counter()
            status_field = next((f for f in fields if f.lower() in ("http code", "http status code", "status code")), None)
            nofollow = next((f for f in fields if f.lower() in ("nofollow", "is_nofollow")), None)
            issue = next((f for f in fields if f.lower() in ("issue", "issue name", "name")), None)
            summaries.append({"file": path.name, "rows": len(rows), "columns": fields,
                              "referring_domains_in_export": len(domains) if source else None,
                              "top_source_domains": domain_counts.most_common(10),
                              "nofollow_rows": sum(r.get(nofollow, "").lower() in ("true", "yes", "1") for r in rows) if nofollow else None,
                              "http_status_counts": dict(Counter(r.get(status_field, "") for r in rows)) if status_field else None,
                              "top_issues": Counter(r.get(issue, "") for r in rows).most_common(10) if issue else []})
        except Exception as e:
            summaries.append({"file": path.name, "error": str(e)[:160]})
    return summaries


def public_inventory(site):
    """Read published posts from the paginated public Blogger feed."""
    posts, offset = [], 1
    while True:
        url = site.rstrip('/') + '/feeds/posts/default?' + urlencode({'alt':'json','max-results':100,'start-index':offset})
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as response:
            feed = json.load(response)['feed']
        entries = feed.get('entry', [])
        for entry in entries:
            link = next((v['href'] for v in entry.get('link', []) if v.get('rel') == 'alternate'), None)
            if not link: raise ValueError('Public feed entry has no article URL')
            posts.append({'url':link, 'title':entry['title']['$t'], 'content':entry.get('content',{}).get('$t','')})
        offset += len(entries)
        total = int(feed.get('openSearch$totalResults',{}).get('$t', len(posts)))
        if len(posts) >= total: return posts
        if not entries: raise ValueError('Public feed ended before its reported total')


def audit_posts(blogger, blog_id, site):
    posts, token = [], None
    if blogger is None:
        posts = public_inventory(site)
    while blogger is not None:
        page = blogger.posts().list(blogId=blog_id, status="LIVE", view="ADMIN",
                                    maxResults=100, pageToken=token).execute()
        posts.extend(page.get("items", []))
        token = page.get("nextPageToken")
        if not token: break
    urls = [p["url"] for p in posts]
    print(f"Auditing {len(urls)} published articles on {site}", flush=True)
    normalized_urls = {clean_url(url) for url in urls}
    with ThreadPoolExecutor(max_workers=3) as pool:
        fetched = dict(zip(urls, pool.map(get_url, urls)))
    incoming = Counter()
    audits = []
    checks = {}
    for p in posts:
        url = p["url"]
        response = fetched[url]
        issues = []
        if response["status"] != 200: issues.append(f"page response {response['status']}")
        raw = response.get("html", "")
        full = Tags(); full.feed(raw)
        extract = ArticleExtractor(); extract.feed(raw)
        body = "".join(extract.parts) if extract.found else p.get("content", "")
        tags = Tags(); tags.feed(body)
        if raw and not full.canonicals: issues.append("missing canonical")
        elif raw and [clean_url(u) for u in full.canonicals] != [clean_url(url)]: issues.append("canonical differs or duplicated")
        if response["status"] == 200 and not raw: issues.append("unverified response 200: HTML unavailable")
        if any("noindex" in x.lower() for x in full.robots): issues.append("noindex")
        if not tags.images: issues.append("missing article image")
        if any(not x.get("alt", "").strip() for x in tags.images): issues.append("missing/empty image alt")
        links = set()
        for href in tags.links:
            target = urldefrag(urljoin(url, href))[0]
            if urlparse(target).scheme not in ("https", "http"): continue
            links.add(target)
            normalized = clean_url(target)
            if normalized in normalized_urls and normalized != clean_url(url): incoming[normalized] += 1
            checks[target] = "link"
        for image in tags.images:
            if image.get("src"):
                target = urljoin(url, image["src"])
                if urlparse(target).scheme in ("http", "https"): checks[target] = "image"
        audits.append({"url": url, "title": p["title"], "issues": issues,
                       "page_status": response["status"], "body_observed": bool(raw and extract.found),
                       "links": sorted(links), "images": [urljoin(url, x["src"]) for x in tags.images if x.get("src")]})
    pending = [u for u in checks if u not in fetched]
    print(f"Checking {len(pending)} additional link/image targets on {site}", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        fetched.update(zip(pending, pool.map(get_url, pending)))
    for a in audits:
        a["incoming_article_links"] = incoming[clean_url(a["url"])]
        if not incoming[clean_url(a["url"])]: a["issues"].append("no incoming links from published article bodies")
        for url in a["links"] + a["images"]:
            r = fetched[url]
            if r["status"] in (404, 410): a["issues"].append(f"broken {checks.get(url, 'link')}: {url}")
            elif r["status"] is None or r["status"] >= 400:
                a["issues"].append(f"unverified response {r['status']}: {url}")
            elif url in a["images"] and not r.get("type", "").startswith("image/"):
                a["issues"].append(f"image URL did not return image content: {url}")
    return audits


def md(value):
    return str(value).replace("|", "/").replace("\n", " ")


def inspect_sample(sc, site, urls):
    """Read stored Google index records for a bounded sample, not live tests."""
    rows = []
    for url in list(dict.fromkeys(urls))[:3]:
        if not url.startswith(site):
            continue
        try:
            result = sc.urlInspection().index().inspect(body={
                "inspectionUrl": quote(url, safe=":/?&=%#@+;"), "siteUrl": site,
            }).execute().get("inspectionResult", {}).get("indexStatusResult")
            if not result:
                raise ValueError("No index status returned")
            rows.append({"url": url, **{key: result.get(key) for key in (
                "verdict", "coverageState", "indexingState", "pageFetchState",
                "lastCrawlTime", "googleCanonical", "userCanonical")}})
        except Exception as exc:
            rows.append({"url": url, "error": type(exc).__name__})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-crawl", action="store_true")
    parser.add_argument("--skip-inspection", action="store_true", help="Skip the bounded Google indexing sample")
    args = parser.parse_args()
    today = datetime.now(ZoneInfo("Asia/Karachi")).date()
    end = today - timedelta(days=3)
    start = end - timedelta(days=27)
    prev_end, prev_start = start - timedelta(days=1), start - timedelta(days=28)
    REPORTS.mkdir(exist_ok=True)
    sc = ga = blogger = None
    auth_error = None
    try:
        c = creds()
        sc = build("searchconsole", "v1", credentials=c, cache_discovery=False)
        ga = build("analyticsdata", "v1beta", credentials=c, cache_discovery=False)
        blogger = build("blogger", "v3", credentials=c, cache_discovery=False)
    except Exception:
        auth_error = 'Google authorization unavailable. Reconnect using gsc_auth.py; public article audits remain available.'
    all_data = {"date": str(today), "current_window": [str(start), str(end)],
                "previous_window": [str(prev_start), str(prev_end)], "sites": {}, "ahrefs": ahrefs_csvs()}
    lines = [f"# Growth report — {today}", "", f"Current: {start}–{end}. Previous: {prev_start}–{prev_end}.",
             "Final GSC data requested; last three days excluded for reporting lag. These are separate 28-day periods.", ""]
    for name, site, prop, _, _ in BLOGS:
        print(f"Collecting {name}…", flush=True)
        d = {}; all_data["sites"][name] = d
        lines.extend([f"## {name}", ""])
        try:
            if sc is None: raise RuntimeError(auth_error)
            for label, a, z in (("current", start, end), ("previous", prev_start, prev_end)):
                totals = search_rows(sc, site, a, z, [])
                d[label] = totals[0] if totals else {"impressions": 0, "clicks": 0, "ctr": 0, "position": None}
                d[label + "_pages"] = search_rows(sc, site, a, z, ["page"])
            for metric in ("impressions", "clicks"):
                now, old = d["current"][metric], d["previous"][metric]
                lines.append(f"- {metric.title()}: {now:g}; previous {old:g}; change {now-old:+g}")
            lines.append(f"- CTR: {d['current']['ctr']:.2%}")
            d["priority_pages"] = prioritize(d["current_pages"], d["previous_pages"])
            lines.extend(["", "### Five page priorities", "", "| Page | Impressions | Position | Action |", "|---|---:|---:|---|"])
            for r in d["priority_pages"]:
                lines.append(f"| {md(r['url'])} | {r['impressions']:g} | {r['position']:.1f} | {r['action']} |")
            if not d["priority_pages"]: lines.append("| No page-level data available | — | — | Investigate discovery and indexing |")
            d["queries"] = search_rows(sc, site, start, end, ["query", "page"])
            lines.extend(["", "### Query opportunities (positions 8–50)", "", "| Query | Page | Impressions | Position |", "|---|---|---:|---:|"])
            opp = sorted([r for r in d["queries"] if 8 <= r["position"] <= 50], key=lambda r: -r["impressions"])
            for r in opp[:20]: lines.append(f"| {md(r['keys'][0])} | {md(r['keys'][1])} | {r['impressions']:g} | {r['position']:.1f} |")
            if not opp: lines.append("| None in available data | — | — | — |")
            queries = {}
            for r in d["queries"]: queries.setdefault(r["keys"][0], set()).add(r["keys"][1])
            d["overlap_candidates"] = {q: sorted(p) for q,p in queries.items() if len(p) > 1}
            lines.append(f"\nQueries shown for multiple pages: {len(d['overlap_candidates'])}; review intent before calling these duplicates.")
        except Exception as exc:
            d["gsc_error"] = str(exc)[:250]; lines.append(f"GSC unavailable: {md(d['gsc_error'])}")
        try:
            if ga is None: raise RuntimeError(auth_error)
            response = ga.properties().runReport(property=prop, body={
                "dateRanges": [{"startDate": str(start), "endDate": str(end)}],
                "dimensions": [{"name": "sessionSourceMedium"}, {"name": "landingPagePlusQueryString"}],
                "metrics": [{"name": "sessions"}, {"name": "engagedSessions"}], "limit": 10000}).execute()
            d["referrals"] = [{"source": r["dimensionValues"][0]["value"], "landing": r["dimensionValues"][1]["value"],
                               "sessions": int(r["metricValues"][0]["value"]), "engaged": int(r["metricValues"][1]["value"])}
                              for r in response.get("rows", []) if any(x in r["dimensionValues"][0]["value"].lower() for x in ("dev.to", "medium.com"))]
            lines.extend(["", "### DEV and Medium referrals", ""])
            for r in d["referrals"]: lines.append(f"- {md(r['source'])}: {r['sessions']} sessions / {r['engaged']} engaged; landing {md(r['landing'])}")
            if not d["referrals"]: lines.append("No attributed DEV/Medium sessions in this period; this is not evidence that no links exist.")
        except Exception as exc:
            d["ga_error"] = str(exc)[:250]; lines.append(f"GA4 unavailable: {md(d['ga_error'])}")
        if not args.skip_crawl:
            try:
                blog_id = "8491425780932094856" if "studenttimepk" in site else "6645616362681304579"
                d["audit"] = audit_posts(blogger, blog_id, site)
                d["inventory_source"] = "public Blogger feed" if blogger is None else "Blogger API LIVE inventory"
                lines.extend(["", "### Published article audit", "", "| Page | Incoming article links | Findings |", "|---|---:|---|"])
                for r in d["audit"]:
                    if r["issues"]: lines.append(f"| {md(r['url'])} | {r['incoming_article_links']} | {md('; '.join(r['issues']))} |")
                lines.append(f"\nAudited {len(d['audit'])} published posts. 403/429/timeouts are unverified, not confirmed broken links.")
            except Exception as exc:
                d["crawl_error"] = str(exc)[:250]; lines.append(f"Crawl unavailable: {md(d['crawl_error'])}")
        if not args.skip_inspection:
            if sc is None:
                d["indexing_error"] = auth_error
            else:
                targets = [site]
                targets.extend(r["url"] for r in d.get("priority_pages", [])[:1])
                targets.extend(r["url"] for r in d.get("audit", [])[:1])
                d["indexing"] = inspect_sample(sc, site, targets)
                if any(r.get("error") for r in d["indexing"]):
                    d["indexing_error"] = "One or more indexing inspections were unavailable; earlier findings remain open."
                lines.extend(["", "### Google indexing sample", "",
                    "Stored Google records for up to three selected URLs; not a live URL test or a whole-site indexed-page count.", "",
                    "| URL | Google coverage | Last crawl |", "|---|---|---|"])
                for row in d["indexing"]:
                    lines.append(f"| {md(row['url'])} | {md(row.get('coverageState') or row.get('error'))} | {md(row.get('lastCrawlTime') or 'Unknown')} |")
        lines.append("")
    lines.extend(["## Ahrefs CSV imports", ""])
    if not all_data["ahrefs"]: lines.append("No CSV exports found in ahrefs_exports/. Import pending; no backlink counts inferred.")
    for r in all_data["ahrefs"]: lines.append(f"- {md(r)}")
    lines.extend(["", "## Interpretation", "", "Small impression counts are noisy. Priorities are suggestions for review; this report changes no content. GSC query rows can omit anonymized data, so query sums need not match site totals. Engaged sessions measure engagement, not confirmed human visitors."])
    (REPORTS / "growth_latest.json").write_text(json.dumps(all_data, indent=2, ensure_ascii=False))
    (REPORTS / "growth_latest.md").write_text("\n".join(lines) + "\n")
    print(f"Saved {REPORTS / 'growth_latest.md'}", flush=True)


if __name__ == "__main__": main()
