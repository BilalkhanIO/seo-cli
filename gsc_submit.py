#!/usr/bin/env python3
"""Submit sitemaps to Search Console via API (needs full webmasters scope)."""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

tok = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
creds = Credentials(
    token=tok["access_token"],
    refresh_token=tok.get("refresh_token"),
    token_uri=tok.get("token_uri", "https://oauth2.googleapis.com/token"),
    client_id=tok["client_id"],
    client_secret=tok["client_secret"],
    scopes=tok.get("scopes"),
)
if not creds.valid:
    creds.refresh(Request())

svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

SITE = "https://studenttimepk.blogspot.com/"
SITEMAPS = [
    "https://studenttimepk.blogspot.com/sitemap.xml",
    "https://studenttimepk.blogspot.com/sitemap-pages.xml",
]
for sm in SITEMAPS:
    try:
        svc.sitemaps().submit(siteUrl=SITE, feedpath=sm).execute()
        print(f"SUBMITTED: {sm}")
    except Exception as e:
        print(f"FAILED {sm}: {e}", file=sys.stderr)

# List back to confirm
print("\n--- Sitemaps now registered ---")
res = svc.sitemaps().list(siteUrl=SITE).execute()
for s in res.get("sitemap", []):
    c = s.get("contents", [{}])
    submitted = c[0].get("submitted", "?") if c else "?"
    print(f"  {s.get('path')}  | type={s.get('type')} | submitted_urls={submitted} | pending={s.get('isPending')}")
