#!/usr/bin/env python3
"""Automated indexing flow — submit sitemaps to GSC + all live URLs to Bing, for every blog.
Run after publishing new/updated posts. Fully automated (no manual steps)."""
import json
import os
import re
import urllib.request

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CONF = os.path.expanduser("~/.config/claude-seo/oauth-token.json")
BING_KEY = open("/home/kwikcoders/seo/bing_key.txt").read().strip()
BING = "https://ssl.bing.com/webmaster/api.svc/json"

BLOGS = [
    {"name": "Students Time", "gsc": "https://studenttimepk.blogspot.com/",
     "bing": "https://studenttimepk.blogspot.com", "sitemap": "https://studenttimepk.blogspot.com/sitemap.xml"},
    {"name": "Learner's Link", "gsc": "https://learners-link.blogspot.com/",
     "bing": "https://learners-link.blogspot.com", "sitemap": "https://learners-link.blogspot.com/sitemap.xml"},
]


def creds():
    t = json.load(open(CONF))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    if not c.valid:
        c.refresh(Request())
    return c


def bing_post(ep, body):
    req = urllib.request.Request(f"{BING}/{ep}?apikey={BING_KEY}", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    return urllib.request.urlopen(req, timeout=40).read()


C = creds()
sc = build("searchconsole", "v1", credentials=C, cache_discovery=False)
GIDX = "https://indexing.googleapis.com/v3/urlNotifications:publish"


def google_index_ping(url):
    body = json.dumps({"url": url, "type": "URL_UPDATED"}).encode()
    req = urllib.request.Request(GIDX, data=body,
                                 headers={"Authorization": f"Bearer {C.token}",
                                          "Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).read()


for b in BLOGS:
    print(f"\n=== {b['name']} ===")
    # 1) GSC sitemap
    try:
        sc.sitemaps().submit(siteUrl=b["gsc"], feedpath=b["sitemap"]).execute()
        print(f"  GSC sitemap submitted: {b['sitemap']}")
    except Exception as e:
        print(f"  GSC sitemap error: {str(e)[:90]}")
    # collect live URLs from sitemap
    try:
        sm = urllib.request.urlopen(b["sitemap"], timeout=30).read().decode()
        urls = [b["gsc"]] + re.findall(r"<loc>([^<]+)</loc>", sm)
        urls = list(dict.fromkeys(urls))
    except Exception as e:
        print(f"  sitemap fetch error: {str(e)[:90]}")
        continue
    # 2) Bing — submit all live URLs
    try:
        ok = 0
        for i in range(0, len(urls), 100):
            bing_post("SubmitUrlbatch", {"siteUrl": b["bing"], "urlList": urls[i:i + 100]})
            ok += len(urls[i:i + 100])
        print(f"  Bing: submitted {ok} URLs")
    except Exception as e:
        print(f"  Bing error: {str(e)[:90]}")
    # 3) Google Indexing API — ping each URL (accepted != guaranteed indexed for blog pages)
    gok, gerr = 0, ""
    for u in urls:
        try:
            google_index_ping(u)
            gok += 1
        except Exception as e:
            gerr = str(e)[:80]
            break
    print(f"  Google Indexing API: {gok}/{len(urls)} pinged" + (f" (stopped: {gerr})" if gerr else ""))

print("\nIndexing flow complete. (Google GSC 'Request Indexing' button is UI-only; "
      "Indexing API pings are best-effort for blog pages.)")
