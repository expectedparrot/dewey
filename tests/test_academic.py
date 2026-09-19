import json
import urllib.error
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dewey.academic import fetch_page, request_json
from dewey.cli import app
from dewey.models import BibEntry
from dewey.repo import DeweyError, DeweyRepo


@pytest.fixture
def review(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    repo = DeweyRepo.init(tmp_path)
    seed = repo.create_source(BibEntry(entry_type="article", key="seed", fields={
        "title": "Seed paper", "doi": "10.1234/seed",
    }))
    return repo, seed, CliRunner()


def s2_paper(title="A new validation study", doi="10.1234/new"):
    return {"paperId": "new-paper", "title": title, "authors": [{"name": "A. Researcher"}],
            "year": 2026, "externalIds": {"DOI": doi}, "abstract": "New results."}


def invoke(runner, args):
    return runner.invoke(app, [*args, "--json"], catch_exceptions=False)


def test_forward_citations_queue_then_link_in_correct_direction(review):
    repo, seed, runner = review
    response = {"data": [{"citingPaper": s2_paper()}], "next": 50}
    with patch("dewey.academic.request_json", return_value=response) as request:
        result = invoke(runner, ["traverse", "citations", seed, "--provider", "semantic-scholar"])
    assert result.exit_code == 0
    assert request.call_args.args[1].endswith("DOI%3A10.1234%2Fseed/citations")
    payload = json.loads(result.stdout)
    assert payload["next_cursor"] == "50"
    assert payload["complete"] is False
    assert len(repo.list_source_ids()) == 1
    candidate = repo.load_discovery().candidates[0]
    assert candidate.cited_by_source_id is None
    assert len(candidate.provenance) == 1
    assert candidate.provenance[0].source_id == seed
    assert candidate.provenance[0].relation == "citations"
    assert candidate.status == "candidate"
    assert not repo.load_links(seed).outgoing
    invoke(runner, ["discover", "decide", candidate.candidate_id, "--status", "relevant", "--rationale", "Direct validation"])
    result = invoke(runner, ["discover", "accept", candidate.candidate_id])
    new_id = json.loads(result.stdout)["source_id"]
    assert [link.target for link in repo.load_links(new_id).outgoing] == [seed]
    assert not repo.load_links(seed).outgoing


def test_multiple_seeds_and_providers_deduplicate_without_losing_edges(review):
    repo, seed, runner = review
    second_seed = repo.create_source(BibEntry(entry_type="article", key="second", fields={"title": "Second seed"}))
    for provider, parent in [("firecrawl", seed), ("openalex", second_seed)]:
        result = invoke(runner, ["discover", "add", "--title", "A validation study", "--doi", "10.1234/new",
                                 "--via-source", parent, "--relation", "citations", "--provider", provider])
        candidate_id = json.loads(result.stdout)["candidate"]["candidate_id"]
    candidates = repo.load_discovery().candidates
    assert len(candidates) == 1
    assert len(candidates[0].provenance) == 2
    result = invoke(runner, ["discover", "accept", candidate_id])
    new_id = json.loads(result.stdout)["source_id"]
    assert {link.target for link in repo.load_links(new_id).outgoing} == {seed, second_seed}
    assert not repo.load_links(seed).outgoing
    assert not repo.load_links(second_seed).outgoing
    third_seed = repo.create_source(BibEntry(entry_type="article", key="third", fields={"title": "Third seed"}))
    invoke(runner, ["discover", "add", "--title", "A validation study", "--doi", "10.1234/new",
                    "--via-source", third_seed, "--relation", "citations", "--provider", "semantic-scholar"])
    assert len(repo.load_discovery().candidates) == 1
    assert {link.target for link in repo.load_links(new_id).outgoing} == {seed, second_seed, third_seed}


@pytest.mark.parametrize("relation,forward,backward", [("citations", True, False), ("references", False, True), ("related", False, False)])
def test_manual_provenance_directions_and_resolution(review, relation, forward, backward):
    repo, seed, runner = review
    result = invoke(runner, ["discover", "add", "--title", "Another paper", "--via-source", seed, "--relation", relation])
    candidate_id = json.loads(result.stdout)["candidate"]["candidate_id"]
    existing = repo.create_source(BibEntry(entry_type="article", key="existing", fields={"title": "Another paper"}))
    for _ in range(2):
        assert invoke(runner, ["discover", "resolve", candidate_id, existing]).exit_code == 0
    assert len(repo.load_links(existing).outgoing) == int(forward)
    assert len(repo.load_links(seed).outgoing) == int(backward)


def test_openalex_resolution_and_pagination():
    record = {"id": "https://openalex.org/W2", "title": "A paper", "doi": "https://doi.org/10.1/new",
              "authorships": [{"author": {"display_name": "Researcher"}}], "publication_year": 2026,
              "abstract_inverted_index": {"results": [1], "New": [0]}}
    with patch("dewey.academic.request_json", side_effect=[
        {"id": "https://openalex.org/W1"}, {"results": [record], "meta": {"count": 2, "next_cursor": "abc"}},
    ]) as request:
        page = fetch_page("openalex", "question", seed_source_id="src_seed", paper_id="doi:10.1/seed", cursor="previous")
    assert request.call_args.args[2]["filter"] == "cites:W1"
    assert request.call_args.args[2]["cursor"] == "previous"
    assert page.next_cursor == "abc"
    assert not page.complete
    assert page.candidates[0].abstract == "New results"
    assert page.candidates[0].doi == "10.1/new"


def test_firecrawl_uses_paper_index_and_citers_not_similarity():
    payload = {"success": True, "results": [{"paperId": "123", "primaryId": "arxiv:2508.17407",
               "title": "A relevant paper", "ids": {"arxiv": ["2508.17407"]}}], "truncated": False, "poolSize": 8}
    with patch("dewey.academic.request_json", return_value=payload) as request:
        page = fetch_page("firecrawl", "validation", seed_source_id="src_seed", paper_id="arxiv:2401.12345")
    assert request.call_args.args[1].endswith("/arxiv%3A2401.12345/similar")
    assert request.call_args.args[2]["mode"] == "citers"
    assert page.complete is None  # ranked pool does not prove exhaustive traversal
    assert page.candidates[0].url == "https://arxiv.org/abs/2508.17407"
    with patch("dewey.academic.request_json", return_value=payload) as request:
        fetch_page("firecrawl", "validation")
    assert request.call_args.args[1].endswith("/search/research/papers")
    assert request.call_args.args[2]["query"] == "validation"


def test_search_cap_without_cursor_does_not_claim_complete():
    with patch("dewey.academic.request_json", return_value={"data": [s2_paper()], "total": 5000}):
        page = fetch_page("semantic-scholar", "query")
    assert page.next_cursor is None
    assert page.complete is False


def test_failure_is_not_empty_search_and_records_no_candidates(review):
    repo, seed, runner = review
    with patch("dewey.academic.request_json", side_effect=DeweyError("academic_provider_failed", "rate limited")):
        result = invoke(runner, ["traverse", "citations", seed, "--provider", "semantic-scholar"])
    assert result.exit_code != 0
    assert not json.loads(result.stdout)["ok"]
    assert not repo.load_discovery().candidates
    log = json.loads(repo.log_path.read_text().splitlines()[-1])
    assert log["ok"] is False
    with patch("dewey.academic.request_json", return_value={"data": []}):
        result = invoke(runner, ["discover", "search", "nothing", "--provider", "semantic-scholar"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["complete"] is True


def test_bad_provider_page_is_not_partially_imported(review):
    repo, seed, runner = review
    with patch("dewey.academic.request_json", return_value={"data": [s2_paper(), {}]}):
        result = invoke(runner, ["discover", "search", "query", "--provider", "semantic-scholar"])
    assert result.exit_code != 0
    assert not repo.load_discovery().candidates


def test_http_failure_does_not_expose_key(monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "secret-not-for-logs")
    error = urllib.error.HTTPError("https://example.org/?api_key=secret-not-for-logs", 429, "secret-not-for-logs", {}, None)
    with patch("dewey.academic.urllib.request.urlopen", side_effect=error):
        with pytest.raises(DeweyError) as exc:
            request_json("openalex", "https://api.openalex.org/works", {})
    assert "429" in exc.value.message
    assert "secret-not-for-logs" not in exc.value.message


def test_hosted_firecrawl_does_not_send_proxy_key_to_rest(monkeypatch):
    monkeypatch.setenv("FIRECRAWL_API_URL", "https://example.org/mcp")
    with patch("dewey.academic.urllib.request.urlopen") as request:
        with pytest.raises(DeweyError, match="MCP"):
            request_json("firecrawl", "https://api.firecrawl.dev/v2/search/research/papers", {})
    request.assert_not_called()


def test_url_attachment_preserves_source_and_metadata(review):
    repo, seed, runner = review
    with patch("dewey.cli.convert_url_with_firecrawl", return_value=("# Complete paper\n", "v2")) as convert:
        result = invoke(runner, ["add", "document", seed, "https://example.org/paper"])
        assert result.exit_code == 0
        assert invoke(runner, ["add", "document", seed, "https://example.org/paper"]).exit_code == 2
    assert convert.call_count == 1
    assert repo.list_source_ids() == [seed]
    assert repo.load_entry(seed).fields["doi"] == "10.1234/seed"
    assert repo.load_metadata(seed).markdown_source == "https://example.org/paper"
    assert invoke(runner, ["state", "mark-read", seed]).exit_code == 0
    with patch("dewey.cli.convert_url_with_firecrawl", side_effect=DeweyError("failed", "Retrieval failed")):
        assert invoke(runner, ["add", "document", seed, "https://example.org/updated", "--replace"]).exit_code != 0
    assert repo.load_metadata(seed).markdown_source == "https://example.org/paper"
    assert repo.load_state(seed).read_depth == "full-text"
