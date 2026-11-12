# SEO Playbook — studenttimepk.blogspot.com
> **Historical notes only.** This playbook contains dated plans and assumptions that may no longer be true (including impressions, indexing, API availability and old post plans). Do not execute its old checklist without rechecking current evidence. Use [`SEO-WORKBENCH.md`](SEO-WORKBENCH.md) for current commands and [`docs/seo-technical-reference.md`](docs/seo-technical-reference.md) for source-linked technical guidance and Google API capabilities.

_The sections below are preserved as historical context; verify them before acting._

## Target market (IMPORTANT)
**Audience = tier-1 English markets: US · UK · Canada · EU** (high AdSense CPM ~$8–15 vs ~$0.50 for PK).
All content is globally framed — **no Pakistan/local angle**. Keyword research runs in US/UK/CA geo, not PK.

## 0. The core problem (why there's no traffic)
Search Console proved it: **0 clicks / 0 impressions**. The site is effectively invisible because:
1. **Homepage "Redirect error"** (from a March glitch — the redirect is fixed now, but Google backed off and hasn't re-crawled).
2. **Thin + duplicate content** → posts get **"Discovered – currently not indexed"** (Google found them, decided they're not worth indexing).

**The fix = rebuild trust:** kill duplicates → strong pillars → re-crawl → index → rank. That's this whole playbook.

---

## 1. What's DONE ✅
- **Search Console connected** (read + **write**). Sitemap `sitemap.xml` (128 URLs) **submitted via API**.
- **3 pillars built & live** (consolidation):
  | Pillar | URL | Words |
  |---|---|---|
  | Free AI Courses w/ Certificates (Global + Pakistan) | `/2026/07/free-ai-courses-with-certificates-in.html` | 1,533 |
  | GPT-5.6 for Developers (Sol/Terra/Luna) | `/2026/07/gpt-56-goes-public-what-developers.html` | 1,429 |
  | Google Antigravity 2.0 | `/2026/07/google-antigravity-20-ai-agents-for.html` | 1,465 |
- **2 posts upgraded** to ~1,700w: AI Singularity, AI Agents (GPT-5.6 & agents).
- **19 duplicates drafted** (unpublished, reversible) so their URLs 404 for redirects.

---

## 2. YOUR TO-DO (manual — I can't do these via API)

### A. Add 19 Custom Redirects
Blogger → **Settings → Errors and redirects → Custom Redirects** → New → tick **Permanent ✅**.

**→ Cert pillar** `To: /2026/07/free-ai-courses-with-certificates-in.html`
```
/2026/08/free-ai-certifications-surge-in-2026.html
/2026/07/free-ai-certifications-surge-in-2026.html
/2026/07/free-ai-certifications-surge-in-2026_01933436756.html
/2026/08/free-ai-certification-gains-momentum.html
/2026/07/ai-certifications-go-free-top-free.html
/2026/07/ai-certifications-accelerate-careers-in.html
/2026/07/ai-certifications-boom-2026-free.html
/2026/07/open-free-ai-certifications-online-in.html
/2026/07/free-ai-for-social-impact-certification.html
/2026/07/free-ai-certification-launches-ai-for.html
/2026/07/free-ai-certification-for-social-impact.html
```
**→ GPT-5.6 pillar** `To: /2026/07/gpt-56-goes-public-what-developers.html`
```
/2026/08/gpt-56-debuts-ai-harvests-speed-risk.html
/2026/07/gpt-56-release-what-it-means-for-devs.html
/2026/07/gpt-56-rollout-transforms-ai-coding.html
/2026/07/gpt-56-rollout-reshapes-ai-development.html
```
**→ Antigravity pillar** `To: /2026/07/google-antigravity-20-ai-agents-for.html`
```
/2026/08/google-signals-agi-within-reach-with.html
/2026/07/antigravity-and-gemini-api-new-ai.html
/2026/07/google-antigravity-20-new-agent-first.html
/2026/07/google-antigravity-20-agentic-coding.html
```
**→ EU AI Act pillar** `To: /2026/08/eu-ai-act-updates-what-developers-must.html`
```
/2026/08/eu-ai-regulation-crackdown-sets-new.html
/2026/07/ai-governance-debate-heats-up.html
/2026/07/ai-governance-in-focus-un-ai-for-good.html
/2026/07/ai-governance-in-focus-new-un.html
/2026/07/eu-ai-rules-move-forward-what.html
```
**→ AI Singularity (Post 1)** `To: /2026/08/ai-singularity-debate-heats-up-as.html`
```
/2026/08/ai-singularity-threshold-what.html
```
**→ OpenAI Astra pillar** `To: /2026/08/openai-astra-next-gen-ai-model-and-what.html`
```
/2026/08/openai-gpt-56-astra-what-it-means-for.html
```
**→ AI Agents pillar** `To: /2025/10/mastering-ai-agent-orchestration-rise.html`
```
/2026/07/gemini-35-and-agent-first-dev-platform.html
/2026/07/agentic-ai-tooling-google-io-2026.html
```
**→ AI Security pillar** `To: /2026/08/ai-in-dev-why-fixing-vulnerabilities-is.html`
```
/2026/07/openai-hugging-face-security-incident.html
/2026/07/ai-driven-patch-tuesday-windows-11-july.html
/2026/07/hugging-face-breach-in-2026-what.html
/2026/07/ai-safety-models-do-things-we-didnt.html
/2026/07/ai-dev-tools-under-duress-how-to-shield.html
```
**→ AI Coding Tools pillar** `To: /2026/07/ai-dev-tools-boom-what-build-2026.html`
```
/2026/07/ai-powered-ide-features-boost-developer.html
/2026/07/copilot-gets-organized-ai-agents-now.html
/2026/07/visual-studio-2026-ai-next-gen-coding.html
/2026/07/chrome-devtools-ai-update-boost-your-ai.html
/2026/07/github-copilot-browser-tools-ga-ai.html
/2026/07/codex-micro-keyboard-sparks-new.html
/2026/07/chrome-devtools-ai-overhaul-boosts.html
/2026/07/openrouter-gives-developers-free-ai.html
/2026/07/chrome-devtools-ai-next-wave-for-web.html
/2026/07/ai-native-dev-tools-cloudflares.html
/2026/07/ai-enhanced-chrome-devtools-next-wave.html
```

### B. Paste meta descriptions (Post → Search Description)
- **Cert pillar:** `Free AI courses with certificates in 2026—the best free options from Google, Microsoft, IBM, Coursera & Elements of AI, which ones employers value, and how to add them to your CV.`
- **GPT-5.6 pillar:** `GPT-5.6 for developers: compare the Sol, Terra & Luna variants, see which to use, pricing, and how to evaluate and migrate safely in 2026.`
- **Antigravity pillar:** `Google Antigravity 2.0 explained: features, pricing, the new CLI & SDK, how to use it, and how it compares to Claude Code. Your 2026 developer guide.`
- **Post 2 (AI agents):** `GPT-5.6 pushes AI agents into real developer workflows—learn the building blocks of agentic AI, practical steps to start, and the guardrails you need.`
- **EU AI Act pillar:** `EU AI Act 2026 explained for developers: risk tiers, key deadlines, what you must do, penalties, and how AI governance is evolving worldwide.`
- **AI Coding Tools pillar:** `The best AI coding tools for developers in 2026: GitHub Copilot, VS Code AI, Google Antigravity, Chrome DevTools AI & OpenRouter—free picks and how to choose.`
- **AI Security pillar:** `AI security for developers in 2026: fix AI-generated code vulnerabilities, secure your pipeline, handle generative AI risks like prompt injection, and stay safe.`

### C. Request Indexing (GSC → URL Inspection → Request Indexing)
The homepage + 3 pillars:
```
https://studenttimepk.blogspot.com/
/2026/07/free-ai-courses-with-certificates-in.html
/2026/07/gpt-56-goes-public-what-developers.html
/2026/07/google-antigravity-20-ai-agents-for.html
```
(Re-do this for each new pillar as we build them.)

---

## 3. Consolidation ROADMAP (remaining — I execute these)
Same pattern each time: research keywords → build 1 pillar → draft dupes → give you redirects.

| Cluster | Live posts | Plan |
|---|---:|---|
| **AI Dev Tools** (Chrome DevTools ×3, Copilot, IDE, VS, GitHub, Codex, OpenRouter) | 9 | 1 pillar: "Best AI Coding Tools 2026" + keep distinct ones |
| **EU AI Act / Governance** (EU Act ×2, UN Gov ×2) | 6 | 1 pillar: "EU AI Act & AI Governance 2026" |
| **AI Agents** (Copilot agents, Gemini agent, I/O agentic, orchestration) | 4 | Fold into existing AI-agents post or 1 pillar |
| **AI Security** (vulnerabilities, HuggingFace breach ×2, patch) | 4 | 1 pillar: "AI Security for Developers 2026" |
| **AI Singularity** (×2) | 2 | Keep Post 1; redirect the 2nd |
| **Astra** (OpenAI Astra + GPT-5.6&Astra) | 2 | 1 pillar or fold into GPT-5.6 |
| **"AI News" roundups / misc** (in the 68 "other") | ~68 | Finer pass: many unique news items; merge obvious dupes, prune stale |
| **Off-niche** (IP address, wealth, sand art, Mandela) | ~4 | Prune or de-index (don't fit an AI-dev blog) |
| **Ruby lessons / HTML** | 5 | Separate mini-topic; keep or spin to own hub |

**Target end state:** ~124 posts → ~35–45 strong, keyword-targeted pages.

---

## 4. Keyword Research process (per pillar)
1. **Seeds** from the topic → 2. **Autocomplete + question-mining** (I automate) → 3. **Cluster by intent** → 4. **Pick 1 primary + secondaries + FAQ questions** (favor **long-tail + Pakistan** = winnable) → 5. **Difficulty check** via SERP → 6. **Map** primary→title/H1/URL/meta, secondaries→H2s, questions→FAQ → 7. **GSC striking-distance loop** (positions 8–20) once indexed = highest-ROI, automated by the monitor.

## 5. Backlink process
- **Prereq:** linkable pillars (done/ongoing).
- **Tier 1 (you, this week):** social profiles → blog (LinkedIn, X, FB Page, Pinterest, Medium manual republish/import with canonical, and DEV Community adapted draft with canonical).
- **DEV workflow:** publish the original on Blogger first → create a genuinely adapted DEV article → set `canonical_url` to the original Blogger URL → save as draft → human review → publish → track referral sessions and the canonical in Search Console. Never publish an identical mass copy.
- **Medium workflow:** use Medium's manual import/editor because new API integrations are closed; verify the original URL/source attribution before publishing.
- **Tier 2:** community answers (Reddit, Quora, **Pakistani student/tech FB groups** = your edge), guest posts.
- **Automate:** discovery (Common Crawl), DA checks (Moz free), outreach drafts (me). **Never automate posting** = spam = penalty.
- **Avoid:** paid links, PBNs, fiverr backlinks.

---

## 6. Automation & tools (in this folder)
| File | Does |
|---|---|
| `blogger_cli.py` | Read/update/draft posts via Blogger API |
| `gsc_submit.py` | Submit sitemaps via API |
| `gsc_monitor.py` | Weekly report: GSC totals, striking-distance keywords, index status |
| `gsc_opportunities.py` | 90-day GSC query/page report for positions 8–20 and refresh priorities |
| `growth_report.py` | Both blogs: separate 28-day GSC comparisons, top-five page priorities, positions 8–50, GA4 DEV/Medium referrals, published article link/image/canonical audit, Ahrefs CSV imports. Read-only; run weekly manually. |
| `seo_workbench.py` | One job runner: SQLite history, dated report snapshots, new/persistent/resolved/reopened issues and a prioritized action queue. `run` uses saved reports; `run --refresh` collects current measurements. No publishing stage. |
| `seo_pipeline_check.py` | Live/local HTML gate: word count, headings, canonical, links, images, schema, noindex |
| `content_review.py` | Local Textstat readability and Vale writing rules; long sentences, repetition, wordiness and claims to review. No paid API. |
| `open_source_link_check.py` | Pinned Lychee link checker; outputs JSON and logs to reports/. No paid API. |
| `content_brief_template.md` | Evidence, intent, source-check and original-example checklist before writing. |
| `install_seo_tools.py` | Installs pinned Lychee/Vale official releases with verified SHA-256; Textstat dependencies use requirements-content.txt. |
| `manual_seo_tasks_latest.md` | Current manual meta-description and Search Console indexing checklist |
| `gsc_auth.py` | Google OAuth (GSC) |
| `trends_research.py` | **Google Trends** — trend direction + rising/breakout keywords (free, no login). Usage: `python trends_research.py "seed1" "seed2" --geo PK` |
| `bing_submit.py` | **Bing URL Submission** — submit URLs for indexing (10k/day quota). Re-run after publishing new pillars |
| `devto_update_pillar_draft.py` | Create/update a **DEV Community draft** with a canonical link to the original Blogger pillar; review before publishing |
| PageSpeed (via `claude-seo run pagespeed_check.py <url> --api-key $(cat psi_key.txt)`) | Core Web Vitals / Lighthouse scores |

**Content checks:** use `seo_pipeline_check.py` for technical validation and editorial review for source accuracy, relevance and originality. Do not report unavailable model/tool scores. Word count is measured from the article body and is informational, not a ranking threshold.

**Image integration (verified October 27, 2026):** Pexels API credentials work. Markdown uploads must use `build_content()` with `**Image query:**`; it retrieves a lead image with dimensions, alt text and linked photographer/Pexels credit. API failures stop upload. `repair_post_images.py` audits specific missing images; `--apply` backs up posts before patching. `upload_drafts.py` checks LIVE, DRAFT and SCHEDULED posts in ADMIN view to prevent duplicates. Run `python3 -m unittest test_image_pipeline` after changes.

### Free tools — connected vs available
| Tool | Value | Status |
|---|---|---|
| Google Search Console | queries, index, sitemap | ✅ connected (read+write) |
| Google Autocomplete | keyword ideas | ✅ |
| Google Trends | rising/breakout keywords | ✅ (`trends_research.py`) |
| Common Crawl | backlink graph | ✅ (baseline: 0 links) |
| PageSpeed Insights | Core Web Vitals | ✅ connected (`psi_key.txt`) |
| GA4 | traffic/conversions | ✅ auth done — ⚠️ no GA4 property for this blog (create one in Blogger to use) |
| Bing Webmaster + URL Submission | bonus indexing (Bing/ChatGPT/DuckDuckGo) | ✅ connected (`bing_key.txt`) — 104 URLs submitted |
| Moz free API | Domain Authority | ⏳ optional, free key |

**Run the weekly monitor manually:**
```
/home/kwikcoders/.local/share/claude-seo/.venv/bin/python /home/kwikcoders/seo/gsc_monitor.py
```
**To schedule it yourself (weekly, Mon 9am):** `crontab -e` and add:
```
0 9 * * 1 /home/kwikcoders/.local/share/claude-seo/.venv/bin/python /home/kwikcoders/seo/gsc_monitor.py >> /home/kwikcoders/seo/seo_monitor.log 2>&1
```

---

## 7. Priority order (the plan)
1. **You:** redirects + meta descriptions + Request Indexing (Section 2) ← unblocks indexing
2. **Me:** keep consolidating clusters (Section 3) ← more strong pillars
3. **You:** Tier-1 backlinks (Section 5) ← trust + crawl paths
4. **Ongoing:** weekly monitor → once impressions appear, chase striking-distance keywords
- **OpenAI Astra pillar:** `OpenAI Astra explained: what OpenAI's reported next-gen model does (math, reasoning, theoretical CS), how it compares to GPT-5.6, and how developers should prepare.`
- **AI Agents pillar:** `AI agents explained: how agentic AI works (planning, tool use, memory), real workflow automation examples, top platforms, and how to build your first agent.`

---

## Learner's Link (learners-link.blogspot.com) — AdSense "Low value content" fix
_2026-09-15 — finance blog, US/UK/CA/EU audience_

**AdSense violation (exact):** "Low value content" → minimum content requirements / unique high-quality content / thin-content guidelines.

**Root cause = keyword cannibalization + off-niche.** 61 live posts, but 33 were near-duplicates/off-niche
(e.g. 9× "balance transfer 0% APR", 12× "high-yield savings", 2× identical "HELOC vs Personal Loan").

**Fix DONE (reversible — reverted to draft, content preserved):**
- Drafted **32 zero-impression duplicates** (kept the ranking/strongest post per cluster).
- Drafted **1 off-niche** ("Enterprise WordPress Multisite Migration").
- Result: **28 unique, high-quality finance posts** live.
- Trust pages verified present: Privacy Policy, Contact Us, About Us ✅.
- Sitemap resubmitted to GSC; 29 clean URLs pushed to Bing.

**YOUR TO-DO (manual):**
1. **AdSense → Request Review** (site now meets minimum-content / unique-content bar).
2. **GSC → Request Indexing** for the strong finance pages (page-1 candidates).
3. **Publish OAuth app to Production** (Cloud Console → OAuth consent screen → PUBLISH APP) to stop the 7-day token expiry.

**Scripts:** `ll_consolidate.py` (analyze, read-only) · `ll_do_consolidate.py` (execute draft) · `auth_link.py`+`finish_auth.py` (manual OAuth when token dies).
