# SEO Agent — Standard Operating Procedure
_A repeatable, research-driven pipeline. Rule #0: **never assume — pull real data, then act.**_

Applies to any Blogger post on any of the connected blogs. Run the phases in order. Do not skip RESEARCH.

---

## Phase 1 — RESEARCH (no assumptions)
Gather facts before touching the post. For the target post/topic, collect:
1. **Current state** — `blogger_cli.py get <blog_id> <post_id> --field content` → title, word count, existing labels, internal links, schema.
2. **Ranking reality (GSC)** — `gsc_query.py query -p <property> --days 90 --dimensions query,page` → *which keywords this page already ranks for and at what position*. This defines the primary keyword when the page is indexed.
3. **Demand** — `trends_research.py "<seed>" --geo US` (geo = **US/UK/CA**, never PK) + Google Autocomplete → rising + established keywords.
4. **Index state** — `gsc_inspect.py <url> -s <site>` → indexed / discovered / unknown.
5. **Cannibalization** — list sibling posts targeting the same intent; check each one's impressions (`--dimensions page`).

**Output of Phase 1:** primary keyword, secondary keywords, FAQ questions (from the real queries the cluster ranks for), index state, and a keep/merge decision for duplicates.

For sources, run `python3 research_library.py collect <explicit-public-source-url> ...` and `python3 research_library.py search 'terms'`. This uses Trafilatura and a local SQLite source index. Record retrieval dates and confirm each factual claim yourself; successful extraction is not factual verification. Document/PDF/browser extraction remains optional; consult `SEO-WORKBENCH-PLAN.md` and `reports/research-platform-projects-2026-10-27.md`.

## Phase 2 — DECIDE (rule-based, not by vibes)
Use `python3 seo_workbench.py improve` for a review packet for existing articles: candidates, diffs, GSC evidence and editorial tasks. `improve --apply` applies validated technical repairs with backups and reruns measurements. Reviewed substantive revisions use `article_improver.py stage` then `apply --post`. Follow `ARTICLE-IMPROVEMENT-WORKFLOW.md`; no new post is required to improve an existing URL.

| Situation (from Phase 1 data) | Action |
|---|---|
| Page has impressions / ranks | **OPTIMIZE** — keep the content, fix title/meta/H1/links/schema. Do **not** rewrite from scratch (protects the ranking). |
| Page is thin / 0 impressions / not indexed | **REWRITE** to the content standard below. |
| True duplicate of a stronger page (0–low impressions) | **CONSOLIDATE** — draft it, output a redirect → the stronger page. |
| Page ranks on page 1 for its own keyword | **KEEP** — never merge a page-1 winner into another. |

## Phase 3 — WRITE / OPTIMIZE (content standard)
Prepare `content_brief_template.md` using the current page/query evidence and source checks. After drafting, run `python3 content_review.py <draft.md|article.html>` for local Textstat readability and Vale writing-rule suggestions. Review the actual flagged passages; scores are advisory and do not validate facts. Run `python3 open_source_link_check.py <draft.md|article.html>` for independent Lychee link validation. Read `reports/open-source-seo-research-2026-10-27.md` for tool scope and limitations.

Every published post must hit:
- **Title** — primary keyword front-loaded, ≤ 60 chars, includes the year if seasonal.
- **Length** — answer the search intent completely. Competitor length is context, not a publishing gate or ranking requirement. Measure article body only; never pass an invented word count to `serp_analysis.py`.
- **Structure** — one clear topic H1 (via title; note the theme H1 caveat), 6–8 `<h2>`, a **FAQ `<h2>`** with 5 Q&As that answer the *real ranking queries* verbatim.
- **Internal links** — ≥ 3 contextual, hub-and-spoke within the cluster.
- **External sources** — 1–3 real, authoritative, `target="_blank" rel="noopener"`.
- **Schema** — validate Article/BlogPosting JSON-LD and avoid duplicate theme markup. FAQs are optional; ordinary blogs should not expect FAQ rich results.
- **Images** — add `**Image query:**` to Markdown drafts. `build_content()` calls Pexels before upload; failure must stop upload. Verify image relevance, public image response, descriptive alt text, dimensions, and linked attribution. Use eager loading for the lead image and lazy loading for later images.
- **Labels** — 3–6 consistent tags.
- **HTML hygiene** — valid tags (no broken `<strong`), no `<h1>`/`<html>`/`<body>` in content.

### YMYL / accuracy rules (mandatory)
- **Never fabricate** stats, benchmarks, prices, APRs, product names/terms, dates, or quotes.
- Finance / health / legal topics → advice-framed ("how to choose"), attribute any specifics as "reported," tell readers to confirm at the source.
- Review factual accuracy, useful examples, sourcing and originality. If an external quality tool is unavailable, report that; do not invent a score or an AI-detection result.

## Phase 4 — PUSH (send everything the API accepts)
`blogger_cli.py update <blog_id> <post_id> --title "…" --content-file page.html --labels "a,b,c"`
- Sends: title, content (incl. schema + internal links), labels. (Per `BLOGGER-API-REFERENCE.md`.)
- Does **not** send: search description (API can't) → output it for manual paste.

## Phase 5 — VERIFY + DISTRIBUTE (evidence, not assumption)
Run `python3 seo_workbench.py run --refresh` for the combined measurement workflow and persistent issue history. For existing evidence only, use `python3 seo_workbench.py run`. Review `reports/action_queue_latest.md`. See `SEO-WORKBENCH.md` for failure handling, source timestamps and issue transitions. This runner performs analysis only and does not authorize publishing or deletion.

1. Re-fetch live: `parse_html.py` → confirm **1 topical H1 target**, word count, internal links, **schema present**, no broken tags.
2. Run editorial review; record unavailable checks. The technical gate does not certify factual quality or ranking potential.
3. Submit to **Bing** (`bing_submit.py` / SubmitUrl) — automated indexing.
4. Run `gsc_opportunities.py` and prioritize queries/pages in positions 8–20.
   Run `python3 growth_report.py` for both sites: separate 28-day comparisons, query opportunities at positions 8–50, five page priorities, overlapping queries, DEV/Medium landing-page referrals, article links/images/canonicals, and CSV imports from `ahrefs_exports/`. Use `--skip-crawl` for a faster analytics-only report. API or crawl errors must appear as unavailable, never zero. Review low-count results before acting. This script performs no publishing or scheduling.
5. Run `seo_pipeline_check.py` against the live URL; it must pass.
6. Create a **DEV Community adapted draft** with the original Blogger URL as `canonical_url`; review and publish manually after confirming it adds distinct value.
7. Use **Medium manual import/editor** when appropriate; verify source attribution/canonical before publishing.
8. **Output the manual to-do**: meta description text, redirect From→To list, request-indexing URLs, DEV/Medium review or publish actions, any theme fix. Never claim these are done — they're the human's step.

---

## Guardrails (the "don't assume" contract)
- Pull GSC + current content **before** every decision.
- Never redirect a URL without checking its impressions first.
- Never re-date a post unless content genuinely changed.
- Never mark a manual step (meta, redirect, indexing) as "done."
- Target geo is **US / UK / CA / EU** — content is globally framed, never Pakistan-local.
- After every push, verify live. Report evidence (scores, counts), not claims.
