#!/usr/bin/env python3
"""Students Time cleanup: draft off-niche/thin/spam/political/duplicate posts.
Niche = AI & tech learning (students + developers), global. Reversible (revert to draft).
Usage: python st_cleanup.py [--apply]"""
import json, os, re, sys, time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

APPLY = "--apply" in sys.argv
BID = "8491425780932094856"
posts = json.load(open("/home/kwikcoders/seo/st_posts.json"))

def cat(p):
    t = p["title"].lower(); w = p["words"]
    if re.search(r"palestine|epstein|gaza|sumud|flotilla|coronavirus|phishing", t): return "POLITICAL"
    if re.search(r"on this day|facebook is cancelling|meet is now|bug bounty|is hiring|research intern|research scientist|software engineer -|neural architecture", t): return "JOBSPAM"
    if re.search(r"hipaa|shopify plus|white label|cloud migration|workato|godaddy developer|muse image api|reporting software for agencies|migration agency|migration consulting|migration strategy", t): return "B2BSPAM"
    if re.search(r"pakistani|admissions in pakistan", t): return "PAKISTAN"
    if re.search(r"gpt-5\.6", t) and "gpt-live" not in t: return "GPT56DUP"
    if w < 600: return "THIN"
    return "KEEP"

# GPT-5.6 dups: keep the single most comprehensive (max words), draft the rest
gpt = sorted([p for p in posts if cat(p) == "GPT56DUP"], key=lambda x: -x["words"])
gpt_keep = {gpt[0]["id"]} if gpt else set()

draft = []
for p in posts:
    ct = cat(p)
    if ct == "KEEP":
        continue
    if ct == "GPT56DUP" and p["id"] in gpt_keep:
        continue
    draft.append((p, ct))

print(f"{'APPLYING' if APPLY else 'DRY RUN'} — drafting {len(draft)} of {len(posts)} posts")
print(f"GPT-5.6 keeper: {gpt[0]['title'][:50] if gpt else '-'}\n")
from collections import Counter
print("By category:", dict(Counter(ct for _, ct in draft)))

svc = None
if APPLY:
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    c.refresh(Request())
    svc = build("blogger", "v3", credentials=c, cache_discovery=False)
    ok = 0
    for p, ct in draft:
        try:
            svc.posts().revert(blogId=BID, postId=p["id"]).execute(); ok += 1
            time.sleep(0.25)
        except Exception as e:
            print(f"  FAIL {p['title'][:40]}: {str(e)[:50]}")
    print(f"\n✅ Drafted {ok}/{len(draft)}. Live now: {len(posts)-ok}")
else:
    for p, ct in sorted(draft, key=lambda x: x[1]):
        print(f"  [{ct:9}] {p['words']:>4}w  {p['title'][:52]}")
    print(f"\nLive after: {len(posts)-len(draft)}  (rerun with --apply)")
