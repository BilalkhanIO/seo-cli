# Existing-article pipeline status — 31 October 2026

Implemented: refresh measurements → find/prioritize issues → prepare per-article briefs, candidate HTML and diffs → stage researched editorial revisions → apply existing-post updates with backups and conflict checks → verify saved content and publication details → audit again and track issue history.

The earlier authenticated repair batch saved and verified updates to 62 distinct articles. A subsequent researched Meta course revision corrected its title and misleading free-certificate/course claims. There are 63 change records and 63 backup files, including that second revision to an already repaired article.

The fresh public audit on 31 October covered all 94 published articles using Blogger's public feeds. Comparing the earlier saved audit with this fresh observation:

| Finding | Before | Current |
|---|---:|---:|
| Confirmed broken link/image occurrences | 71 | 8 |
| Articles without incoming article-body links | 13 | 3 |
| Articles without images | 2 | 0 |

These are technical observations, not evidence of ranking or traffic growth. Network responses can change. Blocked responses and timeouts remain unverified.

Remaining observed issues include eight broken-link occurrences, two images without alt text and two pages with duplicate/conflicting canonical tags. The latter pages contain their current canonical plus an obsolete URL:

- `/2026/03/free-ai-tools-for-assignment-writing-in.html`
- `/2026/02/blog-post.html`

Review article/theme canonical markup before editing. Remaining broken links include FTC references, an edX program, Allrecipes, and one internal Ubuntu reference. Unavailable replacement responses do not establish a safe editorial replacement.

Google's refresh token is currently expired or revoked. Fresh GSC/GA4 measurements and further Blogger edits are blocked. The audit now continues through public inventory while explicitly marking Google metrics unavailable. Historical opportunities remain historical; they are not refreshed results. No additional live changes were made during this disconnected verification run.

To reconnect, run `python3 gsc_auth.py` locally and complete Google consent. Then run:

```sh
python3 seo_workbench.py improve
```

Review its briefs and diffs. To prepare and apply technical candidates and audit again:

```sh
python3 seo_workbench.py improve --apply
```

Editorial improvements use the staged revision workflow described in `ARTICLE-IMPROVEMENT-WORKFLOW.md`. Provider facts and original examples require research and review. Search Description and Search Console Request indexing remain manual operations.

Validation: 30 regression tests passed, including write-conflict rejection, draft protection, verified content-only updates, public-feed pagination, incomplete-feed rejection, historical issue handling and research/content/image helpers. The fresh workbench run is marked partial because GSC/GA4 were unavailable; public crawling, writing review and link checking completed.

Latest reports: `reports/growth_latest.md`, `reports/action_queue_latest.md`. Immutable run: `reports/workbench/20261031T110758Z-b3495eb4/`. Original repair packet and backups: `reports/improvements/20261027T141051Z/`.
