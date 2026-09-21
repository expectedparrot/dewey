import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dewey.cli import app
from dewey.git_backend import GitProject
from dewey.models import BibEntry
from dewey.repo import DeweyRepo


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def invoke(*args, code=0):
    result = CliRunner().invoke(app, ["git", *args, "--json"], catch_exceptions=False)
    assert result.exit_code == code, result.stdout
    return json.loads(result.stdout)


@pytest.fixture(autouse=True)
def isolated_git(tmp_path, monkeypatch):
    config = tmp_path / "gitconfig"
    config.write_text("[user]\n name = Dewey Test\n email = dewey@example.test\n[init]\n defaultBranch = main\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def project(tmp_path, monkeypatch):
    repo = DeweyRepo.init(tmp_path / "review")
    monkeypatch.chdir(repo.root)
    invoke("init")
    return repo


def add_source(repo, key="seed"):
    return repo.create_source(BibEntry(entry_type="article", key=key, fields={"title": key + " research"}))


def test_init_status_commit_diff_and_ignored_state(project):
    source_id = add_source(project)
    (project.root / ".env").write_text("PRIVATE=yes")
    state = invoke("status")
    assert state["head"] is None
    assert state["summary"]["sources_added"] == 1
    assert "dewey.json" in invoke("diff")["untracked"]
    result = invoke("commit", "-m", "Add seed paper")
    assert result["commit"] == git(project.root, "rev-parse", "HEAD")
    tracked = git(project.root, "ls-files")
    assert "dewey.json" in tracked
    assert ".dewey/" not in tracked
    assert ".env" not in tracked
    assert "docs/index.html" in tracked
    assert "docs/.nojekyll" in tracked
    page = (project.root / "docs/index.html").read_text()
    assert "Expected Parrot" in page
    assert "seed research" in page
    assert invoke("status")["changes"] == []
    assert invoke("commit", "-m", "Nothing", code=2)["error"]["code"] == "git_no_changes"
    (project.source_dir(source_id) / "summary.txt").write_text("A useful finding")
    diff = invoke("diff")
    assert "+A useful finding" in diff["diff"]
    assert diff["summary"]["summaries_changed"] == 1
    invoke("commit", "-m", "Summarize seed")
    assert "A useful finding" in (project.root / "docs/index.html").read_text()


def test_init_flag_enables_git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, ["init", "new-review", "--git", "--json"], catch_exceptions=False)
    assert result.exit_code == 0, result.stdout
    assert Path(json.loads(result.stdout)["git_root"]) == tmp_path / "new-review"


def test_commit_scopes_monorepo_and_preserves_unrelated_staging(tmp_path, monkeypatch):
    git(tmp_path, "init")
    (tmp_path / "unrelated.txt").write_text("first")
    git(tmp_path, "add", "unrelated.txt")
    git(tmp_path, "commit", "-m", "Initial")
    repo = DeweyRepo.init(tmp_path / "reviews" / "with spaces [1]")
    monkeypatch.chdir(repo.root / "sources")
    assert invoke("init")["git_root"] == str(tmp_path)
    assert not (repo.root / ".git").exists()
    (tmp_path / "unrelated.txt").write_text("staged change")
    git(tmp_path, "add", "unrelated.txt")
    invoke("commit", "-m", "Add review")
    assert git(tmp_path, "show", "HEAD:unrelated.txt") == "first"
    assert git(tmp_path, "diff", "--cached", "--name-only") == "unrelated.txt"
    assert invoke("status")["changes"] == []
    assert invoke("status")["repository_clean"] is False
    assert invoke("pull", code=2)["error"]["code"] == "git_dirty"


def test_commit_in_unborn_monorepo_keeps_other_staged_files(tmp_path, monkeypatch):
    git(tmp_path, "init")
    (tmp_path / "outside.txt").write_text("Unrelated initial content")
    git(tmp_path, "add", "outside.txt")
    repo = DeweyRepo.init(tmp_path / "review")
    monkeypatch.chdir(repo.root)
    invoke("commit", "-m", "Review only")
    assert "outside.txt" not in git(tmp_path, "ls-tree", "--name-only", "HEAD")
    assert git(tmp_path, "diff", "--cached", "--name-only") == "outside.txt"


def test_private_files_cannot_be_committed_even_if_force_staged(project):
    path = project.local_dir / "private.txt"
    path.write_text("private")
    git(project.root, "add", "-f", ".dewey/private.txt")
    error = invoke("commit", "-m", "Should fail", code=2)
    assert error["error"]["code"] == "git_private_files_tracked"
    assert GitProject(project).head() is None


def test_validation_refuses_invalid_research_before_commit(project):
    source_id = add_source(project)
    (project.source_dir(source_id) / "links.json").write_text("{broken json")
    error = invoke("commit", "-m", "Invalid", code=3)
    assert error["error"]["code"] == "invalid_project"
    assert GitProject(project).head() is None
    assert git(project.root, "diff", "--cached", "--name-only") == ""


@pytest.fixture
def shared(project, tmp_path):
    source_id = add_source(project)
    invoke("commit", "-m", "Seed")
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    invoke("remote", "add", "origin", str(remote))
    invoke("push", "--remote", "origin")
    clone = tmp_path / "collaborator"
    invoke("clone", str(remote), str(clone))
    return project, DeweyRepo(clone), remote, source_id


def test_clone_push_pull_rebuild_search_and_keep_history(shared, monkeypatch):
    original, clone, remote, source_id = shared
    assert clone.index_db.exists()
    assert clone.stats()["sources"] == 1
    assert invoke("remote", "list")["remotes"][0]["fetch_url"] == str(remote)
    monkeypatch.chdir(clone.root)
    (clone.source_dir(source_id) / "summary.txt").write_text("Replication succeeded")
    invoke("commit", "-m", "Read replication")
    assert invoke("status")["ahead"] == 1
    invoke("push")
    monkeypatch.chdir(original.root)
    before = GitProject(original).head()
    result = invoke("pull")
    assert result["before"] == before
    assert result["after"] != before
    assert (original.source_dir(source_id) / "summary.txt").read_text() == "Replication succeeded"
    assert invoke("status")["behind"] == 0
    result = CliRunner().invoke(app, ["search", "Replication", "--json"], catch_exceptions=False)
    assert json.loads(result.stdout)["results"][0]["source_id"] == source_id
    assert ".dewey" not in git(remote, "ls-tree", "--name-only", "HEAD")


def test_pull_refuses_dirty_and_divergent_work_without_losing_changes(shared, monkeypatch):
    original, clone, remote, source_id = shared
    (original.root / "instructions.md").write_text("Uncommitted work")
    before = GitProject(original).head()
    assert invoke("pull", code=2)["error"]["code"] == "git_dirty"
    assert GitProject(original).head() == before
    invoke("commit", "-m", "Local branch work")
    before = GitProject(original).head()
    monkeypatch.chdir(clone.root)
    (clone.source_dir(source_id) / "summary.txt").write_text("Remote change")
    invoke("commit", "-m", "Remote branch work")
    invoke("push")
    monkeypatch.chdir(original.root)
    error = invoke("pull", code=2)
    assert error["error"]["code"] == "git_failed"
    assert GitProject(original).head() == before
    assert (original.root / "instructions.md").read_text() == "Uncommitted work"
    assert invoke("status")["ahead"] == invoke("status")["behind"] == 1
    remote_head = git(remote, "rev-parse", "HEAD")
    invoke("push", code=2)
    assert git(remote, "rev-parse", "HEAD") == remote_head


def test_pull_reports_invalid_remote_checkout_without_claiming_success(shared, monkeypatch):
    original, clone, _, source_id = shared
    (clone.source_dir(source_id) / "state.json").write_text("{invalid")
    git(clone.root, "add", ".")
    git(clone.root, "commit", "-m", "Invalid external edit")
    git(clone.root, "push")
    monkeypatch.chdir(original.root)
    error = invoke("pull", code=3)
    assert "updated checkout needs repair" in error["error"]["message"]
    assert (original.source_dir(source_id) / "state.json").read_text() == "{invalid"


def test_clone_does_not_overwrite_destination_and_rejects_missing_project(project, tmp_path):
    invoke("commit", "-m", "Initial")
    error = invoke("clone", str(project.root), str(project.root), code=2)
    assert error["error"]["code"] == "git_destination_exists"
    destination = tmp_path / "invalid-clone"
    error = invoke("clone", str(project.root), str(destination), "--project", "missing", code=3)
    assert error["error"]["code"] == "invalid_project"
    assert (destination / "dewey.json").exists()
    assert invoke("clone", str(project.root), str(tmp_path / "escape"), "--project", "../", code=2)["error"]["code"] == "git_invalid_project_path"


def test_clone_project_inside_monorepo(tmp_path, monkeypatch):
    parent = tmp_path / "monorepo"
    parent.mkdir()
    git(parent, "init")
    repo = DeweyRepo.init(parent / "reviews" / "first")
    monkeypatch.chdir(repo.root)
    invoke("commit", "-m", "Add review")
    destination = tmp_path / "cloned-monorepo"
    result = invoke("clone", str(parent), str(destination), "--project", "reviews/first")
    assert result["path"] == str(destination / "reviews" / "first")
    assert result["validated"]


def test_commits_handle_staged_deletions(project):
    source_id = add_source(project)
    invoke("commit", "-m", "Seed")
    (project.root / "extra.txt").write_text("Temporary report")
    invoke("commit", "-m", "Report")
    git(project.root, "rm", "extra.txt")
    invoke("commit", "-m", "Remove report")
    assert "extra.txt" not in git(project.root, "ls-files")
    assert project.load_metadata(source_id)


def test_site_can_be_previewed_and_preserves_existing_non_explorer_page(project):
    docs = project.root / "docs"
    docs.mkdir()
    (docs / "index.html").write_text("<html>My existing homepage</html>")
    error = invoke("site", code=2)
    assert error["error"]["code"] == "site_exists"
    assert (docs / "index.html").read_text() == "<html>My existing homepage</html>"
    (docs / "index.html").rename(docs / "previous.html")
    result = invoke("site")
    assert result["path"] == str(docs / "index.html")
    assert 'name="generator" content="Dewey"' in (docs / "index.html").read_text()
    assert GitProject(project).head() is None


def test_site_rejects_external_symlink(project, tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    (project.root / "docs").symlink_to(external, target_is_directory=True)
    assert invoke("site", code=2)["error"]["code"] == "unsafe_site_path"
    assert not (external / "index.html").exists()


def test_git_commands_outside_a_git_repository_fail_clearly(tmp_path, monkeypatch):
    repo = DeweyRepo.init(tmp_path / "plain-review")
    monkeypatch.chdir(repo.root)
    assert invoke("status", code=2)["error"]["code"] == "git_not_initialized"


def test_push_requires_an_upstream_and_rejects_detached_head(project):
    invoke("commit", "-m", "Initial")
    assert invoke("push", code=2)["error"]["code"] == "git_no_upstream"
    git(project.root, "checkout", "--detach")
    assert invoke("pull", code=2)["error"]["code"] == "git_detached_head"
