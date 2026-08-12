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
```

Firecrawl reads `FIRECRAWL_API_KEY` from the environment or `.env`. Ask before external uploads, paid services, or model inference.

Share the complete managed project with:

```bash
dewey export html
dewey export zip
```

Do not treat discovery candidates as evidence before screening them. Preserve uncertainty and provenance rather than inferring that unavailable evidence is negative evidence.
