"""CLI adapters for Git-backed research projects."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer

from dewey.git_backend import GitProject, clone_project
from dewey.html_export import write_project_site
from dewey.repo import DeweyError


def register_git_commands(app: typer.Typer, emit: Callable, fail: Callable, load_repo: Callable) -> None:
    git_app = typer.Typer(no_args_is_help=True, help="Version and synchronize research using ordinary Git.")
    remote_app = typer.Typer(no_args_is_help=True)
    git_app.add_typer(remote_app, name="remote")
    app.add_typer(git_app, name="git")

    def run(action: str, json_output: bool, operation: Callable) -> None:
        try:
            payload = operation()
        except DeweyError as exc:
            fail(action, exc.code, exc.message, exc.exit_code, json_output)
        except OSError as exc:
            fail(action, "git_io_error", str(exc), 2, json_output)
        emit({"ok": True, "action": action, **payload}, json_output)

    def project(action: str, json_output: bool) -> GitProject:
        return GitProject(load_repo(action, json_output))

    @git_app.command("init")
    def git_init(json_output: bool = typer.Option(False, "--json")) -> None:
        """Enable Git in an existing project, reusing an enclosing repository."""
        action = "git.init"

        def operation():
            git = GitProject.init(load_repo(action, json_output))
            return {"git_root": str(git.root), "text": f"Git enabled at {git.root}"}

        run(action, json_output, operation)

    @git_app.command("clone")
    def git_clone(
        url: str, destination: Path,
        project_path: Path = typer.Option(Path("."), "--project", help="Review directory inside the repository."),
        json_output: bool = typer.Option(False, "--json"),
    ) -> None:
        """Clone, validate the project, and build its local search index."""
        def operation():
            repo = clone_project(url, destination, project_path)
            return {"path": str(repo.root), "validated": True, "text": f"Cloned Dewey project to {repo.root}"}

        run("git.clone", json_output, operation)

    @git_app.command("status")
    def git_status(json_output: bool = typer.Option(False, "--json")) -> None:
        """Show project changes and last-fetched upstream status; does not fetch."""
        def operation():
            result = project("git.status", json_output).status()
            summary = ", ".join(f"{key.replace('_', ' ')}: {value}" for key, value in result["summary"].items() if value)
            result["text"] = (
                f"Git: {result['git_root']} | Branch: {result['branch'] or '(detached)'} | "
                f"Upstream: {result['upstream'] or '(none)'}\n"
                + (f"Ahead: {result['ahead']} | Behind: {result['behind']} (last fetched)\n" if result["upstream"] else "")
                + (summary + "\n" if summary else "")
                + ("\n".join(f"{item['status']} {item['path']}" for item in result["changes"]) or "No project changes")
            )
            return result

        run("git.status", json_output, operation)

    @git_app.command("diff")
    def git_diff(json_output: bool = typer.Option(False, "--json")) -> None:
        """Show tracked project changes against HEAD and list untracked files."""
        def operation():
            result = project("git.diff", json_output).diff()
            result["text"] = result["diff"] or "No tracked changes\n"
            if result["untracked"]:
                result["text"] += "\nUntracked files:\n" + "\n".join(result["untracked"])
            return result

        run("git.diff", json_output, operation)

    @git_app.command("commit")
    def git_commit(
        message: str = typer.Option(..., "-m", "--message"),
        json_output: bool = typer.Option(False, "--json"),
    ) -> None:
        """Validate and commit project changes, preserving unrelated staged files."""
        def operation():
            result = project("git.commit", json_output).commit(message)
            return {**result, "text": f"Committed {result['files']} project files: {result['commit']}"}

        run("git.commit", json_output, operation)

    @git_app.command("site")
    def git_site(json_output: bool = typer.Option(False, "--json")) -> None:
        """Refresh README.md and docs/index.html for sharing the review."""
        def operation():
            result = write_project_site(load_repo("git.site", json_output))
            return {**result, "text": f"Built literature explorer at {result['path']}"}

        run("git.site", json_output, operation)

    @git_app.command("pull")
    def git_pull(json_output: bool = typer.Option(False, "--json")) -> None:
        """Fast-forward the containing repository, then validate and rebuild."""
        def operation():
            result = project("git.pull", json_output).pull()
            return {**result, "text": f"Pulled {result['git_root']}; project validated at {result['after']}"}

        run("git.pull", json_output, operation)

    @git_app.command("push")
    def git_push(
        remote: str | None = typer.Option(None, "--remote", help="Set an upstream on this configured remote."),
        json_output: bool = typer.Option(False, "--json"),
    ) -> None:
        """Push the current repository branch; use --remote origin for its first push."""
        def operation():
            result = project("git.push", json_output).push(remote)
            return {**result, "text": f"Pushed branch {result['branch']} at {result['commit']}"}

        run("git.push", json_output, operation)

    @remote_app.command("add")
    def remote_add(name: str, url: str, json_output: bool = typer.Option(False, "--json")) -> None:
        def operation():
            project("git.remote.add", json_output).add_remote(name, url)
            return {"remote": name, "text": f"Added remote {name}"}

        run("git.remote.add", json_output, operation)

    @remote_app.command("list")
    def remote_list(json_output: bool = typer.Option(False, "--json")) -> None:
        def operation():
            remotes = project("git.remote.list", json_output).remotes()
            return {"remotes": remotes, "text": "\n".join(
                f"{r['name']}\t{r['fetch_url']} (fetch)\n{r['name']}\t{r['push_url']} (push)" for r in remotes
            ) or "No Git remotes"}

        run("git.remote.list", json_output, operation)
