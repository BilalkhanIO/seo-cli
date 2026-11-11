#!/usr/bin/env python3
"""Robust Google OAuth for Search Console + GA4 + Indexing.

Uses run_local_server (reliable), then writes the token in the exact format
claude-seo's google_auth.py expects, so gsc_query/gsc_inspect/ga4_report work.
"""
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRET = "/home/kwikcoders/seo/client_secret.json"
CONF_DIR = os.path.expanduser("~/.config/claude-seo")
TOKEN_PATH = os.path.join(CONF_DIR, "oauth-token.json")
CONFIG_PATH = os.path.join(CONF_DIR, "google-api.json")
SCOPES = [
    "https://www.googleapis.com/auth/webmasters",
    "https://www.googleapis.com/auth/indexing",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/adsense.readonly",
    "https://www.googleapis.com/auth/blogger",
]

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
creds = flow.run_local_server(
    port=8108, open_browser=False,
    authorization_prompt_message="\n>>> Open this URL in your browser to authorize:\n{url}\n",
    access_type="offline", prompt="consent",
)

with open(CLIENT_SECRET) as f:
    c = json.load(f)
c = c[list(c)[0]]

os.makedirs(CONF_DIR, exist_ok=True)
token = {
    "access_token": creds.token,
    "refresh_token": creds.refresh_token,
    "client_id": c["client_id"],
    "client_secret": c["client_secret"],
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": SCOPES,
    "expires_at": creds.expiry.timestamp() if creds.expiry else 0,
}
with open(TOKEN_PATH, "w") as f:
    json.dump(token, f, indent=2)
os.chmod(TOKEN_PATH, 0o600)

config = {}
if os.path.exists(CONFIG_PATH):
    try:
        config = json.load(open(CONFIG_PATH))
    except Exception:
        config = {}
config["oauth_client_path"] = CLIENT_SECRET
with open(CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=2)
os.chmod(CONFIG_PATH, 0o600)

# Also write Blogger token (authorized_user format) so blogger_cli.py uses the SAME auth.
with open("/home/kwikcoders/seo/blogger_token.json", "w") as f:
    f.write(creds.to_json())
os.chmod("/home/kwikcoders/seo/blogger_token.json", 0o600)

print("AUTH_OK: GSC + GA4 + AdSense + Blogger — all tokens written from one auth")
print("refresh_token present:", bool(creds.refresh_token))
