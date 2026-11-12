# On-page SEO checklist — do these on every page

Source: the SEO masterclass slide 13 ("On-page SEO — do these on every page", 80+ items / 11 categories),
reconciled with the repo's `validate.ts` gate and playbook §4 stage 5. **`seo_optimize.py` enforces the
content-level items automatically and self-checks before publishing.** Technical/head items marked *(theme)*
are handled globally by the Blogger theme, not per post; *(UI)* items are Blogger-editor-only (no API).

## 1. What Google indexes first
- [ ] Title tag 40–60 chars, primary keyword front-loaded, one CTR device (year/number/benefit)
- [ ] Meta / Search Description ~150 chars, keyword + benefit *(UI)*
- [ ] Canonical URL *(theme)* · Open Graph + Twitter card *(theme)* · viewport/lang/favicon *(theme)*

## 2. URL — clean, readable, keyword-forward
- [ ] Short, lowercase, hyphenated, primary keyword, no stop words, logical hierarchy *(set before publish; keep live URLs)*

## 3. Headings — structure for skimmers & bots
- [ ] Exactly one H1 (Blogger post title) · body starts at H2 · keywords in H2/H3 · no skipped levels

## 4. Answer the query, fast
- [ ] Primary keyword in the first 100 words · direct answer up top · length ≈ SERP median ±20%

## 5. Every blog post (FAQ)
- [ ] 4–8 real questions (People-Also-Ask style) with direct answers · FAQPage schema

## 6. Every image is a ranking signal
- [ ] Descriptive alt text · descriptive filename · compressed <200 KB · WebP/optimized · lazy-load · responsive
      (Pexels via `pexels_helper.py`: CDN auto-compresses, real alt text, lazy-load)

## 7. Internal links — pass authority across the site
- [ ] 3–6 internal links per 1,000 words · link to money/pillar pages · descriptive anchors · contextual · no orphans

## 8. External links — cite authority, don't steal it
- [ ] 2–3 links to authoritative sources (gov/official/issuer) · rel="nofollow noopener" · open in new tab

## 9. JSON-LD schema
- [ ] BlogPosting/Article · FAQPage (if FAQ) · Organization/author · valid JSON

## 10. E-E-A-T (Experience-Expertise-Authority-Trust)
- [ ] Author/editorial attribution · "Last updated" date · cited sources · editorial-standards note
- [ ] **YMYL (finance): never fabricate offers, APRs, stats, or first-hand experience** — verifiable facts only

## 11. AI-search (SxEO) & mobile
- [ ] Semantic HTML · **Key-Takeaways box** · **comparison table/matrix** · definitions · stats where real
- [ ] Mobile-first: readable font, tap targets, no horizontal scroll *(theme)*

---

### Technical SEO (site-level, 3 things — Blogger handles most)
1. **sitemap.xml** — Blogger auto-generates; submitted to GSC + Bing via `index_flow.py`
2. **robots.txt** — Blogger default is fine (only /search noindexed)
3. **Lighthouse** — Blogger theme dependent; keep images light, avoid heavy widgets

### Off-page (bucket priority: 1–2 legit, skip 3)
Broken-link swap · guest posts · HARO/journalist queries (free) · quality paid (expert only).
**Never PBNs/link farms/Fiverr packages** — they tank rankings. Best link: content good enough to earn them.

### The reusable flow (like the video's `/blog` skill)
`seo_optimize.py` = per-page config → E-E-A-T + Key-Takeaways + Pexels image + table + FAQ + schema +
internal/external links → **gate self-check** → Blogger patch → re-crawl (sitemap/Bing; Google URL Inspection live test and recrawl request when available). Keyword clusters baked into each page's headings/FAQ.
