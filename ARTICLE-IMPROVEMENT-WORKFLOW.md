# Existing-article improvement workflow

## Find and suggest

```sh
python3 seo_workbench.py run --refresh
python3 seo_workbench.py improve
```

The first command collects current Google metrics and technical findings. The second re-fetches the Blogger LIVE inventory, rechecks broken targets and prepares a review packet for each existing article. It does not create a new Blogger post.

`improve` now refreshes measurements before preparing its plan, so it can also be run on its own. If Google authorization expires, public-feed inventory and public technical checks continue, while GSC/GA4 are explicitly unavailable. Article planning and live edits require restored Blogger authorization. Run `python3 gsc_auth.py` locally and complete Google consent, then rerun the workflow. A partial audit does not establish that unavailable measurements improved.

Review `reports/improvement_plan_latest.json` and the matching `reports/improvements/<timestamp>/README.md`. Each article has an HTML candidate, before/after diff and Markdown brief containing its actual GSC queries, source date, editorial tasks and a suggested Search Description for manual review.

Candidate repairs include verified replacement links; unlinking confirmed dead internal URLs while retaining visible text when no relevant replacement is known; missing/broken image replacement; exact duplicate title H1 removal; visible draft-metadata removal; and a small related-reading section using live articles on the same blog with topic overlap. An existing generated related-reading section is not duplicated on subsequent plans.

External links are replaced only through the explicit editorial map and only when the replacement returns 200. Blocked/time-out requests stay unresolved. Exact destination HTTP status does not prove a claim; factual review remains separate. Related-reading links are navigation improvements, not substitutes for editorially chosen links within explanatory paragraphs.

## Apply the technical plan and measure again

```sh
python3 seo_workbench.py improve --apply
```

This prepares the plan, applies valid candidates to existing LIVE posts, then reruns the workbench audit. It backs up each original post and checks content hashes to avoid overwriting another editor's work. Article URL, publication state and original publication date must remain unchanged. A per-post result records verified updates and blocked edits. Blocks return a failing exit status for follow-up; they are not counted as completed work.

To apply only one reviewed candidate:

```sh
python3 article_improver.py apply --post POST_ID
```

## Improve factual content, examples and titles

Use the article brief to research current primary sources and prepare a revised HTML file. Check enrollment/pricing claims, dates, sources and original examples. Run:

```sh
python3 content_review.py drafts/reviewed-article.html
python3 open_source_link_check.py drafts/reviewed-article.html
python3 article_improver.py stage --post POST_ID --content-file drafts/reviewed-article.html --title 'Reviewed descriptive title'
python3 article_improver.py apply --post POST_ID
python3 seo_workbench.py run --refresh
```

The title flag is optional and only used for an explicitly staged editorial revision. The original URL remains unchanged. Stage accepts the current plan's original baseline or its already-applied technical baseline; any unrelated concurrent content edit blocks staging. It rewrites the diff and content fingerprint, so the reviewed revision is concrete before applying.

The tools suggest questions and tasks from measured queries. They do not fabricate search volume, keyword difficulty, facts or automatic article rewrites. A Meta course pilot was reviewed using current provider information to remove contradictory free-certificate claims, a misleading completion-time claim and unsupported pricing examples.

## Verify and recover

After applying, the workflow refetches the Blogger post and compares saved content, title, status, URL and publication date. The fresh growth audit checks public links/images/canonicals and feeds resolved/new findings into SQLite history. Pexels metadata is not a visual quality assessment; review the actual selected photo.

Backup files are saved under the improvement packet's `backups/` directory. To preview a restore, use:

```sh
python3 article_improver.py restore --backup PATH_TO_BACKUP.json --expected-current-hash SHA256
```

Add `--apply` after reviewing the preview. Restore refuses a different current baseline or a changed publication state. It restores content/title only and verifies the result. No post deletion or automatic reversion to draft is used by this workflow.

## Manual SEO items

Blogger Search Description and Google URL Inspection Request indexing remain manual tasks. The generated description is a suggestion, not a claim that metadata was saved. After material improvements, test the clean canonical URL in Search Console, request indexing if appropriate, and evaluate results across subsequent reporting periods.
