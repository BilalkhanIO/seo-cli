# SEO workbench runner

## Commands

```sh
python3 seo_workbench.py run --dry-run
python3 seo_workbench.py run
python3 seo_workbench.py run --refresh
python3 seo_workbench.py history
python3 seo_workbench.py queue
python3 seo_workbench.py improve
python3 seo_workbench.py improve --apply
python3 seo_workbench.py record-change 'https://example.com/post' 'Updated enrollment instructions and verified provider links'
python3 gsc_opportunities.py --blog both --days 90
python3 project_context.py show --site both
python3 keyword_research.py 'meta social media marketing course' --blog st --geo us
```

The default run imports saved reports and labels them cached with their original file timestamps. Refresh runs the growth audit, published-inventory competitor coverage, local Textstat/Vale writing review, and Lychee checks across published article bodies. A refresh can take several minutes. `run`, `history` and `queue` do not modify live posts. `improve` prepares candidates; the explicit `improve --apply` command patches existing live article content with backups and checks, then refreshes measurements. Neither workflow creates new posts, sends outreach, enables schedules or uses paid APIs. See `ARTICLE-IMPROVEMENT-WORKFLOW.md` for staged editorial revisions and restore instructions.

`gsc_opportunities.py` reports three Search Console views from adjacent complete windows: query-only rows, query-to-page clusters, and page-only totals. Use `--blog st|ll|both` and `--days 28|90|180`. Query rows can omit anonymized searches, so visible query counts and page mappings are partial; page-only impressions can exceed impressions attributed to visible queries. Multiple pages for one visible query are review candidates, not automatic cannibalization findings, and no visible overlap does not rule out hidden overlaps. These are observed GSC metrics, not search-volume estimates. This workflow uses the connected Google account and no DataForSEO credits.

`keyword_research.py` combines Google autocomplete and optional Trends observations with the same recent, complete 90-day GSC query/page evidence. GSC pages and weighted positions are retained per phrase; unavailable sources are labeled/skipped rather than converted to zero demand.

`project_context.py` stores owner-provided goals and evidence-backed priority pages in `research/project_context.json`. Keyword reports include the selected blog’s context and retain only GSC queries related to the requested seed; audience remains unrecorded until explicitly supplied. Key pages are review priorities, not a forecast of traffic or revenue.

## Persistence

- `research/workbench.sqlite`: run and stage statuses, source artifact timestamps/hashes, issue lifecycle, observations and editorial change notes.
- `reports/workbench/<run-id>/`: unique report snapshots, action queue and refresh logs.
- `reports/action_queue_latest.md` and `.json`: current unified queue.
- `research/sources.sqlite`: separate source evidence library, managed by `research_library.py`.

Run IDs contain a UTC timestamp and random suffix. Both same-day and repeated runs remain in history. Each captured report is hashed; cached reports are not described as new measurements. API keys are never copied into the workbench database or snapshots.

## Issue lifecycle

Fresh growth runs inspect stored Google index records for up to three selected URLs per blog: the homepage, current-window performance priorities, then the highest-impression URLs from the prior window. This keeps inspection useful when current impressions suddenly fall to zero. Non-indexed URLs and reported redirect failures are queued above content opportunities, even when the public HTML audit is clean. This sample is not a whole-site index count or a live Google URL test. An unavailable inspection preserves earlier findings. Use `growth_report.py --skip-inspection` to omit these API reads explicitly.

The published-page audit also checks rendered HTML for a page title and meta description. Missing descriptions are review cues, not a ranking diagnosis. Search descriptions are managed in Blogger's owner UI; Blogger API v3 does not expose a per-post search-description field. The pipeline does not fill them with formulaic text.

- **New:** first observed finding.
- **Persistent:** the same finding remains present.
- **Resolved:** a successful measurement covers the same source/page and no longer reports the finding.
- **Reopened:** a previously resolved finding appears again.

Missing reports, failed stages, skipped crawls and unaudited pages do not resolve prior issues. Findings from deleted or no-longer-audited pages remain open until reviewed with evidence. Source timestamps help identify stale evidence. The priority score is a review heuristic, not predicted traffic or a ranking score.

When the crawler successfully reads the article body, a blocked external target no longer prevents unrelated confirmed repairs on that article from clearing. An earlier finding about the same blocked target stays open. Reports without explicit successful page/body evidence retain the older conservative coverage rules. Blocked image responses are verification tasks rather than confirmed image failures.

Broken internal links and canonical/noindex issues rank highest. Missing images, external broken links and measurement availability follow. Content opportunities and prose suggestions are lower. HTTP 403/429/timeouts remain verification tasks, not confirmed broken links. Claims flagged in cautionary text need human interpretation.

## Failure handling and concurrency

The runner locks its local job file to prevent overlapping jobs from racing on shared latest reports. Each refresh stage has a timeout and saves its output log. Old latest files are not treated as fresh after a failed command. Other stages continue, and the run is marked partial when any stage is unavailable or a report declares collection errors.

SQLite and reports are local workstation storage. A hosted dashboard needs authentication, access controls and secret handling before remote deployment. Refresh is currently a manual command; no recurring job was enabled.

## Tests

```sh
python3 -m unittest test_article_improver test_seo_workbench test_research_library test_content_review test_growth_report test_image_pipeline
```

## Environment and local preflight

The root `requirements.txt` includes the research, content, competitor and dashboard dependencies. For a clean environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python pipeline_preflight.py
.venv/bin/python dashboard/app.py
```

Existing installations can use the project-local packages under `.tools/python`, `.tools/research-python` and `.tools/competitor-deps`. The pinned Vale and Lychee binaries are installed separately by `install_seo_tools.py`. Preflight checks presence only; it does not establish external API access. The dashboard uses its current Python interpreter by default; `SEO_PYTHON` and `SEO_CLI` can override optional runtime/CLI paths.

## Per-article competitor comparison

```sh
python3 article_competitor_audit.py --refresh-inventory
python3 article_competitor_audit.py --results reports/competitor_results.json --fetch
python3 open_source_link_check.py --published-inventory
python3 open_source_link_check.py --published-inventory --reuse-unchanged
python3 seo_workbench.py run
```

The comparator accepts existing inventories and refreshes only LIVE Blogger records when `--refresh-inventory` is specified. Drafts and duplicate canonical/mobile URLs are excluded. An unavailable refresh retains the dated inventory evidence and marks the run partial. Inputs with no LIVE articles cannot overwrite the prior valid report.

Copy `reports/competitor_results_template.json` to `reports/competitor_results.json` and supply reviewed queries/results. Packets record source, engine, country, language, device, collection time, result type and query review. GSC query mappings are preferred to title fallback when available. Title fallback requires editorial review.

Optional Google-result discovery uses SerpApi only when explicitly requested:

```sh
python3 article_competitor_audit.py --discover --max-searches 10 --country us --language en --device desktop --fetch
```

Save the provider key as `SERPAPI_API_KEY` in the environment or the git-ignored `serpapi_key.txt`. No key is included in reports. Discovery has a mandatory explicit request limit, caches successful SERP/page measurements for seven days and stops on provider errors. It is never enabled by the standard runner. Provider requests can consume account credits; choose the limit before running. Country/language/device are evidence context and must match the intended audience. No API subscription or schedule is enabled automatically.

Comparison states distinguish `pending_search_results`, `comparison_unavailable`, `comparison_partial`, and `comparison_complete`. Complete requires ten distinct organic result URLs at positions 1–10, complete search provenance, a reviewed query and successful extraction of every result. The site's own result can occupy one position and uses the cached Blogger body. Competitor samples and candidate-page discoveries stay partial. Fewer returned results remain explicitly partial rather than being invented.

Reports include article-body word distributions, H1–H3 headings, tables/images and recurring heading-phrase review candidates. Topic candidates are lexical heuristics requiring factual and intent review. Word count is descriptive and does not prescribe a ranking target. The older `serp_analysis.py` now uses the same guarded extraction and the same interpretation.

`open_source_link_check.py --reuse-unchanged` reconciles without network requests when the LIVE article set is unchanged and edited articles only remove references. It retains original HTTP measurement dates and refuses if the inventory changes or an edited article adds a new URL. It does not refresh link status.

The workbench imports competitor coverage into SQLite and its action queue. Missing comparisons keep a run partial, below indexing blockers in priority. Link checks create content-addressed article snapshots and map errors back to published URLs. Failed link-check output preserves the previous valid report. The dashboard's workflow card exposes source dates, coverage, the current site's goals and queued actions. Search figures come from saved dated growth reports; unavailable metrics stay unavailable. AdSense figures are filtered to the selected blog and remain estimated.

See [`docs/seo-technical-reference.md`](docs/seo-technical-reference.md) for the Google API map, source links, official Search Central video courses, and SERP provider eligibility. A saved Google OAuth does not imply Google Ads, Trends alpha, PSI/CrUX API-key, YouTube caption-owner, or paid Ahrefs SERP access.

## Supported blog indexing flow

`python3 index_flow.py` previews tasks. `python3 index_flow.py --apply` submits sitemaps to GSC and eligible page URLs to Bing. Ordinary Blogger posts are never sent to Google's restricted Indexing API. All three former submission paths (`index_flow.py`, `seo_optimize.py`, `st_optimize.py`) use the supported discovery/inspection workflow. Submitting a sitemap is not a confirmation of indexing; browser Live Test and recrawl requests remain separate steps.
