#!/usr/bin/env python3
"""Upload local Markdown article drafts to Blogger as unpublished drafts."""
import html
import json
import os
import re
from pexels_helper import img_block

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE = "/home/kwikcoders/seo"
TOKEN = os.path.expanduser("~/.config/claude-seo/oauth-token.json")
POSTS = [
    ("8491425780932094856", "drafts/students-time-ai-skills-non-technical-professionals.md",
     ["AI Skills", "Career Skills"]),
    ("6645616362681304579", "drafts/learners-link-best-beginner-cash-back-credit-card.md",
     ["Credit Cards", "Personal Finance"]),
    ("6645616362681304579", "drafts/learners-link-robo-advisor-vs-diy-investing.md",
     ["Investing", "Personal Finance"]),
]


def service():
    t = json.load(open(TOKEN))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    c.refresh(Request())
    return build("blogger", "v3", credentials=c, cache_discovery=False)


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r'<a href="\2" rel="nofollow noopener" target="_blank">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def markdown_to_html(raw):
    lines = raw.splitlines()
    out, paragraph, in_list, in_quote = [], [], False, False

    def flush():
        nonlocal paragraph
        if paragraph:
            out.append("<p>" + inline(" ".join(paragraph)) + "</p>")
            paragraph = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for line in lines:
        if not line.strip():
            flush(); close_list()
            if in_quote:
                out.append("</blockquote>"); in_quote = False
            continue
        if re.match(r"\*\*(Primary keyword|Secondary keywords|Suggested URL|Search description|Image query):", line):
            continue
        if line.startswith("# "):
            continue  # Blogger renders the title separately.
        if line.startswith("## "):
            flush(); close_list(); out.append("<h2>" + inline(line[3:].strip()) + "</h2>"); continue
        if line.startswith("### "):
            flush(); close_list(); out.append("<h3>" + inline(line[4:].strip()) + "</h3>"); continue
        if line.startswith("> "):
            flush(); close_list()
            if not in_quote:
                out.append("<blockquote>"); in_quote = True
            out.append("<p>" + inline(line[2:]) + "</p>"); continue
        if line.startswith("- ") or re.match(r"\d+\. ", line):
            flush()
            if not in_list:
                out.append("<ul>"); in_list = True
            item = re.sub(r"^(?:- |\d+\. )", "", line)
            out.append("<li>" + inline(item) + "</li>"); continue
        if line.startswith("|"):
            flush(); close_list()
            cells = [x.strip() for x in line.strip("|").split("|")]
            if all(set(x) <= set("-:") for x in cells):
                continue
            tag = "td" if any("<table" in x for x in out) else "th"
            if tag == "th": out.append("<table><thead><tr>" + "".join("<th>" + inline(x) + "</th>" for x in cells) + "</tr></thead><tbody>")
            else: out.append("<tr>" + "".join("<td>" + inline(x) + "</td>" for x in cells) + "</tr>")
            continue
        if any("<tbody>" in x for x in out) and not any("</tbody></table>" in x for x in out):
            out.append("</tbody></table>")
        paragraph.append(line.strip())
    flush(); close_list()
    if in_quote: out.append("</blockquote>")
    if any("<tbody>" in x for x in out) and not any("</tbody></table>" in x for x in out): out.append("</tbody></table>")
    return "\n".join(out)


def build_content(raw):
    content = markdown_to_html(raw)
    match = re.search(r"^\*\*Image query:\*\*\s*(.+)$", raw, re.M)
    if not match:
        raise ValueError("Add **Image query:** with a relevant Pexels search before upload")
    figure, _ = img_block(match.group(1).strip(), hero=True)
    return figure + "\n" + content


def existing_posts(b, blog_id):
    result = []
    for status in ("DRAFT", "LIVE", "SCHEDULED"):
        token = None
        while True:
            page = b.posts().list(blogId=blog_id, maxResults=100, status=status,
                                  view="ADMIN", pageToken=token, fetchBodies=False).execute()
            result.extend(page.get("items", []))
            token = page.get("nextPageToken")
            if not token:
                break
    return result


def main():
    b = service()
    for blog_id, rel, labels in POSTS:
        path = os.path.join(BASE, rel)
        raw = open(path, encoding="utf-8").read()
        title = re.search(r"^# (.+)$", raw, re.M).group(1)
        existing = existing_posts(b, blog_id)
        if any(p.get("title") == title for p in existing):
            print(f"SKIP already exists: {title}")
            continue
        body = {"kind": "blogger#post", "blog": {"id": blog_id},
                "title": title, "content": build_content(raw), "labels": labels}
        result = b.posts().insert(blogId=blog_id, body=body, isDraft=True).execute()
        print(f"DRAFT CREATED: {result['id']} | {title} | status={result.get('status')}")


if __name__ == "__main__":
    main()
