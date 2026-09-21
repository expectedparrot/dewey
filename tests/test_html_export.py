import json
import re
import shutil

import pytest

from dewey.evidence import EvidenceStore
from dewey.html_export import build_explorer_html, explorer_payload, write_explorer
from dewey.models import BibEntry
from dewey.repo import DeweyError, DeweyRepo


def embedded_payload(path):
    text = path.read_text()
    return json.loads(re.search(r'<script id="dewey-data" type="application/json">(.*?)</script>', text, re.S)[1])


def test_export_preserves_evidence_chain_and_search_coverage(tmp_path):
    repo = DeweyRepo.init(tmp_path / 'review')
    source = repo.create_source(BibEntry(entry_type='article', key='test', fields={'title': 'Test paper'}))
    store = EvidenceStore(repo.root)
    study = store.create_study({'label': 'Experiment', 'design': 'randomized'}, source)
    finding = store.create_finding({
        'outcome': 'Disclosure', 'author_claim': 'Authors claim',
        'evidence_statement': 'Recorded result', 'reviewer_interpretation': 'Limited applicability',
        'locators': [{'page': '12', 'passage': 'Source passage'}],
    }, study.study_id)
    appraisal = store.set_appraisal({
        'framework': 'review', 'dimensions': [], 'overall_judgment': 'limited',
        'applicability': 'Online setting only', 'reviewer': 'Reviewer',
    }, study.study_id)
    theme = store.create_theme({'label': 'Disclosure', 'description': 'Scope'})
    claim = store.create_claim({
        'theme_ids': [theme.theme_id], 'statement': 'Bounded conclusion', 'scope': 'Online setting',
        'evidence': [{'finding_id': finding.finding_id, 'relationship': 'supports', 'rationale': 'Direct evidence'}],
        'confidence': 'low', 'confidence_rationale': 'Single study',
    })
    repo.append_log('discovery.search', query='interviews', complete=False, next_cursor='50')
    repo.append_log('source.private-event', local_path='/private/not-to-publish')
    output = repo.root / 'docs' / 'index.html'
    write_explorer(repo, output)
    data = embedded_payload(output)
    for key, record in [('studies', study), ('findings', finding), ('appraisals', appraisal), ('themes', theme), ('claims', claim)]:
        assert data[key] == [record.model_dump(mode='json')]
    assert data['search_history'][0]['complete'] is False
    assert data['search_history'][0]['next_cursor'] == '50'
    assert len(data['search_history']) == 1
    assert data['studies'][0]['sample_size'] is None
    assert data['sources'][0]['last_read_at'] is None


def test_title_is_stable_after_copy_and_template_tokens_are_literal(tmp_path):
    repo = DeweyRepo.init(tmp_path / 'temporary-name')
    config = repo.load_config()
    config.project_name = None
    config.topic = 'Stable review topic'
    repo.write_config(config)
    shutil.copytree(repo.root, tmp_path / 'other-name')
    assert explorer_payload(DeweyRepo(tmp_path / 'other-name'))['project_name'] == config.topic
    title = '__DATA__ </title><script>alert(1)</script>'
    html = build_explorer_html({'text': '__TITLE__ </script><script>alert(2)</script>'}, title)
    assert '<title>__DATA__ &lt;/title&gt;&lt;script&gt;alert(1)&lt;/script&gt;' in html
    assert '</script><script>alert(2)' not in html
    assert json.loads(re.search(r'type="application/json">(.*?)</script>', html, re.S)[1])['text'].startswith('__TITLE__')


def test_pdf_export_is_portable_and_excludes_private_references(tmp_path):
    repo = DeweyRepo.init(tmp_path / 'review')
    private = tmp_path / 'private.pdf'
    private.write_bytes(b'%PDF private')
    private_id = repo.create_source(BibEntry(entry_type='article', key='private', fields={}), original_pdf_path=str(private))
    source = repo.create_source(BibEntry(entry_type='article', key='archived', fields={}))
    pdf = repo.source_dir(source) / 'source.pdf'
    pdf.write_bytes(b'%PDF archive')
    metadata = repo.load_metadata(source)
    metadata.managed_pdf_path = str(pdf.relative_to(repo.root))
    repo.write_metadata(source, metadata)
    output = repo.root / 'docs' / 'index.html'
    result = write_explorer(repo, output)
    data = {s['source_id']: s for s in embedded_payload(output)['sources']}
    assert data[private_id]['pdf_url'] is None
    assert str(private) not in output.read_text()
    assert len(result['pdf_assets']) == 1
    published = output.parent / data[source]['pdf_url']
    assert published.read_bytes() == pdf.read_bytes()
    shutil.copytree(output.parent, tmp_path / 'moved-site')
    assert (tmp_path / 'moved-site' / data[source]['pdf_url']).is_file()
    # Metadata cannot publish a PDF that points outside the durable corpus.
    pdf.unlink()
    pdf.symlink_to(private)
    write_explorer(repo, output)
    assert next(s for s in embedded_payload(output)['sources'] if s['source_id'] == source)['pdf_url'] is None
    assert not published.exists()


def test_pdf_assets_cannot_escape_through_symlink(tmp_path):
    repo = DeweyRepo.init(tmp_path / 'review')
    source = repo.create_source(BibEntry(entry_type='article', key='paper', fields={}))
    pdf = repo.source_dir(source) / 'source.pdf'
    pdf.write_bytes(b'%PDF archive')
    metadata = repo.load_metadata(source)
    metadata.managed_pdf_path = str(pdf.relative_to(repo.root))
    repo.write_metadata(source, metadata)
    output = repo.root / 'docs' / 'index.html'
    output.parent.mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    (output.parent / 'index.assets').symlink_to(outside, target_is_directory=True)
    with pytest.raises(DeweyError, match='remain beside'):
        write_explorer(repo, output)
    assert list(outside.iterdir()) == []
