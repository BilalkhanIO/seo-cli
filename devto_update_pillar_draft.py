#!/usr/bin/env python3
"""Update the existing DEV draft for the refreshed Students Time pillar."""
import json
import urllib.request
import urllib.error

KEY_PATH = "/home/kwikcoders/seo/devto_api_key.txt"
ARTICLE_ID = "4926030"
API = "https://dev.to/api"
CANONICAL = "https://studenttimepk.blogspot.com/2026/07/free-ai-courses-with-certificates-in.html"
TITLE = "How to Choose Free AI Courses With Certificates in 2026"
TAGS = ["ai", "learning", "beginners", "career"]
BODY = f'''# {TITLE}

“Free AI course” can mean several different things: free lessons, a free digital badge, a free certificate of completion, or free training that prepares you for a paid exam. Before spending time on a course, check which result you will actually receive.

This DEV guide summarizes the updated comparison on [Students Time]({CANONICAL}) and focuses on how developers, students, and career changers can choose a useful learning path.

## Start with the credential terms

- **Free course:** the lessons are available without payment.
- **Free certificate:** the provider issues a certificate at no charge after its requirements are met.
- **Free badge:** the provider issues a shareable digital credential, often after an assessment.
- **Free training, paid exam:** the preparation is free, but a vendor certification exam costs money.
- **Free trial:** access is temporary and may renew as a paid subscription.

A badge is not automatically a professional certification. Use the provider’s exact wording on your CV.

## Good starting points

### OpenAI Academy AI Foundations

This is a short beginner course on AI basics, prompting, context, reviewing outputs, and responsible use. Learners can earn a badge after completing the course and assessment. It is useful for someone who wants practical AI habits without a technical prerequisite.

### Google Cloud Introduction to Generative AI

This introductory course explains what generative AI is, how it differs from traditional machine learning, common model types, and typical applications. It is a good vocabulary-building step before learning APIs or model development.

### Microsoft Learn foundational generative AI skills

Microsoft’s learning path covers generative-AI fundamentals, Copilot Chat, prompt writing, research, content creation, file analysis, and visualization. The available Copilot experience can depend on the learner’s account, license, and organization settings.

### IBM SkillsBuild

IBM’s beginner material combines generative-AI foundations with ethics, risks, prompting, and practical use cases. Its digital credential path is useful for learners who want a shareable record, but account or program conditions may apply.

### Google AI Essentials

Google AI Essentials focuses on practical workplace use, including prompting and productivity. Access and pricing vary by country and platform, so check the current enrollment terms before calling the certificate free.

## Choose by your goal

**For developers:** start with AI literacy, then move to APIs, evaluation, retrieval, security, and deployment. A general prompting course is not the same as technical model-building training.

**For students:** choose courses that explain responsible use, research verification, and academic integrity. Build a study-planning or source-checking project rather than submitting raw AI output.

**For content creators:** practise prompting, editing, fact-checking, image briefs, and usage-rights checks. Keep a record of what you changed in the final work.

**For job seekers:** pair one credential with a portfolio artifact. Explain the task, tool, review process, privacy controls, and outcome.

## A four-week completion plan

1. Choose one course and define the skill you want.
2. Complete the foundation and write down the important terms.
3. Practise prompts on a non-confidential task.
4. Build a small project and verify every important claim.
5. Complete the assessment and save the credential details.
6. Document the project in a portfolio or CV.

## What to verify before enrolling

Check whether the course is available in your country, whether assessments are included, whether the credential is a badge or certificate, whether a lab or exam costs extra, and when the provider last updated the material. Course pricing and credential policies can change quickly.

## Final advice

One finished course and one reviewed project are more valuable than ten bookmarked course pages. Learn the concepts, practise a real workflow, check the output, and describe the credential honestly.

For the complete comparison table and provider links, read the [updated Free AI Courses With Certificates guide]({CANONICAL}).

*This article is educational information. Verify current course access, pricing, and credential requirements with the provider.*
'''


def call(path, method="GET", payload=None):
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
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"DEV API error {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")


def main():
    result = call(f"/articles/{ARTICLE_ID}", method="PUT", payload={"article": {
        "title": TITLE, "body_markdown": BODY, "published": False,
        "tags": TAGS, "canonical_url": CANONICAL,
    }})
    print(f"DEV DRAFT UPDATED: {result.get('id')} | {result.get('url')} | published={result.get('published')}")


if __name__ == "__main__":
    main()
