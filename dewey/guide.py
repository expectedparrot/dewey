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
    dewey discover list
    dewey discover accept <candidate-id>

Prefer stable metadata (DOI, authors, year) and an accessible full text. Do not reject a
paper solely because the PDF is unavailable.

## 3. Read, summarize, and decide

For every source that receives substantive attention, store a short plain-text summary:
the question, approach or evidence, main result, and why it matters to this review. Keep
interpretive detail and quotations in notes. Mark inclusion separately from having read it.

    dewey summary set <source-id> --text "..."
    dewey state set <source-id> included

Summaries should be useful without reopening the paper, but should not overstate findings.
Distinguish the authors' claims from the agent's assessment.

PDF rendering is local through `paper2md` by default. If the user has authorized cloud
upload and `FIRECRAWL_API_KEY` is present, `--backend firecrawl` can use Firecrawl Parse
for OCR and layout-aware Markdown. A key's presence is not itself permission to disclose
a document or incur credits.

## 4. Traverse citations selectively

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

## 5. Iterate until saturation

Use `dewey next` after each material stage. Continue keyword search and citation traversal
while new candidates add concepts, methods, datasets, or contrary evidence. Slow down when
several consecutive relevant papers yield no new useful leads. Before synthesis, resolve
candidate decisions, summarize included sources, inspect contradictory links, and run
`dewey doctor` plus `dewey index rebuild`.
"""
