#!/usr/bin/env python3
"""Keyword research tool: autocomplete harvest -> GSC merge -> cluster -> prioritized list.
Implements the playbook: §1 sources, §10 autocomplete, §2 funnel, keyword clustering.
Usage:
  python keyword_research.py "seed keyword" [--geo us] [--blog st|ll] [--recursive]
Outputs a clustered, prioritized keyword file to keyword_research/<seed>.md
"""
import json, os, re, sys, time, urllib.request, urllib.parse
import argparse
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
QUESTION_PREFIXES = ["how", "what", "why", "when", "which", "can", "is", "are", "best", "free", "top"]
MODIFIERS = ["for", "without", "vs", "near me", "online", "with", str(datetime.now().year)]
STOP = set("a an the for to of in on and or with your you how what why is are can best free top vs".split())

BLOG_SITE = {"st": "https://studenttimepk.blogspot.com/", "ll": "https://learners-link.blogspot.com/"}


def ac(q, geo="us"):
    u = ("https://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl="
         + geo + "&q=" + urllib.parse.quote(q))
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=12))[1]
    except Exception:
        return []


def harvest(seed, geo="us", recursive=False):
    found = set(ac(seed, geo))
    # alphabet soup
    for ch in "abcdefghijklmnopqrstuvwxyz":
        found.update(ac(f"{seed} {ch}", geo)); time.sleep(0.15)
    # question + modifier patterns
    for p in QUESTION_PREFIXES:
        found.update(ac(f"{p} {seed}", geo)); time.sleep(0.15)
    for m in MODIFIERS:
        found.update(ac(f"{seed} {m}", geo)); time.sleep(0.15)
    if recursive:
        seeds2 = sorted(found, key=len)[:8]
        for s in seeds2:
            found.update(ac(s, geo)); time.sleep(0.15)
    return {k.strip().lower() for k in found if k.strip()}


def gsc_queries(blog):
    """Pull recent, complete GSC query/page evidence without losing page mappings."""
    site = BLOG_SITE.get(blog)
    if not site:
        return {}, None
    try:
        from weekly_report import creds
        from googleapiclient.discovery import build
        c = creds()
        sc = build("searchconsole", "v1", credentials=c, cache_discovery=False)
        end = datetime.now(ZoneInfo("Asia/Karachi")).date() - timedelta(days=3)
        start = end - timedelta(days=89)
        rows, offset, page_size = [], 0, 25_000
        while True:
            batch = sc.searchanalytics().query(siteUrl=site, body={
                "startDate": str(start), "endDate": str(end),
                "dimensions": ["query", "page"], "dataState": "final",
                "rowLimit": page_size, "startRow": offset,
            }).execute().get("rows", [])
            rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += len(batch)
        grouped = defaultdict(lambda: {"impressions": 0, "clicks": 0, "weighted_position": 0, "pages": set()})
        for row in rows:
            if len(row.get("keys", [])) < 2:
                continue
            query, page = row["keys"][0].strip().lower(), row["keys"][1]
            parsed = urllib.parse.urlsplit(page)
            page = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path,
                urllib.parse.urlencode([(k, v) for k, v in urllib.parse.parse_qsl(parsed.query) if k != "m"]), ""))
            if not query:
                continue
            item = grouped[query]
            impressions = int(row.get("impressions", 0))
            item["impressions"] += impressions
            item["clicks"] += int(row.get("clicks", 0))
            item["weighted_position"] += float(row.get("position", 0)) * impressions
            item["pages"].add(page)
        result = {
            query: {"impressions": item["impressions"], "clicks": item["clicks"],
                    "position": round(item["weighted_position"] / item["impressions"], 1) if item["impressions"] else None,
                    "pages": sorted(item["pages"])}
            for query, item in grouped.items()
        }
        return result, f"{start} to {end} (90 complete days)"
    except Exception as e:
        print("  (GSC skipped:", str(e)[:50], ")")
        return {}, None


def trends_signal(seed, geo="US"):
    """Google Trends: relative interest, trend direction, related queries and regions.
    Returns a dict; degrades gracefully on rate-limit/errors."""
    out = {"top": [], "rising": [], "regions": [], "avg": None, "direction": None}
    try:
        from pytrends.request import TrendReq
        py = TrendReq(hl="en-US", tz=0)
        py.build_payload([seed], geo=geo.upper(), timeframe="today 12-m")
        # interest over time -> average + direction
        try:
            iot = py.interest_over_time()
            if iot is not None and not iot.empty and seed in iot:
                vals = iot[seed].tolist()
                out["avg"] = round(sum(vals) / len(vals), 1)
                half = len(vals) // 2
                first, second = sum(vals[:half]) or 1, sum(vals[half:])
                out["direction"] = "rising" if second > first * 1.15 else ("falling" if second < first * 0.85 else "steady")
        except Exception:
            pass
        # related queries
        try:
            rel = py.related_queries().get(seed, {}) or {}
            if rel.get("top") is not None:
                out["top"] = [(r["query"], int(r["value"])) for _, r in rel["top"].head(10).iterrows()]
            if rel.get("rising") is not None:
                out["rising"] = [(r["query"], r["value"]) for _, r in rel["rising"].head(10).iterrows()]
        except Exception:
            pass
        # Geographic interest can resolve to states/regions when geo is a country.
        try:
            reg = py.interest_by_region(resolution="COUNTRY", inc_low_vol=False)
            if reg is not None and not reg.empty:
                top = reg[seed].sort_values(ascending=False).head(6)
                out["regions"] = [(c, int(v)) for c, v in top.items() if v > 0]
        except Exception:
            pass
    except Exception as e:
        out["error"] = str(e)[:60]
    return out


def cluster(keywords):
    """Group by the most significant shared token (simple, effective clustering)."""
    clusters = defaultdict(list)
    for kw in keywords:
        toks = [w for w in re.findall(r"[a-z0-9]+", kw) if w not in STOP and len(w) > 2]
        key = None
        # prefer a 2-word head if present, else the longest token
        if len(toks) >= 2:
            key = " ".join(toks[:2])
        elif toks:
            key = toks[0]
        else:
            key = "other"
        clusters[key].append(kw)
    # merge tiny clusters into "misc"
    merged = defaultdict(list)
    for k, v in clusters.items():
        merged[k if len(v) >= 2 else "misc (long-tail)"].extend(v)
    return merged


def related_to_seed(query, seed):
    """Keep only topical GSC queries; do not mix unrelated site queries into a seed report."""
    def tokens(value):
        out = []
        for token in re.findall(r"[a-z0-9]+", value.lower()):
            if token.endswith("ies") and len(token) > 4:
                token = token[:-3] + "y"
            elif token.endswith("s") and len(token) > 4:
                token = token[:-1]
            out.append(token)
        return set(out)
    core = tokens(seed) - STOP - {"course", "class", "training", "free", "top", "best", "guide",
                                  "online", "beginner", "beginners", "certificate", "certification", "credential"}
    query_tokens = tokens(query)
    shared = core & query_tokens
    topic_signals = {"course", "class", "training", "certificate", "certification", "credential",
                     "coursera", "blueprint", "exam", "price", "cost", "free", "learn", "marketing",
                     "advertising", "social", "media"}
    return len(shared) >= 2 or bool(shared and query_tokens & topic_signals)


def focused_clusters(keywords, seed):
    """Group a seed's suggestions by core phrase and closely related course terms."""
    core = {w for w in re.findall(r"[a-z0-9]+", seed.lower()) if w not in STOP}
    groups = defaultdict(list)
    for keyword in keywords:
        words = set(re.findall(r"[a-z0-9]+", keyword.lower()))
        overlap = len(core & words)
        if overlap >= min(2, len(core)):
            key = f"Core topic: {seed}"
        elif overlap:
            key = "Related course and credential variants"
        else:
            key = "Related long-tail"
        groups[key].append(keyword)
    return groups


def intent(kw):
    if re.search(r"\b(buy|price|cheap|near me|sign up|download|discount)\b", kw): return "Transactional"
    if re.search(r"\b(best|top|review|vs|comparison|cheapest)\b", kw): return "Commercial"
    if re.search(r"\b(how|what|why|guide|tutorial|meaning|is|are|can)\b", kw): return "Informational"
    return "Informational"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seed", help="Topic or keyword to research")
    parser.add_argument("--geo", default="us", help="Two-letter autocomplete/Trends region")
    parser.add_argument("--blog", choices=("st", "ll"), help="Merge this site's GSC evidence and project context")
    parser.add_argument("--recursive", action="store_true")
    args = parser.parse_args()
    seed, geo, blog, recursive = args.seed, args.geo, args.blog, args.recursive

    print(f"Harvesting autocomplete for '{seed}' (geo={geo})...")
    kws = harvest(seed, geo, recursive)
    print(f"  {len(kws)} unique phrases from autocomplete")
    gsc_all, gsc_window = gsc_queries(blog) if blog else ({}, None)
    gsc = {query: metrics for query, metrics in gsc_all.items() if related_to_seed(query, seed)}
    if gsc:
        print(f"  + {len(gsc)} seed-related GSC queries merged ({len(gsc_all)} total visible site queries checked)")
        kws.update(gsc.keys())
    print("Pulling Google Trends (demand + rising + geo)...")
    tr = trends_signal(seed, geo)
    trend_demand = {q.lower(): v for q, v in tr.get("top", [])}
    kws.update(trend_demand.keys())
    kws.update(q.lower() for q, _ in tr.get("rising", []))
    if tr.get("error"):
        print("  (Trends limited:", tr["error"], ")")
    else:
        print(f"  Trends: {len(tr.get('top', []))} top + {len(tr.get('rising', []))} rising related")
    clusters = focused_clusters(kws, seed)

    os.makedirs("/home/kwikcoders/seo/keyword_research", exist_ok=True)
    safe = re.sub(r"[^a-z0-9]+", "-", seed.lower()).strip("-")
    path = f"/home/kwikcoders/seo/keyword_research/{safe}.md"
    lines = [f"# Keyword research: {seed}", f"_geo={geo} · {len(kws)} phrases · {len(clusters)} clusters_", "",
             "Autocomplete phrases are suggestions, not search-volume measurements. GSC impressions are observed visibility for this property; Trends values are relative indices.", ""]
    if blog:
        from project_context import render_site_context
        lines.extend(["## Project context", "", render_site_context(blog), ""])
    if gsc_window:
        lines.extend([f"Search Console evidence: {gsc_window}. {len(gsc)} seed-related visible queries retained from {len(gsc_all)} visible site queries; excluded phrases do not match this seed. Impressions are observations, not search-volume estimates.", ""])
    # Google Trends section (demand signal)
    if not tr.get("error") and (tr.get("avg") is not None or tr.get("top") or tr.get("rising") or tr.get("regions")):
        lines.append("## 📈 Google Trends demand")
        if tr.get("avg") is not None:
            lines.append(f"- Interest (0-100 avg, 12mo): **{tr['avg']}** · trend: **{tr.get('direction','?')}**")
        if tr.get("top"):
            lines.append("- **Top related (by demand):** " + "; ".join(f"{q} ({v})" for q, v in tr["top"][:8]))
        if tr.get("rising"):
            lines.append("- **🔥 Rising/breakout:** " + "; ".join(f"{q} (+{v})" for q, v in tr["rising"][:8]))
        if tr.get("regions"):
            lines.append("- **Relative regional interest (0–100):** " + ", ".join(f"{c} ({v})" for c, v in tr["regions"]))
        lines.append("")
    # sort clusters by size
    for cname, members in sorted(clusters.items(), key=lambda x: -len(x[1])):
        lines.append(f"## {cname} ({len(members)})")
        for kw in sorted(set(members)):
            tag = intent(kw)
            g = gsc.get(kw)
            gnote = f"  **[GSC {g['impressions']}i, pos {g['position']}, {len(g['pages'])} page(s)]**" if g else ""
            tnote = f"  **[Trends {trend_demand[kw]}]**" if kw in trend_demand else ""
            lines.append(f"- {kw} — _{tag}_{gnote}{tnote}")
        lines.append("")
    open(path, "w").write("\n".join(lines))
    # console summary
    print(f"\n{'='*46}\nTop clusters for '{seed}':")
    for cname, members in sorted(clusters.items(), key=lambda x: -len(x[1]))[:8]:
        sample = sorted(set(members))[:3]
        print(f"  [{cname}] ({len(members)}): {', '.join(sample)}")
    gsc_kw = sorted((k for k in kws if k in gsc),
                    key=lambda k: (-gsc[k]["impressions"], gsc[k]["position"] or 999, k))
    if gsc_kw:
        print(f"\n  OBSERVED GSC QUERY SIGNALS: {', '.join(gsc_kw[:5])}")
    if not tr.get("error") and (tr.get("avg") is not None or tr.get("top") or tr.get("rising") or tr.get("regions")):
        if tr.get("avg") is not None:
            print(f"\n  📈 TRENDS: relative interest {tr['avg']}/100 ({tr.get('direction') or 'direction unavailable'})")
        else:
            print("\n  📈 TRENDS: no overall interest or related-query signal was available")
        if tr.get("top"):
            print("     top demand: " + ", ".join(f"{q} ({v})" for q, v in tr["top"][:4]))
        if tr.get("rising"):
            print("     🔥 rising: " + ", ".join(f"{q}" for q, v in tr["rising"][:4]))
        if tr.get("regions"):
            print("     relative top regions: " + ", ".join(f"{c}" for c, v in tr["regions"][:5]))
    print(f"\n[saved {len(kws)} keywords to {path}]")


if __name__ == "__main__":
    main()
