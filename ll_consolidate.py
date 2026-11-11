#!/usr/bin/env python3
"""Learner's Link: pull live posts + GSC impressions, cluster near-duplicates,
recommend keep/merge to fix AdSense 'Low value content'. Read-only (no writes)."""
import json, os, re, urllib.request

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BLOG_ID = "6645616362681304579"
SITE = "https://learners-link.blogspot.com/"
CONF = os.path.expanduser("~/.config/claude-seo/oauth-token.json")

t = json.load(open(CONF))
c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                token_uri=t["token_uri"], client_id=t["client_id"],
                client_secret=t["client_secret"], scopes=t.get("scopes"))
if not c.valid:
    c.refresh(Request())

# 1) Live posts (paginate)
blogger = build("blogger", "v3", credentials=c, cache_discovery=False)
posts, tok = [], None
while True:
    resp = blogger.posts().list(blogId=BLOG_ID, maxResults=100, status="LIVE",
                                pageToken=tok, fetchBodies=True).execute()
    posts += resp.get("items", [])
    tok = resp.get("nextPageToken")
    if not tok:
        break

def wc(html):
    return len(re.sub(r"<[^>]+>", " ", html or "").split())

def slug(u):
    return u.rstrip("/").split("/")[-1].replace(".html", "")

live = [{"id": p["id"], "title": p["title"], "slug": slug(p["url"]),
         "words": wc(p.get("content", "")), "url": p["url"]} for p in posts]
print(f"LIVE posts: {len(live)}")

# 2) GSC impressions (90d, page-level)
sc = build("searchconsole", "v1", credentials=c, cache_discovery=False)
body = {"startDate": "2026-06-17", "endDate": "2026-09-15",
        "dimensions": ["page"], "rowLimit": 500}
rows = sc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])
imp = {slug(r["keys"][0]): int(r.get("impressions", 0)) for r in rows}
for p in live:
    p["imp"] = imp.get(p["slug"], 0)

# 3) Clusters
clusters = {
    "Balance transfer cards": r"balance transfer",
    "High-yield savings / CD": r"high-yield|high yield|savings account|no-penalty cd|no penalty cd",
    "Mortgage / refinance": r"mortgage|refinance|appraisal|home loan",
    "Accounting / invoicing SW": r"accounting soft|invoicing|invoice soft|bookkeep",
    "Secured / niche cards": r"secured credit|rideshare|cash ?back credit|premium credit|travel credit",
    "Business credit cards": r"business credit card",
    "Business checking": r"business checking",
    "Personal loans": r"personal loan",
}
seen = set()
total_merge = 0
for name, pat in clusters.items():
    g = [p for p in live if re.search(pat, p["title"].lower())]
    if len(g) < 2:
        continue
    g.sort(key=lambda x: (-x["imp"], -x["words"]))
    keeper = g[0]
    seen.update(p["id"] for p in g)
    print(f"\n=== {name}  ({len(g)} posts) ===")
    print(f"  KEEP  {keeper['imp']:>4}i {keeper['words']:>4}w  {keeper['title'][:52]}")
    for p in g[1:]:
        act = "KEEP " if p["imp"] > 0 else "MERGE"
        if p["imp"] == 0:
            total_merge += 1
        print(f"  {act} {p['imp']:>4}i {p['words']:>4}w  {p['id']}  {p['title'][:46]}")

# 4) Thin posts overall (< 600 words) not already in a cluster
print(f"\n=== THIN posts (<600w), 0 impressions, outside clusters ===")
thin = [p for p in live if p["words"] < 600 and p["imp"] == 0 and p["id"] not in seen]
for p in sorted(thin, key=lambda x: x["words"]):
    print(f"  {p['words']:>4}w  {p['id']}  {p['title'][:50]}")
print(f"\nSUMMARY: {len(live)} live | {total_merge} duplicate-merge candidates | {len(thin)} thin outliers")
