# Implemented pipeline fixes — November 12, 2026

## Result

Implemented the six confirmed gaps from the repository review, including the supporting dependency, dashboard and link-coverage repairs. External SERP data and Google's indexing decisions remain pending. No provider subscription or paid SERP collection was enabled.

## Implemented changes

- **Published inventory:** `article_competitor_audit.py` now filters LIVE posts, deduplicates canonical/mobile URLs, refreshes from Blogger and records dated source evidence. The archived Nov 11 source had 105 LIVE and 149 DRAFT records. The fresh Nov 12 API inventory has **107 LIVE articles: 66 Students Time, 41 Learner's Link**. Drafts are excluded; empty or unavailable refreshes cannot masquerade as complete coverage.
- **Competitor coverage:** results are explicitly pending, unavailable, partial or complete. Complete requires ten unique ranked organic URLs at positions 1–10, search provenance, a reviewed target query and successful article extraction. One measured competitor cannot complete a top-ten audit. The site's own result can occupy one position; it is excluded from competitor length statistics.
- **Search connector:** verified-format JSON imports are supported. Optional SerpApi discovery has an explicit request budget, guarded error handling and seven-day successful-result caching. It is disabled in the standard runner. All **107 actual SERP comparisons remain pending** because no search-results credential/import is configured. The adapter has regression coverage but has not made a live provider request.
- **Content analysis:** body extraction uses explicit article containers and Trafilatura when available. Word min/median/max, H1–H3 headings, images and tables are measured. Recurring heading phrases produce lexical topic-review candidates rather than invented semantic conclusions. Robots, public-address and redirect checks reuse the research library. Unsupported/blocked extraction stays unavailable.
- **Length advice:** `serp_analysis.py` uses the shared measured extraction; removed the recommendation to beat competitor length and any automatic word-count ranking target.
- **Main workflow:** competitor coverage now enters SQLite issue history, immutable snapshots and the action queue. Incomplete comparisons keep the job partial, below indexing blockers in priority. Missing source data cannot imply all SEO work is complete.
- **Link coverage:** dedicated Lychee validation now uses all 107 published article bodies, with content-addressed input snapshots and errors mapped to the article URL. Invalid tool output preserves the prior valid report. Blocked/time-out responses remain verification work.
- **Indexing:** removed ordinary-blog Google Indexing API calls from `index_flow.py`, `seo_optimize.py` and `st_optimize.py`. `index_flow.py` previews by default; `--apply` submits supported GSC sitemaps/Bing URLs. Submission remains distinct from index inclusion. Active documentation is aligned.
- **Dashboard:** removed fixed external Python/plugin paths, reused shared Google credentials, corrected Students Time's property URL, surfaced site goals and coverage/freshness, and retained unknown traffic states. The dashboard uses saved complete-window GSC evidence. AdSense reporting is filtered to the selected blog. Optional Custom Search errors now explain unavailable access rather than claiming API propagation. Local dashboard is bound to 127.0.0.1:5000.
- **Dependencies:** root `requirements.txt` includes pinned direct research/content/comparison/dashboard dependencies. `pipeline_preflight.py` checks modules, external binaries and credential presence without exposing keys. The current local preflight passes. The optional SerpApi credential is absent; its private git-ignored file is prepared.

## Site repair

A full-inventory link audit flagged a YouTube iframe in the existing ChatGPT study guide. Its direct embed returned HTML with HTTP 200 while the YouTube metadata endpoint returned 404, so playback could not be verified. Replaced the unverifiable embed with an original five-minute study exercise. Preserved the publication date, saved a full backup and reviewable diff, checked for concurrent content changes, verified Blogger's saved body, and aligned visible/structured modified dates with the actual edit.

Public verification passed: HTTP 200, exercise present, old iframe absent, article body found, canonical URL matches and no noindex. See `reports/improvements/20261112T-video-exercise/`. The final metadata-only adjustment changed no links; its link-set equivalence is recorded for evidence reuse.

## Verification

- **54 regression tests passed**: comparator coverage/provenance, draft exclusion, canonical deduplication, extraction scope, source-cache behavior, safe URL guards, partial-run semantics, link-source attribution, dashboard unavailable states, existing article repairs and research/image workflows.
- Python compile checks passed for every modified executable module.
- Dashboard JavaScript syntax passed `node --check`.
- Seven dashboard routes returned HTTP 200 in smoke checks, and the running localhost dashboard served the expected per-blog coverage and saved goals.
- This is backend/HTTP and JavaScript validation; no interactive browser visual audit is claimed.
- The complete live growth refresh finished successfully and audited 107 published articles. It found no confirmed issues among its anchor/image/canonical checks; the independent iframe finding above was handled separately. External 403s/timeouts remain unverified.

## Current measurements and target

Latest complete GSC window: **Oct 13–Nov 9**. Students Time: **38 impressions, 0 clicks**. Learner's Link: **0 impressions, 0 clicks**. These metrics predate the Nov 11–12 repairs and do not measure their effect.

The fresh stored inspection sample still reports Students Time's homepage redirect error from the older Nov 11 crawl and the Meta page as crawled-not-indexed from Oct 27; Learner's Link's homepage remains crawled-not-indexed. Owner-reported successful Live Tests remain separate evidence. Index recovery is not confirmed.

The saved owner target remains **$5 Students Time AdSense revenue for Nov 11–17**. No new earnings outcome or causal improvement is claimed in this fix report. Prioritize indexability, useful existing pages, qualified visits and domain-specific AdSense measurement before generating more generic articles.

## Remaining external requirements

1. Provide actual SERP results through `reports/competitor_results.json`, or save a usable SerpApi key in `serpapi_key.txt` (private/git-ignored) and explicitly choose a search-request budget. Review title-fallback target queries and choose country/language/device before broad collection.
2. Google's recrawl/indexing remains external. Use Search Console Live Test and request indexing when available; the connected API reads stored inspection records only.
3. SERP-overlap clustering, backlink-index acquisition and field performance monitoring remain expansion work from the research roadmap; they are not represented as completed by these six fixes.
