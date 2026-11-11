# Blogger API v3 — Capability Map (RESEARCHED, not assumed)
_Source: official discovery doc `googleapis.com/discovery/v1/apis/blogger/v3/rest`. The agent must use only these facts._

## What a Post can carry
| Field | Type | Agent uses it for |
|---|---|---|
| `title` | string | SEO title — front-load the primary keyword, ≤ 60 chars |
| `content` | string (HTML) | Body **+ JSON-LD schema** (`<script type="application/ld+json">` lives here) **+ internal links** |
| `labels` | array | Tags/categories — 3–6 relevant, consistent per cluster |
| `published` | RFC-3339 | Publish/backdate (only re-date on genuine updates) |
| `images` | array | Featured image reference |
| `location` | object | Geotag (rarely used) |
| `customMetaData` | string (JSON) | Theme-readable JSON metadata (NOT the SERP meta) |
| `titleLink`, `readerComments` | string | Title link / comment settings |
| `status` | string | Draft/live (via `isDraft`/`publish`/`revert` params) |

## Request params (posts.update / insert / patch)
`blogId` · `postId` · `publish` (bool) · `revert` (→ draft) · `isDraft` · `fetchBody` · `fetchImages`

## ❌ NOT settable via API (must be manual in Blogger UI)
- **Search Description (meta description)** — not a Post field. → the agent WRITES it and flags it for manual paste (Settings → Meta tags → Enable search description → On; then post sidebar → Search Description).
- **Custom Redirects** — not in the API. → agent outputs the From→To list for manual entry.
- **Request Indexing** — no API for blog URLs. → manual GSC. (Bing URL Submission API works and IS automated.)
- **Theme edits (H1 fix, schema in theme)** — not via Posts API. → agent outputs the exact theme change.

## Handling the gaps (agent rules)
- **Meta description** → generate it, output for manual paste. Never assume it's set.
- **Schema** → embed `BlogPosting` + `FAQPage` JSON-LD directly in `content` (this IS API-settable).
- **H1** → the theme controls H1; if the theme prints the blog name as H1, flag the one-time theme fix. Do not rely on content H2s to be H1.
