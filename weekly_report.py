#!/usr/bin/env python3
"""Weekly SEO tracking report for both blogs.
Pulls the CLEAN signals — GSC organic impressions/clicks + GA4 ENGAGED sessions
(filters out 0-second bots) — appends to history, computes week-over-week deltas,
and writes a dated markdown report to reports/. Run weekly (cron) or on demand.
Usage: python weekly_report.py
"""
import json, os, datetime
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE = "/home/kwikcoders/seo"
REPORTS = os.path.join(BASE, "reports")
HIST = os.path.join(BASE, "tracking_history.json")
os.makedirs(REPORTS, exist_ok=True)

BLOGS = [
    ("Students Time", "https://studenttimepk.blogspot.com/", "properties/406899493",
     "accounts/pub-4779738061304824", "studenttimepk.blogspot.com"),
    ("Learner's Link", "https://learners-link.blogspot.com/", "properties/545155339",
     "accounts/pub-4779738061304824", "learners-link.blogspot.com"),
]


def creds():
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    c.refresh(Request())
    return c


def daterange(days):
    end = datetime.date.today()
    return str(end - datetime.timedelta(days=days)), str(end)


def collect():
    c = creds()
    sc = build("searchconsole", "v1", credentials=c, cache_discovery=False)
    ga = build("analyticsdata", "v1beta", credentials=c, cache_discovery=False)
    ad = build("adsense", "v2", credentials=c, cache_discovery=False)
    s28, e28 = daterange(28)
    out = {}
    for name, site, prop, acct, domain in BLOGS:
        d = {}
        # homepage indexing status (the ST redirect-error watch)
        try:
            r = sc.urlInspection().index().inspect(body={"inspectionUrl": site, "siteUrl": site}).execute()
            idx = (r.get("inspectionResult") or {}).get("indexStatusResult") or {}
            d["home_coverage"] = idx.get("coverageState", "?")
            d["home_lastcrawl"] = (idx.get("lastCrawlTime") or "never")[:10]
        except Exception as ex:
            d["home_coverage"] = "inspect err " + str(ex)[:30]
        # sitemap indexed count
        try:
            sm = sc.sitemaps().list(siteUrl=site).execute().get("sitemap", [])
            ct = (sm[0].get("contents", [{}])[0] if sm else {})
            d["sm_submitted"] = ct.get("submitted", "?"); d["sm_indexed"] = ct.get("indexed", "?")
        except Exception:
            pass
        # GSC 28d totals + top queries
        try:
            g = sc.searchanalytics().query(siteUrl=site, body={
                "startDate": s28, "endDate": e28, "dimensions": [], "rowLimit": 1}).execute().get("rows", [])
            d["gsc_impr"] = int(g[0]["impressions"]) if g else 0
            d["gsc_clicks"] = int(g[0]["clicks"]) if g else 0
            q = sc.searchanalytics().query(siteUrl=site, body={
                "startDate": s28, "endDate": e28, "dimensions": ["query"], "rowLimit": 5}).execute().get("rows", [])
            d["top_queries"] = [(r["keys"][0], int(r["impressions"]), round(r["position"], 1)) for r in q]
        except Exception as ex:
            d["gsc_error"] = str(ex)[:60]
        # GA4 30d: sessions + engaged sessions + avg engagement time
        try:
            r = ga.properties().runReport(property=prop, body={
                "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
                "metrics": [{"name": "sessions"}, {"name": "engagedSessions"},
                            {"name": "averageSessionDuration"}]}).execute().get("rows", [])
            if r:
                m = r[0]["metricValues"]
                d["ga_sessions"] = int(m[0]["value"])
                d["ga_engaged"] = int(m[1]["value"])
                d["ga_avg_dur"] = round(float(m[2]["value"]))
        except Exception as ex:
            d["ga_error"] = str(ex)[:60]
        # AdSense 30d
        try:
            rep = ad.accounts().reports().generate(account=acct, dateRange="LAST_30_DAYS",
                metrics=["IMPRESSIONS", "CLICKS", "ESTIMATED_EARNINGS", "IMPRESSIONS_RPM"],
                filters=[f"DOMAIN_NAME=={domain}"]).execute()
            tot = rep.get("totals", {}).get("cells", [])
            if tot:
                d["ad_impr"], d["ad_clicks"], d["ad_earn"], d["ad_rpm"] = [x.get("value", "0") for x in tot]
        except Exception as ex:
            d["ad_error"] = str(ex)[:60]
        out[name] = d
    return out


def main():
    today = str(datetime.datetime.now(ZoneInfo("Asia/Karachi")).date())
    cur = collect()
    hist = []
    if os.path.exists(HIST):
        try:
            hist = json.load(open(HIST))
        except Exception:
            hist = []
    prev = next((entry for entry in reversed(hist) if entry["date"] < today), None)
    hist = [entry for entry in hist if entry["date"] != today]
    hist.append({"date": today, "data": cur})
    json.dump(hist, open(HIST, "w"), indent=1)

    def delta(name, key):
        if not prev:
            return ""
        p = prev["data"].get(name, {}).get(key)
        n = cur.get(name, {}).get(key)
        if isinstance(p, (int, float)) and isinstance(n, (int, float)):
            diff = n - p
            return f" ({'+' if diff >= 0 else ''}{diff} vs {prev['date']})"
        return ""

    lines = [f"# Weekly SEO Report — {today}", ""]
    if prev:
        lines.append(f"_Compared to previous report: {prev['date']}_\n")
    for name, _, _, _, _ in BLOGS:
        d = cur.get(name, {})
        lines.append(f"## {name}\n")
        cov = d.get("home_coverage", "?")
        flag = "✅" if cov.lower() in ("submitted and indexed", "indexed") else "⚠️"
        lines.append(f"**Indexing:** homepage = {flag} {cov} (crawled {d.get('home_lastcrawl','?')}) · "
                     f"legacy sitemap API indexed field: {d.get('sm_indexed','?')}; submitted: {d.get('sm_submitted','?')}. "
                     "This field is not the property's total indexed pages; use URL Inspection and the Page indexing dashboard.")
        lines.append("")
        lines.append("**Organic search (GSC, 28d) — the real signal:**")
        lines.append(f"- Impressions: **{d.get('gsc_impr', 'n/a')}**{delta(name, 'gsc_impr')}")
        lines.append(f"- Clicks: **{d.get('gsc_clicks', 'n/a')}**{delta(name, 'gsc_clicks')}")
        if d.get("top_queries"):
            lines.append("- Top queries: " + "; ".join(f"{q} ({i}i, pos {p})" for q, i, p in d["top_queries"]))
        lines.append("")
        lines.append("**GA4 engagement (30d; engaged sessions do not prove human traffic):**")
        lines.append(f"- Engaged sessions: **{d.get('ga_engaged', 'n/a')}** of {d.get('ga_sessions', 'n/a')} total"
                     + delta(name, "ga_engaged"))
        lines.append(f"- Avg session duration: {d.get('ga_avg_dur', 'n/a')}s")
        lines.append("")
        lines.append("**AdSense (30d):**")
        lines.append(f"- Impressions {d.get('ad_impr', '0')} | clicks {d.get('ad_clicks', '0')} "
                     f"| RPM ${d.get('ad_rpm', '0')} | earnings ${d.get('ad_earn', '0')}")
        lines.append("")
    lines.append("---")
    lines.append("_Watch GSC impressions — when they climb from ~0, SEO is working and real traffic (then AdSense $) follows._")
    report = "\n".join(lines)
    path = os.path.join(REPORTS, f"report_{today}.md")
    open(path, "w").write(report)
    print(report)
    print(f"\n[saved to {path}]")


if __name__ == "__main__":
    main()
