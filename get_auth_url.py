#!/usr/bin/env python3
"""Step 1: print consent URL, save PKCE verifier + state for step 2."""
import json
from google_auth_oauthlib.flow import Flow

CLIENT_SECRET = "/home/kwikcoders/seo/client_secret.json"
REDIRECT = "http://localhost:8108/"
SCOPES = [
    "https://www.googleapis.com/auth/webmasters",
    "https://www.googleapis.com/auth/indexing",
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/adsense.readonly",
    "https://www.googleapis.com/auth/blogger",
]
flow = Flow.from_client_secrets_file(CLIENT_SECRET, scopes=SCOPES, redirect_uri=REDIRECT,
                                     autogenerate_code_verifier=True)
url, state = flow.authorization_url(access_type="offline", prompt="consent",
                                    include_granted_scopes="true")
json.dump({"code_verifier": flow.code_verifier, "state": state},
          open("/home/kwikcoders/seo/.auth_state.json", "w"))
print(url)
