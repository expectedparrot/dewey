# Dewey Agent Guide

Use Dewey when you need to inspect or update a local bibliography repository stored in `.dewey/`.

Recommended workflow:
- Run `dewey agent-start --json` to inspect repository state.
- If no repository exists, initialize one with `dewey init`.
- Add sources with `dewey add source <path>`.
- Inspect progress with `dewey status`, `dewey list`, and `dewey show <source-id>`.
- Capture analysis context with `dewey notes set`, `dewey notes edit`, and `dewey instructions append`.
- Render markdown from PDFs with `dewey render md <source-id>` or `dewey render md --all`.
- Search accumulated material with `dewey search <query>`.

Important conventions:
- Source data lives under `.dewey/sources/<source-id>/`.
- `entry.bib` is the canonical bibliographic record for a source.
- `notes.md` stores review notes.
- `state.json` tracks inclusion, reading status, and priority.
