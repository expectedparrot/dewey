# Dewey v1 Specification

## 1. Purpose

Dewey is a local, filesystem-backed CLI for agents constructing a literature review or bibliography.

Dewey does **not** perform literature-review reasoning itself. Instead, it provides durable primitives for storing, retrieving, and updating bibliography state so that an external agent can do the intellectual work.

For v1, Dewey is **purely BibTeX-oriented**:

* every source is represented as a BibTeX entry plus associated local artifacts
* PDF files are optional but strongly supported
* if a source has a PDF, Dewey should generate a canonical Markdown representation using `pdf2md`
* Dewey stores workflow state, notes, links, ordering, and search indexes on the filesystem

The source of truth is the contents of `.dewey/`.

---

## 2. Design principles

1. **Filesystem first**

   * All persistent state is stored under `.dewey/`.
   * No network service is required.
   * Any derived index must be rebuildable from files.

2. **Agent-facing, not human-only**

   * Every read command must support JSON output.
   * Text output is for convenience; JSON output is the stable machine interface.

3. **BibTeX is canonical**

   * Every source has exactly one canonical BibTeX record.
   * Metadata fields should map directly onto BibTeX concepts wherever possible.
   * If extra fields are needed for Dewey workflow, they must be stored outside the BibTeX entry in Dewey metadata.

4. **Archival artifact vs working representation**

   * Original PDF, when present, is the archival artifact.
   * Markdown generated from PDF is the agent-facing working representation.
   * Notes and summaries must never be mixed into generated source Markdown.

5. **Deterministic local behavior**

   * Mutating commands should have predictable file effects.
   * Search/index functionality should be local and reproducible.

6. **Derived data is disposable**

   * Search indexes and regenerated Markdown are derived artifacts.
   * The canonical record must remain valid if indexes are deleted and rebuilt.

---

## 3. Supported source model

A Dewey source represents a single bibliographic item in the project.

For v1, a source consists of:

* a stable Dewey source ID
* one canonical BibTeX entry
* Dewey workflow metadata
* optional PDF artifact
* optional generated Markdown representation
* notes
* links to other sources
* workflow state

### 3.1 Source identity

Each source has:

* `source_id`: Dewey stable identifier, format `src_<12 lowercase hex chars>`
* `content_hash`: optional SHA-256 of the managed PDF bytes, when a PDF is present

Rules:

* `source_id` is the canonical Dewey identity
* `content_hash` is a file fingerprint, not the logical identity
* the same `source_id` must remain stable even if Markdown is regenerated
* exact duplicate PDF detection should use SHA-256

Recommended generation:

* generate a random 12-hex suffix, or derive it from UUID bytes
* do **not** use file paths as identity
* do **not** use SHA-256 as the sole logical identifier

---

## 4. On-disk layout

Running `dewey init` creates:

```text
.dewey/
  config.json
  instructions.md
  review_order.json
  sources/
  indexes/
    search.sqlite
  logs/
    activity.jsonl
```

Each source lives at:

```text
.dewey/sources/<source-id>/
  entry.bib
  metadata.json
  state.json
  notes.md
  links.json
  source.pdf                # optional
  source.md                 # optional, generated from PDF
  artifacts/
    pdf2md.stderr.log       # optional
```

### 4.1 File roles

* `config.json`: project config and feature flags
* `instructions.md`: project-level review instructions for the agent
* `review_order.json`: manual ordering of sources
* `indexes/search.sqlite`: derived local search index
* `logs/activity.jsonl`: append-only mutation log

Per source:

* `entry.bib`: canonical BibTeX entry for this source
* `metadata.json`: Dewey-managed metadata not native to BibTeX
* `state.json`: workflow state for the source
* `notes.md`: freeform notes written by the agent
* `links.json`: outgoing and incoming logical links between sources
* `source.pdf`: managed archival copy of source PDF, if present
* `source.md`: generated canonical Markdown representation of the PDF, if present
* `artifacts/pdf2md.stderr.log`: conversion stderr for diagnostics

---

## 5. File schemas

## 5.1 `.dewey/config.json`

```json
{
  "version": 1,
  "project_name": null,
  "bibtex_encoding": "utf-8",
  "pdf_copy_mode": "copy",
  "search_backend": "sqlite_fts5",
  "default_output": "text"
}
```

Rules:

* `version` is the Dewey schema version
* `pdf_copy_mode` values:

  * `copy`: copy added PDFs into Dewey storage
  * `reference`: store original path only, do not copy
* v1 should default to `copy`

## 5.2 `entry.bib`

This file contains exactly one BibTeX entry.

Example:

```bibtex
@article{vaswani2017attention,
  title={Attention Is All You Need},
  author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N. and Kaiser, Lukasz and Polosukhin, Illia},
  year={2017},
  journal={Advances in Neural Information Processing Systems}
}
```

Rules:

* exactly one entry per file
* BibTeX key is canonical for bibliographic export, but not Dewey identity
* Dewey must preserve field order only if convenient; semantic correctness matters more than formatting preservation

## 5.3 `metadata.json`

```json
{
  "source_id": "src_3f1c8a91d2ab",
  "bibtex_key": "vaswani2017attention",
  "entry_type": "article",
  "managed_pdf_path": ".dewey/sources/src_3f1c8a91d2ab/source.pdf",
  "original_pdf_path": "/abs/path/to/attention.pdf",
  "content_hash": "3f1c8a91d2ab4e7d...",
  "markdown_path": ".dewey/sources/src_3f1c8a91d2ab/source.md",
  "markdown_status": "ready",
  "markdown_generator": {
    "name": "pdf2md",
    "version": null
  },
  "created_at": "2026-04-09T14:00:00Z",
  "updated_at": "2026-04-09T14:05:00Z"
}
```

Rules:

* `source_id` must match directory name
* `bibtex_key` must match the single entry in `entry.bib`
* `entry_type` must match BibTeX entry type
* path fields may be null if not applicable
* `markdown_status` values:

  * `missing`
  * `ready`
  * `failed`
  * `stale`

## 5.4 `state.json`

```json
{
  "status": "unread",
  "added_at": "2026-04-09T14:00:00Z",
  "last_read_at": null,
  "included": null,
  "priority": null
}
```

Rules:

* `status` enum values:

  * `unread`
  * `queued`
  * `reading`
  * `read`
  * `included`
  * `excluded`
* `included` is nullable boolean:

  * `true` means selected for inclusion in review/bibliography
  * `false` means explicitly excluded
  * `null` means undecided
* `priority` may be null or integer, lower number = higher priority

## 5.5 `notes.md`

Freeform Markdown file.

Rules:

* may be empty
* must be created at source creation time
* may be edited by agent or user
* Dewey must never overwrite this file except when explicitly requested by a notes command

## 5.6 `links.json`

```json
{
  "outgoing": [
    {
      "target": "src_b19482aa11ef",
      "type": "builds_on",
      "note": "Extends benchmark framing",
      "created_at": "2026-04-09T14:10:00Z"
    }
  ]
}
```

Rules:

* only outgoing links are stored canonically; incoming links are computed dynamically
* allowed `type` values in v1:

  * `builds_on`
  * `contradicts`
  * `compares_to`
  * `uses_method`
  * `uses_dataset`
  * `motivates`
  * `historical_predecessor`
  * `same_work_as`
  * `version_of`
* duplicate identical links should not be created twice

## 5.7 `review_order.json`

```json
{
  "strategy": "manual",
  "order": [
    "src_3f1c8a91d2ab",
    "src_a8e91b20cc10"
  ],
  "notes": "Broad surveys first, then core method papers"
}
```

Rules:

* v1 supports only `manual` strategy
* order list may omit some sources
* omitted sources are considered unordered
* source IDs in `order` must be unique

## 5.8 `logs/activity.jsonl`

Each line is one JSON object.

Example:

```json
{"ts":"2026-04-09T14:10:00Z","action":"source.add","source_id":"src_3f1c8a91d2ab"}
```

Rules:

* append-only
* best-effort logging; failure to write log should fail mutating command only if project integrity would otherwise be ambiguous
* actions should be stable strings like `source.add`, `state.set`, `link.add`, `order.set`, `instructions.set`, `render.md`

---

## 6. Required CLI command surface

Dewey v1 uses the following command groups.

## 6.1 Project commands

### `dewey init`

Creates `.dewey/` in current working directory.

Behavior:

* fail if `.dewey/` already exists, unless `--force` is supplied
* create directory structure
* create default config, instructions, review order, and empty log/index scaffolding

Flags:

* `--force`: overwrite existing Dewey project only if implementation chooses to support it; otherwise reject for v1
* `--json`: emit machine-readable result

Success text output example:

```text
Initialized Dewey repository at .dewey/
```

### `dewey status`

Summarizes project health.

Must report:

* number of sources
* number with PDFs
* number with Markdown ready
* count by workflow status
* number of ordered sources
* total links
* stale or failed Markdown count
* index existence/health

### `dewey doctor`

Validates repository integrity.

Checks:

* required top-level files exist
* every source directory has required files
* every `entry.bib` parses and contains one entry
* metadata and state schemas are valid enough for v1
* links reference existing source IDs
* order file references existing source IDs
* if managed PDF exists and content hash exists, hash matches
* if Markdown exists without PDF, that is allowed only if source was created from non-PDF import and explicitly marked so
* search index can be opened or rebuilt

Exit behavior:

* nonzero exit code on integrity failure

---

## 6.2 Source commands

### `dewey add source <path>`

Adds a source from a local file path.

Supported input types for v1:

* `.pdf`
* `.bib`

Behavior for PDF input:

1. verify file exists
2. compute SHA-256 of file bytes
3. detect exact duplicate by existing `content_hash`
4. if duplicate exists:

   * return existing source by default
   * do not create new source
5. otherwise:

   * generate new `source_id`
   * create source directory
   * copy PDF to `source.pdf` if copy mode is `copy`
   * record original path
   * attempt `pdf2md` conversion
   * write `source.md` if conversion succeeds
   * create placeholder BibTeX entry if none is supplied
   * create metadata, state, notes, links
   * update search index
   * append to activity log

Behavior for `.bib` input:

1. parse file
2. require exactly one BibTeX entry for `add source`; bulk BibTeX import is out of scope for v1 unless separately implemented
3. create source directory
4. write canonical `entry.bib`
5. create metadata, state, notes, links
6. no PDF or Markdown unless later attached
7. update index and log

Required flags:

* `--json`

Optional flags:

* `--bibtex-key <key>`: override BibTeX key for placeholder/generated entry
* `--no-md`: skip Markdown generation for PDF input
* `--force-duplicate`: create new source even if PDF hash already exists
* `--copy/--reference`: override project PDF copy mode for this add

Placeholder BibTeX behavior for PDF input:

* if no BibTeX is supplied at add time, Dewey should create a minimal placeholder entry
* default entry type: `@misc`
* required fields:

  * key
  * title = filename stem or `Unknown Title`
  * file = optional local path if implementation wants
  * note = `Imported from PDF; bibliographic fields incomplete`

### `dewey list`

Lists all sources.

Default columns in text mode:

* source_id
* bibtex_key
* status
* title
* year
* markdown_status

Flags:

* `--json`
* `--status <status>`
* `--has-pdf`
* `--has-md`
* `--ordered`

### `dewey show <source-id>`

Shows full source record.

Must include:

* Dewey IDs and paths
* BibTeX entry
* state
* representation status
* links summary

Flags:

* `--json`

### `dewey remove source <source-id>`

Removes a source from Dewey.

Behavior:

* delete source directory
* remove source from review order
* remove links in other sources that target this source
* update search index
* append log entry

Flags:

* `--yes` to skip confirmation in interactive mode
* `--json`

---

## 6.3 BibTeX commands

## Goal

BibTeX is canonical, so Dewey needs explicit commands to inspect and modify it.

### `dewey bib show <source-id>`

Print the canonical BibTeX entry.

Flags:

* `--json` should return parsed structure in addition to raw text if practical

### `dewey bib set <source-id> --file <path>`

Replace the canonical BibTeX entry with contents of a file.

Rules:

* file must contain exactly one entry
* source ID remains unchanged
* metadata fields `bibtex_key` and `entry_type` must be refreshed from parsed entry
* index must be updated

### `dewey bib edit <source-id> [--field <name> --value <value>]...`

Edits one or more BibTeX fields.

Required v1 capability:

* set or replace field values
* remove field values with explicit `--unset <field>` if implemented

Rules:

* edits must preserve a valid single-entry BibTeX file
* if BibTeX key changes, `metadata.json` must update accordingly

### `dewey cite <source-id>`

Outputs citation material.

Required v1 formats:

* `--format bibtex` (default)
* `--format key` returns BibTeX key only

Optional for v1:

* `--format json`

No APA/MLA formatting required in v1.

---

## 6.4 State commands

### `dewey state set <source-id> <status>`

Sets workflow status.

Allowed status values:

* `unread`
* `queued`
* `reading`
* `read`
* `included`
* `excluded`

Behavior:

* update `state.json`
* if status is `included`, set `included=true`
* if status is `excluded`, set `included=false`
* otherwise leave `included` unchanged unless implementation intentionally derives it
* log action

### `dewey state show <source-id>`

Returns `state.json`.

### `dewey state set-priority <source-id> <int>`

Sets integer priority.

### `dewey state mark-read <source-id>`

Convenience command.

Behavior:

* set status to `read`
* set `last_read_at` to now

---

## 6.5 Notes commands

### `dewey notes show <source-id>`

Print `notes.md`.

### `dewey notes set <source-id> --file <path>`

Replace `notes.md` with file contents.

### `dewey notes edit <source-id> --append <text>`

Required v1 minimal edit behavior:

* append text to notes with trailing newline

Optional:

* open in editor is not required for v1

---

## 6.6 Link commands

### `dewey link add <from-id> <to-id> --type <type>`

Creates an outgoing link.

Optional flags:

* `--note <text>`
* `--json`

### `dewey link list <source-id>`

Shows outgoing and incoming links.

Behavior:

* outgoing from source’s own `links.json`
* incoming computed by scanning other sources

Flags:

* `--json`

### `dewey link remove <from-id> <to-id> --type <type>`

Removes a matching link.

---

## 6.7 Order commands

### `dewey order show`

Prints review order.

### `dewey order set <source-id>...`

Replaces complete manual order.

Rules:

* all source IDs must exist
* duplicates are invalid
* updates `review_order.json`

### `dewey order add <source-id> --before <other-id>`

### `dewey order add <source-id> --after <other-id>`

Insert source into existing order.

Rules:

* exactly one of `--before` or `--after`
* if source already exists in order, it should be moved

### `dewey order remove <source-id>`

Remove source from order only.

---

## 6.8 Instructions commands

### `dewey instructions show`

Print project instructions.

### `dewey instructions set --file <path>`

Replace `instructions.md` with file contents.

### `dewey instructions append <text>`

Append text to instructions.

---

## 6.9 Representation commands

### `dewey render md <source-id>`

Generate or regenerate Markdown from managed PDF using `pdf2md`.

Behavior:

* fail if no PDF exists
* call `pdf2md` on managed PDF or original path depending on storage mode
* write `source.md` on success
* update metadata `markdown_status`, `markdown_path`, generator info, timestamps
* write stderr log if available
* update search index
* log action

### `dewey render md --all`

Regenerate Markdown for all sources with PDFs.

### `dewey cat <source-id>`

Print working representation.

Flags:

* `--representation md` only required in v1
* may default to Markdown if present, otherwise fail

### `dewey path <source-id> --pdf|--md|--notes|--bib`

Return path to requested artifact.

Exactly one selector flag required.

---

## 6.10 Search commands

Search is intentionally basic and local.

Dewey v1 search is retrieval, not reasoning.

### `dewey search <query>`

Default meaning:

* search title, BibTeX fields, notes, and Markdown text if present

### `dewey search --title <query>`

### `dewey search --author <query>`

### `dewey search --bibtex <query>`

### `dewey search --notes <query>`

### `dewey search --fulltext <query>`

Field-specific search.

### `dewey search --status <status>`

### `dewey search --has-pdf`

### `dewey search --has-md`

### `dewey search --linked-to <source-id>`

### `dewey search --link-type <type>`

Structured filters.

Rules:

* multiple filters may be combined
* text queries should be case-insensitive by default
* implementation may use SQLite FTS5 as backend
* files remain canonical; search index is derived

Required JSON output shape:

```json
{
  "query": {
    "fulltext": "scaling law",
    "status": "read"
  },
  "results": [
    {
      "source_id": "src_3f1c8a91d2ab",
      "bibtex_key": "kaplan2020scaling",
      "title": "Scaling Laws for Neural Language Models",
      "status": "read",
      "matches": [
        {
          "field": "markdown",
          "snippet": "... predictable scaling laws ..."
        }
      ]
    }
  ]
}
```

### `dewey index rebuild`

Rebuild full local search index from canonical files.

Sources of indexed text:

* parsed BibTeX fields
* notes.md
* source.md if present
* selected Dewey metadata fields, if useful

### `dewey index stats`

Report index backend and counts.

---

## 7. Required implementation behavior

## 7.1 JSON output contract

All read commands and all mutating commands must support `--json`.

JSON output should include at least:

* `ok`: boolean
* `action`: stable action string
* command-specific payload

Example:

```json
{
  "ok": true,
  "action": "source.add",
  "source_id": "src_3f1c8a91d2ab",
  "duplicate": false
}
```

On failure:

```json
{
  "ok": false,
  "action": "source.add",
  "error": {
    "code": "file_not_found",
    "message": "No file exists at /tmp/missing.pdf"
  }
}
```

## 7.2 Exit codes

Suggested exit codes:

* `0`: success
* `1`: generic command failure
* `2`: invalid user input / validation error
* `3`: repository integrity error
* `4`: not found

Exact mapping may vary, but must be consistent.

## 7.3 Repository discovery

All commands except `init` must locate the nearest `.dewey/` by walking upward from current working directory.

Failure behavior:

* if no project root found, fail with clear error

## 7.4 Atomic writes

Mutating commands should use atomic write strategy where practical:

* write temp file in same directory
* fsync if implementation chooses
* rename into place

This especially applies to:

* metadata.json
* state.json
* links.json
* review_order.json
* instructions.md
* entry.bib

## 7.5 Index synchronization

After any mutation affecting indexed content, Dewey must either:

* update the relevant index entries immediately, or
* mark index stale and require rebuild

Preferred v1 behavior: update immediately when feasible.

---

## 8. Duplicate and conflict handling

## 8.1 Exact duplicate PDFs

By default, adding a PDF whose SHA-256 matches an existing source should return the existing source instead of creating a new one.

JSON response should clearly indicate duplicate reuse.

## 8.2 Duplicate BibTeX keys

BibTeX keys should be unique within a Dewey project.

If a new source would duplicate an existing key:

* either fail with `duplicate_bibtex_key`, or
* automatically rename with suffix like `_2`

Required v1 behavior: choose one policy and document it. Preferred policy: fail unless explicit override is provided.

## 8.3 Broken Markdown generation

If `pdf2md` fails:

* source add still succeeds
* `markdown_status` becomes `failed`
* stderr log is saved if available
* source remains searchable via BibTeX and notes only

---

## 9. BibTeX requirements

V1 is purely BibTeX-based, so implementation must support at least these entry types:

* `article`
* `inproceedings`
* `book`
* `incollection`
* `phdthesis`
* `mastersthesis`
* `techreport`
* `misc`

Dewey does not need to validate against every BibTeX convention perfectly, but it must:

* parse one entry reliably
* expose key, type, and fields
* rewrite entries after edits without corruption

Preferred implementation approach:

* use a real BibTeX parser/writer library
* do not hand-roll BibTeX parsing unless necessary

---

## 10. Search/index requirements

Preferred backend: SQLite with FTS5.

Reason:

* fully local
* rebuildable
* simple deployment
* decent query support

### 10.1 Canonical vs derived

Canonical files:

* `entry.bib`
* `metadata.json`
* `state.json`
* `notes.md`
* `links.json`
* `source.pdf`
* `source.md`
* `instructions.md`
* `review_order.json`

Derived:

* `indexes/search.sqlite`
* any cached snippets or tokenized search tables

### 10.2 Minimum indexed fields per source

* source_id
* bibtex_key
* entry_type
* title
* author
* year
* all BibTeX fields flattened to text
* notes text
* markdown text
* status

### 10.3 Search semantics

* case-insensitive by default
* phrase search support is optional
* ranking may be simple backend default ranking
* deterministic filter behavior is required

---

## 11. Logging requirements

Every mutating command must append one activity record.

Minimum fields:

* `ts`
* `action`
* `source_id` when applicable
* command-specific details

Examples:

```json
{"ts":"2026-04-09T14:00:00Z","action":"source.add","source_id":"src_3f1c8a91d2ab","duplicate":false}
{"ts":"2026-04-09T14:05:00Z","action":"state.set","source_id":"src_3f1c8a91d2ab","status":"reading"}
{"ts":"2026-04-09T14:10:00Z","action":"link.add","from":"src_3f1c8a91d2ab","to":"src_a8e91b20cc10","type":"builds_on"}
```

---

## 12. Non-goals for v1

The following are explicitly out of scope:

* semantic search via embeddings
* automatic citation extraction from PDFs
* automatic metadata completion from Crossref/arXiv/etc.
* APA/MLA/Chicago formatting
* multi-project workspace management
* collaborative locking or concurrency across machines
* web UI
* agent reasoning features like “find seminal works” or “rank importance”
* bulk import of complex mixed corpora beyond simple single-source add

These may be added later, but the v1 data model should not block them.

---

## 13. Recommended Python implementation stack

Recommended, not mandatory:

* CLI: `typer`
* models/validation: `pydantic` or `dataclasses`
* BibTeX parsing: established BibTeX library
* indexing: built-in `sqlite3` with FTS5
* filesystem: `pathlib`
* hashing: `hashlib`
* structured timestamps: UTC ISO-8601

---

## 14. Acceptance criteria

A coding agent has correctly implemented v1 when all of the following are true:

1. `dewey init` creates a valid project structure.
2. `dewey add source paper.pdf` creates a source, stores BibTeX placeholder, computes file hash, and attempts Markdown generation.
3. `dewey add source ref.bib` imports a single BibTeX source correctly.
4. `dewey list`, `show`, `bib show`, `state show`, `link list`, `order show`, and `instructions show` all work in text and JSON mode.
5. `dewey render md <id>` regenerates Markdown from PDF.
6. `dewey search` can retrieve sources from BibTeX text, notes, and Markdown.
7. `dewey state set` persists workflow status.
8. `dewey link add` and `link remove` persist graph structure.
9. `dewey order set` and `order add/remove` persist manual review order.
10. `dewey doctor` catches malformed or broken repository state.
11. Mutations update or rebuild the index as required.
12. All mutating commands log to `activity.jsonl`.
13. No command requires network access.

---

## 15. Example user flow

```bash
dewey init

dewey instructions set --file review_instructions.md

dewey add source papers/attention.pdf
dewey add source refs/bert.bib

dewey bib show src_3f1c8a91d2ab
dewey bib edit src_3f1c8a91d2ab --field title --value "Attention Is All You Need"

dewey state set src_3f1c8a91d2ab reading
dewey notes edit src_3f1c8a91d2ab --append "Foundational transformer paper."

dewey search --fulltext "self-attention"
dewey search --author vaswani

dewey link add src_bert12345678 src_3f1c8a91d2ab --type builds_on

dewey order set src_3f1c8a91d2ab src_bert12345678

dewey status
dewey doctor
```

---

## 16. Implementation guidance for the coding agent

Suggested order of implementation:

1. repository discovery and `init`
2. source model and file schemas
3. BibTeX add/show/edit
4. state/notes/link/order/instructions commands
5. PDF add path, SHA-256, managed copy, and `pdf2md` integration
6. search index and `search` command
7. `status` and `doctor`
8. JSON output standardization and exit codes

Implementation should favor correctness and clear file semantics over cleverness.

The v1 objective is a small, dependable CLI that an external agent can script safely.
