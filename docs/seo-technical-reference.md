# SEO technical reference

This guide summarizes current, source-backed operating rules for a small site SEO workflow. Recheck provider documentation before enabling new APIs; access, quotas and product availability can change.

## Search fundamentals

- Optimize for the reader's task, with accurate and original information. Google does not prescribe a preferred article word count. Generative content must add value; scaled pages made primarily to manipulate rankings can violate spam policies.
- Treat crawling, indexing and ranking as separate stages. A successful fetch, sitemap submission, structured-data validation or indexing request is not a promise of inclusion or ranking.
- For Blogger, test smartphone and desktop requests separately. The platform may redirect smartphone requests to `?m=1`; verify that the mobile variant returns successfully, has equivalent content and metadata, and canonicalizes to the clean URL before calling the stored Search Console redirect status a confirmed site fault. Google's mobile-first guidance covers separate mobile URLs and requires the desktop URL to be canonical; the Blogger support guide describes the platform's `?m=1` behavior.
- Use one stable canonical URL per page, crawlable internal links, accurate titles and useful descriptions. Google may choose a different search snippet than the supplied description.
- Audit mobile rendering, server responses, robots/noindex directives, redirects, canonical tags, internal discovery and image alternatives. Distinguish unavailable checks (such as 403/429/timeouts) from confirmed 404/410 failures.
- Core Web Vitals are user-experience measures, not a ranking guarantee. CrUX field data can be absent on low-traffic URLs; do not turn missing samples into a failed score.
- Compare complete, adjacent Search Console windows and break drops down by page, query, country, device and search type. Queries can be anonymized; page totals may exceed visible query totals.

Primary guidance: [Search Essentials](https://developers.google.com/search/docs/essentials), [SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide), [helpful content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [spam policies](https://developers.google.com/search/docs/essentials/spam-policies), [traffic-drop diagnosis](https://developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops), and [Core Web Vitals](https://web.dev/articles/vitals).

## Google APIs and limits

| API or product | Useful data | Important limit |
|---|---|---|
| Search Console API | Search Analytics, sitemap list/submit, site properties and stored URL Inspection | Inspection is not the UI Live Test and cannot request indexing. Query rows are bounded and may omit anonymized queries. |
| Blogger API v3 | Read and update posts, pages, labels and blog resources | It does not expose every Blogger UI control, including per-post search descriptions. Back up, verify status and URL, read back changes, then check the public page. |
| Google Analytics Data API | Sessions, engagement and landing-page reports | Measures attributed visits, not Search impressions or verified human traffic. |
| AdSense Management API v2 | Account/site reports and estimated earnings | Preserve account timezone and report dimensions; estimated earnings are not finalized payments. |
| Google Indexing API | Eligible `JobPosting` and livestream `VideoObject` notifications | Not a general-purpose indexing API for ordinary articles. |
| PageSpeed Insights API | Lighthouse lab results and sometimes CrUX field data | Field data may be unavailable. Keep lab and field measurements distinct. |
| CrUX API | Aggregated real-user experience metrics | Requires an API key and sufficient privacy/sample volume. |
| Google Trends API | Programmatic search-interest trends | Access is alpha/limited. `pytrends` is unofficial and should be labeled experimental. |
| Google Ads API Keyword Planning | Keyword ideas and historical average search estimates | Requires Ads OAuth, a developer token and suitable account access. Estimates are not Search Console data. |
| YouTube Data API | Public video, channel and playlist metadata | Caption listing/downloading is permission-bound; it is not a public bulk transcript service. Keep links and concise notes rather than copying full creator transcripts. |
| Custom Search JSON API | Programmable search results | Closed to new customers; Google has announced a transition for existing users. |
| Vertex AI Search | Search across a configured, bounded set of domains | Not an unrestricted Google web SERP API. |

References: [Search Console API](https://developers.google.com/webmaster-tools/v1/api_reference_index), [URL Inspection](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect), [Indexing API eligibility](https://developers.google.com/search/apis/indexing-api/v3/using-api), [Blogger API](https://developers.google.com/blogger/docs/3.0/reference), [mobile-first indexing](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing), [Blogger redirect-error guide](https://support.google.com/blogger/community-guide/325142055/redirect-error-search-console-report), [Analytics quotas](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas), [AdSense API](https://developers.google.com/adsense/management/reference/rest), [Trends API](https://developers.google.com/search/apis/trends), [YouTube captions](https://developers.google.com/youtube/data/reference/rest/v3/captions/list), and [Custom Search transition](https://developers.google.com/custom-search/v1/overview).

## SERP and competitor comparisons

An article-by-article top-ten comparison requires actual, dated search results for the intended query, country, language and device. Record the provider, collection time, organic position and result URL. A partial result set stays partial; never fill missing competitors with guesses. Compare search intent, page type, topical coverage, evidence, clarity and useful original material. Word count is descriptive, not a target.

Ahrefs endpoints have different plan and credit requirements. A key restricted to public endpoints does not authorize paid Site Explorer, Keywords Explorer or SERP endpoints. Check account eligibility and unit costs before querying. A manually reviewed results import is a valid alternative if it includes provenance. The public [Ahrefs API docs](https://docs.ahrefs.com/en/api/docs/introduction) and [SERP Overview reference](https://docs.ahrefs.com/en/api/reference/serp-overview/get-serp-overview) describe current access requirements.

## Official learning resources

- [Search fundamentals for beginners](https://www.youtube.com/playlist?list=PLbrFcZbKqjoI)
- [Technical SEO fundamentals](https://www.youtube.com/playlist?list=PLeMjPeaUGn9U)
- [How Google Search crawls pages](https://www.youtube.com/watch?v=JuK7NnfyEuc)
- [How Google Search indexes pages](https://www.youtube.com/watch?v=pe-NSvBTg2o)
- [Anatomy of a Search Result](https://www.youtube.com/watch?v=IosyvXjQvlw)

The [YouTube transcript interface](https://support.google.com/youtube/answer/15930243) can display creator-provided captions when available. API caption access requires permissions. Summarize lessons in your own words and link to the source video.

## Open-source tools reviewed

- [every-app/open-seo](https://github.com/every-app/open-seo): useful provider/MCP architecture; its live data depends on configured DataForSEO access.
- [Google Lighthouse](https://github.com/GoogleChrome/lighthouse): open-source lab auditing for performance and accessibility.
- [Lychee](https://github.com/lycheeverse/lychee): link checking.
- [Vale](https://github.com/errata-ai/vale): editorial style checks.
- [Trafilatura](https://github.com/adbar/trafilatura): article extraction for research workflows.
- [Seonaut](https://github.com/StJudeWasHere/seonaut): technical crawler and issue-severity design reference.

Before adopting a project, check its license, maintenance, dependencies, crawl politeness and evidence for each reported issue. Avoid duplicating capabilities the existing pipeline already provides.
