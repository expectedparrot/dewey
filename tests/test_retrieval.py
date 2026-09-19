import io
import json
import urllib.error
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dewey.models import BibEntry, MarkdownStatus
from dewey.repo import DeweyRepo, sha256_file
from dewey.retrieval import fetch_source_pdf, source_urls
from dewey.cli import app


PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n"


class Response(io.BytesIO):
    def __init__(self, body, url, content_type="application/pdf", content_length=None):
        super().__init__(body)
        self.url = url
        self.headers = {"Content-Type": content_type, "Content-Length": str(content_length or len(body))}

    def geturl(self):
        return self.url


@pytest.fixture
def review(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = DeweyRepo.init(tmp_path)
    source = repo.create_source(BibEntry(entry_type="article", key="example2026", fields={
        "title": "Example Paper", "author": "Researcher, Alice", "year": "2026",
        "doi": "10.1234/example", "url": "https://example.org/paper",
    }))
    metadata = repo.load_metadata(source)
    metadata.open_access_url = "https://example.org/open.pdf"
    repo.write_metadata(source, metadata)
    return repo, source, CliRunner()


def test_download_prioritizes_open_access_and_preserves_bibtex(review):
    repo, source, runner = review
    before = (repo.source_dir(source) / "entry.bib").read_text()
    with patch("dewey.retrieval.urllib.request.urlopen", return_value=Response(PDF, "https://cdn.example.org/paper.pdf")) as get:
        result = fetch_source_pdf(repo, source)
    assert get.call_args.args[0].full_url == "https://example.org/open.pdf"
    assert result["ok"]
    assert (repo.source_dir(source) / "source.pdf").read_bytes() == PDF
    metadata = repo.load_metadata(source)
    assert metadata.content_hash == sha256_file(repo.source_dir(source) / "source.pdf")
    assert metadata.pdf_source_url == "https://cdn.example.org/paper.pdf"
    assert metadata.pdf_retrieved_at
    assert metadata.pdf_retrieval_status == "downloaded"
    assert (repo.source_dir(source) / "entry.bib").read_text() == before
    assert repo.load_state(source).read_depth is None
    with patch("dewey.retrieval.urllib.request.urlopen") as get:
        assert fetch_source_pdf(repo, source)["status"] == "already_present"
    get.assert_not_called()


def test_landing_page_metadata_resolves_against_redirect_not_requested_url(review):
    repo, source, runner = review
    page = b'<html><head><meta name="citation_pdf_url" content="../pdf/paper.pdf"></head></html>'
    with patch("dewey.retrieval.urllib.request.urlopen", side_effect=[
        Response(page, "https://publisher.example.org/article/123", "text/html"),
        Response(PDF, "https://publisher.example.org/pdf/paper.pdf"),
    ]) as get:
        result = fetch_source_pdf(repo, source)
    assert result["ok"]
    assert get.call_args.args[0].full_url == "https://publisher.example.org/pdf/paper.pdf"
    assert [attempt["outcome"] for attempt in result["attempts"]] == ["landing_page", "downloaded"]


def test_paywall_or_html_disguised_as_pdf_does_not_corrupt_source(review):
    repo, source, runner = review
    metadata = repo.load_metadata(source)
    metadata.markdown_status = MarkdownStatus.ready
    metadata.markdown_path = str((repo.source_dir(source) / "source.md").relative_to(repo.root))
    repo.write_metadata(source, metadata)
    (repo.source_dir(source) / "source.md").write_text("Existing full text")
    def response(request, **kwargs):
        return Response(b"<html>Please sign in</html>", request.full_url)
    with patch("dewey.retrieval.urllib.request.urlopen", side_effect=response):
        result = fetch_source_pdf(repo, source)
    assert not result["ok"]
    assert not (repo.source_dir(source) / "source.pdf").exists()
    assert repo.load_metadata(source).markdown_status == "ready"
    assert repo.load_metadata(source).pdf_retrieval_status == "unavailable"
    assert repo.load_metadata(source).pdf_last_attempt_at
    assert (repo.source_dir(source) / "source.md").read_text() == "Existing full text"
    assert json.loads(repo.log_path.read_text().splitlines()[-1])["attempts"]


@pytest.mark.parametrize("body", [b"%PDF-1.4\ntruncated", PDF * 2])
def test_incomplete_or_oversized_pdf_leaves_no_file(review, body):
    repo, source, runner = review
    with patch("dewey.retrieval.MAX_PDF_BYTES", len(PDF)):
        with patch("dewey.retrieval.urllib.request.urlopen", side_effect=lambda request, **kwargs: Response(body, request.full_url)):
            result = fetch_source_pdf(repo, source)
    assert not result["ok"]
    assert not (repo.source_dir(source) / "source.pdf").exists()
    assert not list(repo.source_dir(source).glob(".pdf-download-*"))


def test_pdf_links_are_bounded_and_cited_pdfs_are_not_followed(review):
    repo, source, runner = review
    page = b'<html><a href="https://unrelated.example.org/cited.pdf">Reference</a></html>'
    with patch("dewey.retrieval.urllib.request.urlopen", side_effect=lambda request, **kwargs: Response(page, request.full_url, "text/html")) as get:
        result = fetch_source_pdf(repo, source)
    assert not result["ok"]
    assert all("unrelated" not in call.args[0].full_url for call in get.call_args_list)
    with patch("dewey.retrieval.MAX_ATTEMPTS", 2):
        with patch("dewey.retrieval.urllib.request.urlopen", side_effect=lambda request, **kwargs: Response(
            b'<html><meta name="citation_pdf_url" content="/next?x=' + str(len(request.full_url)).encode() + b'"></html>',
            request.full_url, "text/html",
        )) as get:
            result = fetch_source_pdf(repo, source)
    assert get.call_count <= 2
    assert not result["ok"]


def test_arxiv_url_preserves_version(review):
    repo, source, runner = review
    urls = source_urls(repo, source, "https://arxiv.org/abs/2508.17407v5")
    assert urls[:2] == ["https://arxiv.org/pdf/2508.17407v5", "https://arxiv.org/abs/2508.17407v5"]


def test_fetch_command_failure_is_explicit_and_next_suggests_fallback(review):
    repo, source, runner = review
    runner.invoke(app, ["topic", "set", "--topic", "Tests", "--question", "What works?"])
    runner.invoke(app, ["state", "set", source, "included"])
    error = urllib.error.HTTPError("https://example.org", 404, "Not found", {}, None)
    with patch("dewey.retrieval.urllib.request.urlopen", side_effect=error):
        result = runner.invoke(app, ["fetch", "pdf", source, "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["status"] == "unavailable"
    next_step = json.loads(runner.invoke(app, ["next", "--json"]).stdout)
    assert next_step["phase"] == "retrieve"
    assert next_step["next_steps"][0].startswith(f"dewey add document {source}")
    assert repo.load_state(source).status == "included"


def test_missing_urls_returns_unavailable_without_request(review):
    repo, _, runner = review
    source = repo.create_source(BibEntry(entry_type="misc", key="no_url", fields={"title": "Metadata only"}))
    with patch("dewey.retrieval.urllib.request.urlopen") as get:
        result = fetch_source_pdf(repo, source)
    assert not result["ok"]
    assert result["attempts"] == []
    get.assert_not_called()


def test_accept_with_pdf_failure_keeps_generated_bibtex_and_url(review):
    repo, _, runner = review
    candidate = json.loads(runner.invoke(app, ["discover", "add", "--title", "Screened Study", "--author", "Smith, A.",
                                            "--year", "2026", "--doi", "10.1234/screened", "--url", "https://example.org/study",
                                            "--json"]).stdout)["candidate"]
    error = urllib.error.HTTPError("https://example.org/study", 403, "Forbidden", {}, None)
    with patch("dewey.retrieval.urllib.request.urlopen", side_effect=error):
        result = runner.invoke(app, ["discover", "accept", candidate["candidate_id"], "--fetch-pdf", "--json"])
    assert result.exit_code == 0
    accepted = json.loads(result.stdout)
    assert accepted["ok"]
    assert accepted["pdf_retrieval"]["status"] == "unavailable"
    entry = repo.load_entry(accepted["source_id"])
    assert entry.fields["author"] == "Smith, A."
    assert entry.fields["url"] == "https://example.org/study"
    assert entry.fields["doi"] == "10.1234/screened"
    assert repo.load_discovery().candidates[0].status == "added"
    cited = runner.invoke(app, ["cite", accepted["source_id"], "--format", "bibtex"])
    assert "title={Screened Study}" in cited.stdout


def test_accept_preserves_open_access_url_and_downloads(review):
    repo, _, runner = review
    candidate = json.loads(runner.invoke(app, ["discover", "add", "--title", "Open study", "--json"]).stdout)["candidate"]
    discovery = repo.load_discovery()
    discovery.candidates[0].open_access_url = "https://example.org/oa.pdf"
    repo.write_discovery(discovery)
    with patch("dewey.retrieval.urllib.request.urlopen", return_value=Response(PDF, "https://example.org/oa.pdf")):
        result = runner.invoke(app, ["discover", "accept", candidate["candidate_id"], "--fetch-pdf", "--json"])
    payload = json.loads(result.stdout)
    assert payload["pdf_retrieval"]["ok"]
    assert repo.load_metadata(payload["source_id"]).open_access_url == "https://example.org/oa.pdf"
    assert repo.load_entry(payload["source_id"]).fields["url"] == "https://example.org/oa.pdf"


def test_bibtex_export_uses_included_sources_and_review_order(review):
    repo, source, runner = review
    second = repo.create_source(BibEntry(entry_type="book", key="other2025", fields={"title": "Other Study", "year": "2025"}))
    repo.create_source(BibEntry(entry_type="article", key="excluded", fields={"title": "Unreviewed Study"}))
    runner.invoke(app, ["discover", "add", "--title", "Unverified Candidate"])
    for source_id in (source, second):
        runner.invoke(app, ["state", "set", source_id, "included"])
    runner.invoke(app, ["order", "set", second, source])
    result = runner.invoke(app, ["export", "bibtex", "--status", "included", "--output", "exports/references.bib", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["sources"] == 2
    exported = (repo.root / "exports/references.bib").read_text()
    assert exported.startswith("@book{other2025,")
    assert "@article{example2026," in exported
    assert "doi={10.1234/example}" in exported
    assert "Unreviewed" not in exported
    assert "Unverified" not in exported
