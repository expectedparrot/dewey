---
name: dewey
description: >
  Collect, annotate, and search a literature workspace. Pull PDFs in, render
  them to markdown, attach notes, track review state, and tag sources. Use
  for literature reviews, building a citation database, or maintaining a
  personal research library.
tags:
  - bibliography
  - literature-review
  - citations
  - research
invoke: dewey
examples:
  - Building a bibliography from a directory of PDFs with auto-extracted metadata.
  - Tracking review state across a collection of sources for a literature review.
  - Searching a local literature workspace by tag, author, or content.
  - Assembling a citation database for a paper-in-progress.
  - Organizing accumulated PDFs into a searchable, taggable workspace.
---

# dewey — is this the right method?

This file is a **fit check for the calling agent**. Read it to decide
whether **a dewey workspace** is the right home for the user's literature
work. Dewey is closer to a workspace than a "method": it's the place a
research project's reading lives. Implementation details (commands, file
layouts, CLI shape) are out of scope here — those are in the README.

## What the workspace does

Dewey turns a pile of PDFs and BibTeX entries into a structured,
queryable literature workspace:

- **Sources** — each paper gets a stable id, a canonical BibTeX entry,
  and a directory under `.dewey/sources/<id>/` for everything attached
  to it.
- **Rendered markdown** — PDFs are converted to markdown so the contents
  are searchable, quotable, and readable without leaving the terminal.
- **Notes** — per-source notes (`notes.md`) capture what you actually
  learned from the paper, distinct from the paper itself.
- **Review state** — inclusion (in/out of the project), reading status
  (unread / skimmed / read), and review priority are tracked
  explicitly.
- **Tags and links** — sources are tagged and can be cross-linked.
- **Search** — a single query hits BibTeX records, notes, and rendered
  markdown across the workspace.

The discipline this enables: **every claim in the eventual deliverable
is citable, every paper is findable, every read is tracked.** No more
"I know I read something about that" with no idea where.

## Use this when

- The user is **starting a literature review** and expects to handle
  more than a handful of sources.
- The user is **building a citation database** for a paper, thesis,
  grant, or report — they need a stable bibliography that grows over
  weeks or months.
- The user is **assembling sources for a research agenda** — a recurring
  workspace they'll come back to.
- The user has **accumulated a directory of PDFs** and wants them
  organized, tagged, and searchable rather than living in Downloads.
- The user wants to **track which papers they've actually read** versus
  just downloaded — review state matters.
- The user wants notes and bibliographic records to **travel together**
  so the next time they cite a paper they don't re-read it from scratch.

## Do not use when

- The user is doing **one-off reading** — a single paper for a meeting,
  a quick scan of two articles. Dewey's overhead does not pay off.
- The user wants to **search a corpus they don't yet have**. Dewey
  assumes you've collected the sources; it isn't a discovery tool. For
  online discovery use a different tool (web search, semantic-scholar,
  etc.) and bring results into dewey afterward.
- The deliverable is **qualitative coding of corpus content** —
  applying a coding scheme to extract themes or claims across documents.
  See `recipe:bewley`.
- The user wants **statistical meta-analysis** — extracting effect sizes
  and pooling them across studies. That's a different toolset entirely
  (R `metafor`, Stata, etc.).
- The user wants a **shared, multi-author bibliography** with web UI
  and citation-key sync. Dewey is filesystem-backed and single-user;
  Zotero or similar fits better.

## When tagging vs notes vs review-state matters

Dewey's three first-class annotations earn their keep in different
situations. A workspace that uses none of them is just a folder of PDFs.

- **Tags** earn their keep when sources fall into **>2 thematic
  buckets** the user will want to filter by later (method, topic,
  region, era). For a 10-paper bibliography on one tight topic, tags
  are noise. For a 100-paper review spanning subfields, tags are how
  the user navigates.
- **Notes** earn their keep when the user needs to **cite a specific
  argument or finding** later, not just the paper. If the user only
  ever cites the paper as a whole, notes are optional. If the user is
  going to write "Smith (2019) shows X" and needs to remember exactly
  what X was without re-reading, notes are essential.
- **Review state** earns its keep when the workspace contains **more
  papers than the user can hold in their head** — reading status
  (unread / skimmed / read) and inclusion (in / out of the project)
  prevent re-reading the same paper twice and prevent forgetting why
  a paper was excluded.

Use all three for a serious literature review. Use only the rendered
markdown + search for a smaller, faster project.

## Decision rule for the calling agent

Before dispatching to dewey, confirm:

1. There is a **collection of sources** (or one is being assembled),
   not a single paper.
2. The user expects to **return to this collection over time**, not
   read once and discard.
3. The work is **organizing and citing** sources, not coding their
   content thematically and not pooling effect sizes statistically.

If all three hold, dewey is the right workspace. If the user only has
one paper, send them away with a "you don't need this yet." If they
want thematic coding, route to `recipe:bewley`. If they want
meta-analysis, route to a statistical toolset.
