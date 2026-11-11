# Weekly growth workflow

Run `python3 growth_report.py` once a week. For analytics without HTTP audits, run `python3 growth_report.py --skip-crawl`.

Outputs:

- `reports/growth_latest.md`: readable report for both blogs.
- `reports/growth_latest.json`: source measurements, query/page rows, overlap candidates, referrals and audit findings.
- `ahrefs_exports/`: optional Ahrefs CSV inputs; missing exports are reported as pending.

The report uses two separate 28-day periods, requests final Search Console data and excludes the latest three days. Date boundaries use Asia/Karachi; Search Console's daily data retains its own reporting convention. Queries omitted for privacy can make query sums differ from site totals.

Review the five page priorities for each blog. Verify search intent and sources before making changes; the score is a heuristic based on impressions, position and lost impressions, not a forecast of traffic. Several pages appearing for one query is a review signal, not proof of harmful cannibalization.

For the article audit, prioritize 404/410 links and images, missing images and incorrect canonicals. A timeout, 403 or 429 is an unverified response; check it manually before replacing a link. Counts of incoming links cover published article bodies only and exclude navigation links and external backlinks. Crawling uses three workers and a 15-second per-request timeout.

GA4 referral tables show sessions attributed to dev.to and medium.com and the landing pages. Referrer suppression and app/browser behavior can hide attribution. Use campaign parameters on social links when useful, while leaving canonical URLs clean.

Export Ahrefs Backlinks, Referring domains, Organic keywords and Site Audit issues as CSV. Keep original headers and name each file with its site, report type and date. Imported row counts describe exports only. Public Ahrefs keys do not supply full backlink reports.

No scheduler, external publishing, automatic content removal or paid API usage is enabled by this workflow. Keep a weekly review cadence and evaluate small-data results over several periods.

## Local open-source writing and link checks

Before updating an article, fill `content_brief_template.md`, run `python3 content_review.py`, and review `reports/content_review_latest.md`. This uses Textstat and Vale locally, with advisory checks for readability, repetition, long sentences and overclaims. Use `python3 open_source_link_check.py pillar_free_ai_courses_2026.html` for an independent Lychee check. Failed links and writing suggestions are review tasks; neither command publishes changes.
