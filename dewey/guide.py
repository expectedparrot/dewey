from __future__ import annotations

GUIDE = """# Dewey agent guide

Dewey builds a literature base iteratively. Do not treat discovery as a one-shot search.

## 1. Frame the review

Start with a topic and a research question. The topic supplies broad retrieval terms; the
question determines inclusion. If the question is still provisional, record that explicitly
and refine it after reading a few anchor papers.

    dewey topic set --topic "..." --question "..."

## 2. Seed the corpus

Find a small, diverse set of plausible anchor documents: a recent review, a foundational
paper, and one or two close empirical or methodological papers. Put search results in the
discovery queue before adding them. A candidate is only a lead; a source is part of the
review's durable evidence base.

    dewey discover add --title "..." --doi "..." --url "..."
    dewey discover search "research question" --provider openalex --json
    dewey discover list
    dewey discover accept <candidate-id> --fetch-pdf

Prefer stable metadata (DOI, authors, year) and an accessible full text. Do not reject a
paper solely because the PDF is unavailable.
After screening, accept with --fetch-pdf to try downloading the paper. Dewey uses
recorded open-access, paper, and DOI URLs, including explicit PDF metadata on landing
pages and arXiv PDF links. A failed attempt preserves the source and its BibTeX;
the response reports the retrieval result separately from successful acceptance.
Existing PDFs are reused. Downloads record their resolved URL, timestamp, and checksum.
Academic search supports openalex, semantic-scholar, and firecrawl (Research Index).
Use complementary providers for coverage, not repeated calls to a rate-limited service.
Each call queues one page and reports its next_cursor and coverage status. Continue
with --cursor or record the unvisited pages as a limitation; a failure is not an empty
successful search. For available Firecrawl research MCP tools, use their exposed schema.

Choose providers by the evidence needed:

| Provider | Use it for | Coverage caution |
|---|---|---|
| Firecrawl Research Index | Semantic paper search, question-specific passages, ranked citers | Biomedical/arXiv-heavy; ranked leads are not a citation census |
| OpenAlex | Cross-disciplinary paper discovery and forward citation enumeration | Follow pagination; some seeds and recent papers are absent |
| Semantic Scholar | Complementary search and forward citation graph | Shared unauthenticated rate limits; incomplete coverage |
| Crossref | Verify DOI, author, title, and publication metadata | Not a complete forward-citation index |
| arXiv/NBER/SSRN, publishers, institutions | Primary records, latest versions, accessible full text | Supplement graph discovery with targeted author/topic searches |

Firecrawl's dedicated Research Index is distinct from its ordinary web-search academic
site filter. Inspect the runtime's actual Research MCP tools or CLI before calling them.
The Research API supports paper search, metadata inspection, passage reads, and citation
expansion. `related-papers` defaults to similarity: explicitly choose mode=citers to
find papers citing the seed. mode=references follows the seed's bibliography instead;
mode=similar uses co-citation/bibliographic coupling and proves no direct citation edge.
Use stable primaryId values (doi:, arxiv:, pmid:, pmcid:) and verify the resolved title.

    dewey discover search "research question" --provider firecrawl --limit 20 --json
    dewey discover search "alternative framing" --provider semantic-scholar --limit 50 --json

In hosted runtimes, FIRECRAWL_API_URL may be a scrape MCP proxy, not a Research REST
endpoint. Use exposed research MCP tools there and record results with `discover add`.
For example, inspect the schema of firecrawl_research_related_papers and request
seed_ids, intent, mode="citers", and k. If the tool is unavailable, use OpenAlex or
Semantic Scholar; do not assume ordinary Firecrawl search has citation-graph access.
Current provider contracts: https://docs.firecrawl.dev/features/research,
https://help.openalex.org/api/, https://api.semanticscholar.org/api-docs/graph.

## 3. Read, summarize, and decide

For existing sources without a PDF, try retrieval before manually downloading a file:

    dewey fetch pdf <source-id>
    dewey fetch pdf <source-id> --url "https://example.org/full-paper"

This is a bounded best-effort pass: failed URLs are recorded, and HTML/paywall pages
are not saved as PDFs. If no PDF is obtained, find another accessible version or
retrieve full-text Markdown with `dewey add document <source-id> <full-text-url>`.
Do not exclude an otherwise relevant paper solely because retrieval failed. Keep the
access limitation explicit and avoid detailed claims until the necessary text is read.
Use `dewey render md <source-id>` when Markdown is needed for a downloaded PDF;
choose the authorized backend or read the PDF directly.

For every source that receives substantive attention, store a short plain-text summary:
the question, approach or evidence, main result, and why it matters to this review. Keep
interpretive detail and quotations in notes. Mark inclusion separately from having read it.

    dewey summary set <source-id> --text "..."
    dewey state mark-read <source-id> --depth full-text
    dewey state set <source-id> included

Summaries should be useful without reopening the paper, but should not overstate findings.
Distinguish the authors' claims from the agent's assessment.
For quantitative claims, preserve the metric, denominator, comparator, population,
and locator; do not pool improvements measured on incompatible scales. Firecrawl's
question-specific passage retrieval can check a claim, but is not full-paper reading.
Read the retrieved full text before marking it read. Search snippets and abstracts
support screening, not detailed findings. Use `--depth abstract` for abstract-only
reading and disclose that limitation. Marking a source read preserves its inclusion
or exclusion decision.

Firecrawl is the default Markdown backend. For a new URL-only source, `dewey add source`
records the URL and saves Firecrawl's Markdown; its bibliography starts as a placeholder.
For an existing metadata-only source, use `dewey add document <source-id> <full-text-url>`
or `dewey add document <source-id> <paper.pdf>` to preserve its identifier and provenance.
Local PDFs can be uploaded with `--backend firecrawl`, or processed with the separately
installed `--backend paper2md`. A key's presence is not itself permission to disclose a
document or incur credits.

Accepted discovery candidates already receive an entry.bib generated from their recorded
title, authors, year, DOI, and URL. Verify and enrich this metadata against the paper's
primary record; downloading a PDF does not infer missing citation fields. Export with:

    dewey cite <source-id> --format bibtex
    dewey export bibtex --status included --output references.bib

The bibliography export follows review order, then citation key, and excludes unaccepted
discovery candidates. Omit --status to export all source records. Use `dewey bib set
<source-id> --file verified.bib` or `dewey bib edit` to correct metadata.

## 4. Extract findings and appraise studies

For included sources, represent each empirical study separately. Extract atomic findings
with a page, section, table, figure, or passage locator. Keep the authors' claim, the
reported evidence, and the reviewer's interpretation in separate fields. Appraise each
study using an explicit framework, then inspect the cross-study evidence matrix.

    dewey study create <source-id> --file study.json
    dewey finding add <study-id> --file finding.json
    dewey appraisal set <study-id> --file appraisal.json
    dewey matrix evidence --format csv --output evidence-matrix.csv
    dewey synthesis coverage

One paper may report several studies, and one study may support several findings. Findings
without locators are rejected so later synthesis can always be traced back to the source.
Use `study template`, `finding template`, and `appraisal template` to create valid starting
files. Records can be updated without changing their stable identifiers. Study deletion is
guarded when findings or an appraisal exist; `--cascade` must be explicit to remove them too.

After extraction coverage is complete, organize findings into themes and make bounded claims.
Every claim must link to at least one supporting finding and should explicitly record evidence
that contradicts or qualifies it. Confidence is a reviewer judgment with a written rationale,
not an automatic count of papers.

    dewey theme template --output theme.json
    dewey theme create --file theme.json
    dewey claim template --output claim.json
    dewey claim create --file claim.json
    dewey claim audit

Themes organize the review; they do not contain evidence directly. Claims carry the argument,
and their evidence links preserve the relationship of each finding as supporting,
contradicting, or qualifying.

When the claim audit is clean, position the review as an article before drafting. The article
specification records context, thesis, literature streams, study roles, intellectual timeline,
and section logic. This prevents an evidence inventory from masquerading as a literature review.

    dewey report audit --strict --json
    dewey report article-template --output article.json
    dewey report article-set --file article.json
    dewey report context --output .dewey/synthesis/report-context.json
    dewey report brief --output .dewey/synthesis/article-brief.md
    dewey report citations --status included --json
    # Write article.md from the brief, then:
    dewey report render article.md --output article.html

JSON is the canonical machine-readable evidence context. The Markdown brief expands every claim
into findings, study details, appraisal, source metadata, and locators, but does not write prose
on the agent's behalf. The manuscript is canonical Markdown; HTML is a Pandoc rendering.
Use the citation keys from `report citations` when writing: `[@smith2024]` for a
parenthetical citation, `@smith2024` for a narrative citation, or
`[@smith2024, p. 7; @jones2025]` for grouped citations with locators. Do not invent keys
or hand-build reference anchors. `report render` uses the corpus BibTeX and Pandoc
citeproc to format citations, link them to internal reference entries, and add DOI,
source-page, open-access, and retrieved PDF URLs when recorded. It copies available
local PDFs for cited papers into `<report-stem>.assets/papers/` beside the HTML and
links those copies. Publish that assets directory alongside the HTML, preserving
relative paths; PDFs are not embedded in the HTML. The JSON result lists pdf_assets
and citation_keys so ep-agent can include them in its report artifacts. A single HTML
upload retains public paper links but cannot serve the separate local PDF copies.
`--csl style.csl` selects a citation style; `--css report.css` preserves report styling.
Unknown citation keys or missing reference entries fail rendering. Only cited papers
appear by default; put a `::: {#refs}` / `:::` fenced div where references should appear,
or let the renderer append them. `report citations` lists all corpus sources unless
filtered; source status still governs how a paper can support the review. Unaccepted
discovery leads are never bibliography sources. Rendering does not download PDFs,
verify bibliographic metadata, or establish that claims are supported. Check the
rendered citation links and publish the returned assets before delivering the report.
The strict audit exits nonzero for reporting gaps, including missing full text, summaries,
or full-text reading records for included sources. Use it as a workflow completion check;
an intact bibliography or a successfully rendered HTML file is not evidence of review quality.
Check the substantive support for claims even when optional paid quality review is skipped.
Keep the report's paper count distinct from its empirical study count. Verify bibliographic
metadata against primary records and use version_of only for versions of the same work.

## 5. Traverse citations selectively

Prefer forward citation waves after screening a diverse set of anchors. Retrieve papers
that cite each anchor, screen the wave, then expand promising new papers. Look for
replications, critiques, updated benchmarks, and methods addressing known limitations.

    dewey traverse citations <source-id> --provider openalex --limit 50 --json
    dewey traverse citations <source-id> --provider semantic-scholar --limit 50 --json
    dewey traverse citations <source-id> --provider firecrawl --limit 20 --json

OpenAlex and Semantic Scholar expose continuation cursors. Firecrawl Research uses
mode=citers and returns ranked leads, not an exhaustive citation census. Seed identity
comes from verified DOI/arXiv metadata or --paper-id; do not guess matches from titles.
Every candidate retains its seed, provider, and direction. On acceptance, a forward
candidate cites the seed, whereas a backward reference is cited by the seed.
For external tools, record leads with `discover add --via-source <source-id>
--relation citations --provider <provider> --query <query>`. Use --relation related for
similarity-only discoveries; similarity is not evidence of a citation.
Follow next_cursor with --cursor, or record unvisited pages as coverage limits. An API
failure is not evidence of saturation. Prioritize recent citers and critical evidence
alongside influential work; do not screen by citation count. When a paper is already in
the corpus, use `dewey discover resolve <candidate-id> <source-id>` to preserve new
discovery paths without adding a duplicate source.

After an anchor paper is judged relevant, inspect its bibliography. Citation traversal is
high recall and low precision: fetch references into the discovery queue, rank them against
the research question, and review the promising subset. Never auto-accept an entire
bibliography.

    dewey traverse references <source-id>
    dewey discover list --status candidate

The traversal reads the References, Bibliography, or Works Cited section of the source's
rendered Markdown. It queues raw citation text first; external catalogs may later enrich
metadata or locate a document, but they are not the authority for what the paper cited.
Preserve the parent source as discovery provenance. Accepting a traversed candidate creates
a `cites` link from the parent paper to the newly added source.

For model-assisted screening, export auditable triage records and construct/run the EDSL
job separately. Inspect prompts, models, and estimated cost before any paid execution.

    dewey discover export-triage --output triage.jsonl

## 6. Iterate until saturation

Use `dewey next` after each material stage. Continue keyword search and citation traversal
while new candidates add concepts, methods, datasets, or contrary evidence. Slow down when
several consecutive relevant papers yield no new useful leads. Before synthesis, resolve
candidate decisions, summarize included sources, extract and appraise their studies,
inspect contradictory links and the evidence matrix, and run `dewey doctor` plus
`dewey index rebuild`.
Before claiming broad coverage, search for recent work by anchor authors and for evidence
that challenges the emerging conclusions. Log the actual queries, screening decisions,
and citation traversal; derive counts from those records rather than estimating unique
candidates from search-result totals. Include a concise study comparison table and preserve
source locators and limitations when adapting the review into practitioner guidance.
Keep independent keyword and recent-author searches alongside forward snowballing so
new, uncited, and disconnected work is not missed. Saturation requires screened waves
and a documented stopping reason, not a fixed paper count or a truncated first page.
"""
