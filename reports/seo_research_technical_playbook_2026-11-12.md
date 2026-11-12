# SEO research and implementation plan — 12 November 2026

This is the current, source-linked technical reference for the Students Time and Learner's Link workflow. It replaces older assumptions in `SEO-PLAYBOOK.md` where those conflict with current Google documentation. Research was checked against Google Search Central, Google developer documentation, official Blogger help, Ahrefs API documentation, and the repositories linked below. Recommendations are evidence-based; they are not promises of rankings, impressions, indexing, or revenue.

## What the evidence says for these two sites

- The latest connected Search Console data is a dated reporting window, not a live forecast. The saved window is 13 October–9 November 2026. Search Console can omit anonymized queries, and zero visible query rows is not proof of zero demand.
- There are 109 current published posts in the refreshed Blogger inventory: 67 Students Time and 42 Learner's Link. The competitor report has 107 `pending_search_results` rows because no eligible SERP source is configured. We have not measured 107 top-10 SERPs.
- GSC shows a sharp Learner's Link visibility stop: the last impression in the date/page, date/device and date/country views was 12 October; the site recorded zero impressions from 13 October through 9 November. Its preceding 28-day period had 192 impressions and 2 clicks; the current period had zero. This is a correlation in GSC, not proof of a cause. Google lists its September 2026 spam update as ending 8 October and its November core update as starting 10 November; the latter began after the reported drop.
- Current stored URL Inspection records say Learner's Link's homepage and its two highest-impression pages from the previous window are `Crawled - currently not indexed`, with successful fetches and self-canonicals. The two inspected Students Time course pages also show that state. Students Time had 38 impressions in the current window (up from 13), all clicks zero; Learner's Link had zero. The Students Time homepage remains a stored `Redirect error`, despite the owner's earlier successful live test. These are stored index records, not live tests.
- One Learner's Link URL previously visible in GSC (`/2026/09/best-cashback-credit-card-for-beginners.html`) now redirects to the current `/2026/10/best-beginner-cash-back-credit-card-how.html` URL, which returns 200. This appears to be a Blogger permalink move; verify that the destination is the intended equivalent and keep the redirect. Google’s saved record for the old URL still reports 404, so the two observations are from different times.
- The new rendered-HTML check found no missing titles/descriptions on Students Time, but 31/42 Learner's Link posts lacked a rendered meta description. The Blogger API v3 does not expose a per-post search-description field; Blogger exposes these controls in its owner UI. The pipeline flags this for review and does not create descriptions from templates. A supplied description is not a guarantee that Google will use it or index the page.
- The last complete link measurement is 12 November 2026 at 09:53 UTC. Its external HTTP results remain dated evidence. The later local reconciliation only removed a dead YouTube embed that is no longer in the published post; it made zero network requests and does not refresh other link statuses.
- The stored Google index sample shows several exclusions/unknown URLs, including a Students Time homepage `Redirect error`, Learner's Link homepage `Crawled - currently not indexed`, and recent posts not yet known or indexed. URL Inspection API reads the stored index version only. Live URL tests and the browser-only Request indexing control remain separate.
- The article audit found many 403/401/503 responses for external links (including Pexels and official sites). They are unverified from this checker, not confirmed broken links. Only 404/410 observations should be treated as confirmed gone without a separate check.
- Recent topical runs include a Students Time study-skills cluster and a Learner's Link freelance cluster. The system should judge each post on distinct user intent, accuracy, original usefulness, sources and internal links. Word count is descriptive; a longer article is not automatically better.

## Evidence-based work order

1. **Crawl and indexability:** test clean canonical URLs on mobile, inspect redirects and response codes, verify robots/noindex/canonical and sitemap membership, then compare live test with the stored URL Inspection result. A successful sitemap submission is only a hint. Do not repeat Request indexing in a loop.
2. **Search visibility:** use complete, adjacent GSC windows and query-only, page-only, and query-page views. Prioritize pages with observed impressions and positions, not guessed search volume. Keep query privacy gaps visible.
3. **Article usefulness:** start from one reader task and one primary intent. Verify time-sensitive claims at their official source. Add an original worked example, checklist, experience, or analysis only where it helps the reader. Cite sources; do not rewrite competitors or generate batches of near-duplicate pages.
4. **Internal discovery:** add a small number of contextual links between genuinely related articles and useful cluster hubs. Avoid sitewide keyword-rich links and links whose only purpose is passing ranking signals.
5. **Snippet and page experience:** make titles accurate and specific; write a useful search description where Blogger exposes that setting. Give images relevant alt text and use distinct images when they communicate different content. Check mobile readability, intrusive ads, HTTPS and Core Web Vitals. Treat lab and field data separately.
6. **Measure change:** save the before/after article body and metadata, record the exact live URL, wait for recrawl, then compare the same GSC windows and query/page pairs. No guaranteed time-to-index or earnings uplift exists.

Google's Search Essentials prioritize helpful people-first content, understandable titles/headings, crawlable links, and correct use of content-specific features. Google does not set a preferred article word count. Scaled pages created mainly to manipulate rankings can violate spam policies, including when generative AI is used without distinctive value. E-E-A-T is a framework in Google's guidance, not a single ranking score. Core Web Vitals are recommended experience measures, not a guarantee of rank.

## Google and adjacent APIs: capability and fit

| API / product | What it can provide here | Access and key limits | Decision |
|---|---|---|---|
| Search Console API | Search Analytics rows; sites; sitemap list/submit; stored index inspection | Existing OAuth. Query rows are bounded and can omit anonymized data. URL Inspection has quotas and only reports the indexed version; it cannot run the UI's Live Test or request indexing. | Core source. Cache data, use complete windows, cap inspection to prioritized URLs, never label stored state as live. |
| Blogger API v3 | Read/write posts, pages, labels, and blog resources; inventory live posts | Existing OAuth with Blogger scope. Some Blogger UI settings are not exposed as ordinary post fields. | Core CMS integration. Guard live edits with status/URL checks, backups, post-write readback, and public verification. |
| Google Analytics Data API v1 | GA4 reports such as sessions, engaged sessions and landing pages | Existing OAuth with analytics.readonly; quotas are token-based and depend on query complexity. | Use to understand attributable visits and engagement, not as a substitute for GSC impressions or proof that sessions are human. |
| AdSense Management API v2 | Account/site inventory and estimated earnings/performance reports | Existing OAuth with adsense.readonly. Report filters/dimensions and account timezone must be explicit; the metric is estimated until finalized. | Keep per-blog reporting, preserve unavailable as unavailable, and label estimates and date windows. |
| Search Console sitemap endpoint | Submit/list sitemaps | Included in Search Console API; submission returns no indexing guarantee. | Use only on change or when status is wrong; do not resubmit the same unchanged sitemap repeatedly. |
| Google Indexing API | Notifications for eligible JobPosting pages and livestream event pages with required structured data | Not a general Blogger-post indexing endpoint. | Disabled for ordinary posts. Use sitemaps, internal discovery, URL Inspection and Search Console UI controls. |
| PageSpeed Insights API | Lighthouse lab diagnostics and, where available, CrUX field data | Google API endpoint; API key recommended. Field data may be absent for low-traffic URLs. | Add as a bounded, cached performance check after the existing crawl workflow is stable. Never turn missing CrUX data into a failing score. |
| Chrome UX Report (CrUX) API | Aggregated real-user metrics at origin or URL granularity | Requires a Google Cloud API key; data only exists where sample/privacy thresholds are met. | Useful field-data alternative when PSI lacks a clear response; cache and label the population/window. |
| Google Trends API | Programmatic, consistently scaled trend data | Google currently describes it as an alpha and accepts applications; access is limited. | Apply if the workflow merits it. Current `pytrends` scraping is unofficial and must be labeled experimental, not a stable Google API. |
| Google Ads API Keyword Planning | Keyword ideas, historical average monthly search data, geography/language targeting | Requires Google Ads OAuth, developer token and appropriate access; planning methods have stricter rate limits. Volume is Ads historical estimate, not GSC data. | Optional research source if credentials and access are supplied; do not block core publishing on it. |
| YouTube Data API v3 | Public video/channel/playlist metadata and search; caption-track management for authorized content | Default `search.list` bucket is 100 calls/day. Caption listing costs quota, and downloading captions requires OAuth; channel-owner/partner permissions apply. | Use for curated official learning resources and metadata. Do not promise bulk transcripts from channels we do not control. |
| Custom Search JSON API | Programmable Search results | Closed to new customers; existing customers must transition by 1 January 2027. | Not a new solution for top-10 competitor research. |
| Vertex AI Search | Search over a bounded set of selected domains | Google presents it as an alternative for up to 50 domains; it is not an unrestricted Google web SERP API. | Could support research over known official sources, not reproduce general top-10 rankings. |

The Search Console API reference lists Search Analytics, Sitemaps, Sites and URL Inspection; it does not expose browser Live Test or Request indexing. Search Console URL inspection allowance is bounded per property/project. For this small portfolio, conservative batching and caching is more appropriate than inspecting all 107 URLs every run.

## Ahrefs and SERP coverage

The connected Ahrefs key previously supplied is scoped to **public endpoints**. Ahrefs documents those as crawler IP/range and free Domain Rating endpoints; this is not permission to call paid Site Explorer, Keywords Explorer or SERP Overview endpoints. Ahrefs SERP Overview can return up to 100 results when the account/key is eligible, but ordinary API requests may consume units (minimum 50 units per paid request). Its free test SERPs are only for the keywords `ahrefs`, `yep`, or `firehose`, so they cannot validate this portfolio's queries.

Current options for actual article-by-article top-10 data:

- Configure an eligible provider key (SerpApi is supported by the existing comparator) and select an explicit maximum number of searches before requesting data.
- If the Ahrefs account has an eligible paid API plan or tracked SERP project, use the API button/API report for a small pilot after checking units and row limits. No such entitlement is established by the public-only key.
- Otherwise, collect manually reviewed result sets in the supplied comparator template, recording country, language, device, date and query. Do not treat generic web-search snippets or a competitor-page sample as a verified top 10.

Until one of these is available, top-10 article comparisons remain pending by design. Do not spend credits by testing random production keywords.

## Video courses and transcript handling

Google Search Central published two official, sequential playlists on 6 October 2026:

1. [Search fundamentals for beginners](https://www.youtube.com/playlist?list=PLbrFcZbKqjoI) — crawling/indexing/serving; Search Console setup and performance; Trends and topic discovery.
2. [Technical SEO fundamentals](https://www.youtube.com/playlist?list=PLeMjPeaUGn9U) — robots and crawl architecture; index debugging and duplicate URLs; rendering, page weight, APIs and bulk Search Console data.

Useful individual official lessons:

- [How Google Search crawls pages](https://www.youtube.com/watch?v=JuK7NnfyEuc) — chapters: crawling (0:49), discovery (1:01), Googlebot (2:09), fetch/render (3:54), sitemaps (5:15).
- [How Google Search indexes pages](https://www.youtube.com/watch?v=pe-NSvBTg2o) — page processing, content and metadata, duplicate/canonical analysis, and why crawling does not guarantee indexing.
- [Anatomy of a Search Result](https://www.youtube.com/watch?v=IosyvXjQvlw) — title links (1:39), snippets (2:06), attribution (3:21).

YouTube's transcript UI can show captions for a video when its creator has captions available. The YouTube Data API caption endpoints require OAuth and sufficient rights to the video; they are not a public transcript-download API for Google's channel. The pipeline should keep video URLs, official descriptions/chapters, and our own concise notes/summaries. It should not scrape YouTube or copy and store whole transcripts from third-party creators.

## Open-source project review

Use projects as implementation references, not as ranking authorities. The existing local pipeline already has safe URL fetching, public-page extraction, a manifest-aware link checker, SQLite issue lifecycle, a Blogger writer, GSC/GA/AdSense reports, and a competitor comparison contract.

- [every-app/open-seo](https://github.com/every-app/open-seo) — useful MCP/provider integration architecture; production data depends on the configured DataForSEO service. Its UI/workflow is not a source of Google's ranking rules.
- [Screaming Frog SEO Spider](https://www.screamingfrog.co.uk/seo-spider/) is a mature commercial crawler reference, not an open-source dependency.
- [Google Lighthouse](https://github.com/GoogleChrome/lighthouse) is the primary open-source lab audit engine to consider for reproducible page-performance checks.
- [Lychee](https://github.com/lycheeverse/lychee) and [Vale](https://github.com/errata-ai/vale) are already pinned in this repository for links and style.
- Emerging GitHub SEO crawler repositories change quickly and may have small maintainer bases or incomplete checks. Before adopting one, verify license, last release, issue history, dependency health, crawl politeness/robots handling, evidence per rule, and whether it duplicates installed tools. No new crawler dependency is justified until that review is done.

## Work remaining

1. Obtain an eligible SERP source/key or use reviewed result packets; then process the highest-priority GSC pages first, not all 107 blindly.
2. Re-run fresh live public crawl and Google data, then investigate the site-wide Learner's Link impression stop and Students Time stored homepage redirect versus the owner's successful mobile Live Test.
3. In Blogger owner UI, check that search descriptions are enabled and review descriptions for the 31 flagged Learner's Link posts; also inspect robots settings, template canonical tags, mobile links and sitemap status. Blogger API v3 does not provide per-post search descriptions, and Search Console API cannot replace the manual Live Test.
4. Audit recent article clusters for distinct intent, authoritative citations, original examples and accurate update dates before publishing more.
5. Add PSI/CrUX with an optional API key and missing-data-safe reports; optionally apply for Google Trends API alpha and Google Ads API access.
6. Replace stale instructions in the historical playbook with links to this guide and the current workbench commands.

## Primary references

- [Google Search Essentials](https://developers.google.com/search/docs/essentials)
- [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [Helpful, reliable, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
- [Google Search spam policies](https://developers.google.com/search/docs/essentials/spam-policies)
- [How Google Search works](https://developers.google.com/search/docs/fundamentals/how-search-works)
- [Crawling and indexing troubleshooting](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors)
- [URL Inspection API](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect)
- [Search Console API reference](https://developers.google.com/webmaster-tools/v1/api_reference_index)
- [Search Console API quotas](https://developers.google.com/webmaster-tools/limits)
- [Blogger API v3](https://developers.google.com/blogger/docs/3.0/reference)
- [Blogger search settings and crawlers](https://support.google.com/blogger/answer/9691230)
- [Google Search Status Dashboard history](https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history)
- [Google's guide to diagnosing Search traffic drops](https://developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops)
- [AdSense Management API v2](https://developers.google.com/adsense/management/reference/rest)
- [Google Analytics Data API quotas](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas)
- [Google Ads keyword ideas](https://developers.google.com/google-ads/api/docs/keyword-planning/generate-keyword-ideas)
- [Google Trends API alpha](https://developers.google.com/search/apis/trends)
- [YouTube captions API](https://developers.google.com/youtube/data/reference/rest/v3/captions/list)
- [Custom Search JSON API transition](https://developers.google.com/custom-search/v1/overview)
- [Ahrefs API introduction and eligibility](https://docs.ahrefs.com/en/api/docs/introduction)
- [Ahrefs public endpoints](https://docs.ahrefs.com/en/api/reference/public)
- [Ahrefs SERP Overview](https://docs.ahrefs.com/en/api/reference/serp-overview/get-serp-overview)
- [Ahrefs free test queries](https://docs.ahrefs.com/en/api/docs/free-test-queries)
