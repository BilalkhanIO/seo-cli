# Additional projects for a research and SEO workbench

Checked October 27, 2026 against GitHub repository metadata and maintainer documentation. These are candidates and architectural references; only Trafilatura was added in this research round.

| Repository | Observed license / status | Role in our tool | Constraint / decision |
|---|---|---|---|
| [Trafilatura](https://github.com/adbar/trafilatura) | Apache-2.0; active | Extract article text and metadata from HTML | Integrated locally at 2.3.1; no paid API required |
| [Crawl4AI](https://github.com/unclecode/crawl4ai) | Apache-2.0; active | Browser rendering and extraction for JavaScript pages | Optional fallback; needs browser runtime and compute; not installed |
| [MarkItDown](https://github.com/microsoft/markitdown) | MIT; active | Convert office documents and other files into research material | Add when document imports are needed; optional integrations can require services |
| [Docling](https://github.com/docling-project/docling) | MIT; active | Complex PDFs, tables and document layout | More dependencies/models; add for document-heavy work |
| [KeyBERT](https://github.com/MaartenGr/KeyBERT) | MIT; active | Extract candidate phrases/topics for content planning | Model downloads and compute; extracted terms are not search volume or difficulty |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | Apache-2.0; active | Research planning, evidence gathering and cited report ideas | Model/search providers may cost money; review citations rather than assuming verification |
| [SearXNG](https://github.com/searxng/searxng) | AGPL-3.0; active | Optional metasearch adapter | Depends on third-party engines, access policies and rate limits; not a guaranteed unlimited search API |
| [Firecrawl](https://github.com/firecrawl/firecrawl) | AGPL-3.0; active | Crawl/map/extract API design | Self-hosting has compute and operational cost; hosted API has separate limits/pricing |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | MIT; archived | Research workflow reference | Avoid as a new core runtime dependency; archived status verified |
| [Flowise](https://github.com/FlowiseAI/Flowise) | GitHub license metadata NOASSERTION; archived | Visual workflow reference | Not selected: archived, license requires direct review before reuse |

## Ideas worth adapting

- Structured extraction with source URLs instead of copying entire pages into prompts.
- Separate retrieval, evidence review, writing and technical checks.
- Show source retrieval dates, text fingerprints and verification state.
- Keep research providers interchangeable: first-party APIs and local imports first, optional paid providers later.
- Maintain a content inventory so a query maps to an existing page before drafting another.
- Treat suggested topics, inferred overlap and readability as review aids, not measured demand or ranking guarantees.

## Implementation completed

`research_library.py` now uses Trafilatura to extract selected public HTML pages into a local SQLite full-text index. It stores the requested URL, final URL, title, retrieval timestamp, text fingerprint, extracted content and metadata. It checks robots policy and rejects private/local source addresses. Re-collecting a URL refreshes one searchable record and reports whether extracted text changed.

The collector downloads only explicitly supplied URLs, not search-engine results or an entire web domain. Extraction is not claim verification. Source text is reference material, not instructions and not automatically republished. No search service, LLM account, paid data provider or public server was enabled.

The SQLite store is for a private local workstation, not a hardened multi-user fetch service. A hosted version would need job isolation, stronger outbound network controls, authentication and per-user quotas before accepting untrusted users' URLs.
