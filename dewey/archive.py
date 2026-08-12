from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

from dewey.repo import DeweyError, DeweyRepo, utc_now

EXCLUDED_PARTS = {".git", ".pytest_cache", ".ruff_cache", "__pycache__"}
EXCLUDED_NAMES = {".DS_Store", ".env"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-.")
    return stem or "dewey-project"


def default_archive_path(repo: DeweyRepo) -> Path:
    project_name = repo.load_config().project_name or repo.root.name
    return repo.root / f"{_safe_stem(project_name)}.dewey.zip"


def _excluded(relative: Path, target: Path, absolute: Path) -> str | None:
    if absolute.is_symlink():
        return "symlink"
    if absolute.resolve() == target:
        return "output_archive"
    if any(part in EXCLUDED_PARTS for part in relative.parts):
        return "generated_or_vcs"
    if relative.name in EXCLUDED_NAMES or relative.name.startswith(".env."):
        return "secret_or_local_environment"
    if relative.name.endswith(".dewey.zip"):
        return "prior_dewey_archive"
    return None


def write_project_archive(repo: DeweyRepo, output: Path | None = None) -> dict[str, Any]:
    target = output or default_archive_path(repo)
    target = target if target.is_absolute() else repo.root / target
    target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.is_dir():
        raise DeweyError("invalid_archive_path", "Archive output must be a file, not a directory", exit_code=2)

    prefix = _safe_stem(repo.root.name)
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    files: list[tuple[Path, Path]] = []
    for path in sorted(repo.root.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(repo.root)
        reason = _excluded(relative, target, path)
        if reason:
            excluded.append({"path": relative.as_posix(), "reason": reason})
            continue
        included.append({"path": relative.as_posix(), "size": path.stat().st_size, "sha256": _sha256(path)})
        files.append((path, relative))

    config = repo.load_config()
    manifest = {
        "format": "dewey-project-archive",
        "format_version": 1,
        "created_at": utc_now(),
        "project_name": config.project_name or repo.root.name,
        "topic": config.topic,
        "research_question": config.research_question,
        "archive_root": prefix,
        "files": included,
        "excluded": excluded,
    }
    try:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path, relative in files:
                archive.write(path, arcname=(Path(prefix) / relative).as_posix())
            archive.writestr(
                (Path(prefix) / "dewey-export-manifest.json").as_posix(),
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            )
    except OSError as exc:
        raise DeweyError("archive_write_failed", str(exc), exit_code=3) from exc
    return {
        "path": str(target),
        "files": len(included),
        "bytes": target.stat().st_size,
        "excluded": excluded,
        "archive_root": prefix,
        "manifest_path": f"{prefix}/dewey-export-manifest.json",
    }
