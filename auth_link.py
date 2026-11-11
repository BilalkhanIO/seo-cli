#!/usr/bin/env python3
"""Print consent URL immediately, then run a tiny server to catch the redirect
and write all tokens (GSC/GA4/AdSense/Blogger) from one authorization."""
import json, os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from google_auth_oauthlib.flow import Flow

CLIENT_SECRET = "/home/kwikcoders/seo/client_secret.json"
CONF_DIR = os.path.expanduser("~/.config/claude-seo")
TOKEN_PATH = os.path.join(CONF_DIR, "oauth-token.json")
PORT = 8108
REDIRECT = f"http://localhost:{PORT}/"
SCOPES = [
    "https://www.googleapis.com/auth/webmasters",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/adsense.readonly",
    "https://www.googleapis.com/auth/blogger",
]

flow = Flow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT)
url, _ = flow.authorization_url(access_type="offline", prompt="consent",
                               include_granted_scopes="true")
print("AUTH_URL: " + url, flush=True)

code_holder = {}

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if "code" in q:
            code_holder["code"] = q["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorized. You can close this tab.</h2>")
        else:
            self.send_response(400); self.end_headers()
    def log_message(self, *a):
        pass

srv = HTTPServer(("0.0.0.0", PORT), H)
while "code" not in code_holder:
    srv.handle_request()

flow.fetch_token(code=code_holder["code"])
creds = flow.credentials

with open(CLIENT_SECRET) as f:
    c = json.load(f)
c = c[list(c)[0]]
os.makedirs(CONF_DIR, exist_ok=True)
token = {
    "access_token": creds.token, "refresh_token": creds.refresh_token,
    "client_id": c["client_id"], "client_secret": c["client_secret"],
    "token_uri": "https://oauth2.googleapis.com/token", "scopes": SCOPES,
    "expires_at": creds.expiry.timestamp() if creds.expiry else 0,
}
json.dump(token, open(TOKEN_PATH, "w"), indent=2)
os.chmod(TOKEN_PATH, 0o600)
with open("/home/kwikcoders/seo/blogger_token.json", "w") as f:
    f.write(creds.to_json())
os.chmod("/home/kwikcoders/seo/blogger_token.json", 0o600)
print("AUTH_OK refresh_token=" + str(bool(creds.refresh_token)), flush=True)
