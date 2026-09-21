import zipfile

import pytest

from dewey.archive import write_project_archive
from dewey.html_export import explorer_payload, write_project_site
from dewey.models import BibEntry, SourceStatus
from dewey.project_readme import END, START, write_project_readme
from dewey.repo import DeweyError, DeweyRepo


def test_readme_summarizes_state_and_preserves_authored_context(tmp_path):
    repo = DeweyRepo.init(tmp_path / 'review')
    source = repo.create_source(BibEntry(entry_type='article', key='paper', fields={'title': 'Paper'}))
    state = repo.load_state(source)
    state.status = SourceStatus.included
    repo.write_state(source, state)
    config = repo.load_config()
    config.research_question = 'Does it work?'
    config.site_url = 'https://research.example/review/'
    repo.write_config(config)
    target = repo.root / 'README.md'
    target.write_text('# Hand-written introduction\nKeep my explanation.\n')
    write_project_site(repo)
    text = target.read_text()
    assert text.startswith('# Hand-written introduction\nKeep my explanation.\n')
    assert 'Does it work?' in text
    assert '[Read the literature explorer](https://research.example/review/)' in text
    assert '| Summary | 0 / 1 |' in text
    assert '1 included' in text
    assert 'Missing reading history does not mean a paper was never read.' in text
    assert text.count(START) == text.count(END) == 1
    (repo.source_dir(source) / 'summary.txt').write_text('Summary')
    target.write_text(text + '\n## My appendix\nKeep this too.\n')
    write_project_readme(repo, explorer_payload(repo))
    text = target.read_text()
    assert '| Summary | 1 / 1 |' in text
    assert text.endswith('\n## My appendix\nKeep this too.\n')
    write_project_readme(repo, explorer_payload(repo))
    assert target.read_text() == text


def test_archive_generates_entry_point_without_inventing_hosting(tmp_path):
    repo = DeweyRepo.init(tmp_path / 'review')
    result = write_project_archive(repo)
    with zipfile.ZipFile(result['path']) as archive:
        readme = archive.read(result['archive_root'] + '/README.md').decode()
    assert '## Review state' in readme
    assert 'No synthesis claims recorded yet.' in readme
    assert 'dewey git site' in readme
    assert 'github.io' not in readme
    assert '/private/' not in readme


def test_readme_rejects_symlinks_and_broken_markers(tmp_path):
    repo = DeweyRepo.init(tmp_path / 'review')
    target = repo.root / 'README.md'
    other = tmp_path / 'other.md'
    other.write_text('Keep')
    target.symlink_to(other)
    data = explorer_payload(repo)
    with pytest.raises(DeweyError, match='symlink'):
        write_project_readme(repo, data)
    assert other.read_text() == 'Keep'
    target.unlink()
    target.write_text('Keep\n' + START)
    with pytest.raises(DeweyError, match='markers'):
        write_project_readme(repo, data)
    assert target.read_text() == 'Keep\n' + START
