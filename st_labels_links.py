#!/usr/bin/env python3
"""Students Time: topical labels + 'Related Guides' internal-link block on every post.
Niche = AI & tech learning. Idempotent. Usage: python st_labels_links.py [--apply]"""
import json, os, re, sys, time
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BID = "8491425780932094856"
APPLY = "--apply" in sys.argv
MARK = "<!--related-guides-->"

# (regex on title, labels, display name) — first match wins
CLUSTERS = [
    ("prompt", r"prompt engineering", ["Prompt Engineering", "AI Skills"], "Prompt Engineering"),
    ("chatgpt", r"chatgpt", ["ChatGPT", "AI for Students"], "ChatGPT"),
    ("ai-courses", r"free ai course|ai course|free course|scholarship|certificat|harvard|unicef|digital garage|social media marketing|language course|html|css|cloud|machine learning|computer vision|wealth management|sand art|leadership course",
     ["Free Courses", "AI Learning"], "Free Courses & Certifications"),
    ("ai-tools", r"ai tool|ai study tool|assignment writing|study tools",
     ["AI Tools", "AI for Students"], "AI Tools for Students"),
    ("learn-ai", r"learn ai|learning ai|ai literacy|ai pathway|ai skill|ai-ready|how artificial intelligence|changing everyday",
     ["Learn AI", "AI Learning"], "Learning AI"),
    ("ai-dev", r"developer|coding|gpt-5|gpt-live|agents|astra|antigravity|devops|ruby|react|ubuntu|web dev|generative ai|godaddy|ip address|wi.?fi|qr code",
     ["AI for Developers", "Developer Tools"], "AI for Developers"),
    ("ai-news", r"ai news|titans|singularity|muse|ai overviews|trending|top 10 ai|new ai|skill gap|databricks",
     ["AI News", "AI Trends"], "AI News & Trends"),
    ("study", r"note-taking|memory|sleep|stress|time management|career|communication|study smarter|admission|studying abroad|calm mind|speak up",
     ["Study Skills", "Student Success"], "Study Skills"),
]

posts = []
def load():
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    c.refresh(Request())
    return build("blogger", "v3", credentials=c, cache_discovery=False)

svc = load()
tok = None
while True:
    r = svc.posts().list(blogId=BID, maxResults=100, status="LIVE", pageToken=tok, fetchBodies=True).execute()
    posts += r.get("items", []); tok = r.get("nextPageToken")
    if not tok: break

def cluster_of(p):
    t = p["title"].lower()
    for key, pat, labels, name in CLUSTERS:
        if re.search(pat, t):
            return key, labels, name
    return "ai-learning", ["AI Learning"], "AI Learning"

for p in posts:
    p["_k"], p["_labels"], p["_name"] = cluster_of(p)
groups = {}
for p in posts:
    groups.setdefault(p["_k"], []).append(p)

def block(p):
    sibs = [s for s in groups[p["_k"]] if s["id"] != p["id"]][:4]
    if not sibs: return ""
    lis = "".join(f'<li><a href="{s["url"]}">{s["title"]}</a></li>' for s in sibs)
    return (f'{MARK}\n<div style="margin-top:2em;padding:1em 1.2em;border:1px solid #e2e8f0;'
            f'border-radius:10px;background:#f8fafc"><h3 style="margin-top:0">Related {p["_name"]} Guides</h3>'
            f'<ul style="margin:0">{lis}</ul></div>')

from collections import Counter
print(f"{'APPLYING' if APPLY else 'DRY RUN'} — {len(posts)} posts")
print("clusters:", dict(Counter(p["_k"] for p in posts)))
changed = 0
for p in posts:
    content = p["content"]
    if MARK not in content:
        content = content + "\n" + block(p)
    body = {"labels": p["_labels"], "content": content}
    if APPLY:
        try:
            svc.posts().patch(blogId=BID, postId=p["id"], body=body).execute(); changed += 1
            time.sleep(0.25)
        except Exception as e:
            print(f"  fail {p['title'][:34]}: {str(e)[:40]}")
print(f"{'updated '+str(changed) if APPLY else 'dry run'} (rerun with --apply)")
