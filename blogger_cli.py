#!/usr/bin/env python3
"""Minimal Blogger API v3 CLI for studenttimepk SEO updates.

Auth: OAuth desktop flow, token cached locally. Scope: manage Blogger blogs.
Note: Blogger API cannot set the per-post "Search Description" (meta description);
      it can update title, content (HTML body), and labels only.
"""
import argparse
import json
import os
import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE = "/home/kwikcoders/seo"
CLIENT_SECRET = os.path.join(BASE, "client_secret.json")
TOKEN = os.path.join(BASE, "blogger_token.json")
SCOPES = ["https://www.googleapis.com/auth/blogger"]


def get_service(open_browser=True):
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            # Fixed port; desktop clients accept any loopback port.
            creds = flow.run_local_server(port=8765, open_browser=open_browser,
                                          authorization_prompt_message=
                                          "\n>>> Open this URL in your browser to authorize:\n{url}\n")
        with open(TOKEN, "w") as f:
            f.write(creds.to_json())
        os.chmod(TOKEN, 0o600)
    return build("blogger", "v3", credentials=creds, cache_discovery=False)


def cmd_auth(args):
    get_service(open_browser=not args.no_browser)
    print("AUTH_OK: token saved to", TOKEN)


def cmd_blogs(args):
    svc = get_service()
    res = svc.blogs().listByUser(userId="self").execute()
    for b in res.get("items", []):
        print(f"{b['id']}\t{b['name']}\t{b['url']}")


def cmd_list(args):
    svc = get_service()
    posts = svc.posts()
    req = posts.list(blogId=args.blog_id, maxResults=args.limit,
                     fetchBodies=False, status="LIVE")
    out = []
    while req is not None and len(out) < args.limit:
        res = req.execute()
        for p in res.get("items", []):
            out.append(p)
        req = posts.list_next(req, res)
    for p in out[:args.limit]:
        print(f"{p['id']}\t{p.get('title','')}\t{p.get('url','')}")


def cmd_get(args):
    svc = get_service()
    p = svc.posts().get(blogId=args.blog_id, postId=args.post_id).execute()
    if args.field == "content":
        sys.stdout.write(p.get("content", ""))
    else:
        print(json.dumps({k: p.get(k) for k in ("id", "title", "url", "labels")}, indent=2))


def cmd_draft(args):
    svc = get_service()
    res = svc.posts().revert(blogId=args.blog_id, postId=args.post_id).execute()
    print(f"DRAFTED: {res['id']}\t{res.get('status')}\t{res.get('url','')}")


def cmd_update(args):
    svc = get_service()
    current = svc.posts().get(blogId=args.blog_id, postId=args.post_id).execute()
    body = {"id": args.post_id, "blog": {"id": args.blog_id}}
    body["title"] = args.title if args.title else current.get("title")
    if args.content_file:
        with open(args.content_file, encoding="utf-8") as f:
            body["content"] = f.read()
    else:
        body["content"] = current.get("content", "")
    if args.labels is not None:
        body["labels"] = [x.strip() for x in args.labels.split(",") if x.strip()]
    elif current.get("labels"):
        body["labels"] = current["labels"]
    res = svc.posts().update(blogId=args.blog_id, postId=args.post_id,
                             body=body, publish=True).execute()
    print("UPDATED:", res["id"], res.get("url"))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("auth"); a.add_argument("--no-browser", action="store_true"); a.set_defaults(func=cmd_auth)
    b = sub.add_parser("blogs"); b.set_defaults(func=cmd_blogs)
    l = sub.add_parser("list"); l.add_argument("blog_id"); l.add_argument("--limit", type=int, default=200); l.set_defaults(func=cmd_list)
    g = sub.add_parser("get"); g.add_argument("blog_id"); g.add_argument("post_id"); g.add_argument("--field", default="meta"); g.set_defaults(func=cmd_get)
    dr = sub.add_parser("draft"); dr.add_argument("blog_id"); dr.add_argument("post_id"); dr.set_defaults(func=cmd_draft)
    u = sub.add_parser("update"); u.add_argument("blog_id"); u.add_argument("post_id")
    u.add_argument("--title"); u.add_argument("--content-file"); u.add_argument("--labels"); u.set_defaults(func=cmd_update)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
