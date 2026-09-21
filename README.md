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

Create a named project directory, then work inside it:

```bash
dewey init my-literature-review
cd my-literature-review
dewey guide
dewey next
```

`dewey init` without a path initializes the current directory. Commands find the
nearest `dewey.json` when run from a project or any of its subdirectories.

## Project files

```text
my-literature-review/
  dewey.json                 # Project settings and schema version
  instructions.md
  review_order.json
  sources/<source-id>/        # BibTeX, metadata, PDFs, Markdown, summaries, notes, links
  discovery/candidates.json  # Leads, screening decisions, and provenance
  discovery/activity.jsonl   # Search queries, coverage, traversal, and screening history
  synthesis/                 # Studies, findings, appraisals, themes, claims, article plan
  reports/
  docs/index.html            # Expected Parrot literature explorer (generated)
  .gitignore
  .dewey/                    # Local indexes, diagnostics, original PDF paths
```

Research files are ordinary, versionable files. Per-source `links.json` records are
the authoritative citation and relationship graph; visualizations and SQLite indexes
are derived. Concise `summary.txt` files remain separate from detailed `notes.md` files.
Initialization creates Git ignore rules for `.dewey/`, environment files, and ZIP
exports; it does not initialize Git or commit anything. PDFs are trackable by default.
Use your own ignore rules or Git LFS if appropriate for your project.

A clone or ZIP export contains the research without local state. Search rebuilds its
index from current files, including changes made through Git or direct editing.
Original machine-specific PDF paths and conversion diagnostics stay under `.dewey/`
and are excluded from ZIP exports. The optional `add source --reference` mode keeps
only a local PDF reference; use the default copy mode for portable full text.

This layout replaces the old all-in-`.dewey/` layout; no compatibility or migration
command is provided.

## Git and the literature explorer

Dewey can use an ordinary Git repository to version and synchronize a review. Git is
optional; local research commands work offline. Use the Git CLI already configured
on your machine, including its identity, SSH keys, and credential helper.

```bash
dewey init my-review --git
cd my-review
dewey git remote add origin git@github.com:your-account/my-review.git
# Add and screen papers, then inspect a checkpoint:
dewey git status
dewey git diff
dewey git site
dewey git commit -m "Screen the first citation wave"
dewey git push --remote origin
```

Use `dewey git init` to enable Git in an existing review. Initialization creates no
commits. `dewey git remote list` shows configured remotes. All Git commands support
`--json` with the usual Dewey result envelope.

To work from a remote project:

```bash
dewey git clone git@github.com:your-account/my-review.git my-review
cd my-review
dewey git pull
# Do a research stage, then:
dewey git commit -m "Add replication evidence"
dewey git push
```

`git status` reports the review's changed files and research counts. Ahead/behind
counts reflect the last fetch; status does not use the network. `git diff` compares
tracked files with HEAD and lists untracked files separately. A checkpoint commits
all current review changes, validates the records, and regenerates the explorer.
Unrelated staged files elsewhere in a containing repository remain staged.
Private local files and environment files are excluded; if they have already been
force-tracked, Dewey refuses a commit or push until they are untracked.

Pull and push require the **whole containing repository** to be clean. Pull explicitly
uses fast-forward-only integration; it does not stash work, merge, or rebase. Resolve
divergent branches with ordinary Git. Push sends only the current branch to its
upstream and never force-pushes. Clone and pull validate project structure and rebuild
the local index. If fetched research is invalid, Dewey returns an error and leaves
the checkout available for inspection with `dewey doctor --json`.

Each shared review gets an auto-generated **`README.md`** with its research question,
recorded conclusions, corpus and screening counts, coverage gaps, and a guide to the
files and workflow. It refreshes with `dewey git site`, `dewey git commit`, and
`dewey export zip`. Hand-written text outside `<!-- dewey:overview:start -->` and
`<!-- dewey:overview:end -->` is preserved; edit the underlying records to change
the generated section. An existing README without markers receives a generated
section at the end.

Set `site_url` in `dewey.json` to the verified public explorer URL to put an
**Open explorer** link near the top of the README. Dewey does not guess a Pages
URL: GitHub project sites inherit a custom domain from the owner's account site,
if one is configured. It does not modify your account website or DNS settings.

Each review's **`docs/index.html`** is an Expected Parrot branded literature
explorer with five views:

- **Overview:** synthesis claims linked to supporting, qualifying, and contradictory findings, plus review completeness.
- **Evidence table:** study design, population, sample, comparator, findings, and appraisal; compare 2–4 studies and export CSV/JSON.
- **Papers:** included papers by default, with search, filters, summaries, readable notes/full text, PDFs, and BibTeX.
- **Citation map:** focused neighborhoods, author/title search, and distinct citation/version relationships.
- **Screening audit:** paginated candidates, discovery provenance, decisions, and recorded search coverage.

The page embeds its code and research data and works directly from disk. Archival
PDFs are copied into `docs/index.assets/papers/`; share that directory alongside
the HTML to retain PDF links. Private local PDF references are never copied.
Filters, comparisons, and paper/claim/study links are stored in the URL. The title
uses `project_name` in `dewey.json`, falling back to the review topic.

`dewey git site` refreshes it without committing; `dewey git commit` refreshes and
includes it automatically. `dewey export html` also defaults to this path. Existing
non-explorer homepages are preserved: move one aside before using `git site` or
`git commit`. No server or build tools are needed to view the export.

For a standalone review repository, configure GitHub **Settings → Pages → Deploy
from a branch**, select the branch you push to and the **`/docs`** folder. Dewey
writes `docs/.nojekyll`; subsequent pushes update the published explorer. See
[GitHub's publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
Dewey generates the site files; hosting settings are configured separately.

Reviews can also live inside a larger repository: `dewey git init` reuses that
repository instead of nesting another one. Commits are scoped to the review, while
pulls and pushes synchronize the repository branch, including any other commits on
it. Clone such a review with `dewey git clone <url> <destination> --project reviews/my-review`.
For Pages in this arrangement, use an Actions deployment for the nested site's
folder; GitHub's branch-based source selector only supports the root or `/docs`.

PDFs use ordinary Git by default. Git LFS can be configured using standard Git LFS
commands; Dewey does not provision it. Concurrent edits to a single record or the
shared discovery queue require ordinary Git conflict resolution. Automatic semantic
merging is not provided.

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
dewey report brief --output synthesis/article-brief.md
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
