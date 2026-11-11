#!/usr/bin/env python3
"""Reusable striking-distance optimizer for Learner's Link (Blogger).
Applies the on-page gate (playbook §4 / validate.ts / slide-13 checklist):
E-E-A-T box + Key Takeaways (w/ internal links) + Pexels image + comparison table +
FAQ + JSON-LD (BlogPosting + FAQPage) + external authority links. Idempotent per block.
Self-validates before pushing; pings Google Indexing API after.
Usage: python seo_optimize.py [--apply] [page_key ...]"""
import json, os, re, sys, urllib.request
sys.path.insert(0, "/home/kwikcoders/seo")
from pexels_helper import img_block
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BLOG_ID = "6645616362681304579"
S = "https://learners-link.blogspot.com"
APPLY = "--apply" in sys.argv
ONLY = [a for a in sys.argv[1:] if not a.startswith("--")]

# ---- page configs (authored; facts verifiable, no fabricated products/rates) ----
PAGES = {
"no-fee-business-checking": {
  "id": "1506865949947533873",
  "url": f"{S}/2026/07/no-fee-business-checking-for.html",
  "title": "No-Fee Business Checking for Freelancers (2026)",
  "keyword": "no-fee business checking for freelancers",
  "image_query": "freelancer business banking laptop desk",
  "image_alt": "Freelancer managing a no-fee business checking account on a laptop",
  "takeaways": [
    "Freelancers and sole proprietors <strong>can open no-fee business checking</strong> with no minimum balance and no monthly maintenance fee.",
    "Look for: <strong>$0 monthly fee, no minimum balance, free ACH transfers, a free debit card, and FDIC insurance</strong> up to $250,000.",
    "Online-first banks and fintechs usually beat big banks on fees; most need only your SSN or EIN and a photo ID to open.",
    "Keeping business and personal money separate protects your liability and makes tax time far simpler.",
  ],
  "internals": [
    ("open a business bank account without an EIN", f"{S}/2026/07/how-to-open-business-bank-account.html"),
    ("build business credit with your EIN", f"{S}/2026/08/how-to-build-business-credit-with-ein.html"),
  ],
  "table": {"caption": "No-fee business checking: where freelancers should look",
    "headers": ["Account type", "Monthly fee", "Min balance", "Best for"],
    "rows": [
      ["Online business checking", "$0", "None", "Freelancers who bank digitally"],
      ["Fintech / neobank", "$0", "None", "Fast sign-up, built-in invoicing"],
      ["Big-bank business checking", "$0-15 (waivable)", "Often required", "Cash deposits / branch access"],
    ]},
  "faqs": [
    ("Can freelancers get free business checking?",
     "Yes. Many online banks and fintechs offer business checking with no monthly fee and no minimum balance, aimed specifically at freelancers and sole proprietors."),
    ("Do you need an LLC to open a business checking account?",
     "No. Sole proprietors can open business checking without an LLC, though an LLC adds liability separation. You typically apply with your SSN (or EIN if you have one)."),
    ("Do you need an EIN for business checking?",
     "Not always. Sole proprietors can often use their SSN. An EIN is required if you have employees or run as an LLC/corporation, and it is free from the IRS."),
    ("Is business checking FDIC insured?",
     "At an FDIC-member bank, business deposits are insured up to $250,000 per depositor, per bank. Verify the bank on the FDIC BankFind tool."),
    ("Is an online bank safe for my business money?",
     "Yes, as long as the bank (or its partner bank) is FDIC insured. Online banks generally charge lower fees than branch banks."),
  ],
  "externals": [
    ("FDIC deposit insurance", "https://www.fdic.gov/resources/deposit-insurance/"),
    ("IRS: apply for an EIN (free)", "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online"),
  ],
},
"savings-europe": {
  "id": "2129285932404875042",
  "url": f"{S}/2026/08/best-savings-accounts-in-europe-2026.html",
  "title": "Best Savings Accounts in Europe (2026 Guide)",
  "keyword": "best savings accounts in europe",
  "image_query": "euro money savings coins europe",
  "image_alt": "Euro notes and coins representing savings accounts in Europe",
  "takeaways": [
    "EU savers are protected up to <strong>&euro;100,000 per person, per bank</strong> under the national Deposit Guarantee Scheme (DGS).",
    "Compare accounts on <strong>interest rate (AER), access (instant vs notice vs fixed term), fees, and DGS coverage</strong>.",
    "Pan-European deposit marketplaces let you open accounts at banks across the EU to reach higher rates while staying DGS-protected.",
    "Interest is often taxable in your country of residence &mdash; check local rules before you commit.",
  ],
  "internals": [
    ("no-penalty CD alternatives", f"{S}/2026/07/no-penalty-cd-alternatives-best-2026.html"),
    ("high-yield savings with no minimum", f"{S}/2026/07/best-high-yield-savings-account-no.html"),
  ],
  "table": {"caption": "Types of savings account in Europe",
    "headers": ["Type", "Access to cash", "Rate", "Best for"],
    "rows": [
      ["Instant-access", "Anytime", "Lower", "Emergency fund / flexibility"],
      ["Notice account", "After 30-95 days' notice", "Medium", "Planned spending"],
      ["Fixed-term deposit", "Locked 6-36 months", "Higher", "Money you won't need soon"],
    ]},
  "faqs": [
    ("Are savings accounts in Europe safe?",
     "Deposits at EU-authorised banks are protected up to €100,000 per person, per bank, under the national Deposit Guarantee Scheme. Confirm the bank is covered before depositing."),
    ("What is the best type of savings account?",
     "It depends on access needs. Instant-access suits an emergency fund; fixed-term deposits pay more if you can lock the money away."),
    ("Can I open a savings account in another EU country?",
     "Often yes — pan-European deposit marketplaces let residents of one EU country open accounts at banks in another, while keeping DGS protection."),
    ("Is savings interest taxed in Europe?",
     "Usually yes, in your country of residence, though rates and allowances vary widely. Some countries offer tax-advantaged savings — check local rules."),
    ("What does AER mean?",
     "Annual Equivalent Rate shows the interest you'd earn over a year including compounding, so you can compare accounts on a like-for-like basis."),
  ],
  "externals": [
    ("EU Deposit Guarantee Schemes", "https://finance.ec.europa.eu/banking/banking-regulation/deposit-guarantee-schemes_en"),
    ("European Central Bank", "https://www.ecb.europa.eu/"),
  ],
},
"invoicing-software": {
  "id": "6997599327595311216",
  "url": f"{S}/2026/07/best-invoicing-software-for-freelancers.html",
  "title": "Best Invoicing Software for Freelancers (2026)",
  "keyword": "best invoicing software for freelancers",
  "image_query": "freelancer invoice laptop working desk",
  "image_alt": "Freelancer creating an invoice on invoicing software",
  "takeaways": [
    "The best invoicing tools for freelancers are <strong>free or under $10-15/month</strong> and send professional invoices, track payment status, and accept online payments.",
    "Look for: <strong>unlimited invoices, card/ACH payments, recurring invoices, expense tracking, and exportable tax reports</strong>.",
    "Free tiers cover low-volume freelancers; paid tiers add automation, reminders, and full accounting.",
    "Pair invoicing with a separate business account to keep your books and taxes clean.",
  ],
  "internals": [
    ("checking account for freelancers with irregular income", f"{S}/2026/07/best-checking-account-for-freelancers.html"),
    ("credit cards for freelancers", f"{S}/2026/07/best-credit-cards-for-freelancers-with.html"),
  ],
  "table": {"caption": "Invoicing software tiers for freelancers",
    "headers": ["Tier", "Typical cost", "Online payments", "Best for"],
    "rows": [
      ["Free tools", "$0", "Via Stripe/PayPal", "Low-volume freelancers"],
      ["Low-cost apps", "Under $15/mo", "Built-in", "Regular client work"],
      ["Accounting suites", "$15-30/mo", "Built-in", "Freelancers who also need bookkeeping"],
    ]},
  "faqs": [
    ("What is the best free invoicing software for freelancers?",
     "Several tools offer free, unlimited professional invoicing and let clients pay by card through Stripe or PayPal — enough for most low-volume freelancers."),
    ("Do freelancers really need invoicing software?",
     "It isn't mandatory, but it gets you paid faster with automatic reminders and keeps clean records for tax time — a big time-saver over manual invoices."),
    ("Can invoicing software accept card payments?",
     "Yes. Most tools integrate Stripe or PayPal so clients can pay a card or bank transfer directly from the invoice; a small processing fee applies."),
    ("What should a freelance invoice include?",
     "Your name/business details, the client's details, an invoice number and date, itemised work, the total, payment terms, and your tax ID where required."),
    ("Is invoicing software worth paying for?",
     "If you send more than a handful of invoices a month, paid tiers pay for themselves through automation, reminders, and expense/tax tracking."),
  ],
  "externals": [
    ("IRS: self-employed recordkeeping", "https://www.irs.gov/businesses/small-businesses-self-employed/recordkeeping"),
    ("SBA: manage your finances", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances"),
  ],
},
"checking-freelancers": {
  "id": "15441177859777022",
  "url": f"{S}/2026/07/best-checking-account-for-freelancers.html",
  "title": "Best Checking Account for Freelancers (2026)",
  "keyword": "checking account for freelancers with irregular income",
  "image_query": "freelancer working laptop coffee finances",
  "image_alt": "Freelancer managing irregular income in a checking account",
  "takeaways": [
    "Freelancers with irregular income need a checking account with <strong>no monthly fee, no minimum balance, and early or fast direct deposit</strong>.",
    "Helpful features: <strong>sub-accounts or 'buckets'</strong> to set aside tax money, fee-free ATMs, and instant transfer to savings.",
    "Set aside <strong>25-30% of each payment for taxes</strong> in a separate account so a big invoice doesn't become a tax surprise.",
    "Keep business income separate from personal spending even before you form an LLC &mdash; it makes bookkeeping far easier.",
  ],
  "internals": [
    ("no-fee business checking for freelancers", f"{S}/2026/07/no-fee-business-checking-for.html"),
    ("best invoicing software for freelancers", f"{S}/2026/07/best-invoicing-software-for-freelancers.html"),
  ],
  "table": {"caption": "What freelancers with irregular income should look for",
    "headers": ["Feature", "Why it matters", "Priority"],
    "rows": [
      ["$0 monthly fee / no minimum", "Lean months don't trigger fees", "Essential"],
      ["Early / fast direct deposit", "Access client payments sooner", "High"],
      ["Sub-accounts (tax bucket)", "Auto-separate tax money", "High"],
      ["Fee-free ATM network", "Avoid $3+ withdrawal fees", "Medium"],
    ]},
  "faqs": [
    ("What is the best checking account for freelancers with irregular income?",
     "One with no monthly fee, no minimum balance, and features like early direct deposit and sub-accounts for setting aside taxes. Online banks usually lead on fees."),
    ("How much should a freelancer set aside for taxes?",
     "A common rule of thumb is 25-30% of each payment, moved into a separate account, so quarterly estimated taxes are covered without scrambling."),
    ("Do freelancers need a business checking account?",
     "It isn't legally required for sole proprietors, but separating business income from personal spending simplifies taxes and protects you if you later form an LLC."),
    ("Can I open a checking account with irregular income?",
     "Yes. Standard checking accounts don't require proof of steady income to open — you generally just need ID and, for some banks, a small opening deposit."),
    ("Is an online checking account safe for freelancers?",
     "Yes, provided the bank or its partner bank is FDIC insured (up to $250,000 per depositor). Online banks typically charge lower fees than branches."),
  ],
  "externals": [
    ("IRS: estimated taxes for self-employed", "https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes"),
    ("FDIC deposit insurance", "https://www.fdic.gov/resources/deposit-insurance/"),
  ],
},
"open-business-bank": {
  "id": "2656837108654084196",
  "url": f"{S}/2026/07/how-to-open-business-bank-account.html",
  "title": "How to Open a Business Bank Account Without an EIN",
  "keyword": "how to open a business bank account without an ein",
  "image_query": "opening bank account documents signing desk",
  "image_alt": "Sole proprietor opening a business bank account with ID",
  "takeaways": [
    "Sole proprietors can open a business bank account <strong>using their SSN instead of an EIN</strong> at many banks.",
    "Typically you need: <strong>a government photo ID, your SSN, and a business name</strong> (or you trade under your own name).",
    "An EIN is <strong>free from the IRS</strong> and takes minutes online &mdash; getting one is optional for sole proprietors but recommended for privacy.",
    "LLCs, partnerships, and any business with employees <strong>do</strong> need an EIN to open an account.",
  ],
  "internals": [
    ("build business credit with your EIN", f"{S}/2026/08/how-to-build-business-credit-with-ein.html"),
    ("no-fee business checking for freelancers", f"{S}/2026/07/no-fee-business-checking-for.html"),
  ],
  "table": {"caption": "Do you need an EIN to open a business account?",
    "headers": ["Business type", "EIN required?", "Can use SSN?"],
    "rows": [
      ["Sole proprietor (no employees)", "No", "Yes"],
      ["Single-member LLC", "Usually yes", "Sometimes"],
      ["Partnership / multi-member LLC", "Yes", "No"],
      ["Any business with employees", "Yes", "No"],
    ]},
  "faqs": [
    ("Can I open a business bank account without an EIN?",
     "Yes, if you're a sole proprietor. Many banks let you open a business account with your SSN, a photo ID, and your business name. LLCs and employers need an EIN."),
    ("Do I need an EIN as a sole proprietor?",
     "Not to open an account, but an EIN is free from the IRS, protects your SSN privacy, and is required if you hire employees or form an LLC."),
    ("What documents do I need to open a business bank account?",
     "Generally a government photo ID, your SSN or EIN, and your business name or registration. Requirements vary by bank and business structure."),
    ("How long does it take to get an EIN?",
     "Applying online through the IRS takes only a few minutes, and you receive the EIN immediately at the end of the session — at no cost."),
    ("Is it worth separating business and personal banking?",
     "Yes. It simplifies taxes, makes bookkeeping cleaner, and supports the liability protection of an LLC if you form one later."),
  ],
  "externals": [
    ("IRS: apply for an EIN (free)", "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online"),
    ("SBA: open a business bank account", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances"),
  ],
},
"mortgage-freelancers": {
  "id": "952678809542441082",
  "url": f"{S}/2026/07/mortgage-for-freelancers-first-time.html",
  "title": "Mortgage for Freelancers: First-Time Buyer Guide",
  "keyword": "mortgage for freelancers",
  "image_query": "house keys new home mortgage couple",
  "image_alt": "First-time home buyer who is self-employed reviewing a mortgage",
  "takeaways": [
    "Freelancers <strong>can</strong> get a mortgage &mdash; lenders just verify income differently, usually via <strong>2 years of tax returns</strong>.",
    "Lenders average your <strong>net (after-deduction) self-employment income</strong>, so heavy write-offs can lower how much you qualify for.",
    "Strengthen your file: <strong>higher credit score, larger down payment, low debt-to-income</strong>, and clean, consistent records.",
    "Bank-statement loans exist for those with strong cash flow but low taxable income &mdash; expect higher rates.",
  ],
  "internals": [
    ("checking account for freelancers", f"{S}/2026/07/best-checking-account-for-freelancers.html"),
    ("unsecured personal loan comparison", f"{S}/2026/08/unsecured-personal-loan-comparison-2026.html"),
  ],
  "table": {"caption": "How lenders assess a self-employed borrower",
    "headers": ["Factor", "What lenders want", "Freelancer tip"],
    "rows": [
      ["Income history", "2 years of tax returns", "File on time; avoid gaps"],
      ["Net income", "Stable or rising", "Balance write-offs vs qualifying"],
      ["Credit score", "Higher = better rate", "Pay on time; low utilization"],
      ["Down payment", "More reduces risk", "10-20%+ strengthens approval"],
    ]},
  "faqs": [
    ("Can a freelancer get a mortgage?",
     "Yes. Self-employed borrowers qualify by documenting income — usually two years of tax returns — plus credit score, down payment, and debt-to-income like any borrower."),
    ("How many years of self-employment do you need for a mortgage?",
     "Most conventional lenders want two years of self-employment income history, though some accept one year with a strong prior work record in the same field."),
    ("Do tax write-offs hurt mortgage approval?",
     "They can. Lenders qualify you on net income after deductions, so aggressive write-offs lower your documented income and the loan amount you qualify for."),
    ("What is a bank-statement mortgage?",
     "A loan that verifies income from 12-24 months of bank deposits instead of tax returns — useful for freelancers with strong cash flow but low taxable income, usually at higher rates."),
    ("How can freelancers improve their mortgage approval odds?",
     "Raise your credit score, lower debt-to-income, save a larger down payment, keep two years of clean records, and avoid big new debts before applying."),
  ],
  "externals": [
    ("CFPB: mortgages", "https://www.consumerfinance.gov/consumer-tools/mortgages/"),
    ("IRS: self-employed tax center", "https://www.irs.gov/businesses/small-businesses-self-employed/self-employed-individuals-tax-center"),
  ],
},
"hysa-no-minimum": {
  "id": "53874915417182082",
  "url": f"{S}/2026/07/best-high-yield-savings-account-no.html",
  "title": "Best High-Yield Savings Account, No Minimum (2026)",
  "keyword": "best high-yield savings account no minimum",
  "image_query": "piggy bank savings growth coins",
  "image_alt": "High-yield savings account with no minimum balance",
  "takeaways": [
    "A <strong>high-yield savings account (HYSA) with no minimum</strong> lets you earn a competitive APY starting from $0.",
    "HYSAs pay many times the national average savings rate &mdash; almost always found at <strong>online banks</strong> with low overhead.",
    "Confirm: <strong>no minimum balance, no monthly fee, FDIC insured, and easy transfers</strong> to your checking account.",
    "APYs are variable and move with the Fed &mdash; the rate can change after you open the account.",
  ],
  "internals": [
    ("no-penalty CD alternatives", f"{S}/2026/07/no-penalty-cd-alternatives-best-2026.html"),
    ("best savings accounts in Europe", f"{S}/2026/08/best-savings-accounts-in-europe-2026.html"),
  ],
  "table": {"caption": "HYSA vs a traditional savings account",
    "headers": ["Feature", "High-yield (online)", "Traditional (branch)"],
    "rows": [
      ["APY", "Much higher", "Near national average"],
      ["Minimum balance", "Often $0", "Sometimes required"],
      ["Monthly fee", "Usually none", "Common unless waived"],
      ["Access", "Online transfer / app", "Branch + online"],
    ]},
  "faqs": [
    ("What is the best high-yield savings account with no minimum?",
     "Look for an online bank offering a competitive APY, no minimum balance, no monthly fee, and FDIC insurance — those terms matter more than chasing the single highest rate."),
    ("Are high-yield savings accounts safe?",
     "Yes, at an FDIC-insured bank your money is protected up to $250,000 per depositor, per bank — the same protection as any insured savings account."),
    ("Why do online banks offer higher savings rates?",
     "They have no branch network to fund, so they pass the lower overhead to customers as higher APYs and fewer fees."),
    ("Can the APY on a HYSA change?",
     "Yes. High-yield savings rates are variable and typically move with the Federal Reserve, so the rate can rise or fall after you open the account."),
    ("Is there a limit on savings withdrawals?",
     "Banks may limit certain withdrawal types per month. Check the account terms, though many have relaxed the old six-per-month federal limit."),
  ],
  "externals": [
    ("FDIC deposit insurance", "https://www.fdic.gov/resources/deposit-insurance/"),
    ("CFPB: savings accounts", "https://www.consumerfinance.gov/ask-cfpb/category-bank-accounts-and-services/"),
  ],
},
"no-penalty-cd": {
  "id": "4079252246989858223",
  "url": f"{S}/2026/07/no-penalty-cd-alternatives-best-2026.html",
  "title": "No-Penalty CD Alternatives: Best 2026 Options",
  "keyword": "no-penalty cd alternatives",
  "image_query": "savings certificate deposit money planning",
  "image_alt": "Comparing no-penalty CD alternatives for short-term savings",
  "takeaways": [
    "A <strong>no-penalty CD</strong> lets you withdraw your full balance early without the usual interest penalty &mdash; a middle ground between a CD and savings.",
    "Alternatives for short-term cash: <strong>high-yield savings, money market accounts, and Treasury bills</strong>.",
    "Match the tool to your timeline: <strong>need instant access &rarr; HYSA; can lock funds &rarr; a term CD pays more</strong>.",
    "All bank options should be <strong>FDIC insured</strong>; Treasuries are backed by the U.S. government and are state-tax-free.",
  ],
  "internals": [
    ("best high-yield savings account with no minimum", f"{S}/2026/07/best-high-yield-savings-account-no.html"),
    ("best savings accounts in Europe", f"{S}/2026/08/best-savings-accounts-in-europe-2026.html"),
  ],
  "table": {"caption": "No-penalty CD vs short-term cash alternatives",
    "headers": ["Option", "Access to cash", "Rate", "Insured by"],
    "rows": [
      ["No-penalty CD", "Withdraw early, no penalty", "Medium", "FDIC"],
      ["High-yield savings", "Anytime", "Variable", "FDIC"],
      ["Money market account", "Anytime (checks/debit)", "Variable", "FDIC"],
      ["Treasury bills (T-bills)", "At maturity / secondary sale", "Market", "U.S. Treasury"],
    ]},
  "faqs": [
    ("What is a no-penalty CD?",
     "A certificate of deposit that lets you withdraw your entire balance before maturity without the early-withdrawal penalty a standard CD charges — usually at a slightly lower rate."),
    ("What are the best alternatives to a no-penalty CD?",
     "High-yield savings accounts and money market accounts for full flexibility, and Treasury bills for a government-backed, state-tax-free short-term option."),
    ("Are no-penalty CDs worth it?",
     "They suit savers who want a fixed rate but might need the cash early. If you value the highest flexibility, a high-yield savings account is often simpler."),
    ("Are Treasury bills better than CDs?",
     "T-bills are backed by the U.S. government and exempt from state and local tax, which can beat a CD after tax — but a fixed-rate CD may pay more upfront depending on the market."),
    ("Is a money market account the same as a CD?",
     "No. A money market account is a flexible savings account (often with checks or a debit card) at a variable rate, while a CD locks money for a set term at a fixed rate."),
  ],
  "externals": [
    ("TreasuryDirect: Treasury bills", "https://www.treasurydirect.gov/marketable-securities/treasury-bills/"),
    ("FDIC deposit insurance", "https://www.fdic.gov/resources/deposit-insurance/"),
  ],
},
"rideshare-cards": {
  "id": "9216133687508478363",
  "url": f"{S}/2026/07/best-credit-cards-for-rideshare-drivers.html",
  "title": "Best Credit Cards for Rideshare Drivers (2026)",
  "keyword": "best credit cards for rideshare drivers",
  "image_query": "rideshare driver car phone app city",
  "image_alt": "Rideshare driver choosing a rewards credit card for gas and expenses",
  "takeaways": [
    "Rideshare and delivery drivers (Uber, Lyft, DoorDash) should prioritize cards that reward <strong>gas, EV charging, and everyday spend</strong>.",
    "Look for: <strong>bonus cash back on gas/transit, no or low annual fee</strong>, and rewards on phone and car costs.",
    "Track driving expenses in a <strong>separate card or account</strong> &mdash; it makes the mileage or actual-expense deduction simple at tax time.",
    "Building credit first with on-time payments unlocks the better-rewards cards.",
  ],
  "internals": [
    ("credit cards for freelancers", f"{S}/2026/07/best-credit-cards-for-freelancers-with.html"),
    ("checking account for freelancers", f"{S}/2026/07/best-checking-account-for-freelancers.html"),
  ],
  "table": {"caption": "Card types for rideshare & delivery drivers",
    "headers": ["Card type", "Rewards focus", "Annual fee", "Best for"],
    "rows": [
      ["Flat-rate cash back", "Every purchase", "$0 common", "Simplicity"],
      ["Gas & transit bonus", "Fuel / EV charging", "$0-95", "High-mileage drivers"],
      ["Secured card", "Builds credit", "$0 common", "New / rebuilding credit"],
    ]},
  "faqs": [
    ("What is the best credit card for rideshare drivers?",
     "One with strong gas/transit cash back, no or low annual fee, and rewards on everyday spend. High-mileage drivers benefit most from fuel and EV-charging bonuses."),
    ("Can rideshare drivers deduct expenses?",
     "Yes. Self-employed drivers can deduct either the IRS standard mileage rate or actual vehicle expenses on Schedule C — keep clean records of miles and costs."),
    ("Do rideshare drivers need a business credit card?",
     "It isn't required, but using a separate card for driving keeps business and personal spending apart, which simplifies deductions and bookkeeping."),
    ("What credit score do you need for a rewards card?",
     "Most cash-back rewards cards want a score around 670 or higher. If you're below that, a secured card builds credit toward qualifying later."),
    ("Is a gas card or a cash-back card better for drivers?",
     "A general cash-back card is more flexible, while a gas-branded card can pay more at the pump but only there. Many drivers pair a cash-back card with fuel rewards."),
  ],
  "externals": [
    ("IRS: gig economy tax center", "https://www.irs.gov/businesses/gig-economy-tax-center"),
    ("CFPB: credit cards", "https://www.consumerfinance.gov/consumer-tools/credit-cards/"),
  ],
},
"personal-loan": {
  "id": "7767262973809293840",
  "url": f"{S}/2026/08/unsecured-personal-loan-comparison-2026.html",
  "title": "Unsecured Personal Loan Comparison (2026 Guide)",
  "keyword": "unsecured personal loan comparison",
  "image_query": "loan application finance documents calculator",
  "image_alt": "Comparing unsecured personal loan offers and APRs",
  "takeaways": [
    "An <strong>unsecured personal loan needs no collateral</strong> &mdash; approval and your APR depend on credit score and income.",
    "Compare on <strong>APR (not just the monthly payment), origination fee, term, and total cost</strong> over the life of the loan.",
    "<strong>Prequalify with a soft credit check</strong> to compare real rates without hurting your score.",
    "Watch origination fees (often <strong>1-8%</strong>) &mdash; they raise the true cost even when the rate looks low.",
  ],
  "internals": [
    ("mortgage for freelancers", f"{S}/2026/07/mortgage-for-freelancers-first-time.html"),
    ("credit cards for freelancers", f"{S}/2026/07/best-credit-cards-for-freelancers-with.html"),
    ("0% APR balance transfer cards", f"{S}/2026/08/best-0-apr-intro-balance-transfer.html"),
    ("cards for building credit", f"{S}/2026/09/best-credit-card-for-building-credit.html"),
  ],
  "table": {"caption": "Unsecured personal loan vs other borrowing",
    "headers": ["Option", "Collateral", "Typical APR", "Best for"],
    "rows": [
      ["Unsecured personal loan", "None", "Credit-based", "Debt consolidation, big one-offs"],
      ["Secured loan", "Asset required", "Lower", "Lower rate if you have collateral"],
      ["0% APR balance transfer", "None", "0% intro", "Paying off card debt fast"],
      ["Credit card", "None", "Higher", "Small, short-term spend"],
    ]},
  "faqs": [
    ("What is an unsecured personal loan?",
     "A fixed-sum loan that requires no collateral. The lender approves you and sets your APR based on your credit score, income, and debt — not on an asset you pledge."),
    ("What credit score do you need for a personal loan?",
     "Mid-600s and up typically qualifies, with the best APRs going to scores in the 720+ range. Some lenders serve lower scores at higher rates."),
    ("What's the difference between APR and interest rate?",
     "The interest rate is the cost of borrowing the principal; the APR also includes fees like origination, so it reflects the loan's true annual cost — use it to compare offers."),
    ("Does prequalifying for a loan hurt your credit?",
     "No. Prequalification uses a soft credit check that doesn't affect your score. A hard inquiry happens only when you formally apply."),
    ("What is an origination fee?",
     "An upfront fee some lenders charge to process the loan, often 1-8% of the amount, usually deducted from your funds. Factor it into the total cost."),
  ],
  "externals": [
    ("CFPB: personal loans", "https://www.consumerfinance.gov/ask-cfpb/category-loans/"),
    ("FTC: personal loans", "https://consumer.ftc.gov/articles/using-personal-loans-wisely"),
  ],
},
"invoicing-app-expenses": {
  "id": "9092293168699587350",
  "url": f"{S}/2026/07/top-invoicing-app-for-freelancers-with.html",
  "title": "Best Invoicing App With Expense Tracking (2026)",
  "keyword": "invoicing app with expense tracking for freelancers",
  "image_query": "freelancer receipts expense tracking phone app",
  "image_alt": "Freelancer tracking expenses and invoices in one app",
  "takeaways": [
    "The best freelancer apps combine <strong>invoicing with expense and receipt tracking</strong> in one place.",
    "Look for: <strong>receipt capture, mileage tracking, categorized expenses, profit reports, and a tax export</strong>.",
    "Combining invoices and expenses cuts bookkeeping time and makes your <strong>Schedule C deductions</strong> far easier.",
    "Free tiers cover the basics; paid plans add automation and accounting sync.",
  ],
  "internals": [
    ("best invoicing software for freelancers", f"{S}/2026/07/best-invoicing-software-for-freelancers.html"),
    ("checking account for freelancers", f"{S}/2026/07/best-checking-account-for-freelancers.html"),
  ],
  "table": {"caption": "Invoicing apps by expense-tracking depth",
    "headers": ["Tier", "Expense tracking", "Typical cost", "Best for"],
    "rows": [
      ["Invoicing only", "None / manual", "Free", "Occasional invoices"],
      ["Invoicing + expenses", "Receipts, categories", "Under $15/mo", "Active freelancers"],
      ["Full accounting suite", "Expenses + reports + tax", "$15-30/mo", "Freelancers who self-file"],
    ]},
  "faqs": [
    ("What is the best invoicing app with expense tracking for freelancers?",
     "An app that captures receipts, categorizes expenses, and exports a tax summary alongside professional invoicing — so your income and deductions live in one place."),
    ("Why track expenses inside your invoicing app?",
     "Keeping invoices and expenses together means every deductible cost is logged as you go, so Schedule C and quarterly taxes are quick instead of a year-end scramble."),
    ("Can invoicing apps track mileage?",
     "Some do, either automatically via your phone's GPS or by manual entry — useful for claiming the IRS standard mileage deduction if you drive for work."),
    ("Do freelancers really need expense tracking?",
     "If you claim business deductions, yes — the IRS expects records. Automated tracking maximizes legitimate deductions and protects you if you're ever audited."),
    ("Is free expense-tracking software good enough?",
     "Free tiers handle basic receipt logging and invoicing for low-volume freelancers. Paid plans add automation, reports, and accounting sync as your work grows."),
  ],
  "externals": [
    ("IRS: self-employed recordkeeping", "https://www.irs.gov/businesses/small-businesses-self-employed/recordkeeping"),
    ("IRS: Schedule C (Form 1040)", "https://www.irs.gov/forms-pubs/about-schedule-c-form-1040"),
  ],
},
"building-credit": {
  "id": "1548378205830166561", "url": f"{S}/2026/09/best-credit-card-for-building-credit.html",
  "title": "Best Credit Card for Building Credit (2026)",
  "keyword": "best credit card for building credit",
  "image_query": "credit card building credit score wallet",
  "image_alt": "Starter credit card for building credit history",
  "takeaways": [
    "The best cards for building credit are <strong>secured cards and starter cards</strong> that report to all three major bureaus.",
    "Two habits build your score fastest: <strong>pay in full on time</strong> and keep <strong>utilization under 30%</strong>.",
    "A <strong>secured card</strong> (refundable deposit = limit) is the easiest approval if you have no or poor credit.",
    "After 6-12 months of on-time payments you can often <strong>graduate to an unsecured card</strong>.",
  ],
  "internals": [("credit cards for rideshare drivers", f"{S}/2026/07/best-credit-cards-for-rideshare-drivers.html"),
    ("how to compare rewards credit cards", f"{S}/2026/09/how-to-compare-rewards-credit-cards-for.html")],
  "table": {"caption": "Card types for building credit",
    "headers": ["Card type", "Deposit?", "Approval odds", "Best for"],
    "rows": [["Secured card", "Yes (refundable)", "High", "No/poor credit"],
      ["Student card", "No", "Medium", "Students with thin credit"],
      ["Retail store card", "No", "Medium", "Easier approval, in-store use"]]},
  "faqs": [
    ("What is the best credit card for building credit?", "A secured card that reports to all three bureaus is usually the fastest, most accessible way to build credit from scratch or after a setback."),
    ("How long does it take to build credit with a credit card?", "You can see a score within about six months of on-time payments; meaningful improvement typically takes 12-18 months of consistent, low-utilization use."),
    ("Is a secured or unsecured card better for building credit?", "Secured cards are easier to get with no/poor credit. Once your score improves, an unsecured card frees up your deposit and often adds rewards."),
    ("Do starter cards report to credit bureaus?", "The good ones report to all three (Equifax, Experian, TransUnion). Always confirm this before applying — reporting is what actually builds your score."),
    ("What credit score do you need to start?", "Secured cards accept applicants with no score at all, which is why they're the standard starting point for building credit."),
  ],
  "externals": [("CFPB: build credit", "https://www.consumerfinance.gov/ask-cfpb/how-do-i-get-and-keep-a-good-credit-score-en-318/"),
    ("FTC: credit", "https://consumer.ftc.gov/articles/understanding-your-credit")],
},
"grocery-cashback": {
  "id": "7117524185472042366", "url": f"{S}/2026/09/best-beginner-grocery-credit-card.html",
  "title": "Best Cash-Back Credit Card for Groceries (2026)",
  "keyword": "best cashback credit card for groceries",
  "image_query": "grocery shopping supermarket cart credit card",
  "image_alt": "Using a cash-back credit card for grocery shopping",
  "takeaways": [
    "The best grocery cards pay <strong>3-6% cash back at supermarkets</strong>, often with no annual fee for beginners.",
    "Check the fine print: <strong>Walmart and Target usually count as 'superstores,' not supermarkets</strong>, so they may not earn the bonus.",
    "Watch <strong>annual spending caps</strong> on the bonus rate, after which earnings drop to 1%.",
    "Pair a grocery card with a flat-rate card so <strong>every purchase earns something</strong>.",
  ],
  "internals": [("how to compare rewards credit cards", f"{S}/2026/09/how-to-compare-rewards-credit-cards-for.html"),
    ("best credit card for building credit", f"{S}/2026/09/best-credit-card-for-building-credit.html")],
  "table": {"caption": "Ways to earn cash back on groceries",
    "headers": ["Card type", "Grocery rate", "Annual fee", "Best for"],
    "rows": [["Grocery-bonus card", "3-6%", "$0-95", "Heavy grocery spenders"],
      ["Flat-rate card", "1.5-2%", "$0", "Simplicity everywhere"],
      ["Store/warehouse card", "Varies", "Membership", "Loyal to one chain"]]},
  "faqs": [
    ("What is the best cash-back credit card for groceries?", "A card offering 3-6% at supermarkets with no annual fee suits most beginners; heavy spenders may come out ahead with a fee card if the bonus outweighs the cost."),
    ("Do Walmart and Target count as grocery stores?", "Usually no. Card networks classify them as superstores or discount stores, so grocery-bonus rates often don't apply there — check your card's merchant categories."),
    ("Are grocery cash-back caps a problem?", "They can be. Many cards cap the bonus rate at a set annual spend (then pay 1%). If you spend beyond the cap, a second card can keep earning the higher rate."),
    ("Is cash back better than points for groceries?", "Cash back is simpler and predictable. Points can be worth more if you redeem for travel, but they add complexity — beginners usually prefer straight cash back."),
    ("Is an annual fee worth it for a grocery card?", "Only if your grocery spend times the extra cash-back rate exceeds the fee. Do the math on your real monthly spend before choosing a fee card."),
  ],
  "externals": [("CFPB: credit cards", "https://www.consumerfinance.gov/consumer-tools/credit-cards/"),
    ("FTC: credit", "https://consumer.ftc.gov/articles/understanding-your-credit")],
},
"compare-rewards": {
  "id": "8287250562768223093", "url": f"{S}/2026/09/how-to-compare-rewards-credit-cards-for.html",
  "title": "How to Compare Rewards Credit Cards (Beginners)",
  "keyword": "how to compare rewards credit cards",
  "image_query": "comparing credit cards rewards choice",
  "image_alt": "Comparing rewards credit cards side by side",
  "takeaways": [
    "Compare cards on <strong>your actual spending</strong>, not the headline rate &mdash; a category bonus only helps where you spend.",
    "Weigh the <strong>annual fee against the rewards value</strong> you'll realistically earn in a year.",
    "If you ever carry a balance, <strong>APR matters more than rewards</strong> &mdash; interest wipes out cash back fast.",
    "Factor in the <strong>sign-up bonus and redemption options</strong> (cash, statement credit, travel).",
  ],
  "internals": [("best cash-back card for groceries", f"{S}/2026/09/best-beginner-grocery-credit-card.html"),
    ("best credit card for building credit", f"{S}/2026/09/best-credit-card-for-building-credit.html")],
  "table": {"caption": "Reward types compared",
    "headers": ["Reward type", "Simplicity", "Max value", "Best for"],
    "rows": [["Flat cash back", "High", "Medium", "Set-and-forget"],
      ["Category cash back", "Medium", "High (if you fit)", "Concentrated spenders"],
      ["Travel points", "Low", "Highest", "Frequent travelers"]]},
  "faqs": [
    ("How do you compare rewards credit cards?", "Match each card's bonus categories to where you actually spend, subtract the annual fee from expected rewards, then compare sign-up bonuses and how easily you can redeem."),
    ("Is cash back or points better?", "Cash back is simpler and always worth face value. Points can be worth more for travel but require effort — choose based on how much optimizing you'll actually do."),
    ("Is an annual-fee card worth it?", "Only if your rewards minus the fee beat a no-fee card. For most beginners a no-fee flat-rate card wins until spending is high enough to justify a fee."),
    ("Does APR matter if I pay in full?", "No — if you pay the full statement balance every month you never pay interest, so you can ignore APR and optimize purely for rewards."),
    ("How do sign-up bonuses work?", "You earn a lump reward after spending a set amount in the first few months. Only chase one you'd hit through normal spending, never by overspending."),
  ],
  "externals": [("CFPB: credit cards", "https://www.consumerfinance.gov/consumer-tools/credit-cards/"),
    ("FTC: choosing a credit card", "https://consumer.ftc.gov/articles/understanding-your-credit")],
},
"balance-transfer": {
  "id": "1716958127867937811", "url": f"{S}/2026/08/best-0-apr-intro-balance-transfer.html",
  "title": "Best 0% APR Balance Transfer Cards (2026)",
  "keyword": "best 0% apr balance transfer credit cards",
  "image_query": "credit card debt payoff calculator finance",
  "image_alt": "Using a 0% APR balance transfer card to pay off debt",
  "takeaways": [
    "A 0% intro APR balance transfer card gives you <strong>12-21 months to pay down debt interest-free</strong>.",
    "Nearly all charge a <strong>balance transfer fee of 3-5%</strong> of the amount moved &mdash; factor it in.",
    "Have a plan to <strong>clear the balance before the intro period ends</strong>, when the regular APR kicks in.",
    "Don't add new purchases &mdash; they may not get the 0% rate and can grow your balance.",
  ],
  "internals": [("unsecured personal loan comparison", f"{S}/2026/08/unsecured-personal-loan-comparison-2026.html"),
    ("best credit card for building credit", f"{S}/2026/09/best-credit-card-for-building-credit.html")],
  "table": {"caption": "0% balance transfer vs other payoff options",
    "headers": ["Option", "Interest", "Upfront cost", "Best for"],
    "rows": [["0% balance transfer card", "0% intro", "3-5% fee", "Card debt you can clear in ~18 mo"],
      ["Personal loan", "Fixed APR", "0-8% origination", "Larger, longer payoff"],
      ["Pay down highest-APR first", "Existing APR", "None", "No new accounts"]]},
  "faqs": [
    ("What is a balance transfer credit card?", "A card that lets you move existing high-interest debt onto a 0% intro-APR card, so payments go to principal instead of interest for a set promotional period."),
    ("How long do 0% intro periods last?", "Commonly 12 to 21 months. Longer intro periods give more room to pay off, but compare them alongside the transfer fee and the post-intro APR."),
    ("Is there a fee to transfer a balance?", "Almost always — typically 3-5% of the transferred amount. A fee can still be worth it if it's less than the interest you'd otherwise pay."),
    ("Does a balance transfer hurt your credit?", "A new card adds a hard inquiry and lowers your average account age slightly, but paying down the balance improves utilization, which usually helps over time."),
    ("Can you transfer a balance between cards from the same bank?", "Usually no. Most issuers don't allow transfers between their own cards, so you transfer debt from a different bank's card."),
  ],
  "externals": [("CFPB: balance transfers", "https://www.consumerfinance.gov/ask-cfpb/what-is-a-balance-transfer-en-1961/"),
    ("FTC: credit card debt", "https://consumer.ftc.gov/articles/how-get-out-debt")],
},
"robo-vs-diy": {
  "id": "5266964235476748124", "url": f"{S}/2026/08/robo-advisor-vs-diy-investing-for.html",
  "title": "Robo-Advisor vs DIY Investing (2026 Guide)",
  "keyword": "robo-advisor vs diy investing",
  "image_query": "investing app phone portfolio chart",
  "image_alt": "Comparing robo-advisor and DIY investing for beginners",
  "takeaways": [
    "A <strong>robo-advisor automates</strong> portfolio building, rebalancing, and often tax-loss harvesting for a low fee (around 0.25%/year).",
    "<strong>DIY investing</strong> means no advisory fee and full control &mdash; but you pick funds and rebalance yourself.",
    "Beginners who want <strong>hands-off</strong> usually prefer a robo; those who enjoy learning may go DIY with index funds.",
    "You can <strong>do both</strong>: a robo for retirement, a DIY brokerage for hands-on picks.",
  ],
  "internals": [("best beginner investment apps", f"{S}/2026/08/best-beginner-investment-apps-2026-top.html"),
    ("high-yield savings with no minimum", f"{S}/2026/07/best-high-yield-savings-account-no.html")],
  "table": {"caption": "Robo-advisor vs DIY vs human advisor",
    "headers": ["Approach", "Typical cost", "Effort", "Best for"],
    "rows": [["Robo-advisor", "~0.25%/yr", "Low", "Hands-off beginners"],
      ["DIY index investing", "Fund fees only", "Medium", "Learners who want control"],
      ["Human advisor", "~1%/yr", "Low", "Complex finances"]]},
  "faqs": [
    ("Is a robo-advisor or DIY investing better?", "A robo-advisor suits hands-off beginners who want automation; DIY suits people who enjoy learning and want to avoid the advisory fee. Both can work well with low-cost index funds."),
    ("Are robo-advisors worth the fee?", "For many beginners, yes — the ~0.25% fee buys automatic rebalancing and tax-loss harvesting that's easy to skip when investing manually."),
    ("Can you lose money with a robo-advisor?", "Yes. Robo-advisors invest in market funds, so your balance rises and falls with the market — they manage allocation, not risk of loss."),
    ("Is DIY investing hard for beginners?", "Not necessarily. Buying a broad, low-cost index fund and adding to it regularly is simple; the discipline to stay invested matters more than complexity."),
    ("Can you use both a robo-advisor and DIY?", "Absolutely. Many investors use a robo for automated long-term goals and a separate brokerage account for hands-on investing."),
  ],
  "externals": [("SEC: investor.gov basics", "https://www.investor.gov/introduction-investing/investing-basics"),
    ("FINRA: robo-advisors", "https://www.finra.org/investors/insights/robo-advisors")],
},
"build-business-credit": {
  "id": "3093290489204820215", "url": f"{S}/2026/08/how-to-build-business-credit-with-ein.html",
  "title": "How to Build Business Credit With an EIN (2026)",
  "keyword": "how to build business credit with an ein",
  "image_query": "business owner office paperwork laptop",
  "image_alt": "Building business credit with an EIN",
  "takeaways": [
    "Start by getting a <strong>free EIN from the IRS</strong> and opening a business bank account in the business's name.",
    "Open <strong>net-30 vendor accounts and a business credit card that report</strong> to business bureaus.",
    "Pay every account <strong>on time or early</strong> &mdash; payment history drives your business score.",
    "Get a <strong>D-U-N-S number</strong> and monitor your file with Dun &amp; Bradstreet and Experian Business.",
  ],
  "internals": [("open a business bank account without an EIN", f"{S}/2026/07/how-to-open-business-bank-account.html"),
    ("best business credit cards with no revenue", f"{S}/2026/07/best-business-credit-cards-for-new.html")],
  "table": {"caption": "Steps to build business credit",
    "headers": ["Step", "What to do", "Why"],
    "rows": [["1. EIN", "Get free from IRS", "Business identity"],
      ["2. Bank account", "Open in business name", "Separates finances"],
      ["3. Net-30 vendors", "Open reporting accounts", "Builds payment history"],
      ["4. Monitor", "D&B + Experian Business", "Track your score"]]},
  "faqs": [
    ("How do you build business credit with an EIN?", "Get an EIN, open a business bank account and reporting vendor/credit accounts, pay them on time, and get a D-U-N-S number so bureaus can track your business's payment history."),
    ("How long does it take to build business credit?", "A basic business credit file can form within a few months of reporting activity; strong scores that unlock better terms usually take one to two years of consistent payments."),
    ("Do you need an LLC to build business credit?", "No. Sole proprietors can build some business credit with an EIN, but forming an LLC or corporation separates business and personal credit more cleanly."),
    ("Does building business credit affect personal credit?", "Ideally you separate them, but many small-business cards still require a personal guarantee, so early on your personal credit can still be checked."),
    ("What is a D-U-N-S number?", "A free identifier from Dun & Bradstreet that establishes your business in their credit system — many lenders and vendors reference it when extending terms."),
  ],
  "externals": [("IRS: apply for an EIN (free)", "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online"),
    ("SBA: establish business credit", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances")],
},
"cards-freelancers": {
  "id": "4881689637136858025", "url": f"{S}/2026/07/best-credit-cards-for-freelancers-with.html",
  "title": "Best Credit Cards for Freelancers (2026)",
  "keyword": "best credit cards for freelancers",
  "image_query": "freelancer laptop credit card working home",
  "image_alt": "Freelancer choosing a rewards credit card for business expenses",
  "takeaways": [
    "Freelancers benefit most from cards that reward <strong>software, ads, phone, and everyday spend</strong>.",
    "A business card <strong>separates work expenses</strong>, simplifying taxes &mdash; and you can qualify using personal credit.",
    "You can get a business card <strong>with no business revenue</strong>; issuers approve on personal credit + a personal guarantee.",
    "Track spending by category to <strong>maximize Schedule C deductions</strong>.",
  ],
  "internals": [("business credit cards with no revenue", f"{S}/2026/07/best-business-credit-cards-for-new.html"),
    ("checking account for freelancers", f"{S}/2026/07/best-checking-account-for-freelancers.html")],
  "table": {"caption": "Card options for freelancers",
    "headers": ["Card type", "Rewards focus", "Approval basis", "Best for"],
    "rows": [["Business cash back", "Software/ads/phone", "Personal credit", "Separating expenses"],
      ["Personal cash back", "Everyday spend", "Personal credit", "Simplicity"],
      ["Secured card", "Builds credit", "Deposit", "Thin/poor credit"]]},
  "faqs": [
    ("What is the best credit card for freelancers?", "One that rewards your biggest freelance costs — software, advertising, and phone — with no or low annual fee. A business card also keeps expenses separate for taxes."),
    ("Can freelancers get a business credit card?", "Yes. Sole proprietors qualify using their personal credit and income; you can enter your own name and $0 or projected revenue and sign a personal guarantee."),
    ("Should freelancers use a personal or business card?", "A business card separates work spending and simplifies deductions. If you're just starting, a rewards personal card works until your expenses grow."),
    ("Can you deduct credit card fees as a freelancer?", "Interest and fees on a card used for business are generally deductible business expenses. Keep the card for business use only and save records."),
    ("How can freelancers build credit?", "Use a card responsibly — pay in full, keep utilization low — and consider a secured card first if your personal credit is thin."),
  ],
  "externals": [("IRS: gig economy tax center", "https://www.irs.gov/businesses/gig-economy-tax-center"),
    ("CFPB: credit cards", "https://www.consumerfinance.gov/consumer-tools/credit-cards/")],
},
"checking-low-balance": {
  "id": "3610787812796396524", "url": f"{S}/2026/07/no-fee-business-checking-accounts-for.html",
  "title": "No-Fee Business Checking for Low Balances (2026)",
  "keyword": "no-fee business checking for freelancers under $5k",
  "image_query": "small business finances laptop calculator",
  "image_alt": "No-fee business checking for freelancers with low balances",
  "takeaways": [
    "Freelancers keeping <strong>under $5,000</strong> need accounts with <strong>no minimum balance and no monthly fee</strong>.",
    "Online banks and fintechs rarely require a minimum, so a small balance <strong>never triggers a fee</strong>.",
    "If you handle cash, check <strong>cash-deposit limits</strong> &mdash; many online banks limit or don't accept cash.",
    "Confirm the account (or its partner bank) is <strong>FDIC insured</strong> up to $250,000.",
  ],
  "internals": [("no-fee business checking for freelancers", f"{S}/2026/07/no-fee-business-checking-for.html"),
    ("open a business bank account without an EIN", f"{S}/2026/07/how-to-open-business-bank-account.html")],
  "table": {"caption": "Low-balance business checking options",
    "headers": ["Provider type", "Minimum balance", "Cash deposits", "Best for"],
    "rows": [["Online bank", "None", "Limited", "Digital-only freelancers"],
      ["Fintech/neobank", "None", "Often none", "Fast setup + invoicing"],
      ["Big bank (waived)", "Balance/activity", "Yes", "Regular cash deposits"]]},
  "faqs": [
    ("What is the best low-balance business checking account?", "An online or fintech account with no minimum balance and no monthly fee, so a balance under $5,000 never costs you anything to hold."),
    ("Is there a minimum balance for business checking?", "Many online banks have none. Traditional banks often require a minimum or monthly activity to waive the fee — read the terms before opening."),
    ("Are online business bank accounts safe?", "Yes, if the bank or its partner bank is FDIC insured (up to $250,000 per depositor). Verify insurance before depositing funds."),
    ("Can I deposit cash into an online business account?", "Sometimes, through partner ATMs or retailers, but many online banks limit or don't accept cash. If you take cash payments, factor this in."),
    ("What fees should I avoid on business checking?", "Monthly maintenance fees, minimum-balance fees, and per-transaction charges. For a low-balance freelancer, a truly $0 account is the goal."),
  ],
  "externals": [("FDIC deposit insurance", "https://www.fdic.gov/resources/deposit-insurance/"),
    ("SBA: manage your finances", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances")],
},
"checking-new-llc": {
  "id": "3562670923956996307", "url": f"{S}/2026/07/best-business-checking-account-for-new.html",
  "title": "Best Business Checking Account for a New LLC (2026)",
  "keyword": "best business checking account for new llc no fees",
  "image_query": "new business llc bank account documents",
  "image_alt": "Opening a business checking account for a new LLC",
  "takeaways": [
    "A new LLC needs its <strong>EIN and formation documents</strong> to open a business checking account.",
    "Choose a <strong>$0-fee, no-minimum</strong> account so a new LLC isn't charged before revenue arrives.",
    "Keeping LLC money separate <strong>preserves your liability protection</strong> &mdash; don't mix personal funds.",
    "Look for <strong>free ACH, transfers, and a debit card</strong> to run the business day to day.",
  ],
  "internals": [("open a business bank account without an EIN", f"{S}/2026/07/how-to-open-business-bank-account.html"),
    ("how to build business credit with an EIN", f"{S}/2026/08/how-to-build-business-credit-with-ein.html")],
  "table": {"caption": "What a new LLC needs to open an account",
    "headers": ["Requirement", "Detail", "Notes"],
    "rows": [["EIN", "From the IRS (free)", "Required for LLCs"],
      ["Formation docs", "Articles of organization", "Proves the LLC exists"],
      ["Operating agreement", "For multi-member LLCs", "Some banks ask for it"],
      ["Photo ID", "Owner(s)", "Standard KYC"]]},
  "faqs": [
    ("What is the best business checking account for a new LLC?", "One with no monthly fee, no minimum balance, free ACH, and a debit card — so a pre-revenue LLC keeps costs at zero while separating business funds."),
    ("What documents does a new LLC need to open a bank account?", "Typically your EIN, articles of organization, an operating agreement (for multi-member LLCs), and photo ID for the owners."),
    ("Does an LLC need an EIN to open a bank account?", "Yes. Unlike sole proprietors, LLCs generally must provide an EIN — it's free from the IRS and takes minutes to obtain online."),
    ("Can I use a personal account for my LLC?", "You shouldn't. Mixing personal and LLC funds can undermine the liability protection an LLC provides and complicates taxes and bookkeeping."),
    ("Single-member vs multi-member LLC — does it change account opening?", "Multi-member LLCs are more likely to be asked for an operating agreement; both need an EIN and formation documents."),
  ],
  "externals": [("SBA: open a business bank account", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances"),
    ("IRS: apply for an EIN (free)", "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online")],
},
"no-fee-bank-account": {
  "id": "7669432156666039081", "url": f"{S}/2026/07/best-no-fee-business-bank-account-for.html",
  "title": "No-Fee Business Bank Account for Freelancers (2026)",
  "keyword": "freelance business bank account requirements",
  "image_query": "freelancer opening bank account online laptop",
  "image_alt": "Freelancer opening a no-fee business bank account",
  "takeaways": [
    "Freelance business bank account requirements are simple: <strong>a photo ID, your SSN or EIN, and a business name</strong>.",
    "Many online banks offer effectively <strong>zero-balance current accounts for freelancers</strong> &mdash; no minimum, no monthly fee.",
    "Sole proprietors can often open with an <strong>SSN</strong>; an EIN is free and adds privacy.",
    "Confirm <strong>FDIC insurance</strong> and free ACH/transfers before you open.",
  ],
  "internals": [("open a business bank account without an EIN", f"{S}/2026/07/how-to-open-business-bank-account.html"),
    ("no-fee business checking for freelancers", f"{S}/2026/07/no-fee-business-checking-for.html")],
  "table": {"caption": "Freelance business bank account requirements",
    "headers": ["Requirement", "Sole proprietor", "LLC"],
    "rows": [["Photo ID", "Yes", "Yes"],
      ["SSN or EIN", "SSN (EIN optional)", "EIN required"],
      ["Business name", "Yours or DBA", "Registered LLC name"],
      ["Formation docs", "Not needed", "Yes"]]},
  "faqs": [
    ("What are the requirements for a freelance business bank account?", "Generally a government photo ID, your SSN (or EIN), and a business name. Sole proprietors can usually open with an SSN; LLCs need an EIN and formation documents."),
    ("Is there a zero-balance current account for freelancers?", "Yes. Many online banks offer no-minimum, no-monthly-fee business accounts you can run at a zero balance without penalty — ideal for new freelancers."),
    ("Do freelancers need an EIN to open a business account?", "Not as a sole proprietor — an SSN often works. An EIN is free from the IRS, protects your SSN's privacy, and is required for LLCs or if you hire."),
    ("Are no-fee freelance bank accounts safe?", "Yes, when the bank or its partner bank is FDIC insured up to $250,000 per depositor. Confirm insurance before depositing."),
    ("What should freelancers look for in a business bank account?", "No monthly fee, no minimum balance, free ACH and transfers, a debit card, FDIC insurance, and easy online access."),
  ],
  "externals": [("FDIC deposit insurance", "https://www.fdic.gov/resources/deposit-insurance/"),
    ("IRS: apply for an EIN (free)", "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online")],
},
"checking-free-ach": {
  "id": "7117684772533707556", "url": f"{S}/2026/07/best-business-checking-for-new-llc-no.html",
  "title": "Business Checking With Free ACH for a New LLC (2026)",
  "keyword": "business checking account with free ach",
  "image_query": "online banking transfer payment laptop business",
  "image_alt": "Business checking account with free ACH transfers",
  "takeaways": [
    "Free ACH matters for freelancers and LLCs who <strong>pay contractors and receive client payments</strong> electronically.",
    "Look for <strong>free incoming and outgoing ACH</strong>, no per-transfer fees, and reasonable daily limits.",
    "ACH is <strong>cheaper and simpler than wires</strong> for routine business payments.",
    "Pair free ACH with a <strong>$0-fee, no-minimum</strong> account to keep costs at zero.",
  ],
  "internals": [("no-fee business checking for freelancers", f"{S}/2026/07/no-fee-business-checking-for.html"),
    ("best business checking for a new LLC", f"{S}/2026/07/best-business-checking-account-for-new.html")],
  "table": {"caption": "ACH vs wire vs card for business payments",
    "headers": ["Method", "Typical cost", "Speed", "Best for"],
    "rows": [["ACH", "Often free", "1-3 business days", "Payroll, client payments"],
      ["Wire", "$15-30", "Same day", "Large/urgent transfers"],
      ["Card", "~3% fee", "Instant", "Small purchases"]]},
  "faqs": [
    ("What is a business checking account with free ACH?", "An account that lets you send and receive ACH bank transfers at no charge — ideal for paying contractors and getting paid by clients without per-transfer fees."),
    ("Is ACH free on business accounts?", "At many online banks, yes — both incoming and outgoing ACH are free. Traditional banks sometimes charge per transfer or for higher volumes, so check the terms."),
    ("What's the difference between ACH and a wire?", "ACH is a low-cost bank-to-bank transfer that settles in 1-3 days; wires are same-day but usually cost $15-30. Use ACH for routine payments, wires for urgent ones."),
    ("How long does an ACH transfer take?", "Standard ACH typically settles in one to three business days. Some banks offer same-day ACH for an extra fee."),
    ("Are there limits on ACH transfers?", "Yes, banks set daily and monthly ACH limits that vary by account and history. Check the limits if you make large or frequent payments."),
  ],
  "externals": [("CFPB: electronic transfers", "https://www.consumerfinance.gov/consumer-tools/bank-accounts/"),
    ("FDIC deposit insurance", "https://www.fdic.gov/resources/deposit-insurance/")],
},
"business-cards-new-llc": {
  "id": "1970871675402229531", "url": f"{S}/2026/07/best-business-credit-cards-for-new-llc.html",
  "title": "Best Business Credit Cards for a New LLC (2026)",
  "keyword": "best business credit cards for new llc",
  "image_query": "business owner credit card llc office",
  "image_alt": "Choosing a business credit card for a new LLC",
  "takeaways": [
    "A new LLC can get a business credit card using the <strong>owner's personal credit and a personal guarantee</strong>.",
    "You don't need business revenue &mdash; issuers approve on <strong>personal income and credit</strong>.",
    "A business card <strong>separates expenses and helps build business credit</strong> when it reports to business bureaus.",
    "Start with a <strong>no-annual-fee</strong> card and pay in full to avoid interest.",
  ],
  "internals": [("business credit cards with no revenue", f"{S}/2026/07/best-business-credit-cards-for-new.html"),
    ("how to build business credit with an EIN", f"{S}/2026/08/how-to-build-business-credit-with-ein.html")],
  "table": {"caption": "Card options for a new LLC",
    "headers": ["Card type", "Approval basis", "Annual fee", "Best for"],
    "rows": [["Personal-guarantee business card", "Personal credit", "$0-95", "Most new LLCs"],
      ["Secured business card", "Deposit", "$0 common", "Poor/thin credit"],
      ["Corporate/startup card", "Cash on hand", "Often $0", "Funded startups"]]},
  "faqs": [
    ("Can a new LLC get a credit card?", "Yes. A new LLC can get a business credit card based on the owner's personal credit and income, typically with a personal guarantee — business revenue isn't required."),
    ("Do you need revenue for a business credit card as an LLC?", "No. You can enter $0 or projected revenue; issuers weigh your personal income and credit far more heavily for a new LLC."),
    ("Does an LLC need an EIN for a business credit card?", "A single-member LLC can sometimes apply with an SSN, but an EIN is free, common for business cards, and required if you have employees."),
    ("Do you have to sign a personal guarantee?", "For most new LLCs, yes. A personal guarantee makes you personally responsible if the business can't pay, which is how issuers manage the risk."),
    ("Does a business credit card build business credit?", "It can, if the card reports to business credit bureaus. Pay on time and keep utilization low to build a strong business credit file."),
  ],
  "externals": [("SBA: business credit cards", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances"),
    ("IRS: apply for an EIN (free)", "https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online")],
},
"529-plan": {
  "id": "433682616367438950", "url": f"{S}/2026/08/best-state-529-plan-for-tax-benefits.html",
  "title": "Best 529 Plan for Tax Benefits (2026 Guide)",
  "keyword": "best 529 plan for tax benefits",
  "image_query": "college savings education fund piggy bank graduation",
  "image_alt": "Comparing 529 plans for education tax benefits",
  "takeaways": [
    "A <strong>529 plan</strong> lets education savings grow <strong>tax-free</strong> when used for qualified expenses.",
    "Many states give a <strong>state income-tax deduction or credit</strong> for contributions &mdash; check your own state first.",
    "You can invest in <strong>any state's plan</strong>, but your home state's may offer the tax break.",
    "Compare on <strong>fees, investment options, and state tax benefits</strong>, not just returns.",
  ],
  "internals": [("best investment apps for beginners", f"{S}/2026/08/best-beginner-investment-apps-2026-top.html"),
    ("best robo-advisor for beginners", f"{S}/2026/08/best-robo-advisor-for-beginners-2026.html")],
  "table": {"caption": "What to compare in a 529 plan",
    "headers": ["Factor", "Why it matters", "Tip"],
    "rows": [["State tax break", "Deduction/credit", "Check home state first"],
      ["Fees", "Eat into returns", "Prefer low-cost index options"],
      ["Investment options", "Age-based vs static", "Age-based is hands-off"],
      ["Flexibility", "Qualified uses", "K-12, college, some Roth rollover"]]},
  "faqs": [
    ("What is the best 529 plan for tax benefits?", "The best plan is often your home state's, because many states give a tax deduction or credit only for their own plan. If your state offers no break, choose a low-fee out-of-state plan with strong investment options."),
    ("Do 529 plans reduce federal taxes?", "Contributions aren't federally deductible, but earnings grow tax-free and withdrawals for qualified education expenses are federally tax-free. Many states add their own deduction or credit."),
    ("Can I use any state's 529 plan?", "Yes — you can open almost any state's plan regardless of where you live. But your home state's plan may be the only one that gives you a state tax break."),
    ("What can 529 funds be used for?", "Qualified expenses include college tuition, fees, books, and room and board, plus limited K-12 tuition, and — under recent rules — some rollovers to a Roth IRA subject to limits."),
    ("Are 529 plans worth it?", "For most families saving for education, yes — tax-free growth plus a possible state tax break beats a taxable account. Confirm the specifics with your state's plan and a tax professional."),
  ],
  "externals": [("SEC investor.gov: 529 plans", "https://www.investor.gov/introduction-investing/investing-basics/investment-products/529-plans"),
    ("IRS: 529 plans", "https://www.irs.gov/newsroom/529-plans-questions-and-answers")],
},
"robo-advisor-beginners": {
  "id": "4875672917697655672", "url": f"{S}/2026/08/best-robo-advisor-for-beginners-2026.html",
  "title": "Best Robo-Advisor for Beginners (2026 Guide)",
  "keyword": "best robo-advisor for beginners",
  "image_query": "investing app phone automated portfolio chart",
  "image_alt": "Beginner using a robo-advisor to invest",
  "takeaways": [
    "A <strong>robo-advisor</strong> builds and manages a diversified portfolio for you, hands-off, for a low fee (~<strong>0.25%/yr</strong>).",
    "Best for beginners who want <strong>automatic rebalancing and tax-loss harvesting</strong> without picking funds.",
    "Compare on <strong>fees, account minimums, and features</strong> (goals, IRAs, human advisor access).",
    "You can start with a <strong>small amount</strong> &mdash; many have low or no minimums.",
  ],
  "internals": [("robo-advisor vs DIY investing", f"{S}/2026/08/best-beginner-investment-apps-2026-top.html"),
    ("best 529 plan for tax benefits", f"{S}/2026/08/best-state-529-plan-for-tax-benefits.html")],
  "table": {"caption": "What to compare in a robo-advisor",
    "headers": ["Factor", "Typical", "Tip"],
    "rows": [["Fee", "~0.25%/yr", "Lower is better"],
      ["Minimum", "$0-500", "Low = easy start"],
      ["Features", "Rebalancing, tax-loss harvest", "Worth the fee"],
      ["Accounts", "Taxable + IRA", "Use IRA for retirement"]]},
  "faqs": [
    ("What is the best robo-advisor for beginners?", "The best beginner robo-advisor has a low fee (~0.25%), a low or no minimum, automatic rebalancing, and easy goal setup. Match it to whether you want a taxable account, an IRA, or access to a human advisor."),
    ("Are robo-advisors good for beginners?", "Yes — they handle diversification, rebalancing, and often tax-loss harvesting automatically, so beginners can invest sensibly without picking individual funds."),
    ("How much do robo-advisors cost?", "Most charge about 0.25% of assets per year, plus the underlying fund fees. That's far cheaper than a traditional human advisor (~1%)."),
    ("How much do I need to start with a robo-advisor?", "Many have low or no minimums, so you can start with a small amount and add regularly. Consistent contributions matter more than the starting sum."),
    ("Can you lose money with a robo-advisor?", "Yes — robo-advisors invest in market funds, so your balance rises and falls with the market. They manage allocation and risk level, not the risk of loss itself."),
  ],
  "externals": [("SEC investor.gov: robo-advisers", "https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/robo-advisers"),
    ("FINRA: robo-advisors", "https://www.finra.org/investors/insights/robo-advisors")],
},
"investment-apps-beginners": {
  "id": "6701571685594586911", "url": f"{S}/2026/08/best-beginner-investment-apps-2026-top.html",
  "title": "Best Investment Apps for Beginners (2026)",
  "keyword": "best investment apps for beginners",
  "image_query": "stock investing app smartphone beginner finance",
  "image_alt": "Beginner using an investment app on a phone",
  "takeaways": [
    "The best beginner investment apps offer <strong>low/no fees, fractional shares, and a simple interface</strong>.",
    "Look for <strong>commission-free trading, IRA options, and educational content</strong>.",
    "<strong>Fractional shares</strong> let you start with a few dollars instead of a whole share.",
    "For hands-off investing, consider a <strong>robo-advisor</strong> instead of picking stocks.",
  ],
  "internals": [("best robo-advisor for beginners", f"{S}/2026/08/best-robo-advisor-for-beginners-2026.html"),
    ("best 529 plan for tax benefits", f"{S}/2026/08/best-state-529-plan-for-tax-benefits.html")],
  "table": {"caption": "What to look for in a beginner investing app",
    "headers": ["Feature", "Why", "Tip"],
    "rows": [["Commission-free", "Keeps costs down", "Now standard"],
      ["Fractional shares", "Start with $ not shares", "Great for beginners"],
      ["IRA option", "Tax-advantaged retirement", "Use it early"],
      ["Education", "Learn as you go", "Reduces mistakes"]]},
  "faqs": [
    ("What is the best investment app for beginners?", "The best beginner app has commission-free trading, fractional shares, an IRA option, and a clean, simple interface with educational content. Pick one that matches whether you want to pick investments or automate them."),
    ("How much money do I need to start investing?", "Very little — apps with fractional shares let you start with a few dollars. Investing consistently over time matters far more than the amount you begin with."),
    ("Are investment apps safe?", "Reputable apps are members of SIPC, which protects securities in your account up to limits if the broker fails (this is not protection against market losses). Verify SIPC membership before funding."),
    ("Should beginners pick stocks or use a robo-advisor?", "Many beginners do better with a robo-advisor or a broad index fund, which spreads risk automatically. Picking individual stocks takes more knowledge and carries more risk."),
    ("What is a fractional share?", "A slice of a single share, so you can invest a set dollar amount even in expensive stocks. It lets beginners diversify with very little money."),
  ],
  "externals": [("SEC investor.gov: investing basics", "https://www.investor.gov/introduction-investing/investing-basics"),
    ("FINRA: fund analyzer", "https://www.finra.org/investors")],
},
"switch-direct-deposit": {
  "id": "4556685599215420547", "url": f"{S}/2026/08/how-to-switch-direct-deposit-to-new.html",
  "title": "How to Switch Direct Deposit to a New Bank (2026)",
  "keyword": "how to switch direct deposit",
  "image_query": "online banking direct deposit paycheck laptop",
  "image_alt": "Switching direct deposit to a new bank account",
  "takeaways": [
    "Switching direct deposit takes three steps: <strong>open the new account, submit a direct-deposit form, and confirm the first deposit lands</strong>.",
    "You'll need your new account's <strong>routing and account numbers</strong>.",
    "<strong>Keep the old account open</strong> until the first paycheck hits the new one.",
    "Update any <strong>autopay bills</strong> linked to the old account too.",
  ],
  "internals": [("best checking account for freelancers", f"{S}/2026/07/best-checking-account-for-freelancers.html"),
    ("no-fee business checking for freelancers", f"{S}/2026/07/no-fee-business-checking-for.html")],
  "table": {"caption": "Switch direct deposit in 3 steps",
    "headers": ["Step", "What to do", "Note"],
    "rows": [["1. Open account", "Get routing + account #", "Choose no-fee"],
      ["2. Submit form", "Give employer new details", "Direct-deposit form"],
      ["3. Confirm", "Check first deposit lands", "Keep old account open"]]},
  "faqs": [
    ("How do I switch my direct deposit to a new bank?", "Open the new account, give your employer a direct-deposit form with the new routing and account numbers, then keep your old account open until the first paycheck lands in the new one."),
    ("What do I need to change direct deposit?", "Your new bank's routing number and account number, and your employer's direct-deposit form (often in a payroll portal). Some banks can pre-fill the form for you."),
    ("How long does it take to switch direct deposit?", "Usually one to two pay cycles. Payroll changes don't always take effect immediately, which is why you keep the old account open until you confirm the switch."),
    ("Should I close my old account after switching?", "Not right away. Keep it open until the first deposit hits the new account and you've moved any autopay bills, then close it to avoid fees."),
    ("Can I split direct deposit between two accounts?", "Many employers let you split your paycheck by percentage or amount across accounts — useful for automatically saving a portion each payday."),
  ],
  "externals": [("CFPB: bank accounts", "https://www.consumerfinance.gov/consumer-tools/bank-accounts/"),
    ("CFPB: switching banks", "https://www.consumerfinance.gov/ask-cfpb/category-bank-accounts-and-services/")],
},
"etsy-invoicing": {
  "id": "5881481550215363041", "url": f"{S}/2026/07/best-invoicing-app-for-etsy-sellers-low.html",
  "title": "Best Invoicing App for Etsy Sellers (2026)",
  "keyword": "best invoicing app for etsy sellers",
  "image_query": "etsy small business seller invoice laptop crafts",
  "image_alt": "Etsy seller managing invoices and expenses",
  "takeaways": [
    "Etsy sellers need an app that tracks <strong>sales, fees, and expenses</strong> for clean bookkeeping and taxes.",
    "Look for <strong>low-volume-friendly pricing</strong>, expense capture, and profit reports.",
    "Etsy handles checkout, but a separate tool helps with <strong>custom invoices and tax records</strong>.",
    "Keep business money separate to simplify <strong>Schedule C</strong> at tax time.",
  ],
  "internals": [("best invoicing software for freelancers", f"{S}/2026/07/best-invoicing-software-for-freelancers.html"),
    ("best invoicing app with expense tracking", f"{S}/2026/07/top-invoicing-app-for-freelancers-with.html")],
  "table": {"caption": "Invoicing/bookkeeping for Etsy sellers",
    "headers": ["Need", "Why", "Priority"],
    "rows": [["Track Etsy fees", "They cut profit", "High"],
      ["Expense capture", "Materials, shipping", "High"],
      ["Custom invoices", "Off-Etsy/custom orders", "Medium"],
      ["Tax reports", "Schedule C ready", "High"]]},
  "faqs": [
    ("What is the best invoicing app for Etsy sellers?", "The best option tracks your Etsy sales and fees, captures expenses like materials and shipping, and exports tax-ready reports — with pricing that suits low-volume sellers."),
    ("Do Etsy sellers need invoicing software?", "Etsy handles checkout, but a bookkeeping/invoicing tool helps track fees and expenses, send custom invoices for off-Etsy orders, and prepare accurate taxes."),
    ("How do Etsy sellers handle taxes?", "Report income and deduct business expenses (materials, shipping, Etsy fees) on Schedule C. Good expense tracking through the year makes this straightforward — keep records."),
    ("Can I send custom invoices as an Etsy seller?", "Yes — for custom or off-platform orders, an invoicing app lets you send professional invoices and accept payment outside Etsy's standard checkout."),
    ("Is free invoicing software enough for Etsy?", "For low-volume sellers, free tiers that track expenses and send basic invoices are often enough. Upgrade when your volume or bookkeeping needs grow."),
  ],
  "externals": [("IRS: self-employed recordkeeping", "https://www.irs.gov/businesses/small-businesses-self-employed/recordkeeping"),
    ("SBA: manage your finances", "https://www.sba.gov/business-guide/manage-your-business/manage-your-finances")],
},
}

MARK = "<!--related-guides-->"


def creds():
    t = json.load(open(os.path.expanduser("~/.config/claude-seo/oauth-token.json")))
    c = Credentials(token=t["access_token"], refresh_token=t.get("refresh_token"),
                    token_uri=t["token_uri"], client_id=t["client_id"],
                    client_secret=t["client_secret"], scopes=t.get("scopes"))
    if not c.valid: c.refresh(Request())
    return c


def eeat_box(cfg):
    ex = cfg["externals"]
    return ('<div class="author-eeat" style="font-size:.9em;color:#475569;border-left:3px solid #6366f1;'
            'padding:.4em 0 .4em 1em;margin:0 0 1.2em"><strong>Reviewed by the Learner&#39;s Link '
            'editorial team</strong> &middot; <em>Last updated: September 2026</em><br>'
            f'Researched from official sources including <a href="{ex[0][1]}" rel="nofollow noopener" '
            f'target="_blank">{ex[0][0]}</a>'
            + (f' and <a href="{ex[1][1]}" rel="nofollow noopener" target="_blank">{ex[1][0]}</a>' if len(ex) > 1 else '')
            + '. We accept no payment to feature specific providers.</div>')


def takeaways_box(cfg):
    lis = "".join(f"<li>{b}</li>" for b in cfg["takeaways"])
    il = cfg.get("internals", [])
    if il:
        links = " and ".join(f'<a href="{u}">{a}</a>' for a, u in il)
        lis += f"<li>Related: see our guides on {links}.</li>"
    return ('<div class="key-takeaways" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;'
            'padding:1em 1.3em;margin:0 0 1.4em"><h2 style="margin-top:0">Key takeaways</h2><ul>'
            + lis + "</ul></div>")


def table_html(cfg):
    t = cfg["table"]
    head = "".join(f"<th>{h}</th>" for h in t["headers"])
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in t["rows"])
    return (f'<h2>{t["caption"]}</h2><div style="overflow-x:auto">'
            '<table border="1" cellpadding="8" cellspacing="0" '
            'style="border-collapse:collapse;width:100%;min-width:480px">'
            f'<thead><tr style="background:#f1f5f9">{head}</tr></thead><tbody>{body}</tbody></table></div>')


def faq_html(cfg):
    return '<h2>Frequently asked questions</h2>' + "".join(
        f"<h3>{q}</h3><p>{a}</p>" for q, a in cfg["faqs"])


def schema_html(cfg):
    sch = {"@context": "https://schema.org", "@graph": [
        {"@type": "BlogPosting", "headline": cfg["title"], "about": cfg["keyword"],
         "url": cfg["url"], "dateModified": "2026-09-15",
         "author": {"@type": "Organization", "name": "Learner's Link"},
         "publisher": {"@type": "Organization", "name": "Learner's Link"}},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
            for q, a in cfg["faqs"]]}]}
    return '<script type="application/ld+json">' + json.dumps(sch) + "</script>"


def gate(cfg, html):
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
    words = len(text.split())
    hrefs = re.findall(r'href="([^"]+)"', html)
    internal = [h for h in hrefs if "learners-link.blogspot.com" in h]
    external = [h for h in hrefs if h.startswith("http") and "learners-link" not in h]
    errs = []
    tl = len(cfg["title"])
    if tl > 70 or tl < 25: errs.append(f"title-length({tl})")
    if not re.search(r"<h2", html, re.I): errs.append("no-h2")
    if "application/ld+json" not in html: errs.append("no-schema")
    if "<img" not in html.lower(): errs.append("no-image")
    if not internal and not external: errs.append("no-links")
    warns = []
    if not (40 <= tl <= 60): warns.append(f"title{tl}")
    if len(internal) < max(3, round(words / 1000 * 3)): warns.append(f"internal{len(internal)}")
    if len(external) < 2: warns.append(f"external{len(external)}")
    if cfg["keyword"].split()[0].lower() not in " ".join(text.split()[:100]).lower():
        warns.append("kw-early")
    return errs, warns, words, len(internal), len(external)


def build(cfg, body):
    if MARK in body:
        main, related = body.split(MARK, 1); related = MARK + related
    else:
        main, related = body, ""
    img, _ = ("", None)
    if "<img" not in main.lower():
        img, _ = img_block(cfg["image_query"], cfg.get("image_alt"))
    # strip any prior injected blocks to stay idempotent
    for cls in ('author-eeat', 'key-takeaways'):
        main = re.sub(rf'<div class="{cls}".*?</div>', '', main, flags=re.S)
    main = re.sub(r'<h2>Frequently asked questions</h2>.*?(?=<h2|$)', '', main, flags=re.S)
    main = re.sub(r'<script type="application/ld\+json">.*?</script>', '', main, flags=re.S)
    return (eeat_box(cfg) + takeaways_box(cfg) + img + table_html(cfg)
            + main + faq_html(cfg) + schema_html(cfg) + related)


def gindex_ping(c, url):
    req = urllib.request.Request("https://indexing.googleapis.com/v3/urlNotifications:publish",
        data=json.dumps({"url": url, "type": "URL_UPDATED"}).encode(),
        headers={"Authorization": f"Bearer {c.token}", "Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=30).getcode()


def main():
    c = creds()
    b = build_svc = __import__("googleapiclient.discovery", fromlist=["build"]).build(
        "blogger", "v3", credentials=c, cache_discovery=False)
    keys = ONLY or list(PAGES)
    for k in keys:
        cfg = PAGES.get(k)
        if not cfg:
            print(f"! unknown page: {k}"); continue
        post = b.posts().get(blogId=BLOG_ID, postId=cfg["id"]).execute()
        new_html = build(cfg, post["content"])
        errs, warns, words, ni, ne = gate(cfg, new_html)
        print(f"\n=== {k} ===")
        print(f"  title '{cfg['title']}' ({len(cfg['title'])}c) | {words}w | int {ni} ext {ne}")
        print(f"  errors: {errs or 'NONE ✅'} | warns: {warns or 'none'}")
        if APPLY and not errs:
            b.posts().patch(blogId=BLOG_ID, postId=cfg["id"],
                            body={"title": cfg["title"], "content": new_html}).execute()
            try:
                code = gindex_ping(c, cfg["url"])
                print(f"  ✅ PATCHED + Google ping {code}")
            except Exception as e:
                print(f"  ✅ PATCHED (Google ping deferred: {str(e)[:40]})")
        elif APPLY and errs:
            print("  ❌ not applied (gate errors)")
    if not APPLY:
        print("\n(dry run — add --apply to write)")


if __name__ == "__main__":
    main()
