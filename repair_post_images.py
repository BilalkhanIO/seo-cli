#!/usr/bin/env python3
"""Back up and add a Pexels lead image to specific recent posts missing one."""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from pexels_helper import img_block
from upload_drafts import service

TARGETS = [
    ("8491425780932094856", "4793757617058466971", "professional working laptop"),
    ("8491425780932094856", "948226746784118980", "online learning laptop"),
    ("6645616362681304579", "5321579619218609454", "credit card payment"),
    ("6645616362681304579", "4147227867597976287", "financial planning desk"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    api = service()
    backup = Path(__file__).parent / "backups" / "post-images"
    for blog_id, post_id, query in TARGETS:
        post = api.posts().get(blogId=blog_id, postId=post_id, view="ADMIN").execute()
        if "<img" in post.get("content", "").lower():
            print(f"SKIP image exists: {post['title']}")
            continue
        if not args.apply:
            print(f"MISSING: {post_id} {post['title']}; query={query}")
            continue
        figure, _ = img_block(query, hero=True)
        backup.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = backup / f"{post_id}-{stamp}.json"
        path.write_text(json.dumps(post, ensure_ascii=False, indent=2))
        api.posts().patch(blogId=blog_id, postId=post_id,
                          body={"content": figure + "\n" + post.get("content", "")}).execute()
        saved = api.posts().get(blogId=blog_id, postId=post_id, view="ADMIN").execute()
        assert "images.pexels.com" in saved["content"]
        assert saved.get("status") == post.get("status"), "Unexpected publication state change"
        print(f"VERIFIED image added: {post_id} status={saved.get('status')}; backup={path}")


if __name__ == "__main__":
    main()
