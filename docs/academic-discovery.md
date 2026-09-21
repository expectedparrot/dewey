# Academic discovery contracts

`dewey guide` owns the research workflow, provider selection, and stopping guidance.
Integrating agents should follow it rather than maintain a separate literature-review
procedure. This document supplies API detail and integration limits.

Dewey supports one-page academic keyword search and forward-citation retrieval from
OpenAlex, Semantic Scholar, and Firecrawl Research. These are discovery operations;
results stay candidates until reviewed. No SDK or additional dependency is required.

| Provider | Search | Forward citations | Pagination |
|---|---|---|---|
| OpenAlex | `/works?search=...` | Resolve verified DOI/work ID, then `/works?filter=cites:W...`, newest first | Opaque `next_cursor`; supply `--cursor` |
| Semantic Scholar | `/graph/v1/paper/search` | `/paper/{id}/citations`, normalize `citingPaper` | Numeric next offset exposed as `next_cursor` |
| Firecrawl Research | `/v2/search/research/papers` | `/papers/{id}/similar` with `mode=citers` and review question as `intent` | Ranked top-k; `complete=null` because coverage is unknown |

Limits are 1–100 records per call. There is no hidden automatic pagination or paid
model screening. `complete=true` describes exhaustion of that provider query, not
coverage of a field. Failures return nonzero, log failure separately, and do not
import a partial malformed page. Provider keys and raw error responses are not logged.
Observe provider quotas and any required authorization for paid use.

For a forward traversal, use source DOI metadata, an arXiv URL where supported, or
`--paper-id` with a verified provider identifier. OpenAlex does not resolve arXiv
identifiers directly: use a verified OpenAlex work ID or a different provider. An
unresolved seed should be logged as a coverage gap, not silently title-matched.

Successful calls record query, seed, provider, input/next cursor, fetched/new candidate
counts, candidate IDs, and coverage status in `discovery/activity.jsonl`.
Each candidate retains provider record ID and direction in its provenance. Existing
DOI/arXiv/title deduplication preserves sightings from different seeds and providers.
Acceptance or resolution writes `candidate --cites--> seed` for forward discoveries,
`seed --cites--> candidate` for references, and no citation edge for similarity leads.

Use `discover accept <candidate-id> --fetch-pdf` after screening to try the recorded
full-text locations. Acceptance preserves `open_access_url` on the source and generates
its BibTeX entry even if downloading fails. `fetch pdf <source-id>` can retry or use an
explicit `--url`. The downloader stores PDF bytes, resolved URL, timestamp, checksum,
and attempt history. It follows explicit publisher PDF metadata, not arbitrary PDF links
to cited papers, and does not invoke paid conversion. Check the downloaded paper's identity
before using it as evidence. Export reviewed citations with
`dewey export bibtex --status included --output references.bib`.

For tools outside Dewey, including hosted Firecrawl research MCP tools:

```bash
dewey discover add --title "..." --doi "..." --via-source <seed-source-id> \
  --relation citations --provider firecrawl --query "review question"
```

The existing `FIRECRAWL_API_URL` is a scrape MCP proxy, not a Research REST base URL.
The direct adapter refuses to send scoped proxy credentials to Firecrawl REST. Use
the exposed research tools when supported by that hosted runtime. Firecrawl's
Research Index focuses on biomedical sources and arXiv, so supplement it for broader
social-science coverage. Query-specific passages are useful for checking a finding
but do not establish that the entire paper was read.

Prefer screened forward waves from diverse anchors, with recent-author searches,
independent keyword queries, and selective bibliography traversal. Avoid citation-count
thresholds that exclude new work. Retain stopping reasons and unvisited pages; do not
treat API failures or a top-k ranked result set as saturation.

Provider contracts checked 2026-09-19:

- [Firecrawl Research Index and modes](https://docs.firecrawl.dev/features/research)
- [Firecrawl search response](https://docs.firecrawl.dev/api-reference/endpoint/research-search-papers)
- [Firecrawl related-paper response](https://docs.firecrawl.dev/api-reference/endpoint/research-related-papers)
- [OpenAlex API](https://help.openalex.org/api/)
- [OpenAlex citation recipes](https://help.openalex.org/how-to/api-recipes/)
- [Semantic Scholar Graph API](https://api.semanticscholar.org/api-docs/graph)
