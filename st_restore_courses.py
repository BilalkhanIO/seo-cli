#!/usr/bin/env python3
"""Restore (republish) the course + scholarship posts drafted in the ST cleanup.
They're on-niche (AI/education for students). Thin ones will be EXPANDED during optimization.
Usage: python st_restore_courses.py [--apply]"""
import json, os, re, sys, time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

APPLY = "--apply" in sys.argv
BID = "8491425780932094856"
posts = json.load(open("/home/kwikcoders/seo/st_posts.json"))

# course/scholarship pattern — education content to restore
COURSE = r"course|scholarship|learn |harvard|unicef|computer vision|wealth management|crouse|language courses|\bhtml\b|\bcss\b|cloud identity|cloud computing|machine learning|digital garage|nelson mandela|sand art"
# these were drafted but are NOT courses/scholarships — leave drafted
NOT_COURSE = r"future technology|top technology trends|fiverr"

restore = []
for p in posts:
    t = p["title"].lower()
    if p["words"] < 600 and re.search(COURSE, t) and not re.search(NOT_COURSE, t):
        restore.append(p)

print(f"{'APPLYING' if APPLY else 'DRY RUN'} — restoring {len(restore)} course/scholarship posts\n")
svc = None
if APPLY:
    tok = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=tok["access_token"], refresh_token=tok.get("refresh_token"),
                    token_uri=tok["token_uri"], client_id=tok["client_id"],
                    client_secret=tok["client_secret"], scopes=tok.get("scopes"))
    c.refresh(Request())
    svc = build("blogger", "v3", credentials=c, cache_discovery=False)
ok = 0
for p in sorted(restore, key=lambda x: -x["words"]):
    if APPLY:
        try:
            svc.posts().publish(blogId=BID, postId=p["id"]).execute(); ok += 1
            print(f"  ✅ {p['words']:>4}w  {p['title'][:52]}")
            time.sleep(0.25)
        except Exception as e:
            print(f"  ✗ {p['title'][:40]}: {str(e)[:50]}")
    else:
        print(f"  {p['words']:>4}w  {p['title'][:54]}")
if APPLY:
    print(f"\n✅ Republished {ok}/{len(restore)}. (Thin ones will be expanded during optimization.)")
else:
    print(f"\n(rerun with --apply to republish)")
