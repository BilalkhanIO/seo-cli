#!/usr/bin/env python3
"""Submit URLs to Bing for indexing via Bing Webmaster URL Submission API (free)."""
import json
import sys
import urllib.request
import urllib.parse

KEY = open("/home/kwikcoders/seo/bing_key.txt").read().strip()
BASE = "https://ssl.bing.com/webmaster/api.svc/json"

URLS = [
    "https://studenttimepk.blogspot.com/",
    "https://studenttimepk.blogspot.com/2026/07/free-ai-courses-with-certificates-in.html",
    "https://studenttimepk.blogspot.com/2026/07/gpt-56-goes-public-what-developers.html",
    "https://studenttimepk.blogspot.com/2026/07/google-antigravity-20-ai-agents-for.html",
    "https://studenttimepk.blogspot.com/2026/08/eu-ai-act-updates-what-developers-must.html",
    "https://studenttimepk.blogspot.com/2026/07/ai-dev-tools-boom-what-build-2026.html",
    "https://studenttimepk.blogspot.com/2026/08/ai-in-dev-why-fixing-vulnerabilities-is.html",
    "https://studenttimepk.blogspot.com/2026/08/ai-singularity-debate-heats-up-as.html",
    "https://studenttimepk.blogspot.com/2026/08/gpt-56-and-rise-of-ai-agents-for.html",
]


def get(ep, params=None):
    url = f"{BASE}/{ep}?apikey={KEY}"
    if params:
        url += "&" + urllib.parse.urlencode(params)
    return json.loads(urllib.request.urlopen(url, timeout=30).read().decode())


def post(ep, body):
    url = f"{BASE}/{ep}?apikey={KEY}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


sites = get("GetUserSites").get("d") or []
urls = [s.get("Url") for s in sites if isinstance(s, dict)]
print("Verified Bing sites:", urls or "(none)")
if not urls:
    print("No sites yet — add studenttimepk in bing.com/webmasters first.")
    sys.exit(0)

# pick the matching site
site = next((u for u in urls if "studenttimepk" in u), urls[0])
site = site.rstrip("/")
print("Using siteUrl:", site)

q = get("GetUrlSubmissionQuota", {"siteUrl": site}).get("d", {})
print(f"Quota — daily: {q.get('DailyQuota')}, monthly: {q.get('MonthlyQuota')}")

try:
    res = post("SubmitUrlbatch", {"siteUrl": site, "urlList": URLS})
    print(f"\nSUBMITTED {len(URLS)} URLs to Bing ✅  (response: {res.get('d')})")
    for u in URLS:
        print("  →", u)
except Exception as e:
    body = getattr(e, "read", lambda: b"")()
    print("Submit error:", str(e)[:150])
    print(body[:400].decode("utf-8", "replace") if body else "")
