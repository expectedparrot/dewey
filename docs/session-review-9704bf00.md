# Silicon-sampling session review

Reviewed 2026-09-19. The main failure is premature evidence synthesis and completion,
with smaller CLI and retrieval problems adding wasted work.

Follow-up implementation: Dewey now owns the expanded provider-selection and
forward-snowballing guidance in `dewey guide`, with API details in
[academic-discovery.md](academic-discovery.md). It also implements academic search,
forward traversal, directional provenance, and URL attachment to existing sources.
ep-agent's literature skill now delegates the research workflow to Dewey; its
Semantic Scholar helper handles provider failures and citation pagination correctly.
PDF retrieval, BibTeX export, and linked HTML report rendering are also implemented;
report citations resolve to internal references with recorded paper URLs and local PDF
assets. The original recommendations and initial implementation snapshot below are
retained as the review record. Current validation: 70 Dewey tests and 13 targeted ep-agent
tests passed, with strict lint passing for the revised skill. Public OpenAlex and
Semantic Scholar citation responses were smoke-tested; Firecrawl uses documented
response fixtures. The runtime dependency still needs a release/pin update.

Evidence inspected:

- [Session transcript](https://www.expectedparrot.com/research-agent/sessions/9704bf00-dd99-48c8-80e4-a42b1880bf78)
- [Final report Markdown](https://www.expectedparrot.com/api/macaw/sessions/9704bf00-dd99-48c8-80e4-a42b1880bf78/files/sessions/topic_silicon-sampling-literature-review/study_a/writeup/report.md)
- [Search log](https://www.expectedparrot.com/api/macaw/sessions/9704bf00-dd99-48c8-80e4-a42b1880bf78/files/sessions/topic_silicon-sampling-literature-review/study_a/literature/search_log.md)
- Dewey checkout at `08f395a` and ep-agent checkout at `f907e53`, especially
  `research_agent/skills/workflow-literature-review/SKILL.md`, its command reference,
  and `scripts/semantic_scholar_search.py`.

The published transcript abbreviates shell commands and omits most successful tool
results. I did not inspect the session's `.dewey` directory or frozen workflow gate
definitions. Accordingly, lack of a visible operation is not proof it never occurred,
and the exact gate implementation used in this session remains unverified. The
evidence does not support a precise latency, token, or cost comparison.

## Findings and recommended changes

| Priority | Evidence | Change | Owner |
|---|---|---|---|
| High | After creating 28 BibTeX entries, the assistant says it will annotate all papers from detailed search information, then declares all included. The two user-suggested additions explicitly use `mark-read --depth abstract`. | Require full-text retrieval, reading depth, separate summaries, located findings, and appraisal before detailed synthesis. Wire a machine-checkable readiness audit into completion. | ep-agent integration; Dewey audit |
| High | No discovery, study, finding, appraisal, claim, or report-audit commands are visible. The ep-agent skill bypasses these existing Dewey features. | Start with `dewey guide`; initialize topic/question; use the discovery queue and explicit screening; run `dewey next` after stages; draft from evidence context. Make the CLI authoritative rather than maintaining a second, incomplete workflow. | ep-agent |
| High | The initial report misses General Social Agents and the critical Toubia work; both arrive through user correction. | Add recent-author searches, searches for contrary evidence, and selective forward/backward citation traversal before declaring saturation. Preserve parent papers and decisions. Do not use a target paper count as a completion criterion. | ep-agent |
| High | The report claims citation snowballing and approximately 130 unique candidates. The visible search log lists query result totals but no deduplicated candidate ledger or citation-traversal record. | Generate methods counts from discovery/screening records. Distinguish papers, empirical studies, reviews, and conceptual sources. Claim only the search procedures actually documented. | ep-agent; future Dewey search ledger |
| Medium | The skill says to add BibTeX and then ingest a URL. The transcript subsequently removes URL-added duplicates. | Attach a retrieved document to the existing source ID. Local PDF attachment already exists. Add URL/Markdown attachment support for existing sources; use DOI/arXiv identities for duplicate detection. Do not delete retrieved sources merely to repair counts. | Dewey and ep-agent |
| Medium | `mark-read` changes an included source's status to `read`, although its `included` boolean stays true. The transcript later repairs an included count for Argyle. | Preserve explicit inclusion/exclusion when recording reading depth; verify both list membership and state. | Dewey, fixed locally |
| Medium | `next` tests PDF paths only and checks retrieval only for sources lacking summaries. | Recognize stored URL Markdown, detect missing files, and prioritize retrieval/reading for included papers even when they already have summaries. | Dewey, fixed locally |
| Medium | The final report pools different error-reduction metrics into a 26–54% range, uses strong universal recommendations, and the FAQ repeats these conclusions. | Preserve metric, denominator, population, benchmark, locator, and limitations for each quantitative claim. Derive practitioner answers from located findings, with applicability caveats. Require deterministic traceability checks even when optional paid review is skipped. | ep-agent |
| Low | `dewey --version` fails and cancels sibling reads at startup. | Support a repository-independent version command and smoke-test the actual pinned CLI in the runtime build. | Dewey fixed locally; ep-agent integration |
| Low | Three parallel Semantic Scholar searches are rate-limited, followed by unavailable WebSearch, then working Firecrawl. | Choose available search tools up front; limit concurrency on constrained APIs; honor backoff and switch providers after a bounded failure. | ep-agent |
| Low | The search helper sleeps after its final 429 retry and returns an empty result for failure. | Avoid the terminal sleep and distinguish provider failure from a successful zero-result search, so outages cannot count toward saturation. | ep-agent |
| Low | The FAQ request triggers plan mode, an agent, and repeated filesystem/build-command searches despite an existing report. | Reuse the known report assets and compilation command for a derivative artifact. Include a short study-comparison table in the initial academic report. | ep-agent |

## Changes implemented in this checkout

- Added `dewey --version` without requiring an initialized review.
- Preserved included/excluded status during `state mark-read`.
- Shared the full-text availability check across reading, `next`, and report audit.
  Ready Markdown counts; missing files do not. Excluded sources no longer generate
  retrieval/summary recommendations.
- Made `next` request missing full text or full-text reading before extraction,
  even if a preliminary summary already exists.
- Added report-readiness issues for an empty included corpus and included sources
  lacking full text, full-text reading records, or summaries.
- Added `dewey report audit --strict --json`, returning exit code 1 for gaps.
  Without `--strict`, the existing informational exit-code behavior remains.
- Updated the CLI guide and README to describe evidence requirements and the strict audit.

The audit validates recorded evidence structure, not whether the agent genuinely read
the paper, whether locators support the claims, or whether the search is exhaustive.
These remain review responsibilities. Abstract-level scoping reviews remain possible;
they should be labeled and must not be presented as complete full-text reviews.

## Initial ep-agent integration recommendations

At the initial review, no ep-agent files had been changed and its dependency pinned
Dewey at `08f395a`. The follow-up above implements the skill and helper changes.
Hosted sessions require publication plus a runtime dependency/lockfile update and deployment.

1. Replace the literature skill's parallel workflow with a short guide-driven sequence.
   Keep the existing full-text requirement, but enforce it through recorded evidence.
   The current skill already prohibits detailed abstract-only synthesis; adding that
   sentence again would not solve this session's failure.
2. Use `dewey report audit --strict --json` as a command verifier for full-review
   completion, alongside repository integrity and report-rendering checks. Verify the
   command is available in the deployed version before freezing a workflow.
3. Correct the BibTeX-plus-URL ingestion instructions; use existing PDF attachment until
   URL attachment is implemented. Do not label unrelated papers `version_of` merely
   because they share authors; use a substantively justified relationship.
4. Add a recorded-session regression evaluation: abstract-only evidence must not pass
   as full review; a missing recent contrary anchor should trigger more discovery;
   source counts must survive repeated reading; metadata-to-full-text ingestion must
   preserve source IDs; provider failures must not be reported as saturation.
5. Add a startup smoke test for `--version`, `guide`, `next`, and the strict report audit
   against the installed pinned package. In this local environment, the bare `dewey`
   executable lacked `guide`, while `python -m dewey` loaded this checkout correctly.
   That local mismatch does not establish which version ran in the hosted session.

## Initial validation

`pytest -q`: 35 passed. `python -m compileall -q dewey` and `git diff --check`
passed. Regression coverage includes URL Markdown, missing stored files, exclusion
and inclusion preservation, abstract-only and empty audit rejection, and a complete
evidence workflow that passes the strict audit. No packaging files changed.
