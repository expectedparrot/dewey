# Dewey

![Dewey, a scholarly parrot exploring a library](assets/dewey-literature-parrot.png)

Dewey is an agent-facing CLI for building auditable literature reviews. It keeps papers, rendered text, summaries, discovery provenance, screening decisions, citations, and review state in one local project.

Human documentation: [tutorial](https://expectedparrot.github.io/dewey/) · [source](docs/index.html)

## Copy and paste into Codex or Claude Code

```text
Use Dewey to manage this literature review. If `dewey` is unavailable, install it with
`uv tool install git+https://github.com/expectedparrot/dewey.git`. Work inside the review
directory. Run `dewey init` only if it is not already a Dewey project, then run
`dewey guide` and `dewey next`. Carry out the recommended action and rerun `dewey next`
after each material step. Use `--json` when structured output is helpful and run
`dewey doctor` before relying on or sharing the project. Ask before uploading a PDF,
using Firecrawl or another paid service, or running model inference. Do not treat
discovery candidates as evidence until they have been screened.
```

## Install

```bash
git clone https://github.com/expectedparrot/dewey.git
cd dewey
uv sync
uv run dewey --help
```

Or install it as a tool:

```bash
uv tool install git+https://github.com/expectedparrot/dewey.git
```

## Run

Start or resume inside the intended project directory:

```bash
dewey init
dewey guide
dewey next
```

Follow `dewey next` after every material step. Use `--json` for structured output. Run `dewey doctor` before relying on project state.

Use `dewey --version` for environment checks. Before declaring a full literature review
complete, run `dewey report audit --strict --json`: it exits nonzero when reporting gaps
remain, including included sources without stored full text, full-text reading records,
or summaries. The default audit remains informational. These checks validate recorded
evidence coverage, not the accuracy of the reviewer's interpretation.

For publicly reachable papers, pass the URL directly. Dewey uses Firecrawl to
retrieve clean Markdown and records the URL as source provenance:

```bash
dewey add source https://example.org/paper.pdf
dewey add source paper.pdf --backend firecrawl
dewey add source paper.pdf --backend paper2md  # optional local backend
dewey add document <source-id> retrieved-paper.pdf
dewey add document <source-id> https://example.org/full-paper
```

Use `add document` after screening a metadata-only citation and retrieving its full text;
it preserves the existing source identifier and discovery provenance.

Try to obtain the original PDF as part of screened acceptance, or for an existing source:

```bash
dewey discover accept <candidate-id> --fetch-pdf
dewey fetch pdf <source-id>
dewey fetch pdf <source-id> --url https://example.org/paper
```

The downloader tries recorded open-access, paper, and DOI URLs, follows explicit PDF
metadata on landing pages, and resolves arXiv abstract URLs to PDFs. It stores successful
downloads as `source.pdf`, with their resolved URL, retrieval timestamp, and SHA-256.
It makes a bounded pass, checks PDF signature/completeness, and never overwrites an
existing PDF. A failed download leaves the citation and any existing Markdown intact.
`fetch pdf` exits nonzero if unavailable; `discover accept --fetch-pdf` still accepts
the screened source and reports the download result separately. Plain `discover accept`
continues to be metadata-only. Retrieval does not mark a paper read or run conversion.

Accepted discovery candidates automatically receive BibTeX from their metadata:

```bash
dewey cite <source-id> --format bibtex
dewey export bibtex --status included --output references.bib
```

Omit `--status` to export all source records. Unaccepted candidates are never exported.
Verify incomplete metadata before publication; a bare URL/PDF import starts with a
placeholder citation, and PDF retrieval does not infer missing author/title fields.

Search academic indexes and follow forward citations into the discovery queue:

```bash
dewey discover search "research question" --provider openalex --limit 50 --json
dewey traverse citations <source-id> --provider openalex --limit 50 --json
dewey traverse citations <source-id> --provider semantic-scholar --limit 50 --json
dewey traverse citations <source-id> --provider firecrawl --limit 20 --json
```

Screen each wave before accepting papers or expanding new seeds. Forward discoveries
retain their seed and create `new paper -> seed` citation links on acceptance. Repeated
sightings deduplicate while preserving provenance. Continue paginated results using
`--cursor <next_cursor>`; failures are explicit and never count as empty searches.
Firecrawl uses the dedicated Research Index's `citers` mode. Its ranked results have
unknown exhaustive coverage, even when no further cursor is available. Combine forward
snowballing with selective backward references and recent keyword/author searches.

Optional credentials are `OPENALEX_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, and
`FIRECRAWL_API_KEY`. Direct Research REST calls do not use the hosted scrape proxy;
with `FIRECRAWL_API_URL`, use exposed research MCP tools and queue leads with
`discover add --via-source <source-id> --relation citations --provider firecrawl`.
Use `--relation related` for similarity results so no citation edge is invented.
See the [provider contracts and limitations](docs/academic-discovery.md).

Firecrawl is the default Markdown backend and reads `FIRECRAWL_API_KEY` from the
environment or `.env`. When `FIRECRAWL_API_URL` is set, Dewey calls the
`firecrawl_scrape` MCP tool at that URL; this supports scoped proxy credentials
in hosted sandboxes. The optional local `paper2md` backend must be installed
separately. Ask before external uploads, paid services, or model inference.

Share the complete managed project with:

```bash
dewey export html
dewey export zip
```

For synthesis, represent papers as studies and atomic, source-located findings. Keep the
authors' claims separate from reported evidence and reviewer interpretation, add an
explicit appraisal, and export a cross-study matrix:

```bash
dewey study create <source-id> --file study.json
dewey finding add <study-id> --file finding.json
dewey appraisal set <study-id> --file appraisal.json
dewey matrix evidence --format csv --output evidence-matrix.csv
dewey synthesis coverage
```

Generate starting files with `dewey study template --output study.json` (and the corresponding
`finding` and `appraisal` commands). Study and finding records support `show`, `list`, `update`,
and guarded `delete` workflows. The evidence matrix can be filtered by study, source, outcome,
design, or appraisal judgment and exported as JSON, CSV, or Markdown.

Once extraction is complete, `dewey theme` organizes the field and `dewey claim` records
evidence-weighted synthesis statements. Claim evidence links are explicitly classified as
supporting, contradicting, or qualifying. `dewey claim audit` flags unused findings, empty
themes, and claims that contain no contrary or qualifying evidence.

Reporting is Markdown first. Before drafting, create an article specification that records the
substantive context, thesis, literature streams, role of each study, intellectual timeline, and
section-level argument:

```bash
dewey report article-template --output article.json
dewey report article-set --file article.json
dewey report brief --output .dewey/synthesis/article-brief.md
```

The brief combines that editorial judgment with the reviewed claims, appraisals, and source
locators. It is context for a writing agent, not manuscript prose. Write the actual article as
Markdown, then use Pandoc through `dewey report render article.md --output article.html`.
Run `dewey report citations --status included --json` for citation keys, copyable Markdown,
and available source links. Write citations as `[@smith2024]`, `@smith2024`, or
`[@smith2024, p. 7; @jones2025]`; the renderer uses corpus BibTeX to format them and
generate linked references. Each reference gets recorded DOI, source-page, open-access,
and PDF links. Available local PDFs for cited papers are copied into
`article.assets/papers/`; distribute that directory alongside `article.html` to keep
local PDF links working. Rendering does not fetch or convert PDFs. Unknown citation
keys fail rather than silently producing unresolved references.

```bash
dewey report citations --status included --json
# Write article.md with citations from that list, then:
dewey report render article.md --output writeup/article.html --json
# Optional: --css report.css --csl journal-style.csl
```

The render result lists `citation_keys`, `pdf_assets`, and Pandoc `warnings` for report
artifact collection. References are appended unless the manuscript contains a Pandoc
`::: {#refs}` fenced div. Only cited sources appear by default. Citation syntax and
formatting follow [Pandoc's citation support](https://pandoc.org/MANUAL.html#citations).
`dewey report context` remains the canonical structured evidence export, and `dewey report audit`
checks whether the underlying synthesis is ready for drafting.

Do not treat discovery candidates as evidence before screening them. Preserve uncertainty and provenance rather than inferring that unavailable evidence is negative evidence.
