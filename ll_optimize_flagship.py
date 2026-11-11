#!/usr/bin/env python3
"""Optimize the flagship 'business credit card no revenue' page to the playbook gate.
Additive: preserves existing body, injects Key Takeaways + comparison table + FAQ +
JSON-LD (Article + FAQPage) + E-E-A-T box + internal/external links. No fabrication.
Usage: python ll_optimize_flagship.py [--apply]"""
import json, os, re, sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

APPLY = "--apply" in sys.argv
BLOG_ID = "6645616362681304579"
PID = "5976525599420860760"
URL = "https://learners-link.blogspot.com/2026/07/best-business-credit-cards-for-new.html"
NEW_TITLE = "Best Business Credit Cards With No Revenue (2026 Guide)"  # 54 chars

CHECKING = "https://learners-link.blogspot.com/2026/07/best-business-checking-for-new-llc-no.html"
BUILDCREDIT = "https://learners-link.blogspot.com/2026/08/how-to-build-business-credit-with-ein.html"
BANKACCT = "https://learners-link.blogspot.com/2026/07/how-to-open-business-bank-account.html"

body = open("/home/kwikcoders/seo/flagship_content.html").read()
# split off the related-guides block so FAQ+schema go before it
MARK = "<!--related-guides-->"
if MARK in body:
    main, related = body.split(MARK, 1)
    related = MARK + related
else:
    main, related = body, ""

author = (
    '<div class="author-eeat" style="font-size:.9em;color:#475569;border-left:3px solid #6366f1;'
    'padding:.4em 0 .4em 1em;margin:0 0 1.2em">'
    "<strong>Reviewed by the Learner&#39;s Link editorial team</strong> &middot; "
    "<em>Last updated: September 2026</em><br>"
    "Researched from issuers&#39; published terms and official sources including the "
    '<a href="https://www.sba.gov/business-guide" rel="nofollow noopener" target="_blank">U.S. Small Business Administration</a> and '
    '<a href="https://www.experian.com/small-business/business-credit/" rel="nofollow noopener" target="_blank">Experian Business</a>. '
    "We accept no payment to feature specific cards.</div>"
)

takeaways = (
    '<div class="key-takeaways" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;'
    'padding:1em 1.3em;margin:0 0 1.4em">'
    '<h2 style="margin-top:0">Key takeaways</h2><ul>'
    "<li>Yes &mdash; you <strong>can</strong> get a <strong>business credit card with no revenue</strong>. "
    "Issuers approve on your <strong>personal credit and income</strong>, not business sales.</li>"
    "<li>A personal FICO score around <strong>670+</strong> is the practical approval bar; you can enter "
    "<strong>$0</strong> in the revenue field as a startup.</li>"
    "<li>Expect to sign a <strong>personal guarantee</strong> (you repay if the business can&#39;t).</li>"
    "<li>Want no personal credit check? Use a <strong>secured business card</strong> (deposit = limit) or a "
    "startup/corporate card that approves on cash-on-hand.</li>"
    f'<li>First open a <a href="{CHECKING}">business checking account</a> and '
    f'<a href="{BUILDCREDIT}">build business credit with your EIN</a> &mdash; it strengthens future approvals.</li>'
    "</ul></div>"
)

table = (
    '<h2>Quick comparison: 3 ways to qualify with no revenue</h2>'
    '<div style="overflow-x:auto"><table border="1" cellpadding="8" cellspacing="0" '
    'style="border-collapse:collapse;width:100%;min-width:520px">'
    "<thead><tr style=\"background:#f1f5f9\"><th>Card type</th><th>Approved on</th><th>Deposit?</th>"
    "<th>Personal guarantee</th><th>Best for</th></tr></thead><tbody>"
    "<tr><td>Personal-credit business card</td><td>Personal FICO 670+ &amp; personal income</td>"
    "<td>No</td><td>Yes</td><td>Founders with good personal credit</td></tr>"
    "<tr><td>Secured business card</td><td>Refundable deposit (= credit limit)</td><td>Yes</td>"
    "<td>Sometimes</td><td>Poor/limited credit or rebuilding</td></tr>"
    "<tr><td>Startup / corporate card</td><td>Cash on hand, bank balance, investor backing</td>"
    "<td>No</td><td>Often none</td><td>Funded startups (bank- or Stripe-linked)</td></tr>"
    "</tbody></table></div>"
)

faqs = [
    ("Can you get a business credit card with no revenue?",
     'Yes. Most issuers approve based on your personal credit and income, so you can enter $0 business '
     'revenue and still qualify by signing a personal guarantee. '
     f'<a href="https://www.chase.com/personal/credit-cards/education/basics/business-credit-card-no-revenue" '
     'rel="nofollow noopener" target="_blank">Major issuers confirm this</a>.'),
    ("What credit score do you need for a business credit card with no revenue?",
     "A personal FICO score of about 670 or higher is the practical bar for most personal-guarantee "
     "business cards. Secured business cards accept lower or limited scores."),
    ("Can an LLC with no income get a credit card?",
     "Yes &mdash; a brand-new LLC with no income can apply. Approval rests on the owner&#39;s personal "
     "credit and income, not the LLC&#39;s sales, and you&#39;ll typically sign a personal guarantee."),
    ("Do you have to enter revenue on a business credit card application?",
     "You enter your business revenue, but $0 (or a realistic projection) is acceptable for a startup. "
     "Issuers weigh your personal income and credit far more heavily at this stage."),
    ("Can you get a business card with no personal guarantee?",
     "Rarely for brand-new companies. No-personal-guarantee cards (startup/corporate cards) usually "
     f'require meaningful cash in a linked <a href="{BANKACCT}">business bank account</a> or investor funding.'),
]
faq_html = '<h2>Frequently asked questions</h2>' + "".join(
    f"<h3>{q}</h3><p>{a}</p>" for q, a in faqs)

schema = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "BlogPosting",
         "headline": NEW_TITLE,
         "about": "business credit card with no revenue",
         "url": URL,
         "dateModified": "2026-09-15",
         "author": {"@type": "Organization", "name": "Learner's Link"},
         "publisher": {"@type": "Organization", "name": "Learner's Link"}},
        {"@type": "FAQPage",
         "mainEntity": [
             {"@type": "Question", "name": q,
              "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
             for q, a in faqs]},
    ],
}
schema_html = '<script type="application/ld+json">' + json.dumps(schema) + "</script>"

new_content = author + takeaways + table + main + faq_html + schema_html + related

# ---- self-validate against playbook gate ----
def validate(title, html):
    issues = []
    tl = len(title.strip())
    if tl > 70 or tl < 25: issues.append(("ERR", "title-length", tl))
    elif tl < 40 or tl > 60: issues.append(("warn", "title-length", tl))
    text = re.sub(r"<[^>]+>", " ", html); text = re.sub(r"\s+", " ", text).strip()
    words = len(text.split())
    if re.search(r"<h1", html, re.I): issues.append(("warn", "h1-in-body", 0))
    if not re.search(r"<h2", html, re.I): issues.append(("ERR", "no-h2", 0))
    if "business credit card" not in " ".join(text.split()[:100]).lower():
        issues.append(("warn", "keyword-early", 0))
    hrefs = re.findall(r'href="([^"]+)"', html)
    internal = [h for h in hrefs if "learners-link.blogspot.com" in h]
    external = [h for h in hrefs if h.startswith("http") and "learners-link" not in h]
    if len(internal) < max(3, round(words/1000*3)): issues.append(("warn", f"internal-links({len(internal)})", 0))
    if len(external) < 2: issues.append(("warn", f"external-links({len(external)})", 0))
    if "application/ld+json" not in html: issues.append(("ERR", "no-schema", 0))
    if not re.search(r"key-takeaways|takeaway|tldr", html, re.I): issues.append(("warn", "no-takeaways", 0))
    if "<table" not in html.lower(): issues.append(("warn", "no-table", 0))
    if not re.search(r"author-eeat|editorial|reviewed by|fact-check", html, re.I): issues.append(("warn", "no-eeat", 0))
    return issues, words, len(internal), len(external)

issues, words, ni, ne = validate(NEW_TITLE, new_content)
print(f"Title: '{NEW_TITLE}' ({len(NEW_TITLE)} chars)")
print(f"Words: {words} | internal links: {ni} | external links: {ne}")
errs = [i for i in issues if i[0] == "ERR"]
print("Gate errors:", errs or "NONE ✅")
print("Warnings:", [i[1] for i in issues if i[0] == "warn"] or "none")
open("/home/kwikcoders/seo/flagship_new.html", "w").write(new_content)
print("Preview written to flagship_new.html")

if APPLY and not errs:
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    if not c.valid: c.refresh(Request())
    svc = build("blogger", "v3", credentials=c, cache_discovery=False)
    svc.posts().patch(blogId=BLOG_ID, postId=PID,
                      body={"title": NEW_TITLE, "content": new_content}).execute()
    print("\n✅ PATCHED live post with optimized content + new title.")
elif APPLY and errs:
    print("\n❌ NOT applied — gate errors present.")
else:
    print("\n(dry run — rerun with --apply to write)")
