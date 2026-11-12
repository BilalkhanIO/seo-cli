# Both-blog impression diagnosis and repairs — 11 November 2026

Status: DONE_WITH_CONCERNS. The verified website repairs and reporting correction are complete. Google indexing has not recovered; the Learner’s Link manual request was blocked by its daily quota.

## What is actually wrong

The immediate visibility bottleneck is Google indexing. None of 12 selected home, hub and new-article URLs was indexed in its stored inspection record: eight were crawled but not indexed, three had redirect errors and one was unknown to Google. This is a selected sample, not a complete site-wide index count. Public HTTP 200 responses do not establish inclusion in Google’s index.

| Blog | Latest 28-day impressions | Previous 28-day impressions | Last date with impressions through Nov 8 |
|---|---:|---:|---|
| Students Time | 46 | 5 | 2026-10-27 |
| Learner's Link | 1 | 191 | 2026-10-12 |

Latest period: 2026-10-12 to 2026-11-08. Previous period: 2026-09-14 to 2026-10-11. Both latest periods had zero clicks. These measurements predate today’s repairs and cannot show their effect.

## Redirect and sitemap findings

The owner ran Google Live Tests for both homepages. Both returned “URL is available to Google” and “Page can be indexed.” The stored index results still describe earlier crawl failures or exclusions. A successful Live Test establishes current fetchability, not indexing or recovery. The owner also reports no Manual actions or Security issues. Those browser reports were owner-checked, not independently read by the API.

Desktop and smartphone Googlebot-user-agent probes also succeeded. Clean mobile URLs took a single Blogger redirect to `?m=1`, then returned HTTP 200; direct mobile variants returned HTTP 200. These are our HTTP probes, not Google’s own live-test service. No redirect loop, forced JavaScript redirect or meta refresh was found in the checked markup. The exact cause of Google’s earlier failed crawl remains unproven; no speculative redirect or slug changes were applied.

Both public XML sitemaps parse successfully, contain the expected 65 and 40 post URLs, have no duplicate entries, and fetch without redirect under the mobile user-agent probe. After resubmission, Google’s sitemap API reported successful downloads today with zero errors and warnings. The owner’s earlier “Temporary processing error” does not describe the latest sitemap fetch status. Sitemap submission and successful download do not guarantee indexing. The legacy sitemap indexed field is not used as a whole-site index count.

## What was repaired and published

15 existing LIVE articles updated, with per-post backups, content-hash conflict checks and post-write verification. URLs, publication states and original publication dates were retained.

- Restored 12 missing hero images using three visually inspected, attributed Pexels photos with descriptive alt text and dimensions. These are illustrative images, not proof of product use or a guarantee of rankings.
- Added a source-backed credential verification example, worksheet and accurate CV wording to the new course-certificate guide.
- Added a documented Zoho Invoice example and an original recipient-delivery test/checklist to the new invoice-receipt guide. It now distinguishes this procedural test from the older app-comparison guide. No paid-account test or unsupported feature guarantee is claimed.
- Added three contextual links from established course, study-planning and invoicing hubs, including links to the two newly orphaned articles.

All 15 changed pages were publicly refetched and passed content-specific checks, self-canonical checks, article-body presence and no-noindex checks. The final whole-site crawl covered 105 live articles. It found no missing article images, empty alt text, orphan articles, confirmed broken links or canonical conflicts. External 403s and timeouts remain unverified. One Learner’s Link URL timed out and produced 39 repeated link warnings; a targeted follow-up fetched that URL successfully with HTTP 200. The immutable full-crawl snapshot retains the timeout, and the separate follow-up records its successful response.

## Pipeline correction

The old runner could report a clean public crawl while leaving Google indexing exclusions out of its routine queue. Added a bounded stored-index sample to `growth_report.py:222` and high-priority indexing findings in `seo_workbench.py:81`. Each fresh run checks at most three selected URLs per blog: homepage, current performance priority and newest audited article when available. It does not inspect every page, run Google Live Test or request indexing. A quota/API error remains unavailable and cannot clear an earlier exclusion.

37 regression tests passed after the code edits. New tests cover sample bounds, non-indexed statuses, API failures, prioritization and preserving old exclusions during unavailable checks. The live full refresh completed all stages and now surfaces six indexing blockers in the queue instead of treating public HTTP success as recovery.

## Google crawl requests and next action

- Students Time homepage: owner confirmed “Indexing requested” and addition to the priority crawl queue. Not yet confirmed indexed.
- Learner’s Link homepage: Live Test passed, but Request indexing returned daily quota exceeded. The request was NOT submitted. Retry on November 12, 2026 after the quota resets; do not repeat requests today.
- Keep both clean homepage URLs and existing canonicals. Do not force mobile variants into the canonical sitemap or add JavaScript redirects as an unverified workaround.
- Inspect the affected new study/invoice URLs after the homepage requests are processed. Use Google Live Test to distinguish a current fetch failure from the stored index record. If a live test fails, investigate that exact failed hop before changing settings.
- Track actual indexing and impressions over subsequent reporting windows. More generic articles or repeated sitemap submissions are not substitutes for indexed, useful core pages. No manual penalty, algorithmic penalty, ranking recovery or exact explanation for Google’s content-selection decision has been established.

## OAuth monitoring note

The saved refresh token had expired/revoked again; access was restored with the owner’s new consent. Repeated seven-day expiry can occur when an external Google OAuth app remains in Testing, but this project’s publishing status was not accessible through the granted scopes. Check Google Cloud → Google Auth Platform → Audience before assuming that is the cause. No cloud audience setting was changed.

## Evidence and reproduction

- Current performance and stored sample: `reports/growth_latest.json` / `.md`
- Initial 12-URL Google sample: `reports/indexing_diagnostic_2026-11-11.json`
- Daily visibility: `reports/daily_search_2026-11-11.json`
- Owner browser checks: `reports/owner_console_checks_2026-11-11.json`
- HTTP redirect probes: `reports/redirect_probes_2026-11-11.json`
- Sitemap API and XML checks: `reports/sitemap_status_2026-11-11.json`
- Published packet, diffs and backups: `/home/kwikcoders/seo/reports/improvements/20261111T072426Z-indexing-recovery`
- Public repair verification: `reports/recovery_public_verification_2026-11-11.json`
- Timeout follow-up: `reports/timeout_followup_2026-11-11.json`
- Final immutable workbench run: `reports/workbench/20261111T072736Z-0c576efc/`

Regression command: `python3 -m unittest test_article_improver test_seo_workbench test_research_library test_content_review test_growth_report test_image_pipeline`

## DEBUG REPORT

Symptom: Both blogs show little or no recent Google impressions.
Root cause: Selected core URLs are excluded from Google’s index; historical redirect failures and non-indexed crawl decisions block visibility. The reporting pipeline did not routinely surface those exclusions. The exact Google selection/earlier redirect cause remains unproven.
Fix: Published 15 verified article repairs; restored missing images and discoverability; improved two thin guides; resubmitted valid sitemaps; added bounded Google index-status sampling and high-priority queue findings.
Evidence: 15 verified API saves and 15 public checks; 105-article crawl; Google Live Tests passed per owner; both sitemaps downloaded without errors; Students Time request confirmed; Learner’s Link request quota failure explicitly retained.
Regression test: `test_growth_report.py:9`, `test_growth_report.py:18`, `test_seo_workbench.py:36`, `test_seo_workbench.py:41`; 37 tests passed.
Status: DONE_WITH_CONCERNS — website/reporting changes complete; Google indexing and the Learner’s Link request remain pending.
Scope: Both hosted blogs and the existing reporting modules. No run-owned filesystem freeze was acquired because the investigation spans these site-wide paths; no other scope boundary was removed.

## Primary references

- [Google Page indexing report](https://support.google.com/webmasters/answer/7440203?hl=en)
- [URL Inspection and Live Test](https://support.google.com/webmasters/answer/9012289/)
- [Requesting recrawling does not guarantee indexing](https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl)
- [Microsoft achievements and credentials](https://learn.microsoft.com/en-us/training/support/faq)
- [Zoho Invoice expense recording](https://www.zoho.com/in/invoice/help/expense/expenses.html)
- [Zoho Invoice attachment instructions](https://www.zoho.com/en-sg/invoice/help/invoice/new-invoice.html)
- [Google OAuth token expiration](https://developers.google.com/identity/protocols/oauth2)
