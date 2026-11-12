# Pipeline gap review — November 12, 2026

## Scope and evidence

Reviewed the current OpenSEO README, package metadata, plugin workflow list and DataForSEO setup guide; GitHub SEO repository search; selected primary project repositories; and local runner, competitor audit, dashboard, keyword tool, indexing flow and reports. Repository feature descriptions establish intended capabilities, not independently verified runtime quality. This is a focused architecture and workflow review, not a completed test of every endpoint or a fresh crawl of both live blogs.

The owner's target remains $5 Students Time AdSense revenue for November 11–17. Saved November 4–10 baseline: approximately $0.02 from 87 ad impressions, impression RPM $0.19. At unchanged RPM, $5 requires approximately 26,316 ad impressions. These historical observations are not a forecast. Stored GSC indexing exclusions remain a priority; latest saved metrics predate the recent content corrections.

## What we have and what is missing

| Capability | Local evidence | Gap | Improvement and completion evidence |
|---|---|---|---|
| GSC/GA4/Blogger/AdSense | Current scripts and verified prior API use | Credentials and metrics are handled by several separate scripts | One credential adapter with availability checks; one timestamped site scorecard with comparable complete windows |
| Technical audit | growth_report.py checks published bodies, links, images, canonicals; stored index sample | Index sample is bounded; sitemap membership, redirect history, duplicate titles and descriptions, crawl depth and performance are not combined into one coverage view | Add per-page coverage and observation dates; join crawl/index/sitemap facts and show unknown states |
| Competitor top 10 | article_competitor_audit.py accepts supplied URLs | No automated SERP adapter; zero measured competitor comparisons in saved report | Provider adapter or documented import with query, engine, country, language, device, collected_at and result position; retain raw evidence and budget cap |
| Article inventory | Saved input has 254 records: Students Time 65 LIVE + 90 DRAFT; Learner's Link 40 LIVE + 59 DRAFT | Competitor tool includes drafts, reports 254 instead of 105 published articles; source fixed to Nov 11 | Filter LIVE records, deduplicate canonical URLs, refresh inventory, record post update/hash; report 65+40 for this snapshot |
| Content extraction | New comparator uses Beautiful Soup article/main selectors | Generic main can include chrome; no extraction confidence, robots policy, redirect/public-IP controls or fetch cache; dependency requires PYTHONPATH | Reuse research_library.py public URL/robots controls and Trafilatura extraction; retain extraction method, response, timestamp and hash; unavailable stays unavailable |
| Word length | New comparator stores body count and competitor median | Older serp_analysis.py says beat median to win and counts much of page body | Retire contradictory length recommendations; compare article content with article content and treat length as descriptive |
| Topics and gaps | Competitor headings saved in JSON | No recurring-topic calculation or actual gap comparison; median is available with only one successful fetch | Aggregate topic frequency by distinct competitor pages, compare covered concepts, show sample size and extraction uncertainty; offer reviewable suggestions |
| Keyword clustering | Seed-related GSC filtering and lexical buckets | No SERP-overlap clustering; many variants group by shared words, which does not prove intent | Use canonical top-10 URL intersections when data exists; keep lexical clusters explicitly heuristic; save reviewed query-to-page targets |
| Workflow integration | seo_workbench.py refresh stages: growth, writing, links | Competitor audit, project context and detailed GSC report are separate commands | Add optional stage adapters and dashboard coverage/freshness display; pending SERP data cannot mark audit complete |
| Links | Lychee and live body checks exist | Dedicated runner Lychee input is one fixed pillar file | Expand from published inventory and deduplicate checked targets; preserve 403/429/timeouts as unverified |
| Indexing | GSC sitemap and stored inspection paths exist | index_flow.py still pings ordinary articles using restricted Google Indexing API; other older publishing helpers may also contain it | Remove ordinary-article pings across entry points. Use sitemaps/discovery and stored inspections; browser live tests and requests remain explicit owner actions |
| Change measurement | SQLite issue history, backups and editorial notes exist | No consistent join of post revision, Google recrawl and subsequent GSC/GA4/AdSense outcomes | Save change timestamp, source/hash, intended query, pre-change window and later complete windows; label effects unobserved until measurements arrive |
| Dashboard | Flask endpoints exist, local loopback binding | Hard-coded external interpreter/plugin paths; report generations aren't unified | Use configured project runtime; show run ID, source timestamps, missing dependencies and partial state on every workflow |
| Backlinks | Ahrefs CSV import, DEV drafts and Medium manual workflow | No independent backlink index or comprehensive new/lost link monitoring | Import timestamped provider/GSC exports and measure qualified referral engagement; use editorial relevant mentions; API access alone creates no links |
| Packaging | requirements-content.txt and requirements-research.txt | New comparator dependency installed separately; no shared reproducible environment | Single dependency manifest/lock and documented bootstrap; environment preflight before running jobs |

## Repositories worth using

1. **every-app/open-seo** — learn provider adapters, project scoping, keyword/competitor/rank workflows and MCP interfaces. Its self-hosted data depends on DataForSEO. Open source does not include a free Google SERP or backlink database. Keep our Blogger publishing and AdSense outcome workflow, which are tailored to these sites. https://github.com/every-app/open-seo
2. **StJudeWasHere/seonaut** — independent technical audit, issue severities, redirect and duplicate metadata checks. Evaluate export ingestion before deploying another whole dashboard/database. https://github.com/StJudeWasHere/seonaut
3. **adbar/trafilatura** — article extraction and metadata; already used in our research library. Reuse existing integration in competitor analysis. https://github.com/adbar/trafilatura
4. **lycheeverse/lychee** — link checking already integrated. Broaden coverage before adding a second link checker. https://github.com/lycheeverse/lychee
5. **GoogleChrome/lighthouse** — performance/accessibility audits for home, course hub and priority article on mobile/desktop; lab results must remain distinct from field Core Web Vitals. https://github.com/GoogleChrome/lighthouse
6. **johnoconnor0/keyword-clustering** — study explicit keyword/page mappings, hybrid similarity and gap exports. SERP overlap is optional data, not a free SERP collection source. https://github.com/johnoconnor0/keyword-clustering
7. **clawnify/OpenSEO** — separate project from every-app/open-seo. Its README describes live SERP competitor research and apply-able editorial edits; adapt the reviewed-diff idea to Blogger. It also relies on a SERP provider for live rankings. https://github.com/clawnify/OpenSEO

Do not install all of these. Check license/version/dependencies before copying code, preserve attribution where required, and prefer narrow adapters over replacing the working stack.

## Implementation order

### P0 — measurement and integrity

Fix published inventory, prevent unsupported indexing calls, remove word-count ranking promises, record dependency/runtime requirements, and expose missing competitor coverage. Acceptance: 105 published articles for the cached Nov 11 inventory; zero draft records compared as published; no unsupported Google article pings; all incomplete comparisons remain visible.

### P1 — complete the per-article comparison

Connect a SERP provider or verified result import. Select a reviewed target query from observed GSC mappings or an explicitly marked title fallback. Measure up to ten organic results with engine/location/device/time evidence, page-type and extraction metadata, word-count distribution, H1–H3 structure, recurring topics/questions, tables/images and useful original material. Separate incomplete extraction from missing content. Cache per query/location/time and per fetched URL; stop on limits rather than silently substituting fabricated results.

Acceptance: every LIVE article has a coverage state, including pending query review, missing SERP data, partial extraction or comparison complete. Completion requires the expected available result set and documented measurement coverage; one successful competitor is a partial sample. Produce an editorial brief with gaps, sources, proposed changes and a factual review step.

### P2 — close the publishing/measurement loop

Join comparison briefs to existing article repair packets, retain backups/hash conflicts, verify the published body/canonical/indexability, then wait for Google recrawl and complete reporting windows. Track crawl status, impressions/clicks, engaged sessions, AdSense impressions/RPM/earnings. Treat changes as experiments with observational outcomes, not proven causality.

### P3 — expand only after the above works

SERP-overlap topic maps, crawl depth/internal-link graph, scheduled monitoring with explicit activation, backlink export history and then optional MCP/UI improvements. AI visibility and large-scale content generation have lower immediate value for the current indexing/revenue bottleneck.

## Remaining inputs

A usable SERP data source or verified top-10 exports is needed for actual ranking comparisons. The local comparator currently has no such connection. There is no supported free-data shortcut in the reviewed open-source code. Project audience and desired search country/language should be recorded before a site-wide paid collection. No subscription or external publishing was activated during this review.

## Primary sources

- https://github.com/every-app/open-seo
- https://github.com/every-app/open-seo/blob/main/plugins/openseo/README.md
- https://github.com/every-app/open-seo/blob/main/docs/DATAFORSEO_API_KEY.md
- https://github.com/search?q=seo&type=repositories
- https://github.com/StJudeWasHere/seonaut
- https://github.com/adbar/trafilatura
- https://github.com/lycheeverse/lychee
- https://github.com/GoogleChrome/lighthouse
- https://github.com/johnoconnor0/keyword-clustering
- https://github.com/clawnify/OpenSEO
- https://developers.google.com/search/apis/indexing-api/v3/using-api

## Implementation follow-up

The confirmed inventory, comparison-status, topic-review, runner/dashboard, dependency and unsupported-indexing fixes were implemented on November 12. See `reports/pipeline_fixes_2026-11-12.md` for validation and remaining external requirements. Actual top-ten SERP measurements still depend on provider credentials or a sourced import; the tool reports them as pending.
