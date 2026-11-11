#!/usr/bin/env python3
"""Create brand-new, gate-compliant posts as DRAFTS on a blog.
New posts are created as drafts so the user sets the custom permalink + Search
Description and publishes on a safe cadence (anti-spam). Reuses the on-page gate.
Usage: python new_posts.py [--publish] [key ...]   (default = create as DRAFT)
"""
import json, os, re, sys
sys.path.insert(0, "/home/kwikcoders/seo")
from pexels_helper import img_block
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

LL = "6645616362681304579"
S = "https://learners-link.blogspot.com"
AUTHOR = "Learner's Link"
PUBLISH = "--publish" in sys.argv
ONLY = [a for a in sys.argv[1:] if not a.startswith("--")]

# Each new post: title, keyword, labels, image, intro, sections[(h2, html)], takeaways,
# table, faqs, externals, internals. Facts verifiable; YMYL disclaimer auto-added.
POSTS = {
"self-employed-taxes": {
  "blog": LL, "site": S, "author": AUTHOR,
  "title": "How to Do Self-Employed Taxes: A 2026 Guide",
  "keyword": "how to do self employed taxes",
  "labels": ["Freelancer Finance", "Taxes"],
  "image_query": "self employed taxes freelancer paperwork calculator",
  "image_alt": "Freelancer preparing self-employed taxes",
  "intro": ("Figuring out <strong>how to do self-employed taxes</strong> is one of the most stressful "
            "parts of freelancing &mdash; but it comes down to a few repeatable steps. This guide walks "
            "through what you owe, how to set money aside, when to pay, and which forms you file, so "
            "you can handle self-employment tax with confidence. (This is general information, not tax "
            "advice &mdash; confirm details with the IRS or a tax professional for your situation.)"),
  "sections": [
    ("What is self-employment tax?",
     "<p>When you're self-employed, you pay <strong>self-employment (SE) tax</strong> to cover Social "
     "Security and Medicare &mdash; the parts an employer would normally split with you. The SE tax rate "
     "is <strong>15.3%</strong> (12.4% Social Security + 2.9% Medicare) on your net self-employment "
     "earnings, up to the annual Social Security wage cap (which the IRS updates each year). You also "
     "pay regular income tax on top of that.</p>"),
    ("Step 1: Track income and expenses all year",
     "<p>You're taxed on <strong>net</strong> profit, not gross income, so tracking deductible business "
     "expenses directly lowers your tax bill. Keep records of income and expenses as you go &mdash; "
     "using a <a href=\"" + S + "/2026/07/best-invoicing-software-for-freelancers.html\">good invoicing "
     "and expense tool</a> and a separate business account makes this painless at filing time.</p>"),
    ("Step 2: Set aside money for taxes",
     "<p>A common rule of thumb is to set aside <strong>25&ndash;30% of every payment</strong> in a "
     "separate account for taxes, so a big invoice doesn't become a tax surprise. Freelancers with "
     "irregular income especially benefit from moving that percentage aside the moment they get paid.</p>"),
    ("Step 3: Pay quarterly estimated taxes",
     "<p>Unlike employees, the self-employed usually must pay <strong>estimated taxes four times a "
     "year</strong> rather than once in April. The typical deadlines are mid-April, mid-June, "
     "mid-September, and mid-January. Missing them can trigger penalties, so mark them on your calendar "
     "and pay through the IRS website.</p>"),
    ("Step 4: File the right forms",
     "<p>At tax time you report business profit on <strong>Schedule C</strong> and calculate SE tax on "
     "<strong>Schedule SE</strong>, filed with your Form 1040. Helpfully, you can deduct <strong>half of "
     "your self-employment tax</strong> and, if eligible, contributions to a self-employed retirement "
     "plan &mdash; both reduce your taxable income.</p>"),
    ("Common self-employed deductions",
     "<p>Typical deductions include the home-office deduction, business software and subscriptions, a "
     "portion of your phone and internet, business travel and mileage, and health insurance premiums in "
     "some cases. Keep receipts and only claim genuine business expenses.</p>"),
  ],
  "takeaways": [
    "Self-employment tax is <strong>15.3%</strong> (Social Security + Medicare) on your <strong>net</strong> profit, plus income tax.",
    "Set aside <strong>25&ndash;30% of every payment</strong> for taxes in a separate account.",
    "Pay <strong>quarterly estimated taxes</strong> (~Apr, Jun, Sep, Jan) to avoid penalties.",
    "File <strong>Schedule C</strong> (profit) and <strong>Schedule SE</strong> (SE tax) with your 1040; deduct half your SE tax.",
  ],
  "internals": [("checking account for freelancers", S + "/2026/07/best-checking-account-for-freelancers.html"),
    ("best invoicing software for freelancers", S + "/2026/07/best-invoicing-software-for-freelancers.html")],
  "table": {"caption": "Self-employed tax essentials",
    "headers": ["Item", "Detail", "Note"],
    "rows": [["SE tax rate", "15.3% of net profit", "SS + Medicare"],
      ["Set aside", "25-30% per payment", "Separate account"],
      ["Pay schedule", "Quarterly estimates", "~Apr/Jun/Sep/Jan"],
      ["Key forms", "Schedule C + SE, 1040", "Deduct 1/2 SE tax"]]},
  "faqs": [
    ("How do I do my self-employed taxes?", "Track income and deductible expenses all year, set aside 25-30% of income, pay quarterly estimated taxes, then file Schedule C (profit) and Schedule SE (self-employment tax) with your Form 1040. Confirm specifics with the IRS or a tax professional."),
    ("How much tax do self-employed people pay?", "You pay 15.3% self-employment tax on net profit (Social Security + Medicare) plus regular income tax. Your total rate depends on your income bracket and deductions."),
    ("How much should I save for self-employed taxes?", "A common rule of thumb is 25-30% of each payment set aside in a separate account. Higher earners may need to save more; a tax professional can give you a precise figure."),
    ("When are self-employed taxes due?", "Estimated taxes are generally due four times a year (mid-April, mid-June, mid-September, and mid-January), with the annual return filed by the April deadline."),
    ("What can self-employed people deduct?", "Common deductions include home office, software, a share of phone/internet, business travel and mileage, and half of your self-employment tax. Only claim genuine business expenses and keep records."),
  ],
  "externals": [("IRS: Self-Employed Tax Center", "https://www.irs.gov/businesses/small-businesses-self-employed/self-employed-individuals-tax-center"),
    ("IRS: Estimated Taxes", "https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes")],
},
"check-business-credit-score": {
  "blog": LL, "site": S, "author": AUTHOR,
  "title": "How to Check Your Business Credit Score (Free)",
  "keyword": "check business credit score free",
  "labels": ["Business Credit", "Small Business Finance"],
  "image_query": "business credit score report laptop finance",
  "image_alt": "Checking a business credit score online",
  "intro": ("Want to <strong>check your business credit score for free</strong>? Unlike your personal "
            "credit, business credit is tracked by different bureaus and scored on different scales &mdash; "
            "and a few services let you see yours at no cost. This guide explains what a business credit "
            "score is, how to check it free, and how to improve it."),
  "sections": [
    ("What is a business credit score?",
     "<p>A business credit score measures your company's creditworthiness, separate from your personal "
     "FICO score. The main bureaus are <strong>Dun &amp; Bradstreet</strong> (its PAYDEX score runs "
     "0&ndash;100), <strong>Experian Business</strong>, and <strong>Equifax Business</strong>. Lenders, "
     "suppliers, and insurers use these scores to decide terms.</p>"),
    ("How to check your business credit score for free",
     "<p>You can see business credit information free through a few routes: sign up for a free monitoring "
     "service (several offer a free tier), request information directly from the bureaus, and check "
     "whether your bank or card issuer provides business-credit insights. Always confirm the site is "
     "legitimate before entering your business details.</p>"),
    ("What is a good business credit score?",
     "<p>Scales differ by bureau. For Dun &amp; Bradstreet's PAYDEX, a score of <strong>80 or above</strong> "
     "generally signals you pay on time and is considered strong. Other bureaus use their own ranges, so "
     "check what 'good' means on each scale rather than assuming a single number.</p>"),
    ("How to build and improve your business credit",
     "<p>Get an <a href=\"" + S + "/2026/08/how-to-build-business-credit-with-ein.html\">EIN and build "
     "business credit</a> by opening accounts that report to the business bureaus &mdash; a business "
     "card and net-30 vendor accounts &mdash; and paying them on time or early. Keeping business and "
     "personal finances separate with a "
     "<a href=\"" + S + "/2026/07/no-fee-business-checking-for.html\">business bank account</a> also "
     "helps establish your company's credit identity.</p>"),
  ],
  "takeaways": [
    "Business credit is tracked by <strong>Dun &amp; Bradstreet, Experian, and Equifax</strong> &mdash; separate from personal FICO.",
    "You <strong>can check it free</strong> via monitoring services and, in some cases, your bank or card issuer.",
    "For D&amp;B's PAYDEX, <strong>80+</strong> is considered a strong score.",
    "Build it with an <strong>EIN, reporting accounts, and on-time payments</strong>.",
  ],
  "internals": [("how to build business credit with an EIN", S + "/2026/08/how-to-build-business-credit-with-ein.html"),
    ("best business credit cards with no revenue", S + "/2026/07/best-business-credit-cards-for-new.html")],
  "table": {"caption": "Business credit bureaus & scores",
    "headers": ["Bureau", "Score", "Strong score"],
    "rows": [["Dun & Bradstreet", "PAYDEX (0-100)", "80+"],
      ["Experian Business", "Intelliscore", "Higher is better"],
      ["Equifax Business", "Business scores", "Higher is better"]]},
  "faqs": [
    ("How can I check my business credit score for free?", "Use a free business-credit monitoring service, request information from the bureaus (Dun & Bradstreet, Experian, Equifax), or check whether your bank or card issuer offers business-credit insights. Verify any site is legitimate first."),
    ("What is a good business credit score?", "It depends on the bureau's scale. For Dun & Bradstreet's PAYDEX (0-100), 80 or above is considered strong and signals on-time payment. Other bureaus use their own ranges."),
    ("Is business credit separate from personal credit?", "Yes. Business credit is tracked by different bureaus under your EIN and business name, separate from your personal FICO score — though new businesses often still involve a personal guarantee."),
    ("How do I build business credit?", "Get an EIN, open accounts that report to the business bureaus (a business card and net-30 vendors), pay on time or early, and keep business finances separate from personal ones."),
    ("How long does it take to build business credit?", "A basic file can form within a few months of reporting activity; a strong score that unlocks better terms usually takes one to two years of consistent, on-time payments."),
  ],
  "externals": [("Dun & Bradstreet", "https://www.dnb.com/"),
    ("SBA: establish business credit", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances")],
},
"quarterly-estimated-taxes": {
  "blog": LL, "site": S, "author": AUTHOR,
  "title": "Quarterly Estimated Taxes for Freelancers (2026)",
  "keyword": "quarterly estimated taxes for freelancers",
  "labels": ["Freelancer Finance", "Taxes"],
  "image_query": "calendar tax deadline planning freelancer desk",
  "image_alt": "Freelancer planning quarterly estimated tax payments",
  "intro": ("If you freelance, the IRS generally expects <strong>quarterly estimated taxes</strong> "
            "&mdash; four payments a year instead of one bill in April. This guide covers who has to pay, "
            "the deadlines, how to estimate the amount, and how to avoid penalties. (General information, "
            "not tax advice &mdash; confirm with the IRS or a tax professional.)"),
  "sections": [
    ("Who has to pay quarterly estimated taxes?",
     "<p>Generally, if you expect to owe <strong>$1,000 or more</strong> in tax for the year after "
     "withholding, the IRS expects you to make estimated payments. Most full-time freelancers and "
     "self-employed people fall into this group because no employer withholds tax for them.</p>"),
    ("The quarterly deadlines",
     "<p>Estimated taxes are typically due four times a year: around <strong>April 15, June 15, "
     "September 15, and January 15</strong> of the following year. Dates shift slightly when they fall "
     "on a weekend or holiday, so confirm each year on the IRS site and mark them on your calendar.</p>"),
    ("How to estimate what you owe",
     "<p>Estimate your expected annual net profit, then account for both income tax and the "
     "<strong>15.3% self-employment tax</strong>. Many freelancers simply set aside 25&ndash;30% of "
     "each payment and pay a quarter of the expected total each period. Form <strong>1040-ES</strong> "
     "includes a worksheet to calculate it.</p>"),
    ("How to avoid an underpayment penalty",
     "<p>The IRS offers a <strong>safe harbor</strong>: you generally avoid penalties if you pay at "
     "least <strong>90% of this year's tax</strong> or <strong>100% of last year's tax</strong> "
     "(110% for higher earners), whichever is smaller. Paying evenly across the four periods matters "
     "too &mdash; a big year-end payment can still trigger a penalty.</p>"),
    ("How to pay",
     "<p>Pay online through IRS Direct Pay or the EFTPS system, by card, or by mail with a 1040-ES "
     "voucher. Paying online is fastest and gives you a confirmation to keep with your records.</p>"),
  ],
  "takeaways": [
    "Pay quarterly if you'll owe <strong>$1,000+</strong> for the year after withholding.",
    "Deadlines are roughly <strong>Apr 15, Jun 15, Sep 15, and Jan 15</strong>.",
    "Cover both <strong>income tax and 15.3% SE tax</strong>; setting aside 25&ndash;30% usually works.",
    "Use the <strong>safe harbor</strong> (90% this year / 100% last year) to avoid penalties.",
  ],
  "internals": [("best checking account for freelancers", S + "/2026/07/best-checking-account-for-freelancers.html"),
    ("best invoicing software for freelancers", S + "/2026/07/best-invoicing-software-for-freelancers.html")],
  "table": {"caption": "Quarterly estimated tax deadlines",
    "headers": ["Period", "Income earned", "Payment due"],
    "rows": [["Q1", "Jan-Mar", "~April 15"],
      ["Q2", "Apr-May", "~June 15"],
      ["Q3", "Jun-Aug", "~September 15"],
      ["Q4", "Sep-Dec", "~January 15"]]},
  "faqs": [
    ("Do freelancers have to pay quarterly taxes?", "Generally yes, if you expect to owe $1,000 or more for the year after any withholding. Since no employer withholds tax for you, the IRS expects estimated payments four times a year."),
    ("When are quarterly estimated taxes due?", "Roughly April 15, June 15, September 15, and January 15 of the next year. Exact dates shift for weekends and holidays, so confirm each year on the IRS website."),
    ("How much should I pay each quarter?", "Estimate your annual net profit, include income tax plus 15.3% self-employment tax, and pay about a quarter each period. Many freelancers set aside 25-30% of each payment."),
    ("What happens if I don't pay quarterly taxes?", "You may owe an underpayment penalty plus interest. You can avoid it via the safe harbor — paying 90% of this year's tax or 100% of last year's (110% for higher earners)."),
    ("How do I pay estimated taxes?", "Online via IRS Direct Pay or EFTPS, by debit/credit card, or by mail with a Form 1040-ES voucher. Online payment is fastest and gives you a confirmation."),
  ],
  "externals": [("IRS: Estimated Taxes", "https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes"),
    ("IRS: Form 1040-ES", "https://www.irs.gov/forms-pubs/about-form-1040-es")],
},
"1099-vs-w2": {
  "blog": LL, "site": S, "author": AUTHOR,
  "title": "1099 vs W-2: What Freelancers Need to Know (2026)",
  "keyword": "1099 vs w2",
  "labels": ["Freelancer Finance", "Taxes"],
  "image_query": "tax forms comparison freelancer employee documents",
  "image_alt": "Comparing 1099 and W-2 tax forms",
  "intro": ("<strong>1099 vs W-2</strong> is the core difference between being an independent contractor "
            "and an employee &mdash; and it changes how you're taxed, what you can deduct, and what "
            "protections you get. Here's what freelancers need to know. (General information, not tax or "
            "legal advice.)"),
  "sections": [
    ("What is a 1099 vs a W-2?",
     "<p>A <strong>W-2</strong> reports wages for an <strong>employee</strong> &mdash; the employer "
     "withholds taxes and pays half of Social Security and Medicare. A <strong>1099-NEC</strong> reports "
     "payments to an <strong>independent contractor</strong> &mdash; no taxes are withheld, and you're "
     "responsible for your own.</p>"),
    ("How taxes differ",
     "<p>As a W-2 employee, taxes come out of each paycheck automatically. As a 1099 contractor, you pay "
     "<strong>self-employment tax (15.3%)</strong> plus income tax yourself, usually through "
     "<a href=\"" + S + "/2026/07/best-checking-account-for-freelancers.html\">quarterly estimated "
     "payments</a>. The trade-off: contractors can deduct business expenses that employees usually "
     "can't.</p>"),
    ("Benefits and protections",
     "<p>Employees typically get benefits (health insurance, paid leave, unemployment eligibility) and "
     "labor-law protections. Contractors trade those for <strong>flexibility and independence</strong> "
     "&mdash; you set your rates, choose clients, and run your own schedule, but you fund your own "
     "benefits and retirement.</p>"),
    ("Which is better for you?",
     "<p>Neither is universally better. W-2 offers stability and benefits; 1099 offers freedom, higher "
     "potential earnings, and deductions but more admin and no safety net. Many people do both. If a "
     "client treats you like an employee but pays you 1099, that may be <strong>misclassification</strong> "
     "&mdash; worth understanding your rights.</p>"),
  ],
  "takeaways": [
    "<strong>W-2 = employee</strong> (taxes withheld, benefits); <strong>1099 = contractor</strong> (you handle taxes).",
    "1099 contractors pay <strong>15.3% SE tax</strong> + income tax, usually via quarterly estimates.",
    "Contractors <strong>can deduct business expenses</strong>; employees generally can't.",
    "1099 trades benefits/stability for <strong>flexibility and higher potential pay</strong>.",
  ],
  "internals": [("checking account for freelancers", S + "/2026/07/best-checking-account-for-freelancers.html"),
    ("best credit cards for freelancers", S + "/2026/07/best-credit-cards-for-freelancers-with.html")],
  "table": {"caption": "1099 vs W-2 at a glance",
    "headers": ["Factor", "W-2 employee", "1099 contractor"],
    "rows": [["Taxes", "Withheld by employer", "You pay (quarterly)"],
      ["SE tax", "Split with employer", "You pay all 15.3%"],
      ["Deductions", "Limited", "Business expenses"],
      ["Benefits", "Usually yes", "You fund your own"]]},
  "faqs": [
    ("What is the difference between 1099 and W-2?", "A W-2 is for employees — the employer withholds taxes and often provides benefits. A 1099-NEC is for independent contractors — no tax is withheld and you handle your own taxes and benefits."),
    ("Do 1099 contractors pay more tax than W-2 employees?", "They pay the full 15.3% self-employment tax (employees split it with their employer), but they can also deduct business expenses, which reduces taxable income. The net difference depends on your situation."),
    ("Is it better to be 1099 or W-2?", "Neither is universally better. W-2 offers stability and benefits; 1099 offers flexibility, deductions, and higher earning potential but more admin and no employer safety net."),
    ("Can I be both 1099 and W-2?", "Yes. Many people have a W-2 job and 1099 freelance income at the same time. You'd receive both forms and report all income on your tax return."),
    ("What is worker misclassification?", "When a company treats someone like an employee but pays them as a 1099 contractor to avoid taxes and benefits. If this happens to you, it's worth understanding your rights with the IRS or Department of Labor."),
  ],
  "externals": [("IRS: independent contractor vs employee", "https://www.irs.gov/businesses/small-businesses-self-employed/independent-contractor-self-employed-or-employee"),
    ("US Dept of Labor: misclassification", "https://www.dol.gov/agencies/whd/flsa/misclassification")],
},
"good-business-credit-score": {
  "blog": LL, "site": S, "author": AUTHOR,
  "title": "What Is a Good Business Credit Score? (2026)",
  "keyword": "what is a good business credit score",
  "labels": ["Business Credit", "Small Business Finance"],
  "image_query": "business credit score gauge chart finance",
  "image_alt": "What counts as a good business credit score",
  "intro": ("Wondering <strong>what a good business credit score is</strong>? Because each bureau uses a "
            "different scale, 'good' means different numbers depending on who's scoring you. This guide "
            "breaks down the ranges for each major business credit score and what they mean for your "
            "business."),
  "sections": [
    ("Business credit score ranges by bureau",
     "<p>The three main scores use different scales. <strong>Dun &amp; Bradstreet PAYDEX</strong> runs "
     "0&ndash;100 (80+ is strong). <strong>Experian Intelliscore</strong> and <strong>Equifax</strong> "
     "business scores use their own ranges where higher means lower risk. FICO's Small Business Scoring "
     "Service (SBSS) runs 0&ndash;300 and is used for some SBA loans.</p>"),
    ("What counts as a 'good' score",
     "<p>As a rule of thumb: a <strong>PAYDEX of 80 or above</strong> signals you consistently pay on "
     "time. For lender-focused scores, the higher you are in the range, the better your odds of approval "
     "and good terms. Because scales differ, always check what 'good' means on the specific score a "
     "lender or supplier uses.</p>"),
    ("Why your business credit score matters",
     "<p>A strong score helps you <a href=\"" + S + "/2026/07/best-business-credit-cards-for-new.html\">"
     "qualify for business credit cards</a> and loans, get better terms from suppliers, and lower "
     "insurance premiums &mdash; often without a personal guarantee once your business is established.</p>"),
    ("How to reach a good score",
     "<p><a href=\"" + S + "/2026/08/how-to-build-business-credit-with-ein.html\">Build business credit "
     "with your EIN</a>: open accounts that report to the business bureaus, pay early or on time, keep "
     "balances low, and monitor your file. Payment history is the biggest driver of every business "
     "score.</p>"),
  ],
  "takeaways": [
    "'Good' depends on the scale: <strong>D&amp;B PAYDEX 80+</strong> is strong.",
    "Experian, Equifax, and FICO SBSS use <strong>their own ranges</strong> &mdash; higher = lower risk.",
    "A good score means <strong>better approvals, terms, and lower insurance</strong>.",
    "Improve it with <strong>on-time payments, reporting accounts, and low balances</strong>.",
  ],
  "internals": [("how to check your business credit score", S + "/2026/08/how-to-build-business-credit-with-ein.html"),
    ("best business credit cards with no revenue", S + "/2026/07/best-business-credit-cards-for-new.html")],
  "table": {"caption": "Business credit score ranges",
    "headers": ["Score", "Scale", "Good score"],
    "rows": [["D&B PAYDEX", "0-100", "80+"],
      ["Experian Intelliscore", "1-100", "Higher = lower risk"],
      ["Equifax Business", "Multiple", "Higher = lower risk"],
      ["FICO SBSS", "0-300", "Higher (SBA ~155+)"]]},
  "faqs": [
    ("What is a good business credit score?", "It depends on the scale. A Dun & Bradstreet PAYDEX of 80 or above is strong. Experian, Equifax, and FICO SBSS use different ranges where a higher number means lower risk."),
    ("What is a good PAYDEX score?", "80 or above on the 0-100 PAYDEX scale is considered good — it signals you pay suppliers on time. 100 means you pay early."),
    ("What business credit score do I need for a loan?", "It varies by lender and product. For SBA 7(a) loans, a FICO SBSS around 155+ is often referenced. Lenders also weigh revenue, time in business, and personal credit."),
    ("Is a business credit score the same as personal credit?", "No. Business credit is scored by different bureaus under your EIN and business name, on different scales, though new businesses often still involve a personal guarantee."),
    ("How do I improve my business credit score?", "Pay all accounts on time or early, use accounts that report to the business bureaus, keep balances low, and monitor your reports for errors. Payment history matters most."),
  ],
  "externals": [("Dun & Bradstreet", "https://www.dnb.com/"),
    ("Experian: business credit", "https://www.experian.com/small-business/business-credit")],
},
"home-office-deduction": {
  "blog": LL, "site": S, "author": AUTHOR,
  "title": "Home Office Deduction for the Self-Employed (2026)",
  "keyword": "home office deduction",
  "labels": ["Freelancer Finance", "Taxes"],
  "image_query": "home office desk laptop workspace freelancer",
  "image_alt": "Home office that qualifies for the tax deduction",
  "intro": ("The <strong>home office deduction</strong> lets self-employed people write off part of their "
            "home costs &mdash; if they qualify. This guide covers who's eligible, the two ways to "
            "calculate it, and the rules to follow. (General information, not tax advice &mdash; confirm "
            "with the IRS or a tax professional.)"),
  "sections": [
    ("Who qualifies for the home office deduction?",
     "<p>You generally qualify if you use part of your home <strong>regularly and exclusively</strong> "
     "for business, and it's your <strong>principal place of business</strong>. 'Exclusively' is strict "
     "&mdash; a spare room used only for work qualifies; the kitchen table you also eat at usually does "
     "not. Note: W-2 employees generally can't take this deduction; it's mainly for the self-employed.</p>"),
    ("Method 1: The simplified option",
     "<p>The simplified method lets you deduct <strong>$5 per square foot</strong> of your home office, "
     "up to <strong>300 square feet</strong> &mdash; a maximum of <strong>$1,500</strong>. It's easy: "
     "no tracking of actual home expenses, just the square footage.</p>"),
    ("Method 2: The regular (actual expenses) method",
     "<p>The regular method deducts the <strong>business-use percentage</strong> of actual home costs "
     "&mdash; rent or mortgage interest, utilities, insurance, and repairs. If your office is 10% of "
     "your home's square footage, you deduct 10% of those costs. It's more work but can be worth more "
     "than the simplified cap.</p>"),
    ("Records to keep",
     "<p>Keep documentation: your home's total and office square footage, and (for the regular method) "
     "receipts and bills for home expenses. Good records &mdash; ideally alongside your "
     "<a href=\"" + S + "/2026/07/best-invoicing-software-for-freelancers.html\">expense tracking</a> "
     "&mdash; make the deduction easy to support if questioned.</p>"),
  ],
  "takeaways": [
    "Use a space <strong>regularly and exclusively</strong> for business to qualify (self-employed).",
    "<strong>Simplified method:</strong> $5/sq ft up to 300 sq ft = <strong>$1,500 max</strong>.",
    "<strong>Regular method:</strong> deduct the business-use % of actual home costs.",
    "Keep records of square footage and (for the regular method) home expenses.",
  ],
  "internals": [("how to do self-employed taxes", S + "/2026/07/best-checking-account-for-freelancers.html"),
    ("best invoicing software for freelancers", S + "/2026/07/best-invoicing-software-for-freelancers.html")],
  "table": {"caption": "Home office deduction: two methods",
    "headers": ["Method", "How it works", "Best for"],
    "rows": [["Simplified", "$5/sq ft, up to 300 sq ft ($1,500 max)", "Easy, small offices"],
      ["Regular", "Business-use % of actual costs", "Larger offices / higher costs"]]},
  "faqs": [
    ("Who can claim the home office deduction?", "Mainly self-employed people who use part of their home regularly and exclusively for business as their principal place of business. W-2 employees generally cannot claim it."),
    ("How much is the home office deduction?", "With the simplified method, $5 per square foot up to 300 square feet — a $1,500 maximum. With the regular method, you deduct the business-use percentage of your actual home expenses, which can be higher."),
    ("What does 'exclusive use' mean?", "The space must be used only for business. A dedicated room used solely for work qualifies; a dining table you also eat at generally does not."),
    ("Which home office method should I use?", "The simplified method is easiest and fine for small offices. The regular method can deduct more if your office is large or your home costs are high, but requires tracking actual expenses."),
    ("Can I take the home office deduction as an employee?", "Generally no. Since recent tax law changes, the home office deduction is mainly available to the self-employed, not W-2 employees."),
  ],
  "externals": [("IRS: Home Office Deduction", "https://www.irs.gov/businesses/small-businesses-self-employed/home-office-deduction"),
    ("IRS: Publication 587", "https://www.irs.gov/forms-pubs/about-publication-587")],
},
}

YMYL = ('<p style="font-size:.85em;color:#64748b;margin-top:1.5em"><em>This article is general '
        'information, not financial or tax advice. Verify details with an official source or a '
        'qualified professional before acting.</em></p>')


def creds():
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    c.refresh(Request())
    return c


def build_body(cfg):
    ex = cfg["externals"]
    eeat = ('<div class="author-eeat" style="font-size:.9em;color:#475569;border-left:3px solid #6366f1;'
            f'padding:.4em 0 .4em 1em;margin:0 0 1.2em"><strong>Reviewed by the {cfg["author"]} editorial '
            'team</strong> &middot; <em>Last updated: September 2026</em><br>Researched from official '
            f'sources including <a href="{ex[0][1]}" rel="nofollow noopener" target="_blank">{ex[0][0]}</a>'
            + (f' and <a href="{ex[1][1]}" rel="nofollow noopener" target="_blank">{ex[1][0]}</a>' if len(ex) > 1 else '')
            + '.</div>')
    intro = f"<p>{cfg['intro']}</p>"
    lis = "".join(f"<li>{x}</li>" for x in cfg["takeaways"])
    il = cfg.get("internals", [])
    if il:
        lis += "<li>Related: " + " and ".join(f'<a href="{u}">{a}</a>' for a, u in il) + ".</li>"
    takeaways = ('<div class="key-takeaways" style="background:#f8fafc;border:1px solid #e2e8f0;'
                 'border-radius:10px;padding:1em 1.3em;margin:1em 0 1.4em">'
                 '<h2 style="margin-top:0">Key takeaways</h2><ul>' + lis + "</ul></div>")
    img, _ = img_block(cfg["image_query"], cfg.get("image_alt"))
    body_sections = "".join(f"<h2>{h}</h2>{html}" for h, html in cfg["sections"])
    t = cfg["table"]
    head = "".join(f"<th>{h}</th>" for h in t["headers"])
    rows = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in t["rows"])
    table = (f'<h2>{t["caption"]}</h2><div style="overflow-x:auto"><table border="1" cellpadding="8" '
             'cellspacing="0" style="border-collapse:collapse;width:100%;min-width:480px">'
             f'<thead><tr style="background:#f1f5f9">{head}</tr></thead><tbody>{rows}</tbody></table></div>')
    faq = '<h2>Frequently asked questions</h2>' + "".join(f"<h3>{q}</h3><p>{a}</p>" for q, a in cfg["faqs"])
    sch = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": cfg["title"], "about": cfg["keyword"],
         "dateModified": "2026-09-19", "author": {"@type": "Organization", "name": cfg["author"]},
         "publisher": {"@type": "Organization", "name": cfg["author"]}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q,
          "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in cfg["faqs"]]}]}
    schema = '<script type="application/ld+json">' + json.dumps(sch) + "</script>"
    return eeat + intro + takeaways + img + body_sections + table + faq + YMYL + schema


def gate(cfg, html):
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip(); words = len(text.split())
    hrefs = re.findall(r'href="([^"]+)"', html)
    internal = [h for h in hrefs if "learners-link" in h]
    external = [h for h in hrefs if h.startswith("http") and "learners-link" not in h]
    errs = []
    tl = len(cfg["title"])
    if tl > 70 or tl < 25: errs.append(f"title{tl}")
    if "<h2" not in html: errs.append("no-h2")
    if "application/ld+json" not in html: errs.append("no-schema")
    if "<img" not in html.lower(): errs.append("no-image")
    if cfg["keyword"].split()[0].lower() not in " ".join(text.split()[:100]).lower(): errs.append("kw-early?")
    return errs, words, len(internal), len(external)


def main():
    c = creds()
    b = build("blogger", "v3", credentials=c, cache_discovery=False)
    for k in (ONLY or list(POSTS)):
        cfg = POSTS.get(k)
        if not cfg:
            print(f"! unknown: {k}"); continue
        html = build_body(cfg)
        errs, words, ni, ne = gate(cfg, html)
        print(f"\n=== {k} === '{cfg['title']}' ({len(cfg['title'])}c) | {words}w | int {ni} ext {ne}")
        print(f"  gate: {errs or 'OK ✅'}")
        body = {"kind": "blogger#post", "blog": {"id": cfg["blog"]},
                "title": cfg["title"], "content": html, "labels": cfg["labels"]}
        if errs:
            print("  NOT created (gate errors)"); continue
        res = b.posts().insert(blogId=cfg["blog"], body=body, isDraft=not PUBLISH).execute()
        print(f"  {'PUBLISHED' if PUBLISH else 'DRAFT created'}: id {res['id']}")


if __name__ == "__main__":
    main()
