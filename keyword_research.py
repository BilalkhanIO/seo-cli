#!/usr/bin/env python3
"""Keyword research tool: autocomplete harvest -> GSC merge -> cluster -> prioritized list.
Implements the playbook: §1 sources, §10 autocomplete, §2 funnel, keyword clustering.
Usage:
  python keyword_research.py "seed keyword" [--geo us] [--blog st|ll] [--recursive]
Outputs a clustered, prioritized keyword file to keyword_research/<seed>.md
"""
import json, os, re, sys, time, urllib.request, urllib.parse
from collections import defaultdict

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
QUESTION_PREFIXES = ["how", "what", "why", "when", "which", "can", "is", "are", "best", "free", "top"]
MODIFIERS = ["for", "without", "vs", "near me", "online", "with", "2026"]
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
    """Pull real queries the blog already gets impressions for (the best source)."""
    site = BLOG_SITE.get(blog)
    if not site:
        return {}
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
        c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                        token_uri=t["token_uri"], client_id=t["client_id"],
                        client_secret=t["client_secret"], scopes=t.get("scopes"))
        c.refresh(Request())
        sc = build("searchconsole", "v1", credentials=c, cache_discovery=False)
        rows = sc.searchanalytics().query(siteUrl=site, body={
            "startDate": "2026-06-21", "endDate": "2026-09-19",
            "dimensions": ["query"], "rowLimit": 200}).execute().get("rows", [])
        return {r["keys"][0].lower(): (int(r["impressions"]), round(r["position"], 1)) for r in rows}
    except Exception as e:
        print("  (GSC skipped:", str(e)[:50], ")")
        return {}


def trends_signal(seed, geo="US"):
    """Google Trends: relative interest, trend direction, top/rising related, top countries.
    Returns a dict; degrades gracefully on rate-limit/errors."""
    out = {"top": [], "rising": [], "countries": [], "avg": None, "direction": None}
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
        # regional interest (which countries want it — key for US/UK/CA targeting)
        try:
            reg = py.interest_by_region(resolution="COUNTRY", inc_low_vol=False)
            if reg is not None and not reg.empty:
                top = reg[seed].sort_values(ascending=False).head(6)
                out["countries"] = [(c, int(v)) for c, v in top.items() if v > 0]
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


def intent(kw):
    if re.search(r"\b(buy|price|cheap|near me|sign up|download|discount)\b", kw): return "Transactional"
    if re.search(r"\b(best|top|review|vs|comparison|cheapest)\b", kw): return "Commercial"
    if re.search(r"\b(how|what|why|guide|tutorial|meaning|is|are|can)\b", kw): return "Informational"
    return "Informational"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print('Usage: python keyword_research.py "seed keyword" [--geo us] [--blog st|ll] [--recursive]')
        return
    seed = args[0]
    geo = next((a.split("=")[1] for a in sys.argv if a.startswith("--geo=")), "us")
    blog = next((a.split("=")[1] for a in sys.argv if a.startswith("--blog=")), None)
    recursive = "--recursive" in sys.argv

    print(f"Harvesting autocomplete for '{seed}' (geo={geo})...")
    kws = harvest(seed, geo, recursive)
    print(f"  {len(kws)} unique phrases from autocomplete")
    gsc = gsc_queries(blog) if blog else {}
    if gsc:
        print(f"  + {len(gsc)} real GSC queries merged")
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
    clusters = cluster(kws)

    os.makedirs("/home/kwikcoders/seo/keyword_research", exist_ok=True)
    safe = re.sub(r"[^a-z0-9]+", "-", seed.lower()).strip("-")
    path = f"/home/kwikcoders/seo/keyword_research/{safe}.md"
    lines = [f"# Keyword research: {seed}", f"_geo={geo} · {len(kws)} keywords · {len(clusters)} clusters_", ""]
    # Google Trends section (demand signal)
    if not tr.get("error"):
        lines.append("## 📈 Google Trends demand")
        if tr.get("avg") is not None:
            lines.append(f"- Interest (0-100 avg, 12mo): **{tr['avg']}** · trend: **{tr.get('direction','?')}**")
        if tr.get("top"):
            lines.append("- **Top related (by demand):** " + "; ".join(f"{q} ({v})" for q, v in tr["top"][:8]))
        if tr.get("rising"):
            lines.append("- **🔥 Rising/breakout:** " + "; ".join(f"{q} (+{v})" for q, v in tr["rising"][:8]))
        if tr.get("countries"):
            lines.append("- **Top countries:** " + ", ".join(f"{c} ({v})" for c, v in tr["countries"]))
        lines.append("")
    # sort clusters by size
    for cname, members in sorted(clusters.items(), key=lambda x: -len(x[1])):
        lines.append(f"## {cname} ({len(members)})")
        for kw in sorted(set(members)):
            tag = intent(kw)
            g = gsc.get(kw)
            gnote = f"  **[GSC {g[0]}i, pos {g[1]}]**" if g else ""
            tnote = f"  **[Trends {trend_demand[kw]}]**" if kw in trend_demand else ""
            lines.append(f"- {kw} — _{tag}_{gnote}{tnote}")
        lines.append("")
    open(path, "w").write("\n".join(lines))
    # console summary
    print(f"\n{'='*46}\nTop clusters for '{seed}':")
    for cname, members in sorted(clusters.items(), key=lambda x: -len(x[1]))[:8]:
        sample = sorted(set(members))[:3]
        print(f"  [{cname}] ({len(members)}): {', '.join(sample)}")
    gsc_kw = [k for k in kws if k in gsc]
    if gsc_kw:
        print(f"\n  PRIORITY (already ranking — GSC): {', '.join(sorted(gsc_kw, key=lambda k: -gsc[k][0])[:5])}")
    if not tr.get("error"):
        print(f"\n  📈 TRENDS: interest {tr.get('avg','?')}/100 ({tr.get('direction','?')})")
        if tr.get("top"):
            print("     top demand: " + ", ".join(f"{q} ({v})" for q, v in tr["top"][:4]))
        if tr.get("rising"):
            print("     🔥 rising: " + ", ".join(f"{q}" for q, v in tr["rising"][:4]))
        if tr.get("countries"):
            print("     top geo: " + ", ".join(f"{c}" for c, v in tr["countries"][:5]))
    print(f"\n[saved {len(kws)} keywords to {path}]")


if __name__ == "__main__":
    main()
