# Dewey

Collect, annotate, and search a literature workspace. Pull PDFs in, render them to markdown, attach notes, track review state, and tag sources. Use for literature reviews, building a citation database, or maintaining a personal research library.

Core capabilities:
- Initialize a repository under `.dewey/`
- Add BibTeX or PDF sources
- Track reading status, inclusion state, and review priority
- Attach notes and repository-wide instructions
- Render markdown from PDFs
- Link related sources and manage review order
- Search bibliographic records, notes, and generated markdown

Common commands:
- `dewey init`
- `dewey add source paper.bib`
- `dewey add source paper.pdf`
- `dewey status`
- `dewey list`
- `dewey show <source-id>`
- `dewey notes edit <source-id> --append "..."`
- `dewey render md <source-id>`
- `dewey search <query>`
