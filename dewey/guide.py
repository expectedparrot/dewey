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

Firecrawl is the default Markdown backend. For publicly reachable papers, pass the URL
directly to `dewey add source`; Dewey records the URL and saves Firecrawl's Markdown.
Local PDFs can be uploaded with `--backend firecrawl`, or processed with the separately
installed `--backend paper2md`. A key's presence is not itself permission to disclose a
document or incur credits.

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

    dewey report audit
    dewey report article-template --output article.json
    dewey report article-set --file article.json
    dewey report context --output .dewey/synthesis/report-context.json
    dewey report brief --output .dewey/synthesis/article-brief.md
    # Write article.md from the brief, then:
    dewey report render article.md --output article.html

JSON is the canonical machine-readable evidence context. The Markdown brief expands every claim
into findings, study details, appraisal, source metadata, and locators, but does not write prose
on the agent's behalf. The manuscript is canonical Markdown; HTML is a Pandoc rendering.

## 5. Traverse citations selectively

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
"""
