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
```

The default run imports saved reports and labels them cached with their original file timestamps. Refresh runs the growth audit, local Textstat/Vale writing review, and Lychee pillar link check. A refresh can take several minutes. `run`, `history` and `queue` do not modify live posts. `improve` prepares candidates; the explicit `improve --apply` command patches existing live article content with backups and checks, then refreshes measurements. Neither workflow creates new posts, sends outreach, enables schedules or uses paid APIs. See `ARTICLE-IMPROVEMENT-WORKFLOW.md` for staged editorial revisions and restore instructions.

## Persistence

- `research/workbench.sqlite`: run and stage statuses, source artifact timestamps/hashes, issue lifecycle, observations and editorial change notes.
- `reports/workbench/<run-id>/`: unique report snapshots, action queue and refresh logs.
- `reports/action_queue_latest.md` and `.json`: current unified queue.
- `research/sources.sqlite`: separate source evidence library, managed by `research_library.py`.

Run IDs contain a UTC timestamp and random suffix. Both same-day and repeated runs remain in history. Each captured report is hashed; cached reports are not described as new measurements. API keys are never copied into the workbench database or snapshots.

## Issue lifecycle

Fresh growth runs also inspect stored Google index records for a maximum of three selected URLs per blog: the homepage, a performance priority and the newest crawled article when available. Non-indexed URLs and reported redirect failures are queued above content opportunities, even when the public HTML audit is clean. This sample is not a whole-site index count or a live Google URL test. An unavailable inspection preserves earlier findings. Use `growth_report.py --skip-inspection` to omit these API reads explicitly.

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
