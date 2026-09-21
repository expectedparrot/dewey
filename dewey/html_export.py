from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import quote

from dewey.bibtex import dump_entry
from dewey.evidence import EvidenceStore
from dewey.project_readme import write_project_readme
from dewey.repo import DeweyError, DeweyRepo, atomic_write_text, utc_now


def author_surname(author: str) -> str:
    author = author.strip()
    if not author:
        return "Unknown"
    if "," in author:
        return author.split(",", maxsplit=1)[0].strip()
    return author.split()[-1]


def citation_label(authors: str, year: str, title: str = "") -> str:
    surnames = [author_surname(author) for author in authors.split(" and ") if author.strip()]
    if not surnames:
        words = title.replace("[", "").replace("]", "").split()
        names = " ".join(words[:6]) + ("…" if len(words) > 6 else "") if words else "Unresolved citation"
    elif len(surnames) == 1:
        names = surnames[0]
    elif len(surnames) == 2:
        names = f"{surnames[0]} & {surnames[1]}"
    else:
        names = f"{surnames[0]} et al."
    return f"{names} ({year})" if year else names


def explorer_payload(repo: DeweyRepo) -> dict[str, Any]:
    config = repo.load_config()
    order = repo.load_order().order
    positions = {source_id: index for index, source_id in enumerate(order)}
    sources = []
    links = []
    for source_id in repo.list_source_ids():
        entry = repo.load_entry(source_id)
        metadata = repo.load_metadata(source_id)
        state = repo.load_state(source_id)
        source_dir = repo.source_dir(source_id)
        summary_path = source_dir / "summary.txt"
        notes_path = source_dir / "notes.md"
        markdown = ""
        if metadata.markdown_path:
            markdown_path = repo.root / metadata.markdown_path
            if markdown_path.exists():
                markdown = markdown_path.read_text(encoding="utf-8")
        outgoing = [item.model_dump(mode="json") for item in repo.load_links(source_id).outgoing]
        for item in outgoing:
            links.append({"from": source_id, "to": item["target"], "type": item["type"], "note": item["note"]})
        sources.append(
            {
                "source_id": source_id,
                "bibtex_key": entry.key,
                "bibtex": dump_entry(entry),
                "entry_type": entry.entry_type,
                "title": entry.title(),
                "authors": entry.author(),
                "year": entry.year(),
                "citation_label": citation_label(entry.author(), entry.year(), entry.title()),
                "doi": entry.fields.get("doi"),
                "url": entry.fields.get("url"),
                "status": state.status.value,
                "last_read_at": state.last_read_at,
                "read_depth": state.read_depth.value if state.read_depth else None,
                "metadata_incomplete": not bool(entry.author() and entry.year() and entry.title()),
                "has_pdf": managed_pdf(repo, source_id) is not None,
                "pdf_url": None,
                "priority": state.priority,
                "markdown_status": metadata.markdown_status.value,
                "generator": metadata.markdown_generator.model_dump(mode="json"),
                "summary": summary_path.read_text(encoding="utf-8").strip() if summary_path.exists() else "",
                "notes": notes_path.read_text(encoding="utf-8").strip() if notes_path.exists() else "",
                "markdown": markdown,
                "outgoing": outgoing,
                "order": positions.get(source_id),
            }
        )
    sources.sort(key=lambda item: (item["order"] is None, item["order"] or 0, item["title"].casefold()))
    label_groups: dict[str, list[dict[str, Any]]] = {}
    for source in sources:
        label_groups.setdefault(source["citation_label"], []).append(source)
    for group in label_groups.values():
        if len(group) < 2:
            continue
        for index, source in enumerate(sorted(group, key=lambda item: item["title"].casefold())):
            label = source["citation_label"]
            source["citation_label"] = (
                label.removesuffix(")") + f"{chr(97 + index)})"
                if label.endswith(")")
                else f"{label} [{chr(97 + index)}]"
            )
    evidence = EvidenceStore(repo.root)
    history = []
    if repo.history_path.exists():
        for line in repo.history_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("action") in {"discovery.search", "traversal.citations", "traversal.references"}:
                history.append(record)
    return {
        "generated_at": utc_now(),
        "project_name": config.project_name or config.topic or "Literature review",
        "repository_url": repository_url(repo),
        "topic": config.topic,
        "research_question": config.research_question,
        "instructions": repo.instructions_path.read_text(encoding="utf-8").strip(),
        "sources": sources,
        "candidates": [item.model_dump(mode="json") for item in repo.load_discovery().candidates],
        "links": links,
        "studies": [item.model_dump(mode="json") for item in evidence.studies()],
        "findings": [item.model_dump(mode="json") for item in evidence.findings()],
        "appraisals": [item.model_dump(mode="json") for item in evidence.appraisals()],
        "themes": [item.model_dump(mode="json") for item in evidence.themes()],
        "claims": [item.model_dump(mode="json") for item in evidence.claims()],
        "search_history": history,
    }


def managed_pdf(repo: DeweyRepo, source_id: str) -> Path | None:
    """Only publish archival PDFs inside the corpus, never private local references."""
    stored = repo.load_metadata(source_id).managed_pdf_path
    if not stored:
        return None
    path = (repo.root / stored).resolve()
    return path if path.is_relative_to(repo.sources_dir.resolve()) and path.is_file() else None


def repository_url(repo: DeweyRepo) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(repo.root), "remote", "get-url", "origin"],
                                capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?", result.stdout.strip())
    return "https://github.com/" + match.group(1) if match else None


def build_explorer_html(payload: dict[str, Any], title: str) -> str:
    assets = Path(__file__).parent / "assets"
    template = (assets / "explorer.html").read_text(encoding="utf-8")
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    replacements = {
        "__STYLE__": (assets / "explorer.css").read_text(encoding="utf-8"),
        "__SCRIPT__": (assets / "explorer.js").read_text(encoding="utf-8"),
        "__TITLE__": html.escape(title),
        "__DATA__": data,
    }
    return re.sub(r"__STYLE__|__SCRIPT__|__TITLE__|__DATA__", lambda match: replacements[match.group()], template)


def write_explorer(repo: DeweyRepo, output: Path, title: str | None = None) -> dict[str, Any]:
    payload = explorer_payload(repo)
    resolved_title = title or payload["project_name"]
    target = output if output.is_absolute() else repo.root / output
    target.parent.mkdir(parents=True, exist_ok=True)
    asset_root = target.parent / (target.stem + ".assets")
    if not asset_root.resolve().is_relative_to(target.parent.resolve()):
        raise DeweyError("unsafe_asset_path", "Explorer assets must remain beside the HTML", 2)
    manifest = asset_root / "manifest.json"
    previous_assets = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else []
    pdf_assets = []
    asset_names = []
    for source in payload["sources"]:
        pdf = managed_pdf(repo, source["source_id"])
        if pdf is None:
            continue
        # Source IDs are model data: filenames must not be usable as paths.
        if not re.fullmatch(r"[\w-]+", source["source_id"]):
            raise DeweyError("invalid_source_id", "Cannot export an unsafe source identifier", 3)
        relative = Path(target.stem + ".assets") / "papers" / (source["source_id"] + ".pdf")
        destination = target.parent / relative
        if not destination.resolve().is_relative_to(target.parent.resolve()):
            raise DeweyError("unsafe_asset_path", "Explorer assets must remain beside the HTML", 2)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if pdf != destination.resolve():
            shutil.copyfile(pdf, destination)
        source["pdf_url"] = quote(relative.as_posix())
        pdf_assets.append(str(destination))
        asset_names.append(destination.name)
    atomic_write_text(target, build_explorer_html(payload, resolved_title))
    # Remove only files listed by our previous export, leaving unrelated files alone.
    for name in previous_assets:
        if isinstance(name, str) and re.fullmatch(r"[\w-]+\.pdf", name) and name not in asset_names:
            stale = asset_root / "papers" / name
            if stale.resolve().is_relative_to(asset_root.resolve()):
                stale.unlink(missing_ok=True)
    if asset_names or manifest.exists():
        atomic_write_text(manifest, json.dumps(asset_names, indent=2) + "\n")
    return {
        "path": str(target),
        "sources": len(payload["sources"]),
        "candidates": len(payload["candidates"]),
        "links": len(payload["links"]),
        "studies": len(payload["studies"]),
        "findings": len(payload["findings"]),
        "pdf_assets": pdf_assets,
    }


def write_project_site(repo: DeweyRepo) -> dict[str, Any]:
    """Refresh the checked-in, self-contained literature explorer for GitHub Pages."""
    target = repo.root / "docs" / "index.html"
    if target.is_symlink() or not target.resolve().is_relative_to(repo.root):
        raise DeweyError("unsafe_site_path", "docs/index.html must be inside the project and not a symlink", 2)
    if target.exists() and 'id="dewey-data"' not in target.read_text(encoding="utf-8"):
        raise DeweyError("site_exists", "docs/index.html already contains a different page; move it before generating the explorer", 2)
    result = write_explorer(repo, target)
    atomic_write_text(target.parent / ".nojekyll", "")
    result["readme"] = write_project_readme(repo, explorer_payload(repo))
    return result
