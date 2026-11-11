# Research and SEO workbench: proposed architecture

Build around our own sites' measured performance and a source-backed editorial workflow. The existing CLI modules are working components; the dashboard and orchestration below are proposed work, not deployed features.

## Core flow

1. **Measure:** GSC and GA4 snapshots, site inventory, Ahrefs CSV imports.
2. **Prioritize:** page opportunities, lost impressions, query overlap and broken-link findings.
3. **Research:** explicit source URLs, clean extraction, retrieval timestamps, text fingerprints and searchable notes.
4. **Brief:** reader intent, current page owner, source-supported claims, original examples and outline.
5. **Write:** draft creation with source references, relevant images and explicit unresolved questions.
6. **Review:** factual/source review, Textstat/Vale suggestions, Lychee links, HTML/canonical/schema checks.
7. **Publish:** Blogger draft by default, explicit review, backups, state preservation and duplicate prevention.
8. **Distribute:** appropriate DEV adaptation and Medium copy, canonical/source attribution and public URL tracking.
9. **Learn:** compare separate reporting periods and relate observed performance to an editorial change log.

## Components already working

- `growth_report.py`: Google data, priorities, link/image audits and CSV import summaries.
- `research_library.py`: Trafilatura + SQLite source collection/search.
- `content_brief_template.md`: evidence-backed writing specification.
- `content_review.py`: Textstat + Vale local prose review.
- `open_source_link_check.py`: Lychee independent link checks.
- `seo_pipeline_check.py`: article-scope technical checks.
- Pexels integration and Blogger/DEV draft utilities.

## Next build: one job runner and persistent history

Use SQLite for sites, pages, query observations, sources, claims, briefs, draft revisions, audit runs and distribution records. Store credentials separately from report/application data. Each run should have a status, timestamp, input version and output path; network failures should remain explicit rather than becoming zero metrics.

The first runner is now implemented in `seo_workbench.py`. It consumes growth, writing and link reports through adapters, saves dated snapshots and hashes, tracks new/persistent/resolved/reopened issues, and exports one prioritized review queue. `run` imports existing reports without network access; `run --refresh` executes the measurement tools; `run --dry-run` prints the plan without writing. It has no publishing stage. Never turn an already published post back into a draft merely to update distribution content.

## Dashboard after the runner is reliable

Pages: overview, opportunities, sources, briefs, editor, technical audit, distribution and history. Every metric should identify its source, date range and limitations. Surface API/network costs and unavailable data. Add authentication before remote access; no public deployment is implied by this plan.

## Optional capabilities

- Crawl4AI for pages that need browser rendering.
- MarkItDown for office file import; Docling for complex document layouts.
- KeyBERT for topic suggestions, followed by GSC validation.
- GPT Researcher workflow patterns if a model/search budget is available.
- SEOnaut or Unlighthouse for a fuller technical/performance dashboard.

## Success criteria

Before adding more tools, the system should reliably capture evidence, prevent duplicate posts, report broken links, preserve publication state, and show the result of editorial changes. Evaluate organic impressions/clicks and engaged referral sessions over several reporting windows. Do not promise rankings, invent keyword demand or claim a local crawler reproduces Ahrefs' backlink index.
