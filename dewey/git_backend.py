"""Git transport for ordinary Dewey project files; no alternate storage format."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from dewey.html_export import write_project_site
from dewey.repo import DeweyError, DeweyRepo
from dewey.validation import project_issues


def run_git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except FileNotFoundError as exc:
        raise DeweyError("git_unavailable", "Install Git to use dewey git", 2) from exc
    if check and result.returncode:
        raise DeweyError("git_failed", result.stderr.strip() or result.stdout.strip() or "Git command failed", 2)
    return result


def private_path(path: str) -> bool:
    parts = Path(path).parts
    return any(part in {".dewey", ".git"} for part in parts) or any(
        part == ".env" or (part.startswith(".env.") and part != ".env.example") or part.endswith(".dewey.zip")
        for part in parts
    )


def validate_project(repo: DeweyRepo, operation: str) -> None:
    issues = project_issues(repo)
    if issues:
        detail = json.dumps(issues, ensure_ascii=False)
        raise DeweyError(
            "invalid_project", f"{operation}: project validation failed. Run dewey doctor --json. Issues: {detail}", 3,
        )


class GitProject:
    def __init__(self, repo: DeweyRepo) -> None:
        self.repo = repo
        result = run_git(repo.root, "rev-parse", "--show-toplevel", check=False)
        if result.returncode:
            raise DeweyError("git_not_initialized", "Run dewey git init to enable Git for this project", 2)
        self.root = Path(result.stdout.strip()).resolve()
        self.prefix = repo.root.relative_to(self.root).as_posix()
        self.scope = ":/" if self.prefix == "." else ":(top,literal)" + self.prefix

    @classmethod
    def init(cls, repo: DeweyRepo) -> "GitProject":
        # Reuse an enclosing repository instead of silently creating a nested one.
        if run_git(repo.root, "rev-parse", "--show-toplevel", check=False).returncode:
            run_git(repo.root, "init")
        return cls(repo)

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return run_git(self.root, *args, check=check)

    def head(self) -> str | None:
        result = self.git("rev-parse", "--verify", "HEAD", check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    def branch(self) -> str | None:
        result = self.git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    def _project_path(self, path: str) -> str:
        return path if self.prefix == "." else path.removeprefix(self.prefix + "/")

    def _repo_path(self, path: str) -> str:
        return path if self.prefix == "." else self.prefix + "/" + path

    def _changes(self, *, entire_repo: bool = False) -> list[dict[str, str]]:
        args = ["status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames"]
        if not entire_repo:
            args.extend(["--", self.scope])
        records = self.git(*args).stdout.split("\0")
        return [
            {"status": record[:2], "path": record[3:] if entire_repo else self._project_path(record[3:])}
            for record in records if record
        ]

    def _check_operation(self) -> None:
        for name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
            path = Path(self.git("rev-parse", "--git-path", name).stdout.strip())
            if not path.is_absolute():
                path = self.root / path
            if path.exists():
                raise DeweyError("git_operation_in_progress", "Finish or abort the current Git operation first", 2)

    def _check_clean(self) -> None:
        self._check_operation()
        if self._changes(entire_repo=True):
            raise DeweyError(
                "git_dirty", "Commit or stash changes in the containing Git repository before pulling or pushing", 2,
            )
        if not self.branch():
            raise DeweyError("git_detached_head", "Check out a branch before pulling or pushing", 2)

    def _check_private_files(self) -> None:
        tracked = self.git("ls-files", "-z", "--", self.scope).stdout.split("\0")
        paths = [self._project_path(path) for path in tracked if path and private_path(self._project_path(path))]
        if paths:
            raise DeweyError(
                "git_private_files_tracked",
                "Untrack local/private files before committing or pushing: " + ", ".join(paths), 2,
            )

    def _old_json(self, path: str) -> dict[str, Any]:
        result = self.git("show", "HEAD:" + self._repo_path(path), check=False)
        try:
            value = json.loads(result.stdout)
            return value if isinstance(value, dict) else {}
        except ValueError:
            return {}

    def research_summary(self, changes: list[dict[str, str]]) -> dict[str, int]:
        summary = {"sources_added": 0, "sources_removed": 0, "summaries_changed": 0,
                   "notes_changed": 0, "graphs_changed": 0, "synthesis_records_changed": 0,
                   "candidates_added": 0, "candidates_accepted": 0}
        for change in changes:
            path = Path(change["path"])
            if path.parts[0] == "sources":
                if path.name == "entry.bib":
                    if change["status"] in {"??", "A ", "AM"}:
                        summary["sources_added"] += 1
                    elif "D" in change["status"]:
                        summary["sources_removed"] += 1
                for name, key in [("summary.txt", "summaries_changed"), ("notes.md", "notes_changed"),
                                  ("links.json", "graphs_changed")]:
                    if path.name == name:
                        summary[key] += 1
            if path.parts[0] == "synthesis" and path.suffix == ".json":
                summary["synthesis_records_changed"] += 1
        if any(change["path"] == "discovery/candidates.json" for change in changes):
            previous = {c["candidate_id"]: c for c in self._old_json("discovery/candidates.json").get("candidates", [])}
            try:
                current = self.repo.load_discovery().candidates
                summary["candidates_added"] = sum(c.candidate_id not in previous for c in current)
                summary["candidates_accepted"] = sum(
                    c.status == "added" and previous.get(c.candidate_id, {}).get("status") != "added" for c in current
                )
            except (DeweyError, ValueError, OSError):
                pass  # Status remains useful for inspecting malformed working files.
        return summary

    def status(self) -> dict[str, Any]:
        changes = self._changes()
        upstream = self.git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False)
        ahead = behind = None
        if upstream.returncode == 0 and self.head():
            counts = self.git("rev-list", "--left-right", "--count", "HEAD...@{upstream}").stdout.split()
            ahead, behind = map(int, counts)
        return {"project_root": str(self.repo.root), "git_root": str(self.root), "branch": self.branch(),
                "head": self.head(), "upstream": upstream.stdout.strip() if upstream.returncode == 0 else None,
                "ahead": ahead, "behind": behind, "changes": changes,
                "repository_clean": not self._changes(entire_repo=True),
                "summary": self.research_summary(changes)}

    def diff(self) -> dict[str, Any]:
        self._check_private_files()
        status = self.status()
        args = ["diff", "--no-ext-diff", "--no-textconv", "--no-color"]
        # An unborn branch has no HEAD; its initial diff is the staged content.
        args.append("HEAD" if self.head() else "--cached")
        patch = self.git(*args, "--", self.scope).stdout
        return {**status, "diff": patch,
                "untracked": [c["path"] for c in status["changes"] if c["status"] == "??"]}

    def commit(self, message: str) -> dict[str, Any]:
        if not message.strip():
            raise DeweyError("git_empty_message", "Provide a nonempty commit message", 2)
        self._check_operation()
        self._check_private_files()
        changes = self._changes()
        if any("U" in c["status"] or c["status"] in {"AA", "DD"} for c in changes):
            raise DeweyError("git_unmerged", "Resolve Git conflicts before committing", 2)
        paths = [self._repo_path(c["path"]) for c in changes if not private_path(c["path"])]
        if not paths:
            raise DeweyError("git_no_changes", "No project changes to commit", 2)
        validate_project(self.repo, "Commit refused")
        site = write_project_site(self.repo)
        changes = self._changes()
        paths = [self._repo_path(c["path"]) for c in changes if not private_path(c["path"])]
        # Literal paths protect names containing Git pathspec syntax. --only preserves
        # staged changes elsewhere in an enclosing repository.
        specs = [":(top,literal)" + self._repo_path(c["path"]) for c in changes
                 if not private_path(c["path"]) and c["status"] != "D "]
        if specs:
            self.git("add", "--all", "--", *specs)
        summary = self.research_summary(changes)
        self.git("commit", "--only", "-m", message, "--", self.scope)
        return {"commit": self.head(), "files": len(paths), "summary": summary, "site": site["path"]}

    def remotes(self) -> list[dict[str, str]]:
        return [{"name": name, "fetch_url": self.git("remote", "get-url", name).stdout.strip(),
                 "push_url": self.git("remote", "get-url", "--push", name).stdout.strip()}
                for name in self.git("remote").stdout.splitlines()]

    def add_remote(self, name: str, url: str) -> None:
        if name.startswith("-") or url.startswith("-"):
            raise DeweyError("git_invalid_remote", "Remote names and URLs cannot start with '-'", 2)
        self.git("remote", "add", name, url)

    def pull(self) -> dict[str, Any]:
        self._check_clean()
        before = self.head()
        self.git("pull", "--no-rebase", "--ff-only")
        # Validation failures leave the fetched checkout intact and inspectable.
        validate_project(self.repo, "Pull completed, but the updated checkout needs repair")
        return {"before": before, "after": self.head(), "validated": True, "git_root": str(self.root)}

    def push(self, remote: str | None = None) -> dict[str, Any]:
        self._check_clean()
        self._check_private_files()
        validate_project(self.repo, "Push refused")
        if not self.head():
            raise DeweyError("git_no_commits", "Commit the project before pushing", 2)
        if remote is not None:
            if remote not in {item["name"] for item in self.remotes()}:
                raise DeweyError("git_unknown_remote", "Choose a configured remote from dewey git remote list", 2)
            self.git("push", "--no-follow-tags", "--set-upstream", "--", remote, "HEAD:refs/heads/" + str(self.branch()))
        else:
            # Explicit upstream avoids push.default=matching publishing other branches.
            branch = self.branch()
            upstream_remote = self.git("config", "--get", f"branch.{branch}.remote", check=False).stdout.strip()
            upstream_ref = self.git("config", "--get", f"branch.{branch}.merge", check=False).stdout.strip()
            if not upstream_remote or not upstream_ref:
                raise DeweyError("git_no_upstream", "Set an upstream with dewey git push --remote origin", 2)
            self.git("push", "--no-follow-tags", "--", upstream_remote, "HEAD:" + upstream_ref)
        return {"commit": self.head(), "git_root": str(self.root), "branch": self.branch()}


def clone_project(url: str, destination: Path, project: Path = Path(".")) -> DeweyRepo:
    destination = destination.resolve()
    if destination.exists():
        raise DeweyError("git_destination_exists", f"Clone destination already exists: {destination}", 2)
    if url.startswith("-"):
        raise DeweyError("git_invalid_remote", "Repository URL cannot start with '-'", 2)
    root = (destination / project).resolve()
    if not root.is_relative_to(destination):
        raise DeweyError("git_invalid_project_path", "--project must be a path inside the cloned repository", 2)
    destination.parent.mkdir(parents=True, exist_ok=True)
    run_git(destination.parent, "clone", "--", url, str(destination))
    root = (destination / project).resolve()
    if not root.is_relative_to(destination):
        raise DeweyError("git_invalid_project_path", "Project path resolves outside the cloned repository", 2)
    repo = DeweyRepo(root)
    validate_project(repo, f"Clone created at {destination}, but the project needs repair")
    return repo
