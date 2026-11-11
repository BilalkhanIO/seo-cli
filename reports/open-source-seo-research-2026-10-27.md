# Open-source SEO and writing tools — checked October 27, 2026

Repository metadata and maintainer documentation were checked directly on GitHub. Maintenance dates below are repository push dates, not a guarantee of release quality. Open-source software does not include a commercial web-wide backlink index.

| Project | License | Latest push checked | Useful here | Cost/dependency limits | Decision |
|---|---|---|---|---|---|
| [SEOnaut](https://github.com/StJudeWasHere/seonaut) | MIT | 2026-10-08 | Technical audit dashboard, crawl organization and issue prioritization | Go and MySQL; Docker recommended | Candidate for a later dashboard deployment; not installed |
| [OpenSEO](https://github.com/every-app/open-seo) | MIT | 2026-10-26 | Workspace layout, keyword/page reports and report workflows | Research/backlink data requires your own paid DataForSEO key | Architecture reference; not installed |
| [SerpBear](https://github.com/towfiqi/serpbear) | MIT | 2026-05-14 | Rank history, API reporting, country/device tracking | Requires SERP provider/proxy; README flags some older free providers as no longer working | Reference for tracking; keep GSC for free first-party measurements |
| [Lychee](https://github.com/lycheeverse/lychee) | MIT/Apache-2.0 | 2026-10-26 | Independent broken-link checks for draft HTML/Markdown and public pages | No SEO API key; remote sites can block checks | Installed v0.24.2 with official asset SHA-256 verification |
| [Vale](https://github.com/vale-cli/vale) | MIT | 2026-10-24 | Local writing rules, wordiness and unsupported claims | Rules need editorial judgment; not a factual or originality checker | Installed v3.25.1 with official asset SHA-256 verification |
| [Textstat](https://github.com/textstat/textstat) | MIT | 2026-10-26 | Reading ease and grade estimates | Estimates vary with sentence structure and technical vocabulary | Installed v0.7.13 locally; integrated into content_review.py |
| [advertools](https://github.com/eliasdabbas/advertools) | MIT | 2026-06-30 | Sitemap, robots, crawl and text-analysis ideas | Larger Python/Scrapy dependency stack; no proprietary backlink database | Candidate if our crawl workload expands; not installed |
| [Unlighthouse](https://github.com/harlan-zw/unlighthouse) | MIT | 2026-10-27 | Site-wide Lighthouse/performance audits | Browser runtime and compute needed; lab scores differ from real-user data | Candidate for performance batch audits; not installed |

## What we can use immediately

1. Run `python3 content_review.py` for local draft and pillar writing review. Reports are `reports/content_review_latest.md` and `.json`.
2. Run `python3 open_source_link_check.py pillar_free_ai_courses_2026.html` for independent Lychee link checks. Reports are `reports/lychee_latest.json` and `.log`.
3. Fill in `content_brief_template.md` before drafting; derive evidence from the existing growth report and current primary sources.
4. Keep `growth_report.py` for GSC, GA4, page priorities and the article link graph. These provide actual site measurements instead of guessed keyword difficulty.

Textstat and Vale process article text locally. Tools were added to the project; no new accounts, paid data providers, public servers, schedules or backlink posting were enabled. No upstream application source was copied into our own code. Binary license files and provenance are retained where provided in `.tools/`.

## Verified first run

- Installed binaries report Lychee 0.24.2 and Vale 3.25.1; Textstat reports 0.7.13.
- Nine regression tests pass, including extraction that excludes tables, scripts and draft metadata.
- The writing report processed four drafts and the pillar locally. Approximate grade estimates ranged from 8.4 to 10.4; these are suggestions, not grades assigned to authors or ranking signals.
- Vale flagged two phrases in a warning about investment scams; editorial review should keep the warning rather than blindly deleting the phrases.
- Lychee checked the pillar and reported two HTTP 404 course URLs: `/public/courses/ai-for-educators` and `/public/courses/ai-for-college-students` on academy.openai.com. The script executed correctly and exited 2 to signal broken links. Fix those destinations after confirming current provider URLs; the tool run did not change the article.

## Writing limitations

These tools can identify sentences to simplify, repeated wording, and rules we define. They do not verify whether a course is free, an investment claim is accurate, a citation is real, or an article adds useful original experience. Complete those checks during research and editorial review. Do not use automated readability as a ranking guarantee or AI-detection score.

## Reinstallation

`python3 install_seo_tools.py` downloads the pinned official Lychee/Vale releases and verifies the expected archive hashes. `python3 -m pip install --target .tools/python -r requirements-content.txt` installs Textstat in the workspace. The main Textstat version is pinned; its dependencies should be reviewed before future upgrades.
