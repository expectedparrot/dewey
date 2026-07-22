# dewey — local literature-review and bibliography workspace CLI
<!-- id: dewey/dewey -->

dewey manages a local literature-review repository of PDFs, markdown renderings, BibTeX records, notes, workflow state, links, reading order, and search indexes. The agent uses it to help the user build and maintain a traceable review corpus, keep citation metadata aligned with source files, and retrieve evidence while drafting or synthesizing research.

## When to use this
<!-- id: dewey/when-to-use -->

- The user is collecting papers, reports, or source documents for a literature review.
- The task needs local source organization, citation keys, notes, reading states, and cross-source links.
- The user wants search and markdown rendering across a review corpus.
- The review needs durable, inspectable state rather than a one-off summary.

## When this is a stretch (and how to adapt)
<!-- id: dewey/when-stretch -->

- The user has only one paper. Still use dewey if notes, BibTeX, or future corpus growth matter; otherwise direct reading may be enough.
- The source is not a PDF or BibTeX entry. Add whatever source representation is available, then attach notes and metadata manually.
- The user wants qualitative coding of passages across documents. Use dewey for corpus management and [bewley](#bewley/bewley) for code-level qualitative analysis.
- The user wants publication-quality compilation. Use dewey for source management, then [gutenberg](#gutenberg/gutenberg) for the final markdown report.
- The search index is stale or incomplete. Rebuild it before drawing conclusions from search results.

## Decision rule for the calling agent
<!-- id: dewey/decision-rule -->

Before dispatching to dewey, confirm:

1. The central objects are literature sources or documents that need persistent organization.
2. The user needs metadata, notes, reading status, links, or ordering.
3. Retrieval and citation management are part of the workflow.
4. The agent should preserve local provenance rather than just summarize files once.

If yes to the first two and either the third or fourth, dewey is the right method.

## Inputs and elicitation
<!-- id: dewey/inputs -->

### Review objective
<!-- id: dewey/inputs-objective -->

What it is: the research question, scope, and intended output for the literature review.

How the agent elicits this:
- Ask what the user is trying to learn or write.
- Ask whether the corpus is exploratory, systematic, or tied to a specific report section.
- Ask which source types should be included: papers, PDFs, web reports, notes, or existing BibTeX.

Default to suggest: initialize the repository, add sources first, then set reading state and notes as the review proceeds.

Fallback: if the user has no clear review question yet, store sources and add a repository instruction note describing the provisional scope.

### Source files and metadata
<!-- id: dewey/inputs-sources -->

What it is: PDF/markdown/source files plus optional BibTeX metadata.

How the agent elicits this:
- Ask where source files live and whether there is an existing `.bib` file.
- Ask whether duplicate detection should preserve multiple versions or treat them as the same source.
- Ask whether rendered markdown is needed for search, quotation, or downstream synthesis.

Default to suggest: add PDFs first, attach BibTeX when available, then rebuild the index.

Fallback: if BibTeX is missing, add the source and create minimal metadata now; improve citation fields later.

### Review state and synthesis structure
<!-- id: dewey/inputs-state -->

What it is: per-source status, priority, notes, links, reading order, and instructions.

How the agent elicits this:
- Ask how the user wants to triage sources: unread, reading, read, key, exclude, or custom statuses supported by the CLI.
- Ask what relation types matter: supports, contradicts, extends, method, dataset, background.
- Ask whether a manual reading order should drive the next work session.

Default to suggest: mark sources unread on import, assign priority after a quick title/abstract pass, and link sources only when a relationship affects synthesis.

Fallback: if the corpus is too large to structure immediately, add all sources, run search/index, and structure only the subset relevant to the current question.

## Outputs
<!-- id: dewey/outputs -->

dewey maintains a local repository with:

- Source records with stable IDs, file paths, hashes, metadata, and optional rendered markdown.
- BibTeX records and citation keys retrievable through `dewey bib` and `dewey cite`.
- Notes, workflow state, priority, reading order, and repository instructions.
- Links between sources for synthesis graphs or argument structure.
- A search index and rendered markdown views for retrieval.
- An activity log of mutating operations for auditability.

## Workflow
<!-- id: dewey/workflow -->

Canonical sequence:

1. `dewey init` — initialize the literature repository.
2. `dewey add source <path>` — register PDFs, markdown, or source files.
3. `dewey bib set <source-id> --file <path>` or `dewey bib edit <source-id>` — attach citation metadata.
4. `dewey render md <source-id>` or `dewey render md --all` — create markdown representations when needed.
5. `dewey notes set/edit <source-id>` — capture source-specific observations.
6. `dewey state set <source-id> <status>` and `dewey state set-priority` — manage reading workflow.
7. `dewey link add <from> <to> --type <type>` — preserve synthesis relationships.
8. `dewey search <query>` and `dewey index rebuild` — retrieve passages and refresh search.
9. `dewey order set ...` — define a reading or reporting order.

Run `dewey status` and `dewey doctor` when returning to an old repository or after scripted changes.

## Worked examples
<!-- id: dewey/examples -->

### Starting a review from a folder of PDFs
<!-- id: dewey/example-review-folder -->

User: "I have a folder of papers on synthetic survey validation. Can you organize them for a review?"

Agent: "I’ll initialize a dewey repository, add the PDFs, attach BibTeX if you have it, then mark everything unread. What is the review question, and do you want a manual reading order or should I rank by relevance after a first search pass?"

User: "The question is whether LLM agents match human survey responses. I have a references.bib file."

Agent: "Good. I’ll add the PDFs, connect citation metadata, rebuild search, then surface likely key papers for priority review."

```bash
dewey init
dewey add source papers/*.pdf
dewey bib set src_001 --file references.bib
dewey index rebuild
dewey search "LLM agents human survey validation"
dewey state set src_001 reading
```

Output: a searchable local review repository with source IDs, citations, and workflow state.

### Building a synthesis trail
<!-- id: dewey/example-synthesis-trail -->

```bash
dewey notes edit smith2024 --append "Uses human benchmark survey; good Tier 2 comparison source."
dewey link add smith2024 jones2025 --type extends
dewey order add smith2024 --before jones2025
dewey render md --all
dewey cite smith2024
```

Output: notes, source links, reading order, markdown renderings, and a citation key for drafting.

## Quick command reference
<!-- id: dewey/commands -->

For full options, run `dewey <subcommand> --help`.

| Command | Purpose |
|---|---|
| `dewey init` | Initialize a review repository. |
| `dewey status` / `doctor` | Show repository health and workflow state. |
| `dewey add source` / `remove source` | Register or remove source records. |
| `dewey list` / `show` | Browse source records. |
| `dewey bib ...` / `cite` | Manage BibTeX metadata and citation keys. |
| `dewey state ...` | Track reading status and priority. |
| `dewey notes ...` | Store source notes. |
| `dewey link ...` | Create or inspect relationships between sources. |
| `dewey order ...` | Manage manual reading or synthesis order. |
| `dewey instructions ...` | Store repository-level review instructions. |
| `dewey render md` | Create markdown views of sources. |
| `dewey cat` / `path` | Retrieve source content or local paths. |
| `dewey search` / `index ...` | Search and rebuild the local index. |

## Common pitfalls
<!-- id: dewey/pitfalls -->

- Search results are only as current as the index; rebuild after adding or editing rendered text.
- Citation keys can collide when importing BibTeX from multiple sources; resolve before drafting.
- Notes are not a substitute for source links; use links when a relationship affects the synthesis.
- PDF-to-markdown conversion can fail or lose structure; inspect rendered markdown before quoting.
- Removing a source can leave stale references in notes or reading order; run `dewey doctor`.

## Cross-references
<!-- id: dewey/xrefs -->

- Downstream: [gutenberg](#gutenberg/gutenberg) compiles reports drafted from dewey-managed sources.
- Adjacent methods: [bewley](#bewley/bewley) codes qualitative text; [messick](#messick/messick) validates synthetic-study claims using benchmark literature managed here.
- Reporting support: [tufte](#tufte/tufte) checks plots in literature-review reports.

## State contract
<!-- id: dewey/state -->

The dewey repository stores source records, metadata, notes, links, order, instructions, indexes, and an activity log under its local project state. Source IDs are the stable handles the agent should use in notes, links, citations, and commands. Derived search indexes and rendered markdown can be rebuilt; source records, notes, and metadata are durable review state.

## JSON output and error codes
<!-- id: dewey/json -->

dewey supports JSON-style automation for scripting and agent workflows. Treat missing repository, duplicate source, duplicate BibTeX key, missing source ID, conversion failure, and stale-index conditions as recoverable: inspect `dewey doctor`, fix the underlying state, and rerun the command.
