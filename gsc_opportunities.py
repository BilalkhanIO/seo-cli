#!/usr/bin/env python3
"""Build a free, Search Console query and page performance report.

Uses complete periods and separate query-only, query+page, and page-only views.
Search Console may omit anonymized queries, so query coverage is partial.
"""
import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build
from weekly_report import BLOGS, creds

BASE = Path(__file__).resolve().parent
REPORTS = BASE / "reports"
ROW_LIMIT = 25_000
WINDOW_DAYS = 90


def windows(today=None, days=WINDOW_DAYS):
    today = today or datetime.now(ZoneInfo("Asia/Karachi")).date()
    end = today - timedelta(days=3)
    start = end - timedelta(days=days - 1)
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    return (start, end), (previous_start, previous_end)


def clean_url(url):
    p = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k != "m"]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(query), ""))


def fetch_query_pages(sc, site, start, end):
    rows, offset = [], 0
    while True:
        page = sc.searchanalytics().query(siteUrl=site, body={
            "startDate": str(start), "endDate": str(end),
            "dimensions": ["query", "page"], "dataState": "final",
            "rowLimit": ROW_LIMIT, "startRow": offset,
        }).execute().get("rows", [])
        rows.extend(page)
        if len(page) < ROW_LIMIT:
            return rows
        offset += len(page)


def fetch_queries(sc, site, start, end):
    """Fetch query-only rows; GSC may expose a different subset with page dimension."""
    rows, offset = [], 0
    while True:
        page = sc.searchanalytics().query(siteUrl=site, body={
            "startDate": str(start), "endDate": str(end),
            "dimensions": ["query"], "dataState": "final",
            "rowLimit": ROW_LIMIT, "startRow": offset,
        }).execute().get("rows", [])
        rows.extend(page)
        if len(page) < ROW_LIMIT:
            return rows
        offset += len(page)


def fetch_pages(sc, site, start, end):
    """Fetch page-only totals, which include impressions with hidden query details."""
    rows, offset = [], 0
    while True:
        page = sc.searchanalytics().query(siteUrl=site, body={
            "startDate": str(start), "endDate": str(end),
            "dimensions": ["page"], "dataState": "final",
            "rowLimit": ROW_LIMIT, "startRow": offset,
        }).execute().get("rows", [])
        rows.extend(page)
        if len(page) < ROW_LIMIT:
            return rows
        offset += len(page)


def aggregate_queries(rows):
    result = {}
    for row in rows:
        keys = row.get("keys", [])
        query = keys[0].strip() if keys else ""
        if not query:
            continue
        item = result.setdefault(query, {"impressions": 0, "clicks": 0, "position_weight": 0})
        impressions = int(row.get("impressions", 0))
        item["impressions"] += impressions
        item["clicks"] += int(row.get("clicks", 0))
        item["position_weight"] += float(row.get("position", 0)) * impressions
    for item in result.values():
        item["position"] = item.pop("position_weight") / item["impressions"] if item["impressions"] else None
    return result


def aggregate_pages(rows):
    result = {}
    for row in rows:
        keys = row.get("keys", [])
        url = clean_url(keys[0]) if keys else ""
        if not url:
            continue
        item = result.setdefault(url, {"impressions": 0, "clicks": 0, "position_weight": 0})
        impressions = int(row.get("impressions", 0))
        item["impressions"] += impressions
        item["clicks"] += int(row.get("clicks", 0))
        item["position_weight"] += float(row.get("position", 0)) * impressions
    for item in result.values():
        item["position"] = item.pop("position_weight") / item["impressions"] if item["impressions"] else None
    return result


def aggregate(rows):
    queries = {}
    page_clusters = {}
    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 2:
            continue
        query, raw_page = keys[0].strip(), clean_url(keys[1])
        if not query or not raw_page:
            continue
        impressions = int(row.get("impressions", 0))
        clicks = int(row.get("clicks", 0))
        position = float(row.get("position", 0))
        q = queries.setdefault(query, {"impressions": 0, "clicks": 0, "position_weight": 0, "pages": {}})
        q["impressions"] += impressions
        q["clicks"] += clicks
        q["position_weight"] += position * impressions
        page_metrics = q["pages"].setdefault(raw_page, {"impressions": 0, "clicks": 0, "position_weight": 0})
        page_metrics["impressions"] += impressions
        page_metrics["clicks"] += clicks
        page_metrics["position_weight"] += position * impressions
        cluster = page_clusters.setdefault(raw_page, {"impressions": 0, "clicks": 0, "queries": {}})
        cluster["impressions"] += impressions
        cluster["clicks"] += clicks
        cluster["queries"][query] = cluster["queries"].get(query, 0) + impressions

    for item in queries.values():
        item["position"] = item.pop("position_weight") / item["impressions"] if item["impressions"] else None
        item["pages"] = [
            {"url": url, "impressions": values["impressions"], "clicks": values["clicks"],
             "position": values["position_weight"] / values["impressions"] if values["impressions"] else None}
            for url, values in sorted(item["pages"].items(), key=lambda pair: -pair[1]["impressions"])
        ]
    return queries, page_clusters


def intent(query):
    q = query.lower()
    if re.search(r"\b(login|sign in|official site|website)\b", q):
        return "Navigational"
    if re.search(r"\b(price|cost|buy|subscribe|enroll|sign up|apply|login|download)\b", q):
        return "Transactional"
    if re.search(r"\b(best|top|review|compare|comparison|vs|alternative)\b", q):
        return "Commercial"
    if re.search(r"\b(how|what|why|when|which|who|where|can|does|do|is|are|guide|tutorial|course|courses|certificate|certification|training|learn|learning|requirements|resources)\b", q):
        return "Informational"
    return "Unclassified"


def opportunity(position):
    if position is None:
        return "Position unavailable"
    if 8 <= position <= 20:
        return "Near page one; review the query match and snippet"
    if 20 < position <= 50:
        return "Review page relevance before editing"
    if position < 8:
        return "Protect; improve snippet only with enough impressions"
    return "Early signal; do not prioritize from position alone"


def report_site(sc, blog, current_window, previous_window):
    name, site, prop, _, _ = blog
    current = aggregate_queries(fetch_queries(sc, site, *current_window))
    previous = aggregate_queries(fetch_queries(sc, site, *previous_window))
    current_page_totals = aggregate_pages(fetch_pages(sc, site, *current_window))
    previous_page_totals = aggregate_pages(fetch_pages(sc, site, *previous_window))
    page_query_metrics, current_clusters = aggregate(fetch_query_pages(sc, site, *current_window))
    previous_page_queries, previous_clusters = aggregate(fetch_query_pages(sc, site, *previous_window))
    all_queries = []
    for query in set(current) | set(previous):
        now = current.get(query, {"impressions": 0, "clicks": 0, "position": None})
        before = previous.get(query, {"impressions": 0, "clicks": 0, "position": None})
        page_details = page_query_metrics.get(query, {}).get("pages", [])
        position_delta = None
        if now["position"] is not None and before["position"] is not None:
            position_delta = now["position"] - before["position"]
        all_queries.append({
            "query": query, "intent": intent(query),
            "impressions": now["impressions"], "clicks": now["clicks"],
            "position": now["position"], "previous_impressions": before["impressions"],
            "impression_change": now["impressions"] - before["impressions"],
            "previous_position": before["position"], "position_change": position_delta,
            "pages": page_details,
        })
    all_queries.sort(key=lambda x: (-x["impressions"], x["position"] or 999, x["query"]))
    overlaps = [q for q in all_queries if len(q["pages"]) > 1 and q["impressions"]]
    page_rows = []
    for url, totals in sorted(current_page_totals.items(), key=lambda pair: -pair[1]["impressions"]):
        query_data = current_clusters.get(url, {"impressions": 0, "clicks": 0, "queries": {}})
        page_rows.append({"page": url, "impressions": totals["impressions"], "clicks": totals["clicks"],
                          "position": totals["position"],
                          "visible_query_page_impressions": query_data["impressions"],
                          "visible_query_rows": len(query_data["queries"]),
                          "query_detail_gap": max(0, totals["impressions"] - query_data["impressions"]),
                          "queries": sorted(query_data["queries"].items(), key=lambda pair: -pair[1])})
    return {"name": name, "site": site, "property": prop,
            "current_query_only_count": len(current),
            "current_query_page_query_count": len(page_query_metrics),
            "current_query_page_count": len(current_clusters),
            "previous_query_only_count": len(previous),
            "previous_query_page_query_count": len(previous_page_queries),
            "previous_query_page_count": len(previous_clusters),
            "current_page_count": len(current_page_totals),
            "previous_page_count": len(previous_page_totals),
            "current_queries": all_queries, "overlap_candidates": overlaps,
            "page_clusters": page_rows}


def md(value):
    return str(value).replace("|", "/").replace("\n", " ")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blog", choices=("st", "ll", "both"), default="both")
    parser.add_argument("--days", type=int, choices=(28, 90, 180), default=90)
    args = parser.parse_args()
    current_window, previous_window = windows(days=args.days)
    aliases = {"st": "Students Time", "ll": "Learner's Link"}
    selected_name = aliases.get(args.blog)
    blogs = [b for b in BLOGS if selected_name is None or b[0] == selected_name]
    sc = build("searchconsole", "v1", credentials=creds(), cache_discovery=False)
    data = {"created_at": datetime.now(ZoneInfo("Asia/Karachi")).isoformat(),
            "current_window": [str(x) for x in current_window],
            "previous_window": [str(x) for x in previous_window],
            "note": "Observed Search Console queries only; anonymized queries may be omitted. No search-volume estimates are inferred.",
            "sites": [report_site(sc, blog, current_window, previous_window) for blog in blogs]}

    lines = [f"# GSC keyword and page clusters — {data['created_at'][:10]}", "",
             f"Current: {current_window[0]}–{current_window[1]}. Previous: {previous_window[0]}–{previous_window[1]} ({args.days} complete days each).",
             "", data["note"],
             "Query opportunity tables use the query-only report. Page totals use a separate page-only report; query examples and page mappings come from query+page data. Search Console may omit anonymized queries and dimensional exports can expose different subsets. A page's total impressions can exceed the sum of its visible queries. Treat query rows as partial observations, not a complete inventory.", ""]
    for site_data in data["sites"]:
        lines.extend([f"## {site_data['name']}", ""])
        lines.extend(["### Query opportunities", "", f"Query-only: {site_data['current_query_only_count']} visible queries current / {site_data['previous_query_only_count']} previous. Query+page: {site_data['current_query_page_query_count']} visible queries across {site_data['current_query_page_count']} pages current / {site_data['previous_query_page_query_count']} queries across {site_data['previous_query_page_count']} pages previous. Page-only: {site_data['current_page_count']} pages current / {site_data['previous_page_count']} previous.", "", "| Query | Intent | Impressions | Change | Clicks | Position | Position Δ | Page(s) where reported | Review cue |", "|---|---|---:|---:|---:|---:|---:|---|---|"])
        shown = [q for q in site_data["current_queries"] if q["impressions"]]
        for q in shown[:100]:
            pages = "; ".join(p["url"] for p in q["pages"][:3]) or "Not available in query+page rows"
            position = f"{q['position']:.1f}" if q["position"] is not None else "—"
            pos_delta = f"{q['position_change']:+.1f}" if q["position_change"] is not None else "—"
            lines.append(f"| {md(q['query'])} | {q['intent']} | {q['impressions']} | {q['impression_change']:+} | {q['clicks']} | {position} | {pos_delta} | {md(pages)} | {opportunity(q['position'])} |")
        if not shown:
            lines.append("| No query rows in this window | — | 0 | — | 0 | — | — | — | Verify GSC property and reporting lag; query data may be sparse. |")
        lines.extend(["", "### Page totals and visible query clusters", "", "Page impressions/clicks are from the page-only export. The listed queries are only those returned by the query+page export; the difference is query activity without visible query attribution, not a list of known missing terms.", ""])
        for cluster in site_data["page_clusters"][:20]:
            lines.append(f"#### {md(cluster['page'])}")
            position = f"{cluster['position']:.1f}" if cluster["position"] is not None else "unavailable"
            lines.append(f"{cluster['impressions']} page impressions · {cluster['clicks']} page clicks · avg. position {position} · {cluster['visible_query_page_impressions']} impressions attributed to visible queries · {cluster['query_detail_gap']} without visible query attribution")
            for query, impressions in cluster["queries"][:12]:
                lines.append(f"- {md(query)} ({impressions} impressions; {intent(query).lower()})")
            lines.append("")
        lines.extend(["### Multi-page query review", "", "These visible query+page rows appeared on multiple URLs; inspect page intent before calling them cannibalization. This cannot rule out hidden overlaps.", ""])
        if site_data["overlap_candidates"]:
            for q in site_data["overlap_candidates"][:30]:
                lines.append(f"- **{md(q['query'])}** — {q['impressions']} impressions across " + ", ".join(p["url"] for p in q["pages"]))
        else:
            lines.append("No multi-page matches in the visible query+page rows. This does not rule out overlaps hidden by Search Console's reporting limits.")
        lines.append("")

    REPORTS.mkdir(exist_ok=True)
    json_path = REPORTS / "gsc_opportunities_latest.json"
    md_path = REPORTS / "gsc_opportunities_latest.md"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    md_path.write_text("\n".join(lines).rstrip() + "\n")
    print("\n".join(lines))
    print(f"\nSaved {md_path} and {json_path}")


if __name__ == "__main__":
    main()
