#!/usr/bin/env python3
"""Create one reviewed DEV draft with a canonical link to Students Time."""
import json
import urllib.request
import urllib.error

KEY_PATH = "/home/kwikcoders/seo/devto_api_key.txt"
API = "https://dev.to/api"
CANONICAL = "https://studenttimepk.blogspot.com/2026/10/free-ai-content-generation-courses-in.html"
TITLE = "A Beginner's Learning Path for Free Generative AI Courses"
TAGS = ["ai", "productivity", "learning", "beginners"]
BODY = f'''# {TITLE}

Generative AI can write text, create images, summarize information, and help people explore ideas. The difficult part is learning how to use it responsibly instead of collecting random tool tutorials.

I researched a practical beginner path using free learning resources from Google, Microsoft, and IBM. The full course comparison is available on [Students Time]({CANONICAL}); this DEV version focuses on how to choose a path and turn the lessons into a small project.

## Start with the basics

Begin with a short introduction to generative AI. Learn the difference between traditional machine learning and tools that generate new text or images. You should understand that an AI response is a prediction, not automatically a verified fact.

Google’s Introduction to Generative AI is a useful starting point for this foundation. It covers basic concepts, model types, and common applications before you move into hands-on prompting.

## Learn prompting as a workflow

A useful prompt includes:

- the task you want completed;
- the audience and context;
- the information the tool may use;
- constraints such as length, tone, or format;
- a request to identify uncertainty instead of inventing details.

For example, instead of asking “Write a study guide,” try:

> Create a one-page study guide for a beginner learning Python functions. Use five short sections, include one example per section, and mark any concept that needs further checking. Do not invent citations.

Microsoft Learn’s foundational generative AI path is useful for practicing this kind of structured prompting and reviewing output responsibly.

## Add responsible AI checks

Before publishing or submitting AI-assisted work, check:

1. Are the facts current and supported by reliable sources?
2. Did the tool invent a quotation, link, statistic, or citation?
3. Does the content contain private or confidential information?
4. Is the wording original enough for the intended use?
5. Does the image or text have usage restrictions?

IBM SkillsBuild is a good option for learners who want ethics and risk awareness included with the technical basics.

## Build one small project

After completing a course, create a simple portfolio project:

1. Choose a topic you understand.
2. Generate two outlines with different prompts.
3. Check every factual claim against a primary source.
4. Edit the best outline into an original article or presentation.
5. Keep a short record of what the AI produced and what you corrected.

This demonstrates judgment, editing, and verification—not just the ability to copy a chatbot response.

## What “free” really means

Free learning and a free certificate are not always the same. Some providers offer lessons at no charge but charge for a certificate, require an account, or limit access to hands-on labs. Always check the current provider page before enrolling.

For the current course list and provider links, read the full [Free AI Content Generation Courses in 2026 guide]({CANONICAL}).

## Final takeaway

Start with one beginner course, practice structured prompts, and finish a small reviewed project. A credible course plus evidence of careful fact-checking is more useful than a long list of AI tools.

*This article is educational information. Course availability, pricing, and certificate rules can change; verify details with the provider.*
'''


def request(path, method="GET", payload=None):
    key = open(KEY_PATH, encoding="utf-8").read().strip()
    if not key:
        raise SystemExit("DEV API key file is empty")
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"api-key": key, "Accept": "application/vnd.forem.api-v1+json",
               "User-Agent": "students-time-draft-client/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        raise SystemExit(f"DEV API error {e.code}: {detail}")


def main():
    status, me = request("/users/me")
    print(f"Authenticated DEV user: @{me.get('username', '?')}")
    _, drafts = request("/articles/me/unpublished")
    for article in drafts if isinstance(drafts, list) else []:
        if article.get("title") == TITLE:
            print(f"DRAFT ALREADY EXISTS: {article.get('id')} {article.get('url', '')}")
            return
    status, result = request("/articles", method="POST", payload={"article": {
        "title": TITLE, "body_markdown": BODY, "published": False,
        "tags": TAGS, "canonical_url": CANONICAL,
    }})
    print(f"DEV DRAFT CREATED: {result.get('id')} | {result.get('url')} | published={result.get('published')}")


if __name__ == "__main__":
    main()
