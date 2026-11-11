#!/usr/bin/env python3
"""Step 2: exchange the pasted code for tokens; write all token files."""
import json, os, sys
from google_auth_oauthlib.flow import Flow

CLIENT_SECRET = "/home/kwikcoders/seo/client_secret.json"
CONF_DIR = os.path.expanduser("~/.config/claude-seo")
TOKEN_PATH = os.path.join(CONF_DIR, "oauth-token.json")
REDIRECT = "http://localhost:8108/"
SCOPES = [
    "https://www.googleapis.com/auth/webmasters",
    "https://www.googleapis.com/auth/indexing",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/adsense.readonly",
    "https://www.googleapis.com/auth/blogger",
]

arg = sys.argv[1].strip()
# accept either a raw code or the full redirect URL
if "code=" in arg:
    from urllib.parse import urlparse, parse_qs
    arg = parse_qs(urlparse(arg).query)["code"][0]

st = json.load(open("/home/kwikcoders/seo/.auth_state.json"))
flow = Flow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT,
                                     state=st["state"])
flow.code_verifier = st["code_verifier"]
flow.fetch_token(code=arg)
creds = flow.credentials

c = json.load(open(CLIENT_SECRET)); c = c[list(c)[0]]
os.makedirs(CONF_DIR, exist_ok=True)
token = {
    "access_token": creds.token, "refresh_token": creds.refresh_token,
    "client_id": c["client_id"], "client_secret": c["client_secret"],
    "token_uri": "https://oauth2.googleapis.com/token", "scopes": SCOPES,
    "expires_at": creds.expiry.timestamp() if creds.expiry else 0,
}
json.dump(token, open(TOKEN_PATH, "w"), indent=2); os.chmod(TOKEN_PATH, 0o600)
with open("/home/kwikcoders/seo/blogger_token.json", "w") as f:
    f.write(creds.to_json())
os.chmod("/home/kwikcoders/seo/blogger_token.json", 0o600)
print("AUTH_OK refresh_token=" + str(bool(creds.refresh_token)))
