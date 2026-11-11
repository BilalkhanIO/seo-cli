# SEO Audit — studenttimepk.blogspot.com

**Date:** 2026-08-18
**Platform:** Google Blogger (Blogspot)
**Pages in sitemap:** 143 posts + 3 static pages
**Language:** en-GB
**Overall SEO Health Score: 74 / 100** — *Good foundation, held back by two systemic on-page defects*

---

## Scope & Method

Analysis run with the `claude-seo` runtime (headless fetch + HTML parse + JSON-LD +
QRG content scorer). Signals verified on the homepage and a sample of 4 blog posts.
Each finding below states the observation it rests on and how you'd falsify it.

---

## Score by Dimension

| Dimension | Score | Notes |
|---|---:|---|
| Technical foundation | 88 | HTTPS, valid robots.txt, 2 valid sitemaps, self-canonicals, indexable |
| Schema / structured data | 85 | Valid `BlogPosting` on every post; homepage has 12 valid JSON-LD blocks |
| Images | 85 | Sampled post images all have alt text |
| Content quality | 76 | Substantial (1,300–1,600 words), but flagged "repetitive"; E-E-A-T signals thin |
| **On-page / meta** | **58** | **Posts have NO meta description; H1 is the site name, not the post title** |
| AI-search / GEO | 65 | Citable content, but no `llms.txt` and no Twitter Card |

---

## What's Working (keep it)

- **HTTPS + Google infrastructure (GSE).** Fast, secure hosting; HTTP/3 advertised (`Alt-Svc: h3`).
- **`robots.txt` is correct.** Allows crawl, blocks `/search` (thin/duplicate label & archive pages). Declares both sitemaps.
- **Sitemaps valid.** `sitemap.xml` (143 URLs) and `sitemap-pages.xml` (3 URLs) both return HTTP 200 and parse as valid `urlset`.
- **Indexable.** `X-Robots-Tag: all`; self-referencing canonicals on every post.
- **Structured data.** Every post emits a valid `BlogPosting` (with `ImageObject`, `Organization`, `Person`, `WebPage`). This is a real strength for rich results and AI citation.
- **Solid content depth.** Sampled posts run 1,296–1,613 words with clear H2 section structure.
- **Image alt text present** on sampled post images.
- **Homepage meta is well-optimized:** title + a 145-char meta description + Open Graph tags.

---

## Critical / High-Priority Findings

### 1. [HIGH] Every blog post is missing a meta description
- **Observation:** `meta_description` was empty on all 4 sampled posts (homepage has one; posts do not).
- **Impact:** Google auto-generates the SERP snippet from page text — often an awkward first sentence — reducing click-through. You lose control of your most important SERP real estate.
- **Fix (Blogger):** For each post, open **Post settings → Search Description** and write a 140–155 char summary with the target keyword. Also enable **Settings → Meta tags → Search description** at the blog level if not already on.
- **Falsify:** Re-fetch a post; a `<meta name="description">` should be present and non-empty.

### 2. [HIGH] Heading hierarchy is inverted — post title is not the H1
- **Observation:** On every sampled post, the only `<h1>` is **"Students Time"** (the blog name). The actual article title (e.g. *"GPT-5.6 and the Rise of AI Agents for Developers"*) renders as an `<h3>`.
- **Impact:** Weakens the strongest on-page relevance signal. Search engines and AI answer engines use H1 to identify the page's primary topic; here every page claims the same H1.
- **Fix:** This is a **theme/template issue**. Edit the Blogger theme so the post title (`<data:post.title/>`) is wrapped in `<h1>`, and demote the blog title in the header to a `<p>`/`<div>` or `<h2>`. If you're not comfortable editing HTML, switch to a modern SEO-friendly Blogger theme that does this correctly.
- **Falsify:** Re-fetch a post; `h1` should equal the article title, not "Students Time".

---

## Medium-Priority Findings

### 3. [MEDIUM] Content flagged "repetitive"
- **Observation:** QRG content scorer gave post #1 overall 95/100 but raised a `repetitive` flag (repetition_score 31).
- **Impact:** Repeated phrasing/keyword restating can read as padded to both users and Google's helpful-content systems.
- **Fix:** Vary sentence openings and reduce restating the same point across sections; lead sections with concrete specifics (numbers, named tools, dates).
- **Falsify:** Re-run `content_quality.py`; repetition_score should drop and the flag clear.

### 4. [MEDIUM] E-E-A-T signals are thin
- **Observation:** Content targets education/certifications/AI-tools (YMYL-adjacent), but there's no visible author bio, credentials, or "About/Contact" trust surface in the sampled markup.
- **Impact:** For advice/education topics Google weights Experience & Trust heavily.
- **Fix:** Add a real author byline with a short bio + photo, an About page, and a Contact page. Link them in the footer. Consider `Person`/`Author` detail in schema (Blogger already emits a `Person`, make sure it names a real author).
- **Falsify:** An About + author bio page exists and is linked site-wide.

### 5. [MEDIUM] No `llms.txt` (AI-search / GEO)
- **Observation:** `https://studenttimepk.blogspot.com/llms.txt` returns Blogger's soft-404 template, not a real file.
- **Impact:** Minor today, growing. `llms.txt` helps AI answer engines (ChatGPT, Perplexity, Google AI Overviews) understand and cite your site.
- **Fix:** Blogger can't host arbitrary root files easily; this is optional. If you later move to a custom domain/host, add an `llms.txt` listing your key posts.
- **Falsify:** `llms.txt` returns a real, non-HTML document.

---

## Low-Priority / Polish

### 6. [LOW] No Twitter Card tags
- **Observation:** Open Graph present, but `twitter:card` absent on posts.
- **Fix:** Add `twitter:card`, `twitter:title`, `twitter:image` via theme meta tags for better X/Twitter link previews.

### 7. [LOW] Verify internal linking depth
- **Observation:** Raw-HTML parse detected only ~2 in-content links per post (Blogger renders related-post widgets via JS, so this may undercount).
- **Fix:** Add 2–4 **manual contextual internal links** in each post body to related articles. Don't rely on JS widgets alone — hand-placed body links pass stronger signals and are crawler-safe.

### 8. [LOW] Core Web Vitals — field data not measured
- **Observation:** CrUX/GSC field data requires API credentials that aren't configured, so real-user LCP/INP/CLS weren't measured here.
- **Fix:** Connect Google Search Console + PageSpeed API (`/seo google`) to pull field CWV. Blogger themes are generally decent on CWV; the main risk is large hero images (lazy-load + compress).

---

## Prioritized Next Steps
See `ACTION-PLAN.md`.
