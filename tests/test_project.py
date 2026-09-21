import json
import shutil
import subprocess
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from dewey.cli import app
from dewey.evidence import EvidenceStore
from dewey.models import BibEntry, LinkRecord, LinksFile
from dewey.repo import DeweyError, DeweyRepo, find_repo_root, utc_now
from dewey.validation import project_issues


def invoke(*args):
    result = CliRunner().invoke(app, [*args, "--json"], catch_exceptions=False)
    assert result.exit_code == 0, result.stdout
    return json.loads(result.stdout)


def test_named_project_discovery_and_git_tracking(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "my-review"
    root.mkdir()
    (root / ".gitignore").write_text("custom-rule")
    assert invoke("init", "my-review")["path"] == str(root.resolve())
    repo = DeweyRepo(root)
    assert repo.load_config().project_name == "my-review"
    assert find_repo_root(root / "sources") == root.resolve()
    assert (root / ".gitignore").read_text().startswith("custom-rule\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "check-ignore", "-q", ".dewey/cache/search.sqlite"], cwd=root, check=True)
    files = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=root, text=True)
    assert "dewey.json" in files
    assert "discovery/candidates.json" in files
    assert ".dewey/" not in files


def test_init_refuses_to_overwrite_research(tmp_path):
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "keep.txt").write_text("research")
    with pytest.raises(DeweyError, match="Project path already exists"):
        DeweyRepo.init(tmp_path)
    assert (tmp_path / "sources" / "keep.txt").read_text() == "research"
    assert not (tmp_path / "dewey.json").exists()


def test_private_directory_is_not_a_project_marker(tmp_path):
    (tmp_path / ".dewey").mkdir()
    with pytest.raises(DeweyError, match="No Dewey repository"):
        find_repo_root(tmp_path)


def test_copied_project_preserves_research_and_rebuilds_search(tmp_path, monkeypatch):
    repo = DeweyRepo.init(tmp_path / "original")
    seed = repo.create_source(BibEntry(entry_type="article", key="seed", fields={"title": "Original result"}))
    citing = repo.create_source(BibEntry(entry_type="article", key="citing", fields={"title": "Replication"}))
    repo.write_links(citing, LinksFile(outgoing=[LinkRecord(target=seed, type="cites", created_at=utc_now())]))
    EvidenceStore(repo.root).create_study({"label": "Seed experiment", "design": "experiment"}, seed)
    repo.append_log("discovery.search", query="replication", candidate_ids=[], complete=False, next_cursor="50")
    repo.rebuild_index()
    clone_root = tmp_path / "clone"
    shutil.copytree(repo.root, clone_root, ignore=shutil.ignore_patterns(".dewey"))
    clone = DeweyRepo(clone_root)
    monkeypatch.chdir(clone_root / "sources" / seed)
    assert find_repo_root() == clone_root.resolve()
    assert not clone.local_dir.exists()
    assert invoke("search", "Original")["results"][0]["source_id"] == seed
    assert clone.stats()["links"] == 1
    assert clone.load_links(citing).outgoing[0].target == seed
    assert EvidenceStore(clone_root).studies()[0].source_ids == [seed]
    assert json.loads(clone.history_path.read_text())["next_cursor"] == "50"
    # Git checkout/direct edits must not leave search using stale cached content.
    clone.write_entry(seed, BibEntry(entry_type="article", key="seed", fields={"title": "Changed result"}))
    assert invoke("search", "Changed")["results"][0]["source_id"] == seed
    assert invoke("search", "Original")["results"] == []
    assert invoke("doctor")["ok"]


@pytest.mark.parametrize("mode", ["--copy", "--reference"])
def test_pdf_local_paths_and_diagnostics_are_private(tmp_path, monkeypatch, mode):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\nexample")
    repo = DeweyRepo.init(tmp_path / "review")
    monkeypatch.chdir(repo.root)
    with patch("dewey.repo.convert_pdf_with_paper2md", return_value=("# Paper", "test")):
        source_id = invoke("add", "source", str(pdf), mode, "--backend", "paper2md")["source_id"]
    metadata = json.loads((repo.source_dir(source_id) / "metadata.json").read_text())
    assert "original_pdf_path" not in metadata
    assert str(pdf) not in json.dumps(metadata)
    assert repo.load_metadata(source_id).original_pdf_path == str(pdf)
    assert (repo.local_dir / "diagnostics" / source_id / "pdf2md.stderr.log").exists()
    assert not (repo.source_dir(source_id) / "artifacts").exists()
    clone_root = tmp_path / "clone"
    shutil.copytree(repo.root, clone_root, ignore=shutil.ignore_patterns(".dewey"))
    clone = DeweyRepo(clone_root)
    assert clone.load_metadata(source_id).original_pdf_path is None
    assert project_issues(clone) == []
    if mode == "--copy":
        assert (clone.root / metadata["managed_pdf_path"]).read_bytes() == pdf.read_bytes()


def test_mutations_work_after_local_state_is_removed(tmp_path, monkeypatch):
    repo = DeweyRepo.init(tmp_path)
    source_id = repo.create_source(BibEntry(entry_type="article", key="test", fields={"title": "Example"}))
    monkeypatch.chdir(tmp_path)
    shutil.rmtree(repo.local_dir)
    invoke("summary", "set", source_id, "--text", "Durable research")
    assert repo.stats()["sources"] == 1
    shutil.rmtree(repo.local_dir)
    invoke("remove", "source", source_id, "--yes")
    assert repo.stats()["sources"] == 0
