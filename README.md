# Dewey

Dewey is a local, filesystem-backed CLI for managing a literature review or bibliography repository.

It is designed for agent workflows, but it is also usable directly from the terminal. Dewey stores all project state under a `.dewey/` directory inside your working tree. It does not require a server, and it does not require network access during normal use.

For v1, Dewey is BibTeX-first:

- Every source has exactly one canonical BibTeX entry.
- Sources may also have a managed PDF.
- If a PDF exists, Dewey can generate an agent-facing Markdown representation using `paper2md`.
- Dewey stores notes, links, workflow state, review order, and a local search index on disk.

## Status

This repository currently implements:

- Project initialization and repository discovery
- Source import from `.bib` and `.pdf`
- Canonical BibTeX inspection and editing
- Workflow state commands
- Notes commands
- Source linking
- Manual review ordering
- Project instructions
- Markdown rendering through `paper2md`
- Local SQLite FTS5 search
- Repository health checks with `doctor`
- JSON output for read and write commands
- Activity logging for mutating commands

## Requirements

- Python 3.12+
- A shell environment where you can run a Python CLI

Optional but important for PDF workflows:

- `paper2md` installed from GitHub
- `paper2md` backend dependencies if you want real PDF to Markdown conversion to succeed

## Installation

### Local editable install

From this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs the `dewey` CLI entry point declared in [pyproject.toml](/Users/jjhorton/tools/ep/dewey/pyproject.toml).

### `paper2md` install from GitHub

Dewey expects `paper2md` to come from GitHub, not PyPI.

Minimal install:

```bash
pip install "paper2md @ git+https://github.com/expectedparrot/paper2md.git"
```

The upstream `paper2md` project also documents optional backend variants. If Markdown rendering fails because backend dependencies are missing, install the fuller `paper2md` stack appropriate for your environment.

### Running without installing `dewey`

You can also invoke the CLI directly from the repo:

```bash
python3 -m dewey --help
```

If you run from outside the repository and have not installed `dewey`, set `PYTHONPATH` to this project root.

## Core model

A Dewey source is stored at:

```text
.dewey/sources/<source-id>/
  entry.bib
  metadata.json
  state.json
  notes.md
  links.json
  source.pdf                # optional
  source.md                 # optional
  artifacts/
    pdf2md.stderr.log       # diagnostics log for Markdown conversion failures
```

Top-level project files:

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

Important concepts:

- `source_id`: Dewey’s stable identifier, like `src_335517b63c54`
- `entry.bib`: the canonical bibliographic record
- `metadata.json`: Dewey-managed metadata like `content_hash` and Markdown status
- `state.json`: reading workflow status, inclusion state, priority, timestamps
- `notes.md`: freeform user or agent notes
- `links.json`: outgoing source-to-source links
- `search.sqlite`: derived search index, rebuildable from canonical files

## Repository discovery

Every command except `init` walks upward from the current directory to find the nearest `.dewey/`.

That means you can run `dewey` from:

- the repository root
- a nested subdirectory
- a script running inside the project tree

If no `.dewey/` directory is found, the command fails with a repository error.

## Quick start

Initialize a new Dewey repository:

```bash
dewey init
```

Add project instructions:

```bash
dewey instructions set --file review_instructions.md
dewey instructions append "Prioritize survey papers first."
```

Add sources:

```bash
dewey add source refs/attention.bib
dewey add source papers/attention.pdf
```

Inspect and edit the canonical BibTeX:

```bash
dewey bib show src_335517b63c54
dewey bib edit src_335517b63c54 --field title --value "Attention Is All You Need"
```

Track workflow state and notes:

```bash
dewey state set src_335517b63c54 reading
dewey notes edit src_335517b63c54 --append "Foundational transformer paper."
```

Create links and review order:

```bash
dewey link add src_followup1234 src_335517b63c54 --type builds_on
dewey order set src_335517b63c54 src_followup1234
```

Search and validate:

```bash
dewey search attention
dewey status
dewey doctor
```

## Output modes

Most commands support both text output and JSON output.

Use `--json` when scripting:

```bash
dewey list --json
dewey show src_335517b63c54 --json
dewey state set src_335517b63c54 reading --json
```

JSON responses follow a simple shape:

```json
{
  "ok": true,
  "action": "source.add"
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

## Commands

### `dewey init`

Creates a new Dewey repository in the current directory.

Example:

```bash
dewey init
dewey init --json
```

Behavior:

- Creates `.dewey/`, `sources/`, `indexes/`, `logs/`
- Writes default config, instructions, order file, empty activity log, and search index
- Fails if `.dewey/` already exists

### `dewey status`

Summarizes repository health.

Reports:

- source count
- sources with PDFs
- sources with Markdown ready
- workflow status counts
- ordered source count
- link count
- stale or failed Markdown count
- search index presence and stats

Example:

```bash
dewey status
dewey status --json
```

### `dewey doctor`

Validates repository integrity.

Checks include:

- required top-level files
- required per-source files
- BibTeX parsing
- metadata and state validity
- broken links
- broken review-order references
- PDF content-hash mismatches
- search index openability

Example:

```bash
dewey doctor
dewey doctor --json
```

`doctor` exits nonzero on integrity failure.

### `dewey add source <path>`

Adds a source from a `.bib` or `.pdf` file.

Examples:

```bash
dewey add source refs/paper.bib
dewey add source papers/paper.pdf
dewey add source papers/paper.pdf --no-md
dewey add source papers/paper.pdf --copy
dewey add source papers/paper.pdf --reference
dewey add source papers/paper.pdf --force-duplicate
dewey add source papers/paper.pdf --bibtex-key custom_key
```

#### Adding `.bib`

Behavior:

- Parses exactly one BibTeX entry
- Creates a Dewey source directory
- Writes `entry.bib`, `metadata.json`, `state.json`, `notes.md`, and `links.json`
- Indexes the source and appends an activity log record

#### Adding `.pdf`

Behavior:

- Computes SHA-256 of the file
- Detects exact duplicates via `content_hash`
- Reuses the existing source by default if the PDF hash already exists
- Creates a placeholder BibTeX entry if you do not provide one
- Stores the managed PDF if copy mode is active
- Attempts Markdown generation via `paper2md` unless `--no-md` is passed
- Indexes the source and logs the mutation

Current placeholder BibTeX shape:

- entry type: `misc`
- key: filename-derived slug unless overridden
- title: filename stem
- note: `Imported from PDF; bibliographic fields incomplete`

### `dewey list`

Lists all sources.

Example:

```bash
dewey list
dewey list --json
dewey list --status reading
dewey list --has-pdf
dewey list --has-md
dewey list --ordered
```

Default text columns:

- `source_id`
- `bibtex_key`
- `status`
- `title`
- `year`
- `markdown_status`

### `dewey show <source-id>`

Shows the full record for one source.

Includes:

- paths
- metadata
- state
- BibTeX raw and parsed form
- outgoing and incoming links

Example:

```bash
dewey show src_335517b63c54
dewey show src_335517b63c54 --json
```

### `dewey remove source <source-id>`

Deletes a source from Dewey.

Example:

```bash
dewey remove source src_335517b63c54
dewey remove source src_335517b63c54 --yes --json
```

Behavior:

- deletes the source directory
- removes the source from review order
- removes inbound references from other sources’ links
- updates the index
- appends an activity log record

### `dewey bib show <source-id>`

Prints the canonical BibTeX entry.

```bash
dewey bib show src_335517b63c54
dewey bib show src_335517b63c54 --json
```

### `dewey bib set <source-id> --file <path>`

Replaces the canonical BibTeX entry with the contents of a file containing exactly one entry.

```bash
dewey bib set src_335517b63c54 --file replacement.bib
```

Behavior:

- rewrites `entry.bib`
- refreshes `metadata.json` fields `bibtex_key` and `entry_type`
- updates the search index

### `dewey bib edit <source-id>`

Edits individual BibTeX fields.

Examples:

```bash
dewey bib edit src_335517b63c54 --field title --value "New Title"
dewey bib edit src_335517b63c54 --field year --value 2026
dewey bib edit src_335517b63c54 --field title --value "New Title" --field year --value 2026
dewey bib edit src_335517b63c54 --unset journal
```

Special field names:

- `key`: updates the BibTeX key
- `entry_type`: updates the entry type

Duplicate BibTeX keys are rejected.

### `dewey cite <source-id>`

Outputs citation material.

Formats:

- `--format bibtex` (default)
- `--format key`
- `--format json`

Examples:

```bash
dewey cite src_335517b63c54
dewey cite src_335517b63c54 --format key
dewey cite src_335517b63c54 --format json --json
```

### `dewey state set <source-id> <status>`

Sets the workflow status.

Allowed statuses:

- `unread`
- `queued`
- `reading`
- `read`
- `included`
- `excluded`

Examples:

```bash
dewey state set src_335517b63c54 reading
dewey state set src_335517b63c54 included
```

Behavior:

- updates `state.json`
- sets `included=true` if status is `included`
- sets `included=false` if status is `excluded`

### `dewey state show <source-id>`

Prints `state.json`.

```bash
dewey state show src_335517b63c54
dewey state show src_335517b63c54 --json
```

### `dewey state set-priority <source-id> <int>`

Sets integer priority. Lower numbers mean higher priority by convention.

```bash
dewey state set-priority src_335517b63c54 1
```

### `dewey state mark-read <source-id>`

Convenience command to:

- set status to `read`
- set `last_read_at` to now

```bash
dewey state mark-read src_335517b63c54
```

### `dewey notes show <source-id>`

Prints `notes.md`.

```bash
dewey notes show src_335517b63c54
```

### `dewey notes set <source-id> --file <path>`

Replaces `notes.md` with the contents of a file.

```bash
dewey notes set src_335517b63c54 --file notes.md
```

### `dewey notes edit <source-id> --append <text>`

Appends text plus a trailing newline to `notes.md`.

```bash
dewey notes edit src_335517b63c54 --append "Important baseline."
```

### `dewey link add <from-id> <to-id> --type <type>`

Creates an outgoing logical link.

Allowed link types:

- `builds_on`
- `contradicts`
- `compares_to`
- `uses_method`
- `uses_dataset`
- `motivates`
- `historical_predecessor`
- `same_work_as`
- `version_of`

Examples:

```bash
dewey link add src_a src_b --type builds_on
dewey link add src_a src_b --type compares_to --note "Benchmarks overlap"
```

Duplicate identical links are ignored rather than duplicated.

### `dewey link list <source-id>`

Shows outgoing and incoming links.

Incoming links are computed dynamically by scanning other sources.

```bash
dewey link list src_335517b63c54
dewey link list src_335517b63c54 --json
```

### `dewey link remove <from-id> <to-id> --type <type>`

Removes a matching link.

```bash
dewey link remove src_a src_b --type builds_on
```

### `dewey order show`

Prints the current manual review order.

```bash
dewey order show
dewey order show --json
```

### `dewey order set <source-id>...`

Replaces the entire manual order.

```bash
dewey order set src_a src_b src_c
```

All source IDs must exist and duplicates are rejected.

### `dewey order add <source-id> --before <other-id>`

### `dewey order add <source-id> --after <other-id>`

Moves or inserts a source relative to another source.

```bash
dewey order add src_c --before src_a
dewey order add src_b --after src_a
```

Rules:

- exactly one of `--before` or `--after`
- if the source is already in the order, it is moved

### `dewey order remove <source-id>`

Removes a source from the review order without deleting the source itself.

```bash
dewey order remove src_a
```

### `dewey instructions show`

Prints project-level instructions.

```bash
dewey instructions show
```

### `dewey instructions set --file <path>`

Replaces `instructions.md`.

```bash
dewey instructions set --file review_instructions.md
```

### `dewey instructions append <text>`

Appends text to `instructions.md`.

```bash
dewey instructions append "Keep summaries terse."
```

### `dewey render md <source-id>`

Generates or regenerates Markdown from the source PDF using `paper2md`.

```bash
dewey render md src_335517b63c54
dewey render md src_335517b63c54 --json
```

Behavior:

- fails if the source has no PDF
- tries Python import first: `paper2md.converter.convert`
- falls back to shelling out to the `paper2md` CLI if import is unavailable
- writes `source.md` on success
- updates Markdown status and generator version in metadata
- writes diagnostics to `artifacts/pdf2md.stderr.log`
- updates the search index

### `dewey render md --all`

Regenerates Markdown for every source with a PDF.

```bash
dewey render md --all
```

### `dewey cat <source-id>`

Prints the working representation for a source.

Currently only Markdown representation is supported.

```bash
dewey cat src_335517b63c54
dewey cat src_335517b63c54 --representation md
```

### `dewey path <source-id> --pdf|--md|--notes|--bib`

Returns the path to a selected artifact.

Exactly one selector is required.

Examples:

```bash
dewey path src_335517b63c54 --pdf
dewey path src_335517b63c54 --md
dewey path src_335517b63c54 --notes
dewey path src_335517b63c54 --bib
```

### `dewey search`

Searches the local index.

Default positional search:

```bash
dewey search scaling
```

Field-specific search:

```bash
dewey search --title scaling
dewey search --author vaswani
dewey search --bibtex transformer
dewey search --notes "foundational"
dewey search --fulltext "self-attention"
```

Structured filters:

```bash
dewey search --status reading
dewey search --has-pdf
dewey search --has-md
dewey search --linked-to src_335517b63c54
dewey search --link-type builds_on
```

Filters can be combined:

```bash
dewey search --author smith --status read
```

Current search behavior:

- case-insensitive matching through SQLite FTS5
- title, author, BibTeX text, notes, and Markdown are indexed
- JSON results include simple field/snippet matches

### `dewey index rebuild`

Rebuilds the derived search index from canonical files.

```bash
dewey index rebuild
dewey index rebuild --json
```

### `dewey index stats`

Reports index backend and counts.

```bash
dewey index stats
dewey index stats --json
```

## Workflow examples

### Example 1: Add a BibTeX source and annotate it

```bash
dewey add source refs/paper.bib
dewey list
dewey state set src_123456789abc reading
dewey notes edit src_123456789abc --append "Need to verify evaluation details."
dewey bib edit src_123456789abc --field year --value 2026
dewey show src_123456789abc
```

### Example 2: Add a PDF and render Markdown

```bash
dewey add source papers/method.pdf
dewey show src_abcdef123456
dewey cat src_abcdef123456
dewey path src_abcdef123456 --md
```

If `paper2md` is missing or broken, add still succeeds but Markdown status may be `failed`.

### Example 3: Build a review graph

```bash
dewey add source refs/foundation.bib
dewey add source refs/followup.bib

dewey link add src_followup src_foundation --type builds_on
dewey link list src_foundation
dewey search --linked-to src_foundation
```

### Example 4: Set manual reading order

```bash
dewey order set src_survey src_foundation src_followup
dewey order add src_appendix --after src_followup
dewey order show
```

## JSON reference

This section shows representative `--json` responses for the implemented CLI. Exact timestamps, paths, IDs, and snippets will differ, but the response shapes are stable enough for scripting.

### Project commands

`dewey init --json`

```json
{
  "ok": true,
  "action": "project.init",
  "path": "/path/to/project/.dewey",
  "text": "Initialized Dewey repository at .dewey/"
}
```

`dewey status --json`

```json
{
  "ok": true,
  "action": "project.status",
  "counts": {
    "sources": 2,
    "with_pdf": 1,
    "with_markdown_ready": 1,
    "by_status": {
      "unread": 0,
      "queued": 0,
      "reading": 1,
      "read": 1,
      "included": 0,
      "excluded": 0
    },
    "ordered_sources": 2,
    "total_links": 1,
    "stale_or_failed_markdown": 0
  },
  "index": {
    "exists": true,
    "stats": {
      "backend": "sqlite_fts5",
      "path": "/path/to/project/.dewey/indexes/search.sqlite",
      "sources": 2,
      "links": 1
    }
  },
  "text": "Sources: 2 | PDFs: 1 | Markdown ready: 1 | Ordered: 2 | Links: 1 | Markdown stale/failed: 0"
}
```

`dewey doctor --json`

Success:

```json
{
  "ok": true,
  "action": "project.doctor",
  "issues": [],
  "text": "Doctor found no issues"
}
```

Failure:

```json
{
  "ok": false,
  "action": "project.doctor",
  "issues": [
    {
      "code": "broken_link",
      "source_id": "src_a",
      "target": "src_missing"
    }
  ],
  "text": "Doctor found 1 issue(s)"
}
```

### Source commands

`dewey add source ref.bib --json`

```json
{
  "ok": true,
  "action": "source.add",
  "source_id": "src_335517b63c54",
  "duplicate": false,
  "input_type": "bib",
  "text": "Added source src_335517b63c54"
}
```

`dewey add source paper.pdf --json`

```json
{
  "ok": true,
  "action": "source.add",
  "source_id": "src_9ab4c6158d2f",
  "duplicate": false,
  "input_type": "pdf",
  "text": "Added source src_9ab4c6158d2f"
}
```

Duplicate PDF reuse:

```json
{
  "ok": true,
  "action": "source.add",
  "source_id": "src_9ab4c6158d2f",
  "duplicate": true,
  "reused_source_id": "src_9ab4c6158d2f",
  "text": "Reused existing source src_9ab4c6158d2f"
}
```

`dewey list --json`

```json
{
  "ok": true,
  "action": "source.list",
  "sources": [
    {
      "source_id": "src_335517b63c54",
      "bibtex_key": "smith2024example",
      "status": "reading",
      "title": "Example Paper",
      "year": "2024",
      "markdown_status": "missing",
      "has_pdf": false,
      "has_md": false
    }
  ]
}
```

`dewey show <source-id> --json`

```json
{
  "ok": true,
  "action": "source.show",
  "source": {
    "source_id": "src_335517b63c54",
    "paths": {
      "dir": "/path/to/project/.dewey/sources/src_335517b63c54",
      "bib": "/path/to/project/.dewey/sources/src_335517b63c54/entry.bib",
      "notes": "/path/to/project/.dewey/sources/src_335517b63c54/notes.md",
      "pdf": null,
      "md": null
    },
    "metadata": {
      "source_id": "src_335517b63c54",
      "bibtex_key": "smith2024example",
      "entry_type": "article",
      "managed_pdf_path": null,
      "original_pdf_path": null,
      "content_hash": null,
      "markdown_path": null,
      "markdown_status": "missing",
      "markdown_generator": {
        "name": "paper2md",
        "version": null
      },
      "created_at": "2026-04-09T14:51:38Z",
      "updated_at": "2026-04-09T14:51:38Z",
      "markdown_source": null
    },
    "state": {
      "status": "reading",
      "added_at": "2026-04-09T14:51:38Z",
      "last_read_at": null,
      "included": null,
      "priority": null
    },
    "bibtex": {
      "raw": "@article{smith2024example,\n  title={Example Paper}\n}\n",
      "parsed": {
        "entry_type": "article",
        "key": "smith2024example",
        "fields": {
          "title": "Example Paper"
        }
      }
    },
    "links": {
      "outgoing": [],
      "incoming": []
    }
  }
}
```

`dewey remove source <source-id> --yes --json`

```json
{
  "ok": true,
  "action": "source.remove",
  "source_id": "src_3501a1c87cf3",
  "text": "Removed src_3501a1c87cf3"
}
```

### BibTeX commands

`dewey bib show <source-id> --json`

```json
{
  "ok": true,
  "action": "bib.show",
  "source_id": "src_335517b63c54",
  "raw": "@article{smith2024example,\n  title={Example Paper}\n}\n",
  "parsed": {
    "entry_type": "article",
    "key": "smith2024example",
    "fields": {
      "title": "Example Paper"
    }
  },
  "text": "@article{smith2024example,\n  title={Example Paper}\n}"
}
```

`dewey bib set <source-id> --file replacement.bib --json`

```json
{
  "ok": true,
  "action": "bib.set",
  "source_id": "src_335517b63c54",
  "text": "Updated BibTeX for src_335517b63c54"
}
```

`dewey bib edit <source-id> --field title --value "Revised Book" --json`

```json
{
  "ok": true,
  "action": "bib.edit",
  "source_id": "src_335517b63c54",
  "text": "Edited BibTeX for src_335517b63c54"
}
```

`dewey cite <source-id> --format key --json`

```json
{
  "ok": true,
  "action": "cite.show",
  "source_id": "src_335517b63c54",
  "format": "key",
  "citation": "smith2025book",
  "text": "smith2025book"
}
```

`dewey cite <source-id> --format json --json`

```json
{
  "ok": true,
  "action": "cite.show",
  "source_id": "src_335517b63c54",
  "format": "json",
  "citation": {
    "entry_type": "book",
    "key": "smith2025book",
    "fields": {
      "title": "Revised Book",
      "year": "2026",
      "publisher": "Test Press"
    }
  }
}
```

### State commands

`dewey state set <source-id> reading --json`

```json
{
  "ok": true,
  "action": "state.set",
  "source_id": "src_335517b63c54",
  "status": "reading",
  "text": "Set src_335517b63c54 to reading"
}
```

`dewey state show <source-id> --json`

```json
{
  "ok": true,
  "action": "state.show",
  "source_id": "src_335517b63c54",
  "state": {
    "status": "read",
    "added_at": "2026-04-09T14:51:38Z",
    "last_read_at": "2026-04-09T15:10:00Z",
    "included": true,
    "priority": 3
  },
  "text": "{\n  \"status\": \"read\",\n  ...\n}"
}
```

`dewey state set-priority <source-id> 3 --json`

```json
{
  "ok": true,
  "action": "state.set_priority",
  "source_id": "src_335517b63c54",
  "priority": 3,
  "text": "Set priority for src_335517b63c54 to 3"
}
```

`dewey state mark-read <source-id> --json`

```json
{
  "ok": true,
  "action": "state.mark_read",
  "source_id": "src_335517b63c54",
  "text": "Marked src_335517b63c54 as read"
}
```

### Notes commands

`dewey notes show <source-id> --json`

```json
{
  "ok": true,
  "action": "notes.show",
  "source_id": "src_335517b63c54",
  "notes": "Foundational paper.\n",
  "text": "Foundational paper."
}
```

`dewey notes set <source-id> --file notes.md --json`

```json
{
  "ok": true,
  "action": "notes.set",
  "source_id": "src_335517b63c54",
  "text": "Replaced notes for src_335517b63c54"
}
```

`dewey notes edit <source-id> --append "Important baseline." --json`

```json
{
  "ok": true,
  "action": "notes.edit",
  "source_id": "src_335517b63c54",
  "text": "Appended notes for src_335517b63c54"
}
```

### Link commands

`dewey link add src_b src_a --type builds_on --json`

```json
{
  "ok": true,
  "action": "link.add",
  "from": "src_b",
  "to": "src_a",
  "type": "builds_on",
  "text": "Linked src_b -> src_a"
}
```

`dewey link list src_a --json`

```json
{
  "ok": true,
  "action": "link.list",
  "source_id": "src_a",
  "outgoing": [],
  "incoming": [
    {
      "source_id": "src_b",
      "target": "src_a",
      "type": "builds_on",
      "note": null,
      "created_at": "2026-04-09T14:52:02Z"
    }
  ]
}
```

`dewey link remove src_b src_a --type builds_on --json`

```json
{
  "ok": true,
  "action": "link.remove",
  "from": "src_b",
  "to": "src_a",
  "type": "builds_on",
  "text": "Removed link src_b -> src_a"
}
```

### Order commands

`dewey order show --json`

```json
{
  "ok": true,
  "action": "order.show",
  "order": {
    "strategy": "manual",
    "order": [
      "src_a",
      "src_b"
    ],
    "notes": ""
  },
  "text": "src_a\nsrc_b"
}
```

`dewey order set src_a src_b --json`

```json
{
  "ok": true,
  "action": "order.set",
  "order": [
    "src_a",
    "src_b"
  ],
  "text": "Set order for 2 source(s)"
}
```

`dewey order add src_b --before src_a --json`

```json
{
  "ok": true,
  "action": "order.add",
  "order": [
    "src_b",
    "src_a"
  ],
  "text": "Placed src_b in review order"
}
```

`dewey order remove src_b --json`

```json
{
  "ok": true,
  "action": "order.remove",
  "order": [
    "src_a"
  ],
  "text": "Removed src_b from review order"
}
```

### Instructions commands

`dewey instructions show --json`

```json
{
  "ok": true,
  "action": "instructions.show",
  "instructions": "Review carefully.\nThen summarize.\n",
  "text": "Review carefully.\nThen summarize."
}
```

`dewey instructions set --file review_instructions.md --json`

```json
{
  "ok": true,
  "action": "instructions.set",
  "text": "Updated instructions"
}
```

`dewey instructions append "Keep summaries terse." --json`

```json
{
  "ok": true,
  "action": "instructions.append",
  "text": "Appended instructions"
}
```

### Representation commands

`dewey render md <source-id> --json`

```json
{
  "ok": true,
  "action": "render.md",
  "source_id": "src_9ab4c6158d2f",
  "markdown_status": "ready",
  "text": "Rendered Markdown for src_9ab4c6158d2f"
}
```

`dewey render md --all --json`

```json
{
  "ok": true,
  "action": "render.md",
  "results": [
    {
      "source_id": "src_9ab4c6158d2f",
      "markdown_status": "ready"
    }
  ],
  "text": "Rendered Markdown for 1 source(s)"
}
```

`dewey cat <source-id> --json`

```json
{
  "ok": true,
  "action": "representation.cat",
  "source_id": "src_9ab4c6158d2f",
  "representation": "md",
  "content": "# Title\n\nBody\n",
  "text": "# Title\n\nBody"
}
```

`dewey path <source-id> --bib --json`

```json
{
  "ok": true,
  "action": "path.show",
  "source_id": "src_335517b63c54",
  "path": "/path/to/project/.dewey/sources/src_335517b63c54/entry.bib",
  "text": "/path/to/project/.dewey/sources/src_335517b63c54/entry.bib"
}
```

### Search and index commands

`dewey search Foundational --json`

```json
{
  "ok": true,
  "action": "search.query",
  "query": {
    "query": "Foundational"
  },
  "results": [
    {
      "source_id": "src_335517b63c54",
      "bibtex_key": "smith2024example",
      "title": "Example Paper",
      "status": "reading",
      "matches": [
        {
          "field": "notes",
          "snippet": "Foundational paper. "
        }
      ]
    }
  ]
}
```

`dewey search --author Smith --json`

```json
{
  "ok": true,
  "action": "search.query",
  "query": {
    "author": "Smith"
  },
  "results": [
    {
      "source_id": "src_335517b63c54",
      "bibtex_key": "smith2024example",
      "title": "Example Paper",
      "status": "reading",
      "matches": [
        {
          "field": "bibtex",
          "snippet": "@article{smith2024example,   title={Example Paper},   "
        }
      ]
    }
  ]
}
```

`dewey index rebuild --json`

```json
{
  "ok": true,
  "action": "index.rebuild",
  "stats": {
    "backend": "sqlite_fts5",
    "path": "/path/to/project/.dewey/indexes/search.sqlite",
    "sources": 2,
    "links": 1
  },
  "text": "Rebuilt search index"
}
```

`dewey index stats --json`

```json
{
  "ok": true,
  "action": "index.stats",
  "stats": {
    "backend": "sqlite_fts5",
    "path": "/path/to/project/.dewey/indexes/search.sqlite",
    "sources": 2,
    "links": 1
  },
  "text": "{\n  \"backend\": \"sqlite_fts5\",\n  ...\n}"
}
```

### Common JSON errors

Repository missing:

```json
{
  "ok": false,
  "action": "project.status",
  "error": {
    "code": "repo_not_found",
    "message": "No Dewey repository found in this directory tree"
  }
}
```

Source missing:

```json
{
  "ok": false,
  "action": "source.show",
  "error": {
    "code": "source_not_found",
    "message": "No source exists for src_missing"
  }
}
```

Duplicate BibTeX key:

```json
{
  "ok": false,
  "action": "source.add",
  "error": {
    "code": "duplicate_bibtex_key",
    "message": "BibTeX key 'samekey' already exists in src_335517b63c54"
  }
}
```

Render with no PDF:

```json
{
  "ok": false,
  "action": "render.md",
  "error": {
    "code": "pdf_not_found",
    "message": "No PDF exists for src_335517b63c54"
  }
}
```

## Exit codes

The implementation uses consistent nonzero exits:

- `0`: success
- `1`: generic failure
- `2`: invalid user input or validation error
- `3`: repository integrity or discovery error
- `4`: not found

## Activity log

Every mutating command appends a JSON object to:

```text
.dewey/logs/activity.jsonl
```

Examples of logged actions:

- `source.add`
- `source.remove`
- `bib.set`
- `bib.edit`
- `state.set`
- `notes.edit`
- `link.add`
- `order.set`
- `instructions.set`
- `render.md`
- `index.rebuild`

This log is append-only and intended as a lightweight audit trail.

## Testing

Run the automated test suite with:

```bash
/Users/jjhorton/.pyenv/versions/3.12.7/bin/python3 -m unittest discover -s tests -v
```

Current tests cover:

- repository initialization
- source add/list/show/remove
- BibTeX show/set/edit/cite
- state commands
- notes and instructions commands
- link and order commands
- path lookup
- search and index commands
- JSON error paths
- mocked `paper2md` render integration

## Current implementation notes

There are a few details worth knowing about the current codebase:

- Dewey uses a constrained internal BibTeX parser/writer instead of a third-party BibTeX package.
- `paper2md` integration is implemented, but successful real PDF rendering still depends on the runtime having the necessary backend stack.
- The diagnostics log filename is currently `artifacts/pdf2md.stderr.log` for compatibility with the original spec wording, even though the converter is `paper2md`.
- Search is intentionally simple and local. It is retrieval-only, not semantic reasoning.

## Automation cookbook

This section shows common ways to script Dewey from shells, Python, and JSON pipelines.

### Bash: initialize a repo if needed

```bash
if [ ! -d .dewey ]; then
  dewey init --json
fi
```

### Bash: add a source and capture the new source ID

```bash
SOURCE_JSON="$(dewey add source refs/paper.bib --json)"
SOURCE_ID="$(printf '%s\n' "$SOURCE_JSON" | jq -r '.source_id')"
printf 'Added %s\n' "$SOURCE_ID"
```

### Bash: reuse duplicate PDFs safely

If the PDF is already present, Dewey returns the existing source instead of creating a new one.

```bash
SOURCE_ID="$(
  dewey add source papers/method.pdf --json \
  | jq -r '.source_id'
)"
printf 'Using source %s\n' "$SOURCE_ID"
```

### Bash: mark a paper as reading and append notes

```bash
SOURCE_ID="src_335517b63c54"

dewey state set "$SOURCE_ID" reading --json >/dev/null
dewey notes edit "$SOURCE_ID" --append "Read intro and methods. Revisit appendix." --json >/dev/null
```

### Bash: list all reading-state papers

```bash
dewey list --status reading --json | jq -r '.sources[] | [.source_id, .bibtex_key, .title] | @tsv'
```

### Bash: get the BibTeX key for a source

```bash
dewey cite src_335517b63c54 --format key --json | jq -r '.citation'
```

### Bash: build a reading queue from search

```bash
dewey search --author smith --json \
  | jq -r '.results[].source_id' \
  | xargs dewey order set
```

### Bash: find sources linked to a foundational paper

```bash
FOUNDATION="src_foundation123"
dewey search --linked-to "$FOUNDATION" --json | jq -r '.results[] | .source_id'
```

### Bash: validate repo health in CI

```bash
dewey doctor --json >/tmp/dewey-doctor.json
```

If the command exits nonzero, fail the job and inspect the JSON payload.

### `jq`: list unread titles only

```bash
dewey list --json | jq -r '.sources[] | select(.status == "unread") | .title'
```

### `jq`: map source IDs to titles

```bash
dewey list --json | jq '{sources: [.sources[] | {key: .source_id, value: .title}] | from_entries}'
```

### `jq`: extract search snippets

```bash
dewey search attention --json \
  | jq -r '.results[] | .source_id as $id | .matches[]? | [$id, .field, .snippet] | @tsv'
```

### `jq`: surface broken-doctor issues

```bash
dewey doctor --json | jq -r '.issues[]? | [.code, (.source_id // "-"), (.target // "-")] | @tsv'
```

### Python: run Dewey as a subprocess

```python
import json
import subprocess


def dewey(*args: str) -> dict:
    result = subprocess.run(
        ["dewey", *args, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


payload = dewey("list")
for source in payload["sources"]:
    print(source["source_id"], source["title"])
```

### Python: add a source and update its workflow state

```python
import json
import subprocess


def run_json(*args: str) -> dict:
    result = subprocess.run(
        ["dewey", *args, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


added = run_json("add", "source", "refs/paper.bib")
source_id = added["source_id"]

run_json("state", "set", source_id, "reading")
run_json("notes", "edit", source_id, "--append", "Queued for detailed review.")
```

### Python: handle Dewey failures explicitly

```python
import json
import subprocess


cmd = ["dewey", "show", "src_missing", "--json"]
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    payload = json.loads(result.stdout)
    print(payload["error"]["code"])
    print(payload["error"]["message"])
```

### Python: build a local bibliography manifest

```python
import json
import subprocess


sources = json.loads(
    subprocess.run(
        ["dewey", "list", "--json"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
)["sources"]

manifest = {
    source["source_id"]: {
        "key": source["bibtex_key"],
        "title": source["title"],
        "status": source["status"],
    }
    for source in sources
}
```

### Python: retrieve full source records

```python
import json
import subprocess


def get_source(source_id: str) -> dict:
    result = subprocess.run(
        ["dewey", "show", source_id, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)["source"]


source = get_source("src_335517b63c54")
print(source["metadata"]["bibtex_key"])
print(source["state"]["status"])
```

### Agent-style shell loop: annotate all unordered sources

```bash
dewey list --json \
  | jq -r '.sources[].source_id' \
  | while read -r source_id; do
      if ! dewey order show --json | jq -e --arg id "$source_id" '.order.order | index($id)' >/dev/null; then
        dewey notes edit "$source_id" --append "Needs prioritization." --json >/dev/null
      fi
    done
```

### Rebuild the index after scripted file inspection

If you read files directly and suspect index drift, rebuild explicitly:

```bash
dewey index rebuild --json
```

### Practical scripting guidance

- Prefer `--json` for all automation.
- Check exit codes first, then parse JSON.
- Use `source_id` as the stable identifier in scripts, not the BibTeX key.
- Treat `search.sqlite` and generated Markdown as derived artifacts; canonical data lives in the per-source files.
- If you mutate canonical files outside Dewey, run `dewey doctor` and `dewey index rebuild`.

## Troubleshooting

### `No Dewey repository found in this directory tree`

Run `dewey init` in the project root, or move into a directory beneath an existing Dewey repository.

### `paper2md is not installed`

Install it from GitHub:

```bash
pip install "paper2md @ git+https://github.com/expectedparrot/paper2md.git"
```

### PDF add succeeds but Markdown is missing or failed

Check:

- `.dewey/sources/<source-id>/metadata.json`
- `.dewey/sources/<source-id>/artifacts/pdf2md.stderr.log`

Then confirm that:

- `paper2md` is installed
- its backend dependencies are installed
- the PDF is readable by the converter

### Search seems stale

Rebuild the index:

```bash
dewey index rebuild
```

### `duplicate_bibtex_key`

Dewey currently rejects duplicate BibTeX keys. Update the key in your BibTeX file or use `dewey bib edit <source-id> --field key --value <new-key>`.

## Development

Useful commands:

```bash
python3 -m compileall dewey tests
/Users/jjhorton/.pyenv/versions/3.12.7/bin/python3 -m unittest discover -s tests -v
python3 -m dewey --help
```

If you want the CLI entry point instead of `python -m dewey`, install the package into a venv with `pip install -e .`.
