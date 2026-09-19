from __future__ import annotations

import shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

import pytest
from typer.testing import CliRunner

from dewey.cli import app
from dewey.models import BibEntry
from dewey.repo import DeweyError, DeweyRepo
from dewey.reporting import render_with_pandoc, report_citations


class Links(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])


@pytest.fixture
def corpus(tmp_path):
    repo = DeweyRepo.init(tmp_path)
    source_id = repo.create_source(BibEntry(entry_type="article", key="smith2024", fields={
        "author": "Smith, Jane", "title": "Measurement & Evidence", "year": "2024",
        "doi": "10.1234/test", "url": "https://example.org/paper?a=1&b=2",
    }))
    repo.create_source(BibEntry(entry_type="misc", key="other2025", fields={
        "author": "Jones, Sam", "title": "Other Paper", "year": "2025",
    }))
    return repo, source_id


def attach_pdf(repo, source_id):
    pdf = repo.source_dir(source_id) / "source.pdf"
    pdf.write_bytes(b"%PDF-1.4\nTest paper\n%%EOF\n")
    metadata = repo.load_metadata(source_id)
    metadata.managed_pdf_path = str(pdf.relative_to(repo.root))
    metadata.pdf_source_url = "https://example.org/paper.pdf"
    metadata.open_access_url = "https://example.org/open"
    repo.write_metadata(source_id, metadata)
    return pdf


requires_pandoc = pytest.mark.skipif(shutil.which("pandoc") is None, reason="Pandoc integration test")


@requires_pandoc
def test_render_links_citations_to_references_and_portable_pdf(corpus, tmp_path):
    repo, source_id = corpus
    pdf = attach_pdf(repo, source_id)
    manuscript = tmp_path / "drafts" / "report.md"
    manuscript.parent.mkdir()
    manuscript.write_text("# Review\n\n@smith2024 finds a result [@smith2024, p. 7; @other2025].\n")
    output = tmp_path / "export" / "my report.html"
    result = render_with_pandoc(manuscript, output, repo=repo)
    links = Links(output.read_text())
    assert {"#ref-smith2024", "#ref-other2025"} <= set(links.hrefs)
    assert all(unquote(href[1:]) in links.ids for href in links.hrefs if href.startswith("#"))
    assert "https://doi.org/10.1234/test" in links.hrefs
    assert "https://example.org/paper?a=1&b=2" in links.hrefs
    assert "https://example.org/open" in links.hrefs
    assert "https://example.org/paper.pdf" in links.hrefs
    local = f"my%20report.assets/papers/{source_id}.pdf"
    assert local in links.hrefs
    assert (output.parent / unquote(local)).read_bytes() == pdf.read_bytes()
    assert result["citation_keys"] == ["other2025", "smith2024"]
    assert result["pdf_assets"] == [str(output.parent / unquote(local))]
    assert ".dewey" not in output.read_text()
    relocated = tmp_path / "relocated"
    shutil.copytree(output.parent, relocated)
    assert (relocated / unquote(local)).is_file()


@requires_pandoc
def test_unknown_citation_fails_without_replacing_existing_report(corpus, tmp_path):
    repo, source_id = corpus
    attach_pdf(repo, source_id)
    markdown = tmp_path / "report.md"
    markdown.write_text("A result [@smith2024; @invented2026].")
    output = tmp_path / "report.html"
    output.write_text("Existing report")
    with pytest.raises(DeweyError, match="invented2026") as exc:
        render_with_pandoc(markdown, output, repo=repo)
    assert exc.value.code == "unknown_citation"
    assert output.read_text() == "Existing report"
    assert not (tmp_path / "report.assets").exists()


@requires_pandoc
def test_code_examples_are_not_citations_and_uncited_pdfs_not_copied(corpus, tmp_path):
    repo, source_id = corpus
    attach_pdf(repo, source_id)
    markdown = tmp_path / "report.md"
    markdown.write_text("Use `[@invented]`.\n\n```text\n@smith2024\n```\n\nContact a@example.org.\n")
    output = tmp_path / "report.html"
    result = render_with_pandoc(markdown, output, repo=repo)
    assert result["citation_keys"] == []
    assert result["pdf_assets"] == []
    assert "ref-smith2024" not in Links(output.read_text()).ids


@requires_pandoc
def test_missing_local_pdf_does_not_emit_broken_link(corpus, tmp_path):
    repo, source_id = corpus
    attach_pdf(repo, source_id).unlink()
    assert not next(r for r in report_citations(repo) if r["source_id"] == source_id)["has_local_pdf"]
    markdown = tmp_path / "report.md"
    markdown.write_text("A result [@smith2024].")
    output = tmp_path / "report.html"
    result = render_with_pandoc(markdown, output, repo=repo)
    assert result["citation_keys"] == ["smith2024"]
    assert result["pdf_assets"] == []
    assert "https://example.org/paper.pdf" in Links(output.read_text()).hrefs


@requires_pandoc
def test_suppressed_bibliography_cannot_silently_break_links(corpus, tmp_path):
    repo, _ = corpus
    markdown = tmp_path / "report.md"
    markdown.write_text("---\nsuppress-bibliography: true\n---\n\nResult [@smith2024].")
    with pytest.raises(DeweyError) as exc:
        render_with_pandoc(markdown, tmp_path / "report.html", repo=repo)
    assert exc.value.code == "missing_references"


@requires_pandoc
def test_no_corpus_or_citations_still_renders(tmp_path):
    repo = DeweyRepo.init(tmp_path)
    markdown = tmp_path / "report.md"
    markdown.write_text("# Plain report\n\nNo citations.")
    output = tmp_path / "report.html"
    result = render_with_pandoc(markdown, output, repo=repo)
    assert output.is_file()
    assert result["citation_keys"] == []


@requires_pandoc
def test_nocite_can_explicitly_include_uncited_corpus_sources(corpus, tmp_path):
    repo, _ = corpus
    markdown = tmp_path / "report.md"
    markdown.write_text("---\nnocite: '@*'\n---\n\n# Reading list\n")
    result = render_with_pandoc(markdown, tmp_path / "report.html", repo=repo)
    assert result["citation_keys"] == ["other2025", "smith2024"]


@requires_pandoc
def test_custom_style_reference_placement_and_relative_images(corpus, tmp_path):
    repo, _ = corpus
    draft = tmp_path / "draft"
    draft.mkdir()
    (draft / "figure.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><circle r="3"/></svg>'
    )
    manuscript = draft / "report.md"
    manuscript.write_text(
        "# Report\n\nResult [@smith2024].\n\n![Plot](figure.svg)\n\n"
        "# Sources\n\n::: {#refs}\n:::\n\n# Appendix\n\nDetails.\n"
    )
    css = tmp_path / "custom.css"
    css.write_text("body { color: #123456; }")
    csl = tmp_path / "numeric.csl"
    csl.write_text('''<?xml version="1.0" encoding="utf-8"?>
<style xmlns="http://purl.org/net/xbiblio/csl" version="1.0" class="in-text">
<info><title>Test numeric</title><id>https://example.org/style</id>
<updated>2024-01-01T00:00:00Z</updated></info>
<citation><layout prefix="[" suffix="]"><text variable="citation-number"/></layout></citation>
<bibliography><layout><text variable="title"/></layout></bibliography>
</style>''')
    output = tmp_path / "export" / "report.html"
    render_with_pandoc(manuscript, output, css, repo=repo, csl_path=csl)
    rendered = output.read_text()
    assert 'href="#ref-smith2024"' in rendered
    assert "#123456" in rendered
    assert "data:image/svg+xml" in rendered
    assert rendered.index('id="sources"') < rendered.index('id="ref-smith2024"')
    assert rendered.index('id="ref-smith2024"') < rendered.index('id="appendix"')


@requires_pandoc
def test_cli_render_from_project_root_with_relative_paths(corpus, tmp_path, monkeypatch):
    import json

    _, _source_id = corpus
    monkeypatch.chdir(tmp_path)
    Path("writeup").mkdir()
    Path("writeup/report.md").write_text("# Review\n\nResult [@smith2024].")
    result = CliRunner().invoke(app, [
        "report", "render", "writeup/report.md", "--output", "delivery/report.html", "--json",
    ])
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["citation_keys"] == ["smith2024"]
    assert 'href="#ref-smith2024"' in Path(payload["output"]).read_text()
    assert not any("Could not fetch resource" in warning for warning in payload["warnings"])
