# Dewey repository operating contract

Use the CLI as the workflow source of truth:

```bash
dewey guide
dewey next
```

Run `dewey next` after each material literature-building stage. Candidates are
unverified leads; do not treat them as corpus sources until they are screened and
accepted. Store concise source summaries separately from detailed notes.

Citation traversal is a discovery aid, not an inclusion rule. Preserve the paper
that led to each candidate, review candidates before accepting them, and never
bulk-add a bibliography without relevance screening.

`dewey discover export-triage` creates inspectable records for model-assisted
screening. Construct and inspect EDSL Jobs, models, and estimated costs separately;
obtain user approval before paid execution.

Development checks: run `python -m compileall -q dewey`, `git diff --check`, and
`pytest -q`. Build a wheel when packaging changes and verify it contains only the
canonical `dewey` package and distribution metadata.
