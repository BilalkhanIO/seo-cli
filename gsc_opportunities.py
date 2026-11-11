#!/usr/bin/env python3
"""Create a Search Console opportunity report for queries/pages in positions 8-20."""
import datetime
import json
import os
from collections import defaultdict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE = "/home/kwikcoders/seo"
SITE = "https://studenttimepk.blogspot.com/"
OUT = os.path.join(BASE, "reports", "gsc_opportunities_latest.md")


def service():
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    c.refresh(Request())
    return build("searchconsole", "v1", credentials=c, cache_discovery=False)


def main():
    end = datetime.date.today()
    start = end - datetime.timedelta(days=90)
    sc = service()
    query = sc.searchanalytics().query(siteUrl=SITE, body={
        "startDate": str(start), "endDate": str(end),
        "dimensions": ["query", "page"], "rowLimit": 25000,
        "dataState": "all",
    }).execute().get("rows", [])
    grouped = defaultdict(lambda: {"impressions": 0, "clicks": 0, "positions": [], "pages": set()})
    for row in query:
        pos = float(row.get("position", 99))
        if 8 <= pos <= 20:
            q, page = row.get("keys", ["", ""])
            d = grouped[q]
            d["impressions"] += row.get("impressions", 0)
            d["clicks"] += row.get("clicks", 0)
            d["positions"].append(pos)
            d["pages"].add(page)
    rows = sorted(grouped.items(), key=lambda x: (-x[1]["impressions"], sum(x[1]["positions"]) / len(x[1]["positions"])))
    lines = [f"# Students Time GSC Opportunities — {end}", "", f"Window: {start} to {end} (90 days)", "",
             "Queries ranking positions 8–20 are prioritized because they are the closest opportunities for additional impressions and clicks.", "",
             "| Query | Impressions | Clicks | Avg position | Ranking page |", "|---|---:|---:|---:|---|"]
    for q, d in rows[:50]:
        pos = sum(d["positions"]) / len(d["positions"])
        page = sorted(d["pages"])[0]
        lines.append(f"| {q.replace('|', '/') } | {d['impressions']} | {d['clicks']} | {pos:.1f} | {page} |")
    if not rows:
        lines.append("| No current positions 8–20 | 0 | 0 | — | — |")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nSaved to {OUT}")


if __name__ == "__main__":
    main()
