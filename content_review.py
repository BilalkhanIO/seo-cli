#!/usr/bin/env python3
"""Local writing review using Textstat and Vale; no paid services or text upload.

Run with python3 content_review.py
"""
import argparse
from collections import Counter
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / ".tools/python"))
import textstat

VALE = BASE / ".tools/vale/v3.25.1/vale"


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "table"): self.hidden += 1
        if tag in ("p", "li", "h1", "h2", "h3", "tr"): self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "table"): self.hidden = max(0, self.hidden-1)
        if tag in ("p", "li", "h1", "h2", "h3", "tr"): self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)


def prose(raw, suffix):
    if suffix.lower() in (".html", ".htm"):
        p = VisibleText(); p.feed(raw)
        return "".join(p.parts)
    raw = re.sub(r"```.*?```", "", raw, flags=re.S)
    raw = re.sub(r"^\s*\|.*$", "", raw, flags=re.M)
    raw = re.sub(r"^\*\*(?:Primary keyword|Secondary keywords|Suggested URL|Search description|Image query):.*$", "", raw, flags=re.M)
    raw = re.sub(r"!\[[^]]*\]\([^)]*\)", "", raw)
    raw = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", raw)
    return re.sub(r"^\s*#{1,6}\s*", "", raw, flags=re.M)


def review(path):
    text = unescape(prose(path.read_text(), path.suffix))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    metric_text = " ".join(s if s.endswith((".", "!", "?")) else s + "." for s in sentences)
    long_sentences = [s for s in sentences if len(s.split()) > 30]
    paragraphs = [s.strip() for s in text.split("\n") if len(s.split()) > 80]
    normalized = [re.sub(r"\s+", " ", s).strip().lower() for s in sentences if len(s.split()) >= 12]
    duplicates = [(s, n) for s,n in Counter(normalized).items() if n > 1]
    result = {"file": str(path.relative_to(BASE)), "words": len(re.findall(r"\b[\w’-]+\b", text)),
              "flesch_reading_ease": round(textstat.flesch_reading_ease(metric_text), 1),
              "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(metric_text), 1),
              "long_sentences_over_30_words": long_sentences,
              "long_paragraphs_over_80_words": paragraphs, "repeated_sentences": duplicates}
    if VALE.exists():
        run = subprocess.run([str(VALE), "--config", str(BASE / ".vale.ini"), "--output=JSON", str(path)],
                             capture_output=True, text=True, timeout=30, cwd=BASE)
        try: result["vale"] = json.loads(run.stdout)
        except json.JSONDecodeError: result["vale_error"] = run.stderr[:500] or run.stdout[:500]
    else: result["vale_error"] = "Vale not installed"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    files = [Path(p).resolve() for p in args.files] if args.files else sorted((BASE / "drafts").glob("*.md")) + [BASE / "pillar_free_ai_courses_2026.html"]
    results = [review(p) for p in files]
    date = datetime.now(ZoneInfo("Asia/Karachi")).date()
    report = {"date": str(date), "textstat_version": importlib.metadata.version("textstat"),
              "vale_version": "3.25.1", "files": results}
    folder = BASE / "reports"; folder.mkdir(exist_ok=True)
    (folder / "content_review_latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    lines = [f"# Writing review — {date}", "", "Local Textstat + Vale checks. Readability is an estimate, not a Google ranking score, originality check or fact check. Tables, scripts and draft metadata are excluded; list items are treated as separate segments.",
             "", "| Article | Words | Reading ease | Grade estimate | Long sentences | Repeated sentences |", "|---|---:|---:|---:|---:|---:|"]
    for r in results:
        lines.append(f"| {r['file']} | {r['words']} | {r['flesch_reading_ease']} | {r['flesch_kincaid_grade']} | {len(r['long_sentences_over_30_words'])} | {len(r['repeated_sentences'])} |")
    for r in results:
        lines.extend(["", f"## {r['file']}", ""])
        for s in r["long_sentences_over_30_words"][:5]: lines.append(f"- Review long sentence: {s[:350]}")
        for issues in r.get("vale", {}).values():
            for issue in issues[:10]: lines.append(f"- Vale: {issue.get('Message')} (line {issue.get('Line')})")
        if r.get("vale_error"): lines.append(f"- Tool unavailable: {r['vale_error']}")
    (folder / "content_review_latest.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__": main()
