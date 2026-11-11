#!/usr/bin/env python3
"""Classify 28 LL posts into topic clusters; apply labels + append a 'Related Guides'
internal-link block to each. Idempotent (skips if block already present).
Usage: python ll_labels_links.py            -> DRY RUN (prints plan)
       python ll_labels_links.py --apply     -> writes labels + links via Blogger API"""
import json, os, re, sys, time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BLOG_ID = "6645616362681304579"
APPLY = "--apply" in sys.argv
posts = json.load(open("/home/kwikcoders/seo/ll_posts_full.json"))

# cluster: (slug-regex, [labels], display-name). First match wins for primary cluster.
CLUSTERS = [
    ("business-credit", r"business-credit-card|build-business-credit|business-credit-with-ein",
     ["Business Credit", "Small Business Finance"], "Business Credit"),
    ("business-banking", r"business-checking|business-bank-account|no-fee-business",
     ["Business Banking", "Small Business Finance"], "Business Banking"),
    ("freelancer", r"freelancer|freelancers|invoicing|etsy|mortgage-for-freelancers",
     ["Freelancer Finance"], "Freelancer Finance"),
    ("savings", r"savings-account|no-penalty-cd|high-yield-savings",
     ["Savings & CDs"], "Savings & CDs"),
    ("investing", r"investment-app|robo-advisor|diy-investing|529-plan",
     ["Investing"], "Investing"),
    ("credit-cards", r"apr-intro-balance|grocery-credit|building-credit|rewards-credit|rideshare|credit-card-for-building",
     ["Credit Cards"], "Credit Cards"),
    ("loans", r"personal-loan", ["Loans"], "Loans"),
    ("banking", r"switch-direct-deposit|open-business-bank", ["Banking Guides"], "Banking Guides"),
]
MARK = "<!--related-guides-->"

def slug(u): return u.rstrip("/").split("/")[-1]

def cluster_of(p):
    s = slug(p["url"])
    for key, pat, labels, name in CLUSTERS:
        if re.search(pat, s):
            return key, labels, name
    return "credit-cards", ["Personal Finance"], "Personal Finance"

# assign
for p in posts:
    k, labels, name = cluster_of(p)
    p["_cluster"], p["_labels"], p["_cname"] = k, labels, name

# group for related links
groups = {}
for p in posts:
    groups.setdefault(p["_cluster"], []).append(p)

def related_block(p):
    sibs = [s for s in groups[p["_cluster"]] if s["id"] != p["id"]][:4]
    if not sibs:
        return ""
    lis = "".join(f'<li><a href="{s["url"]}">{s["title"]}</a></li>' for s in sibs)
    return (f'{MARK}\n<div style="margin-top:2em;padding:1em 1.2em;border:1px solid #e2e8f0;'
            f'border-radius:10px;background:#f8fafc">'
            f'<h3 style="margin-top:0">Related {p["_cname"]} Guides</h3>'
            f'<ul style="margin:0">{lis}</ul></div>')

print(f"{'APPLYING' if APPLY else 'DRY RUN'} — {len(posts)} posts\n")
for k in groups:
    print(f"[{k}] {len(groups[k])} posts")

svc = None
if APPLY:
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    if not c.valid: c.refresh(Request())
    svc = build("blogger", "v3", credentials=c, cache_discovery=False)

changed = 0
for p in posts:
    content = p["content"]
    if MARK not in content:
        content = content + "\n" + related_block(p)
    body = {"labels": p["_labels"], "content": content}
    if APPLY:
        try:
            svc.posts().patch(blogId=BLOG_ID, postId=p["id"], body=body).execute()
            changed += 1
            print(f"  ✓ {p['_labels']}  +{len([s for s in groups[p['_cluster']] if s['id']!=p['id']][:4])} links  {p['title'][:40]}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ✗ {p['title'][:40]}: {str(e)[:70]}")
    else:
        print(f"  {p['_labels']}  {p['title'][:44]}")
print(f"\n{'Updated '+str(changed) if APPLY else 'Dry run'} — rerun with --apply to write.")
