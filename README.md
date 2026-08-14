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

For PDFs, local `paper2md` is the default. Firecrawl is explicit and uploads the document:

```bash
dewey add source paper.pdf
dewey add source paper.pdf --backend firecrawl
dewey add document <source-id> retrieved-paper.pdf
```

Use `add document` after screening a metadata-only citation and retrieving its full text;
it preserves the existing source identifier and discovery provenance.

Firecrawl reads `FIRECRAWL_API_KEY` from the environment or `.env`. Ask before external uploads, paid services, or model inference.

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
`dewey report context` remains the canonical structured evidence export, and `dewey report audit`
checks whether the underlying synthesis is ready for drafting.

Do not treat discovery candidates as evidence before screening them. Preserve uncertainty and provenance rather than inferring that unavailable evidence is negative evidence.
