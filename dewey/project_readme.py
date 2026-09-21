"""A generated, reviewable entry point for a shared literature project."""
from __future__ import annotations

import html
from collections import Counter
from typing import Any
from urllib.parse import quote, urlsplit

from dewey.repo import DeweyError, DeweyRepo, atomic_write_text

START = '<!-- dewey:overview:start -->'
END = '<!-- dewey:overview:end -->'


def md(value: Any) -> str:
    """Keep record text literal inside Markdown, including tables and links."""
    text = html.escape(str(value or ''), quote=False).replace('\n', ' ')
    for char in '\\`*_{}[]()#+.!|':
        text = text.replace(char, '\\' + char)
    return text


def readme_content(repo: DeweyRepo, data: dict[str, Any]) -> str:
    sources = data['sources']
    included = [s for s in sources if s['status'] == 'included']
    candidates = Counter(c['status'] for c in data['candidates'])
    statuses = Counter(s['status'] for s in sources)
    represented = {sid for study in data['studies'] for sid in study['source_ids']}
    site_url = repo.load_config().site_url
    parts = urlsplit(site_url or '')
    hosted = site_url if parts.scheme in {'https', 'http'} and parts.netloc and not parts.username else None
    lines = [START, f"# {md(data['project_name'])}", '',
             'A literature review built with [Dewey](https://github.com/expectedparrot/dewey), '
             'with paper records, screening decisions, and findings linked to their sources.', '',
             f"**Research question:** {md(data['research_question'] or 'Not yet recorded.')}", '']
    if hosted:
        lines.extend([f"**[Read the literature explorer]({quote(hosted, safe=':/?=&%#@+~')})**", ''])
    lines.extend(['Read the [review scope and instructions](instructions.md). '
                  'The explorer brings together conclusions, study comparisons, papers, citation links, and screening history.', ''])
    if (repo.root / 'docs/index.html').is_file():
        lines.extend(['To browse offline, download or clone this repository and open `docs/index.html` in a browser. '
                      'Keep `docs/index.assets/` alongside it for PDF links. GitHub displays HTML files as source code.', ''])
    else:
        lines.extend(['Run `dewey git site` inside this project to build the local explorer at `docs/index.html`.', ''])
    lines.extend(['## Review state', '', '| Record | Current state |', '| :--- | :--- |',
                  f"| Papers | {len(sources)} total" + (': ' + ', '.join(f'{n} {status}' for status, n in sorted(statuses.items())) if statuses else '') + ' |',
                  f"| Evidence | {len(data['studies'])} studies · {len(data['findings'])} findings · {len(data['appraisals'])} appraisals |",
                  f"| Synthesis | {len(data['themes'])} themes · {len(data['claims'])} claims "
                  f"({sum(c['status'] == 'reviewed' for c in data['claims'])} reviewed, "
                  f"{sum(c['status'] == 'draft' for c in data['claims'])} draft) |",
                  f"| Screening | {len(data['candidates'])} candidates: " +
                  ', '.join(f"{candidates[status]} {label}" for status, label in [
                      ('added', 'added'), ('rejected', 'rejected'), ('candidate', 'undecided'), ('relevant', 'awaiting addition')]) + ' |',
                  f"| Relationships | {sum(e['type'] == 'cites' for e in data['links'])} citation links · "
                  f"{sum(e['type'] != 'cites' for e in data['links'])} non-citation links |", '',
                  '| Included-paper coverage | Recorded / included |', '| :--- | ---: |'])
    for label, count in [
        ('Summary', sum(bool(s['summary']) for s in included)),
        ('Stored full text (PDF or extracted text)', sum(bool(s['has_pdf'] or s['markdown']) for s in included)),
        ('Study extraction', sum(s['source_id'] in represented for s in included)),
        ('Full-text reading history', sum(bool(s['last_read_at']) and s['read_depth'] == 'full-text' for s in included)),
    ]:
        lines.append(f'| {label} | {count} / {len(included)} |')
    lines.extend(['', 'A paper can contain multiple studies. Candidates are discovery leads, not included evidence; '
                  '“added” counts candidate records, not unique papers. Missing reading history does not mean a paper was never read. '
                  'A resolved screening queue does not establish complete search coverage.', '', '## Recorded conclusions', ''])
    for claim in data['claims']:
        path = 'synthesis/claims/' + quote(claim['claim_id'], safe='') + '.json'
        lines.extend([f"- **{md(claim['statement'])}** Scope: {md(claim['scope'])} "
                      f"Confidence: {md(claim['confidence'])}; {claim['status']}. [Evidence and rationale]({path})."])
    if not data['claims']:
        lines.append('No synthesis claims recorded yet.')
    lines.extend(['', '## Repository guide', '',
                  '| Path | Contents |', '| :--- | :--- |',
                  '| [sources/](sources/) | Bibliography, summaries, detailed notes, stored documents, and paper relationships |',
                  '| [synthesis/](synthesis/) | Studies, findings, appraisals, themes, and claims with evidence links |',
                  '| [discovery/](discovery/) | Candidate queue, screening decisions, provenance, and activity history |',
                  '| [reports/](reports/) | Written reviews and exported reports |',
                  '| `docs/` | Generated explorer and portable PDF assets |',
                  '| [dewey.json](dewey.json) | Project title, research question, and settings |',
                  '| [review_order.json](review_order.json) | Reading order |', '',
                  '`.dewey/` holds private local indexes and machine-specific information and is not shared.', '',
                  '## Continue the review', '',
                  'Install [Dewey](https://github.com/expectedparrot/dewey), then run these commands inside the project:', '',
                  '```sh', 'dewey guide', 'dewey next', 'dewey git status', 'dewey git site', '```', '',
                  'For collaborative work, pull a clean checkout with `dewey git pull`, inspect `dewey git diff`, '
                  'then checkpoint with `dewey git commit -m "Describe the research changes"` and `dewey git push`.', '',
                  'This overview is regenerated by `dewey git site`, `dewey git commit`, and `dewey export zip`. '
                  'Edit the underlying research records to update it; text outside the generated markers is preserved.', END, ''])
    return '\n'.join(lines)


def write_project_readme(repo: DeweyRepo, data: dict[str, Any]) -> str:
    target = repo.root / 'README.md'
    if target.is_symlink():
        raise DeweyError('unsafe_readme_path', 'README.md must not be a symlink', 2)
    existing = target.read_text(encoding='utf-8') if target.exists() else ''
    generated = readme_content(repo, data)
    if START in existing or END in existing:
        if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(START) > existing.index(END):
            raise DeweyError('invalid_readme_markers', 'Repair the Dewey overview markers in README.md before regenerating', 2)
        start, end = existing.index(START), existing.index(END) + len(END)
        result = existing[:start] + generated.rstrip('\n') + existing[end:]
    else:
        result = existing + ('\n\n' if existing else '') + generated
    if result != existing:
        atomic_write_text(target, result)
    return str(target)
