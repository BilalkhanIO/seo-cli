#!/usr/bin/env python3
"""Execute LL consolidation: revert the 32 zero-impression duplicate posts to DRAFT.
Same selection as ll_consolidate.py. Reversible (content preserved as drafts)."""
import json, os, re, time

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

blogger = build("blogger", "v3", credentials=c, cache_discovery=False)
sc = build("searchconsole", "v1", credentials=c, cache_discovery=False)

posts, tok = [], None
while True:
    r = blogger.posts().list(blogId=BLOG_ID, maxResults=100, status="LIVE",
                             pageToken=tok, fetchBodies=True).execute()
    posts += r.get("items", [])
    tok = r.get("nextPageToken")
    if not tok:
        break

def wc(h): return len(re.sub(r"<[^>]+>", " ", h or "").split())
def slug(u): return u.rstrip("/").split("/")[-1].replace(".html", "")

rows = sc.searchanalytics().query(siteUrl=SITE, body={
    "startDate": "2026-06-17", "endDate": "2026-09-15",
    "dimensions": ["page"], "rowLimit": 500}).execute().get("rows", [])
imp = {slug(x["keys"][0]): int(x.get("impressions", 0)) for x in rows}

live = [{"id": p["id"], "title": p["title"], "slug": slug(p["url"]),
         "words": wc(p.get("content", "")), "imp": imp.get(slug(p["url"]), 0)} for p in posts]

clusters = {
    "Balance transfer": r"balance transfer",
    "HYSA/CD": r"high-yield|high yield|savings account|no-penalty cd|no penalty cd",
    "Mortgage": r"mortgage|refinance|appraisal|home loan",
    "Accounting": r"accounting soft|invoicing|invoice soft|bookkeep",
    "Niche cards": r"secured credit|rideshare|cash ?back credit|premium credit|travel credit",
    "Business cc": r"business credit card",
    "Business checking": r"business checking",
    "Personal loans": r"personal loan",
}
to_draft = []
for name, pat in clusters.items():
    g = [p for p in live if re.search(pat, p["title"].lower())]
    if len(g) < 2:
        continue
    g.sort(key=lambda x: (-x["imp"], -x["words"]))
    for p in g[1:]:
        if p["imp"] == 0:
            to_draft.append(p)

print(f"Reverting {len(to_draft)} duplicates to DRAFT:\n")
ok = 0
for p in to_draft:
    try:
        blogger.posts().revert(blogId=BLOG_ID, postId=p["id"]).execute()
        ok += 1
        print(f"  DRAFTED  {p['id']}  {p['title'][:52]}")
    except Exception as e:
        print(f"  FAILED   {p['id']}  {str(e)[:60]}")
    time.sleep(0.3)
print(f"\nDone: {ok}/{len(to_draft)} reverted to draft. Live posts now: {len(live)-ok}")
