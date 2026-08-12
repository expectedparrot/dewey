from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Any

import typer

from dewey.bibtex import BibTeXError, dump_entry
from dewey.discovery import (
    candidate_from_citation,
    candidate_id,
    edsl_triage_record,
    extract_reference_entries,
    relevance_score,
)
from dewey.guide import GUIDE
from dewey.html_export import write_explorer
from dewey.models import (
    BibEntry,
    CandidateStatus,
    DiscoveryCandidate,
    LinkRecord,
    LinkType,
    MarkdownStatus,
    SourceStatus,
)
from dewey.repo import (
    DeweyError,
    DeweyRepo,
    atomic_write_text,
    parse_entry_file,
    sha256_file,
    utc_now,
)

app = typer.Typer(no_args_is_help=True)
add_app = typer.Typer(no_args_is_help=True)
remove_app = typer.Typer(no_args_is_help=True)
bib_app = typer.Typer(no_args_is_help=True)
state_app = typer.Typer(no_args_is_help=True)
notes_app = typer.Typer(no_args_is_help=True)
link_app = typer.Typer(no_args_is_help=True)
order_app = typer.Typer(no_args_is_help=True)
instructions_app = typer.Typer(no_args_is_help=True)
render_app = typer.Typer(no_args_is_help=True)
index_app = typer.Typer(no_args_is_help=True)
topic_app = typer.Typer(no_args_is_help=True)
summary_app = typer.Typer(no_args_is_help=True)
discover_app = typer.Typer(no_args_is_help=True)
traverse_app = typer.Typer(no_args_is_help=True)
export_app = typer.Typer(no_args_is_help=True)

app.add_typer(add_app, name="add")
app.add_typer(remove_app, name="remove")
app.add_typer(bib_app, name="bib")
app.add_typer(state_app, name="state")
app.add_typer(notes_app, name="notes")
app.add_typer(link_app, name="link")
app.add_typer(order_app, name="order")
app.add_typer(instructions_app, name="instructions")
app.add_typer(render_app, name="render")
app.add_typer(index_app, name="index")
app.add_typer(topic_app, name="topic")
app.add_typer(summary_app, name="summary")
app.add_typer(discover_app, name="discover")
app.add_typer(traverse_app, name="traverse")
app.add_typer(export_app, name="export")


def wants_json(json_output: bool = False) -> bool:
    return json_output or "--json" in sys.argv


def emit(payload: dict[str, Any], json_output: bool = False) -> None:
    if wants_json(json_output):
        typer.echo(json.dumps(payload, indent=2))
        return
    if "text" in payload:
        typer.echo(payload["text"])
        return
    typer.echo(json.dumps(payload, indent=2))


def fail(action: str, code: str, message: str, exit_code: int = 1, json_output: bool = False) -> None:
    payload = {"ok": False, "action": action, "error": {"code": code, "message": message}}
    if wants_json(json_output):
        typer.echo(json.dumps(payload, indent=2))
    else:
        typer.echo(message, err=True)
    raise typer.Exit(exit_code)


def load_repo(action: str, json_output: bool = False) -> DeweyRepo:
    try:
        return DeweyRepo.discover()
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    raise AssertionError("unreachable")


def update_source_index(repo: DeweyRepo, source_id: str) -> None:
    repo.index_source(source_id)


def source_summary(repo: DeweyRepo, source_id: str) -> dict[str, Any]:
    metadata = repo.load_metadata(source_id)
    state = repo.load_state(source_id)
    entry = repo.load_entry(source_id)
    return {
        "source_id": source_id,
        "bibtex_key": metadata.bibtex_key,
        "status": state.status.value,
        "title": entry.title(),
        "year": entry.year(),
        "markdown_status": metadata.markdown_status.value,
        "has_pdf": bool(metadata.managed_pdf_path or metadata.original_pdf_path),
        "has_md": metadata.markdown_status == MarkdownStatus.ready and bool(metadata.markdown_path),
    }


def normalize_entry_update(entry: BibEntry, fields: list[tuple[str, str]], unset: list[str]) -> BibEntry:
    new_fields = dict(entry.fields)
    for name, value in fields:
        key = name.lower()
        if key == "key":
            entry = BibEntry(entry_type=entry.entry_type, key=value, fields=new_fields)
        elif key == "entry_type":
            entry = BibEntry(entry_type=value.lower(), key=entry.key, fields=new_fields)
        else:
            new_fields[key] = value
            entry = BibEntry(entry_type=entry.entry_type, key=entry.key, fields=new_fields)
    for name in unset:
        key = name.lower()
        if key == "key" or key == "entry_type":
            raise DeweyError("invalid_field", f"Cannot unset {name}", exit_code=2)
        new_fields.pop(key, None)
    return BibEntry(entry_type=entry.entry_type, key=entry.key, fields=new_fields)


def ensure_source_exists(repo: DeweyRepo, source_id: str, action: str, json_output: bool = False) -> None:
    try:
        repo.require_source_dir(source_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)


def incoming_links(repo: DeweyRepo, source_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for other_id in repo.list_source_ids():
        if other_id == source_id:
            continue
        links = repo.load_links(other_id)
        for link in links.outgoing:
            if link.target == source_id:
                result.append(
                    {
                        "source_id": other_id,
                        "target": source_id,
                        "type": link.type.value,
                        "note": link.note,
                        "created_at": link.created_at,
                    }
                )
    return result


def count_total_links(repo: DeweyRepo) -> int:
    return sum(len(repo.load_links(source_id).outgoing) for source_id in repo.list_source_ids())


@app.command()
def init(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "project.init"
    try:
        repo = DeweyRepo.init(Path.cwd())
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit(
        {
            "ok": True,
            "action": action,
            "path": str(repo.dewey_dir),
            "text": "Initialized Dewey repository at .dewey/",
        },
        json_output,
    )


@app.command()
def status(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "project.status"
    repo = load_repo(action, json_output)
    counts = {status.value: 0 for status in SourceStatus}
    source_ids = repo.list_source_ids()
    pdf_count = 0
    md_ready = 0
    stale_or_failed = 0
    summarized = 0
    for source_id in source_ids:
        metadata = repo.load_metadata(source_id)
        state = repo.load_state(source_id)
        counts[state.status.value] += 1
        if metadata.managed_pdf_path or metadata.original_pdf_path:
            pdf_count += 1
        if metadata.markdown_status == MarkdownStatus.ready:
            md_ready += 1
        if metadata.markdown_status in {MarkdownStatus.stale, MarkdownStatus.failed}:
            stale_or_failed += 1
        summary_path = repo.source_dir(source_id) / "summary.txt"
        if summary_path.exists() and summary_path.read_text(encoding="utf-8").strip():
            summarized += 1
    order = repo.load_order()
    discovery = repo.load_discovery()
    candidate_counts = {status.value: 0 for status in CandidateStatus}
    for candidate in discovery.candidates:
        candidate_counts[candidate.status.value] += 1
    index_health = {"exists": repo.index_db.exists(), "stats": repo.stats() if repo.index_db.exists() else None}
    text = (
        f"Sources: {len(source_ids)} | PDFs: {pdf_count} | Markdown ready: {md_ready} | "
        f"Summarized: {summarized} | Candidates: {candidate_counts['candidate']} | "
        f"Ordered: {len(order.order)} | Links: {count_total_links(repo)} | Markdown stale/failed: {stale_or_failed}"
    )
    emit(
        {
            "ok": True,
            "action": action,
            "counts": {
                "sources": len(source_ids),
                "with_pdf": pdf_count,
                "with_markdown_ready": md_ready,
                "by_status": counts,
                "ordered_sources": len(order.order),
                "total_links": count_total_links(repo),
                "stale_or_failed_markdown": stale_or_failed,
                "summarized": summarized,
                "candidates_by_status": candidate_counts,
            },
            "index": index_health,
            "text": text,
        },
        json_output,
    )


@app.command()
def doctor(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "project.doctor"
    repo = load_repo(action, json_output)
    issues: list[dict[str, Any]] = []
    top_level = [repo.config_path, repo.instructions_path, repo.order_path, repo.discovery_path, repo.log_path]
    for path in top_level:
        if not path.exists():
            issues.append({"code": "missing_file", "path": str(path)})
    source_ids = set(repo.list_source_ids())
    for source_id in sorted(source_ids):
        source_dir = repo.require_source_dir(source_id)
        for name in ("entry.bib", "metadata.json", "state.json", "summary.txt", "notes.md", "links.json"):
            if not (source_dir / name).exists():
                issues.append({"code": "missing_source_file", "source_id": source_id, "path": str(source_dir / name)})
        try:
            entry = repo.load_entry(source_id)
        except (DeweyError, BibTeXError, FileNotFoundError) as exc:
            issues.append({"code": "invalid_entry", "source_id": source_id, "message": str(exc)})
            continue
        try:
            metadata = repo.load_metadata(source_id)
            state = repo.load_state(source_id)
            links = repo.load_links(source_id)
        except DeweyError as exc:
            issues.append({"code": exc.code, "source_id": source_id, "message": exc.message})
            continue
        if metadata.source_id != source_id:
            issues.append({"code": "source_id_mismatch", "source_id": source_id})
        if metadata.bibtex_key != entry.key:
            issues.append({"code": "bibtex_key_mismatch", "source_id": source_id})
        if metadata.entry_type != entry.entry_type:
            issues.append({"code": "entry_type_mismatch", "source_id": source_id})
        for link in links.outgoing:
            if link.target not in source_ids:
                issues.append({"code": "broken_link", "source_id": source_id, "target": link.target})
        if metadata.content_hash and metadata.managed_pdf_path:
            pdf_path = repo.root / metadata.managed_pdf_path
            if pdf_path.exists() and sha256_file(pdf_path) != metadata.content_hash:
                issues.append({"code": "content_hash_mismatch", "source_id": source_id})
        if metadata.markdown_path and not (metadata.managed_pdf_path or metadata.original_pdf_path):
            if metadata.markdown_source != "non_pdf_import":
                issues.append({"code": "orphan_markdown", "source_id": source_id})
        _ = state
    order = repo.load_order()
    if len(order.order) != len(set(order.order)):
        issues.append({"code": "duplicate_order_entries"})
    for source_id in order.order:
        if source_id not in source_ids:
            issues.append({"code": "missing_order_source", "source_id": source_id})
    try:
        repo.init_index()
        repo.stats()
    except sqlite3.Error as exc:
        issues.append({"code": "index_error", "message": str(exc)})
    if issues:
        payload = {"ok": False, "action": action, "issues": issues, "text": f"Doctor found {len(issues)} issue(s)"}
        emit(payload, json_output)
        raise typer.Exit(3)
    emit({"ok": True, "action": action, "issues": [], "text": "Doctor found no issues"}, json_output)


@app.command("guide")
def guide_command() -> None:
    typer.echo(GUIDE, nl=False)


@app.command("next")
def next_command(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "workflow.next"
    repo = load_repo(action, json_output)
    config = repo.load_config()
    discovery = repo.load_discovery()
    undecided = [item for item in discovery.candidates if item.status == CandidateStatus.candidate]
    relevant = [item for item in discovery.candidates if item.status == CandidateStatus.relevant]
    source_ids = repo.list_source_ids()
    unsummarized = [
        source_id
        for source_id in source_ids
        if not (repo.source_dir(source_id) / "summary.txt").read_text(encoding="utf-8").strip()
    ]
    if not config.topic or not config.research_question:
        phase = "frame"
        recommendations = ["dewey topic set --topic <topic> --question <research-question>"]
    elif not source_ids and not discovery.candidates:
        phase = "seed"
        recommendations = ["Find 3-5 anchor papers", "dewey discover add --title <title> --doi <doi>"]
    elif undecided:
        phase = "screen"
        recommendations = ["dewey discover list --status candidate", f"Review {len(undecided)} candidate(s)"]
    elif relevant:
        phase = "promote"
        recommendations = [f"dewey discover accept {relevant[0].candidate_id}", f"Accept or reject {len(relevant)} relevant candidate(s)"]
    elif not source_ids:
        phase = "seed"
        recommendations = ["The last candidate set yielded no sources; broaden or revise the search"]
    elif unsummarized:
        phase = "read"
        recommendations = [f"dewey summary set {unsummarized[0]} --text <summary>", f"Summarize {len(unsummarized)} source(s)"]
    else:
        phase = "expand"
        recommendations = ["Traverse citations from a strong included source", "dewey traverse references <source-id>"]
    emit(
        {"ok": True, "action": action, "phase": phase, "next_steps": recommendations, "text": "\n".join(recommendations)},
        json_output,
    )


@topic_app.command("set")
def topic_set(
    topic: str = typer.Option(..., "--topic"),
    question: str = typer.Option(..., "--question"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "topic.set"
    repo = load_repo(action, json_output)
    config = repo.load_config().model_copy(update={"topic": topic.strip(), "research_question": question.strip()})
    repo.write_config(config)
    repo.append_log(action, topic=config.topic, research_question=config.research_question)
    emit({"ok": True, "action": action, "topic": config.topic, "research_question": config.research_question, "text": f"Topic: {config.topic}\nQuestion: {config.research_question}"}, json_output)


@topic_app.command("show")
def topic_show(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "topic.show"
    repo = load_repo(action, json_output)
    config = repo.load_config()
    emit({"ok": True, "action": action, "topic": config.topic, "research_question": config.research_question, "text": f"Topic: {config.topic or '(unset)'}\nQuestion: {config.research_question or '(unset)'}"}, json_output)


@summary_app.command("set")
def summary_set(
    source_id: str,
    text: str | None = typer.Option(None, "--text"),
    file: Path | None = typer.Option(None, "--file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "summary.set"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    if (text is None) == (file is None):
        fail(action, "invalid_arguments", "Specify exactly one of --text or --file", 2, json_output)
    try:
        summary = text if text is not None else file.read_text(encoding="utf-8")  # type: ignore[union-attr]
    except FileNotFoundError:
        fail(action, "file_not_found", f"No file exists at {file}", 4, json_output)
    summary = summary.strip() + "\n"
    atomic_write_text(repo.source_dir(source_id) / "summary.txt", summary)
    repo.index_source(source_id)
    repo.append_log(action, source_id=source_id)
    emit({"ok": True, "action": action, "source_id": source_id, "summary": summary.rstrip(), "text": summary.rstrip()}, json_output)


@summary_app.command("show")
def summary_show(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "summary.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    path = repo.source_dir(source_id) / "summary.txt"
    summary = path.read_text(encoding="utf-8") if path.exists() else ""
    emit({"ok": True, "action": action, "source_id": source_id, "summary": summary, "text": summary}, json_output)


@discover_app.command("add")
def discover_add(
    title: str = typer.Option(..., "--title"),
    author: list[str] = typer.Option([], "--author"),
    year: int | None = typer.Option(None, "--year"),
    doi: str | None = typer.Option(None, "--doi"),
    url: str | None = typer.Option(None, "--url"),
    abstract: str | None = typer.Option(None, "--abstract"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.add"
    repo = load_repo(action, json_output)
    config = repo.load_config()
    candidate = DiscoveryCandidate(
        candidate_id=candidate_id(), title=title.strip(), authors=author, year=year, doi=doi, url=url,
        abstract=abstract, relevance_score=relevance_score(" ".join([title, abstract or ""]), config.topic or config.research_question or ""),
        created_at=utc_now(),
    )
    stored = repo.add_candidate(candidate)
    repo.append_log(action, candidate_id=stored.candidate_id)
    emit({"ok": True, "action": action, "candidate": stored.model_dump(mode="json"), "text": f"{stored.candidate_id}\t{stored.title}"}, json_output)


@discover_app.command("list")
def discover_list(
    status: CandidateStatus | None = typer.Option(None, "--status"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.list"
    repo = load_repo(action, json_output)
    candidates = [item for item in repo.load_discovery().candidates if status is None or item.status == status]
    candidates.sort(key=lambda item: (item.relevance_score is None, -(item.relevance_score or 0), item.title.casefold()))
    data = [item.model_dump(mode="json") for item in candidates]
    text_value = "\n".join(f"{item.candidate_id}\t{item.status.value}\t{item.relevance_score if item.relevance_score is not None else '-'}\t{item.title}" for item in candidates)
    emit({"ok": True, "action": action, "candidates": data, "text": text_value}, json_output)


def _candidate(repo: DeweyRepo, candidate_id_value: str) -> DiscoveryCandidate:
    for item in repo.load_discovery().candidates:
        if item.candidate_id == candidate_id_value:
            return item
    raise DeweyError("candidate_not_found", f"No discovery candidate exists for {candidate_id_value}", exit_code=4)


@discover_app.command("decide")
def discover_decide(
    candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"),
    status: CandidateStatus = typer.Option(..., "--status"),
    rationale: str | None = typer.Option(None, "--rationale"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.decide"
    repo = load_repo(action, json_output)
    if status == CandidateStatus.added:
        fail(action, "invalid_status", "Use discover accept to add a candidate", 2, json_output)
    discovery = repo.load_discovery()
    for index, item in enumerate(discovery.candidates):
        if item.candidate_id == candidate_id_value:
            discovery.candidates[index] = item.model_copy(update={"status": status, "rationale": rationale})
            repo.write_discovery(discovery)
            repo.append_log(action, candidate_id=candidate_id_value, status=status.value)
            emit({"ok": True, "action": action, "candidate": discovery.candidates[index].model_dump(mode="json"), "text": f"{candidate_id_value}: {status.value}"}, json_output)
            return
    fail(action, "candidate_not_found", f"No discovery candidate exists for {candidate_id_value}", 4, json_output)


@discover_app.command("accept")
def discover_accept(candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "discovery.accept"
    repo = load_repo(action, json_output)
    discovery = repo.load_discovery()
    for index, item in enumerate(discovery.candidates):
        if item.candidate_id != candidate_id_value:
            continue
        if item.status == CandidateStatus.added:
            fail(action, "candidate_already_added", f"Candidate already added as {item.added_source_id}", 2, json_output)
        key_base = (item.authors[0].split()[-1] if item.authors else "source") + str(item.year or "")
        key = "".join(ch.lower() for ch in key_base if ch.isalnum()) or item.candidate_id
        existing = repo.existing_bibtex_keys()
        if key in existing:
            key = f"{key}_{item.candidate_id[-4:]}"
        fields = {"title": item.title}
        if item.authors:
            fields["author"] = " and ".join(item.authors)
        if item.year:
            fields["year"] = str(item.year)
        if item.doi:
            fields["doi"] = item.doi
        if item.url:
            fields["url"] = item.url
        source_id = repo.create_source(BibEntry(entry_type="article", key=key, fields=fields))
        if item.cited_by_source_id and item.cited_by_source_id in repo.list_source_ids():
            links = repo.load_links(item.cited_by_source_id)
            links.outgoing.append(LinkRecord(target=source_id, type=LinkType.cites, note="Discovered from bibliography", created_at=utc_now()))
            repo.write_links(item.cited_by_source_id, links)
            repo.index_source(item.cited_by_source_id)
        repo.index_source(source_id)
        discovery.candidates[index] = item.model_copy(update={"status": CandidateStatus.added, "added_source_id": source_id})
        repo.write_discovery(discovery)
        repo.append_log(action, candidate_id=candidate_id_value, source_id=source_id)
        emit({"ok": True, "action": action, "candidate_id": candidate_id_value, "source_id": source_id, "text": f"Added {source_id}: {item.title}"}, json_output)
        return
    fail(action, "candidate_not_found", f"No discovery candidate exists for {candidate_id_value}", 4, json_output)


@discover_app.command("resolve")
def discover_resolve(
    candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"),
    source_id: str = typer.Argument(..., metavar="SOURCE_ID"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.resolve"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    discovery = repo.load_discovery()
    for index, item in enumerate(discovery.candidates):
        if item.candidate_id != candidate_id_value:
            continue
        if item.added_source_id and item.added_source_id != source_id:
            fail(action, "candidate_already_added", f"Candidate already resolved as {item.added_source_id}", 2, json_output)
        if item.cited_by_source_id and item.cited_by_source_id in repo.list_source_ids():
            links = repo.load_links(item.cited_by_source_id)
            if not any(link.target == source_id and link.type == LinkType.cites for link in links.outgoing):
                links.outgoing.append(
                    LinkRecord(target=source_id, type=LinkType.cites, note="Resolved from bibliography", created_at=utc_now())
                )
                repo.write_links(item.cited_by_source_id, links)
                repo.index_source(item.cited_by_source_id)
        discovery.candidates[index] = item.model_copy(
            update={"status": CandidateStatus.added, "added_source_id": source_id}
        )
        repo.write_discovery(discovery)
        repo.append_log(action, candidate_id=candidate_id_value, source_id=source_id)
        emit(
            {
                "ok": True,
                "action": action,
                "candidate_id": candidate_id_value,
                "source_id": source_id,
                "text": f"Resolved {candidate_id_value} as {source_id}",
            },
            json_output,
        )
        return
    fail(action, "candidate_not_found", f"No discovery candidate exists for {candidate_id_value}", 4, json_output)


@discover_app.command("export-triage")
def discover_export_triage(output: Path = typer.Option(..., "--output"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "discovery.export_triage"
    repo = load_repo(action, json_output)
    config = repo.load_config()
    records = [edsl_triage_record(item, config.topic or "", config.research_question or "") for item in repo.load_discovery().candidates if item.status == CandidateStatus.candidate]
    atomic_write_text(output, "".join(json.dumps(record) + "\n" for record in records))
    emit({"ok": True, "action": action, "output": str(output), "records": len(records), "text": f"Wrote {len(records)} triage records to {output}"}, json_output)


@traverse_app.command("references")
def traverse_references(
    source_id: str,
    limit: int = typer.Option(50, "--limit", min=1, max=200),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "traversal.references"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    metadata = repo.load_metadata(source_id)
    if metadata.markdown_status != MarkdownStatus.ready or not metadata.markdown_path:
        fail(action, "markdown_required", f"Render {source_id} to Markdown before traversing its references", 2, json_output)
    markdown_path = repo.root / metadata.markdown_path
    if not markdown_path.exists():
        fail(action, "markdown_missing", f"Markdown file is missing for {source_id}", 4, json_output)
    config = repo.load_config()
    try:
        citations = extract_reference_entries(markdown_path.read_text(encoding="utf-8"))[:limit]
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    topic = " ".join(filter(None, [config.topic, config.research_question]))
    fetched = [candidate_from_citation(citation, source_id, topic) for citation in citations]
    before = len(repo.load_discovery().candidates)
    for candidate in fetched:
        repo.add_candidate(candidate)
    added = len(repo.load_discovery().candidates) - before
    repo.append_log(action, source_id=source_id, fetched=len(fetched), added=added)
    emit({"ok": True, "action": action, "source_id": source_id, "extracted": len(fetched), "added": added, "text": f"Extracted {len(fetched)} references from the document; added {added} new candidates"}, json_output)


@export_app.command("html")
def export_html(
    output: Path = typer.Option(Path("dewey-explorer.html"), "--output"),
    title: str | None = typer.Option(None, "--title"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "export.html"
    repo = load_repo(action, json_output)
    result = write_explorer(repo, output, title)
    repo.append_log(action, **result)
    emit({"ok": True, "action": action, **result, "text": f"Wrote literature explorer to {result['path']}"}, json_output)


@add_app.command("source")
def add_source(
    path: Path,
    bibtex_key: str | None = typer.Option(None, "--bibtex-key"),
    no_md: bool = typer.Option(False, "--no-md"),
    force_duplicate: bool = typer.Option(False, "--force-duplicate"),
    copy_mode: bool = typer.Option(False, "--copy"),
    reference_mode: bool = typer.Option(False, "--reference"),
    backend: str = typer.Option("paper2md", "--backend", help="Markdown backend: paper2md or firecrawl"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "source.add"
    repo = load_repo(action, json_output)
    path = path.resolve()
    if not path.exists():
        fail(action, "file_not_found", f"No file exists at {path}", 4, json_output)
    if copy_mode and reference_mode:
        fail(action, "invalid_flags", "Choose only one of --copy or --reference", 2, json_output)
    suffix = path.suffix.lower()
    if suffix not in {".pdf", ".bib"}:
        fail(action, "unsupported_file_type", f"Unsupported source type: {path.suffix}", 2, json_output)

    if suffix == ".bib":
        try:
            entry = parse_entry_file(path)
            if bibtex_key:
                entry = BibEntry(entry_type=entry.entry_type, key=bibtex_key, fields=dict(entry.fields))
            source_id = repo.create_source(entry)
            update_source_index(repo, source_id)
            repo.append_log(action, source_id=source_id, duplicate=False, input_type="bib")
            emit(
                {
                    "ok": True,
                    "action": action,
                    "source_id": source_id,
                    "duplicate": False,
                    "input_type": "bib",
                    "text": f"Added source {source_id}",
                },
                json_output,
            )
        except DeweyError as exc:
            fail(action, exc.code, exc.message, exc.exit_code, json_output)
        return

    content_hash = sha256_file(path)
    existing = repo.find_by_hash(content_hash)
    if existing and not force_duplicate:
        emit(
            {
                "ok": True,
                "action": action,
                "source_id": existing.source_id,
                "duplicate": True,
                "reused_source_id": existing.source_id,
                "text": f"Reused existing source {existing.source_id}",
            },
            json_output,
        )
        return

    config = repo.load_config()
    mode = "copy" if copy_mode else "reference" if reference_mode else config.pdf_copy_mode
    entry = repo.build_placeholder_entry(path, bibtex_key)
    try:
        source_id = repo.create_source(
            entry,
            original_pdf_path=str(path),
            managed_pdf_path=".dewey/sources/PENDING/source.pdf" if mode == "copy" else None,
            content_hash=content_hash,
            markdown_status=MarkdownStatus.missing,
        )
        source_dir = repo.require_source_dir(source_id)
        metadata = repo.load_metadata(source_id)
        if mode == "copy":
            pdf_dest = source_dir / "source.pdf"
            shutil.copy2(path, pdf_dest)
            metadata.managed_pdf_path = str(pdf_dest.relative_to(repo.root))
        else:
            metadata.managed_pdf_path = None
        metadata.updated_at = utc_now()
        repo.write_metadata(source_id, metadata)
        if not no_md:
            render_result = repo.render_markdown_for_source(source_id, backend=backend)
            metadata.markdown_status = render_result.status
            metadata.markdown_path = render_result.markdown_path
            metadata.markdown_generator.name = render_result.generator_name
            metadata.markdown_generator.version = render_result.generator_version
            repo.write_metadata(source_id, metadata)
        update_source_index(repo, source_id)
        repo.append_log(action, source_id=source_id, duplicate=False, input_type="pdf")
        emit(
            {
                "ok": True,
                "action": action,
                "source_id": source_id,
                "duplicate": False,
                "input_type": "pdf",
                "text": f"Added source {source_id}",
            },
            json_output,
        )
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)


@app.command("list")
def list_sources(
    status: SourceStatus | None = typer.Option(None, "--status"),
    has_pdf: bool = typer.Option(False, "--has-pdf"),
    has_md: bool = typer.Option(False, "--has-md"),
    ordered: bool = typer.Option(False, "--ordered"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "source.list"
    repo = load_repo(action, json_output)
    order = set(repo.load_order().order)
    rows = []
    for source_id in repo.list_source_ids():
        row = source_summary(repo, source_id)
        if status and row["status"] != status.value:
            continue
        if has_pdf and not row["has_pdf"]:
            continue
        if has_md and not row["has_md"]:
            continue
        if ordered and source_id not in order:
            continue
        rows.append(row)
    if wants_json(json_output):
        emit({"ok": True, "action": action, "sources": rows}, True)
        return
    lines = [
        "\t".join(
            [row["source_id"], row["bibtex_key"], row["status"], row["title"], row["year"], row["markdown_status"]]
        )
        for row in rows
    ]
    emit({"ok": True, "action": action, "sources": rows, "text": "\n".join(lines)}, json_output)


@app.command()
def show(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "source.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    metadata = repo.load_metadata(source_id)
    state = repo.load_state(source_id)
    entry = repo.load_entry(source_id)
    links = repo.load_links(source_id)
    payload = {
        "ok": True,
        "action": action,
        "source": {
            "source_id": source_id,
            "paths": {
                "dir": str(repo.source_dir(source_id)),
                "bib": str(repo.source_dir(source_id) / "entry.bib"),
                "notes": str(repo.source_dir(source_id) / "notes.md"),
                "pdf": metadata.managed_pdf_path or metadata.original_pdf_path,
                "md": metadata.markdown_path,
            },
            "metadata": metadata.model_dump(),
            "state": state.model_dump(),
            "bibtex": {"raw": dump_entry(entry), "parsed": entry.as_dict()},
            "links": {
                "outgoing": [link.model_dump() for link in links.outgoing],
                "incoming": incoming_links(repo, source_id),
            },
        },
    }
    if wants_json(json_output):
        emit(payload, True)
        return
    text = "\n".join(
        [
            f"source_id: {source_id}",
            f"bibtex_key: {metadata.bibtex_key}",
            f"status: {state.status.value}",
            f"title: {entry.title()}",
            f"markdown_status: {metadata.markdown_status.value}",
            "",
            dump_entry(entry).rstrip(),
        ]
    )
    payload["text"] = text
    emit(payload, json_output)


@remove_app.command("source")
def remove_source(
    source_id: str,
    yes: bool = typer.Option(False, "--yes"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "source.remove"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    if not yes and sys.stdin.isatty():
        confirmed = typer.confirm(f"Remove {source_id}?")
        if not confirmed:
            fail(action, "aborted", "Removal aborted", 1, json_output)
    shutil.rmtree(repo.require_source_dir(source_id))
    order = repo.load_order()
    order.order = [item for item in order.order if item != source_id]
    repo.write_order(order)
    for other_id in repo.list_source_ids():
        links = repo.load_links(other_id)
        updated = [link for link in links.outgoing if link.target != source_id]
        if len(updated) != len(links.outgoing):
            links.outgoing = updated
            repo.write_links(other_id, links)
            update_source_index(repo, other_id)
    repo.drop_source_from_index(source_id)
    repo.append_log(action, source_id=source_id)
    emit({"ok": True, "action": action, "source_id": source_id, "text": f"Removed {source_id}"}, json_output)


@bib_app.command("show")
def bib_show(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "bib.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    entry = repo.load_entry(source_id)
    raw = dump_entry(entry)
    emit({"ok": True, "action": action, "source_id": source_id, "raw": raw, "parsed": entry.as_dict(), "text": raw.rstrip()}, json_output)


@bib_app.command("set")
def bib_set(source_id: str, file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "bib.set"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    try:
        entry = parse_entry_file(file.resolve())
        existing = repo.existing_bibtex_keys(exclude_source_id=source_id)
        if entry.key in existing:
            raise DeweyError("duplicate_bibtex_key", f"BibTeX key '{entry.key}' already exists in {existing[entry.key]}", 2)
        repo.write_entry(source_id, entry)
        metadata = repo.load_metadata(source_id)
        metadata.bibtex_key = entry.key
        metadata.entry_type = entry.entry_type
        metadata.updated_at = utc_now()
        repo.write_metadata(source_id, metadata)
        update_source_index(repo, source_id)
        repo.append_log(action, source_id=source_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit({"ok": True, "action": action, "source_id": source_id, "text": f"Updated BibTeX for {source_id}"}, json_output)


@bib_app.command("edit")
def bib_edit(
    source_id: str,
    field: list[str] = typer.Option([], "--field"),
    value: list[str] = typer.Option([], "--value"),
    unset: list[str] = typer.Option([], "--unset"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "bib.edit"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    if len(field) != len(value):
        fail(action, "invalid_arguments", "Each --field requires a matching --value", 2, json_output)
    try:
        entry = repo.load_entry(source_id)
        updated = normalize_entry_update(entry, list(zip(field, value)), unset)
        existing = repo.existing_bibtex_keys(exclude_source_id=source_id)
        if updated.key in existing:
            raise DeweyError("duplicate_bibtex_key", f"BibTeX key '{updated.key}' already exists in {existing[updated.key]}", 2)
        repo.write_entry(source_id, updated)
        metadata = repo.load_metadata(source_id)
        metadata.bibtex_key = updated.key
        metadata.entry_type = updated.entry_type
        metadata.updated_at = utc_now()
        repo.write_metadata(source_id, metadata)
        update_source_index(repo, source_id)
        repo.append_log(action, source_id=source_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit({"ok": True, "action": action, "source_id": source_id, "text": f"Edited BibTeX for {source_id}"}, json_output)


@app.command()
def cite(source_id: str, format: str = typer.Option("bibtex", "--format"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "cite.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    entry = repo.load_entry(source_id)
    if format == "bibtex":
        text = dump_entry(entry).rstrip()
        payload = {"ok": True, "action": action, "source_id": source_id, "format": format, "citation": text, "text": text}
    elif format == "key":
        payload = {"ok": True, "action": action, "source_id": source_id, "format": format, "citation": entry.key, "text": entry.key}
    elif format == "json":
        payload = {"ok": True, "action": action, "source_id": source_id, "format": format, "citation": entry.as_dict()}
    else:
        fail(action, "invalid_format", f"Unsupported citation format: {format}", 2, json_output)
        return
    emit(payload, json_output)


@state_app.command("set")
def state_set(source_id: str, status: SourceStatus, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "state.set"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    state = repo.load_state(source_id)
    state.status = status
    if status == SourceStatus.included:
        state.included = True
    elif status == SourceStatus.excluded:
        state.included = False
    repo.write_state(source_id, state)
    update_source_index(repo, source_id)
    repo.append_log(action, source_id=source_id, status=status.value)
    emit({"ok": True, "action": action, "source_id": source_id, "status": status.value, "text": f"Set {source_id} to {status.value}"}, json_output)


@state_app.command("show")
def state_show(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "state.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    state = repo.load_state(source_id)
    emit({"ok": True, "action": action, "source_id": source_id, "state": state.model_dump(), "text": json.dumps(state.model_dump(), indent=2)}, json_output)


@state_app.command("set-priority")
def state_set_priority(source_id: str, priority: int, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "state.set_priority"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    state = repo.load_state(source_id)
    state.priority = priority
    repo.write_state(source_id, state)
    update_source_index(repo, source_id)
    repo.append_log(action, source_id=source_id, priority=priority)
    emit({"ok": True, "action": action, "source_id": source_id, "priority": priority, "text": f"Set priority for {source_id} to {priority}"}, json_output)


@state_app.command("mark-read")
def state_mark_read(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "state.mark_read"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    state = repo.load_state(source_id)
    state.status = SourceStatus.read
    state.last_read_at = utc_now()
    repo.write_state(source_id, state)
    update_source_index(repo, source_id)
    repo.append_log(action, source_id=source_id)
    emit({"ok": True, "action": action, "source_id": source_id, "text": f"Marked {source_id} as read"}, json_output)


@notes_app.command("show")
def notes_show(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "notes.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    text = (repo.source_dir(source_id) / "notes.md").read_text(encoding="utf-8")
    emit({"ok": True, "action": action, "source_id": source_id, "notes": text, "text": text.rstrip()}, json_output)


@notes_app.command("set")
def notes_set(source_id: str, file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "notes.set"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    try:
        text = file.resolve().read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(action, "file_not_found", f"No file exists at {file}", 4, json_output)
        return
    atomic_write_text(repo.source_dir(source_id) / "notes.md", text)
    update_source_index(repo, source_id)
    repo.append_log(action, source_id=source_id)
    emit({"ok": True, "action": action, "source_id": source_id, "text": f"Replaced notes for {source_id}"}, json_output)


@notes_app.command("edit")
def notes_edit(source_id: str, append: str = typer.Option(..., "--append"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "notes.edit"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    path = repo.source_dir(source_id) / "notes.md"
    current = path.read_text(encoding="utf-8")
    separator = "" if not current or current.endswith("\n") else "\n"
    atomic_write_text(path, current + separator + append + "\n")
    update_source_index(repo, source_id)
    repo.append_log(action, source_id=source_id)
    emit({"ok": True, "action": action, "source_id": source_id, "text": f"Appended notes for {source_id}"}, json_output)


@link_app.command("add")
def link_add(
    from_id: str,
    to_id: str,
    type: LinkType = typer.Option(..., "--type"),
    note: str | None = typer.Option(None, "--note"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "link.add"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, from_id, action, json_output)
    ensure_source_exists(repo, to_id, action, json_output)
    links = repo.load_links(from_id)
    for existing in links.outgoing:
        if existing.target == to_id and existing.type == type and existing.note == note:
            emit({"ok": True, "action": action, "from": from_id, "to": to_id, "duplicate": True, "text": "Link already exists"}, json_output)
            return
    links.outgoing.append(LinkRecord(target=to_id, type=type, note=note, created_at=utc_now()))
    repo.write_links(from_id, links)
    update_source_index(repo, from_id)
    repo.append_log(action, **{"from": from_id, "to": to_id, "type": type.value})
    emit({"ok": True, "action": action, "from": from_id, "to": to_id, "type": type.value, "text": f"Linked {from_id} -> {to_id}"}, json_output)


@link_app.command("list")
def link_list(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "link.list"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    outgoing = [link.model_dump() for link in repo.load_links(source_id).outgoing]
    incoming = incoming_links(repo, source_id)
    payload = {"ok": True, "action": action, "source_id": source_id, "outgoing": outgoing, "incoming": incoming}
    if not wants_json(json_output):
        lines = [f"Outgoing: {len(outgoing)}", f"Incoming: {len(incoming)}"]
        payload["text"] = "\n".join(lines)
    emit(payload, json_output)


@link_app.command("remove")
def link_remove(
    from_id: str,
    to_id: str,
    type: LinkType = typer.Option(..., "--type"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "link.remove"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, from_id, action, json_output)
    ensure_source_exists(repo, to_id, action, json_output)
    links = repo.load_links(from_id)
    new_links = [link for link in links.outgoing if not (link.target == to_id and link.type == type)]
    if len(new_links) == len(links.outgoing):
        fail(action, "link_not_found", "No matching link exists", 4, json_output)
    links.outgoing = new_links
    repo.write_links(from_id, links)
    update_source_index(repo, from_id)
    repo.append_log(action, **{"from": from_id, "to": to_id, "type": type.value})
    emit({"ok": True, "action": action, "from": from_id, "to": to_id, "type": type.value, "text": f"Removed link {from_id} -> {to_id}"}, json_output)


@order_app.command("show")
def order_show(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "order.show"
    repo = load_repo(action, json_output)
    order = repo.load_order()
    emit({"ok": True, "action": action, "order": order.model_dump(), "text": "\n".join(order.order)}, json_output)


@order_app.command("set")
def order_set(source_ids: list[str], json_output: bool = typer.Option(False, "--json")) -> None:
    action = "order.set"
    repo = load_repo(action, json_output)
    if len(source_ids) != len(set(source_ids)):
        fail(action, "duplicate_source_id", "Order contains duplicate source IDs", 2, json_output)
    known = set(repo.list_source_ids())
    missing = [source_id for source_id in source_ids if source_id not in known]
    if missing:
        fail(action, "source_not_found", f"Unknown source IDs: {', '.join(missing)}", 4, json_output)
    order = repo.load_order()
    order.order = source_ids
    repo.write_order(order)
    repo.append_log(action)
    emit({"ok": True, "action": action, "order": source_ids, "text": f"Set order for {len(source_ids)} source(s)"}, json_output)


@order_app.command("add")
def order_add(
    source_id: str,
    before: str | None = typer.Option(None, "--before"),
    after: str | None = typer.Option(None, "--after"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "order.add"
    repo = load_repo(action, json_output)
    known = set(repo.list_source_ids())
    if source_id not in known:
        fail(action, "source_not_found", f"No source exists for {source_id}", 4, json_output)
    if (before is None and after is None) or (before is not None and after is not None):
        fail(action, "invalid_arguments", "Specify exactly one of --before or --after", 2, json_output)
    anchor = before or after
    if anchor not in known:
        fail(action, "source_not_found", f"No source exists for {anchor}", 4, json_output)
    order = repo.load_order()
    order.order = [item for item in order.order if item != source_id]
    if anchor in order.order:
        index = order.order.index(anchor)
        insert_at = index if before else index + 1
        order.order.insert(insert_at, source_id)
    else:
        order.order.append(source_id)
    repo.write_order(order)
    repo.append_log(action, source_id=source_id)
    emit({"ok": True, "action": action, "order": order.order, "text": f"Placed {source_id} in review order"}, json_output)


@order_app.command("remove")
def order_remove(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "order.remove"
    repo = load_repo(action, json_output)
    order = repo.load_order()
    order.order = [item for item in order.order if item != source_id]
    repo.write_order(order)
    repo.append_log(action, source_id=source_id)
    emit({"ok": True, "action": action, "order": order.order, "text": f"Removed {source_id} from review order"}, json_output)


@instructions_app.command("show")
def instructions_show(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "instructions.show"
    repo = load_repo(action, json_output)
    text = repo.instructions_path.read_text(encoding="utf-8")
    emit({"ok": True, "action": action, "instructions": text, "text": text.rstrip()}, json_output)


@instructions_app.command("set")
def instructions_set(file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "instructions.set"
    repo = load_repo(action, json_output)
    try:
        text = file.resolve().read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(action, "file_not_found", f"No file exists at {file}", 4, json_output)
        return
    atomic_write_text(repo.instructions_path, text)
    repo.append_log(action)
    emit({"ok": True, "action": action, "text": "Updated instructions"}, json_output)


@instructions_app.command("append")
def instructions_append(text: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "instructions.append"
    repo = load_repo(action, json_output)
    current = repo.instructions_path.read_text(encoding="utf-8")
    separator = "" if not current or current.endswith("\n") else "\n"
    atomic_write_text(repo.instructions_path, current + separator + text + "\n")
    repo.append_log(action)
    emit({"ok": True, "action": action, "text": "Appended instructions"}, json_output)


@render_app.command("md")
def render_md(
    source_id: str | None = typer.Argument(None),
    all: bool = typer.Option(False, "--all"),
    backend: str = typer.Option("paper2md", "--backend", help="Markdown backend: paper2md or firecrawl"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "render.md"
    repo = load_repo(action, json_output)
    if all:
        results = []
        for candidate in repo.list_source_ids():
            metadata = repo.load_metadata(candidate)
            if not (metadata.managed_pdf_path or metadata.original_pdf_path):
                continue
            result = repo.render_markdown_for_source(candidate, backend=backend)
            metadata.markdown_status = result.status
            metadata.markdown_path = result.markdown_path
            metadata.markdown_generator.name = result.generator_name
            metadata.markdown_generator.version = result.generator_version
            metadata.updated_at = utc_now()
            repo.write_metadata(candidate, metadata)
            update_source_index(repo, candidate)
            repo.append_log(action, source_id=candidate)
            results.append({"source_id": candidate, "markdown_status": result.status.value})
        emit({"ok": True, "action": action, "results": results, "text": f"Rendered Markdown for {len(results)} source(s)"}, json_output)
        return
    if source_id is None:
        fail(action, "invalid_arguments", "Provide <source-id> or --all", 2, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    try:
        result = repo.render_markdown_for_source(source_id, backend=backend)
        metadata = repo.load_metadata(source_id)
        metadata.markdown_status = result.status
        metadata.markdown_path = result.markdown_path
        metadata.markdown_generator.name = result.generator_name
        metadata.markdown_generator.version = result.generator_version
        metadata.updated_at = utc_now()
        repo.write_metadata(source_id, metadata)
        update_source_index(repo, source_id)
        repo.append_log(action, source_id=source_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
        return
    emit({"ok": True, "action": action, "source_id": source_id, "markdown_status": result.status.value, "text": f"Rendered Markdown for {source_id}"}, json_output)


@app.command("cat")
def cat_source(
    source_id: str,
    representation: str = typer.Option("md", "--representation"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "representation.cat"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    if representation != "md":
        fail(action, "invalid_representation", f"Unsupported representation: {representation}", 2, json_output)
    metadata = repo.load_metadata(source_id)
    if metadata.markdown_status != MarkdownStatus.ready or not metadata.markdown_path:
        fail(action, "markdown_missing", f"No Markdown representation exists for {source_id}", 4, json_output)
    text = (repo.root / metadata.markdown_path).read_text(encoding="utf-8")
    emit({"ok": True, "action": action, "source_id": source_id, "representation": "md", "content": text, "text": text.rstrip()}, json_output)


@app.command("path")
def path_command(
    source_id: str,
    pdf: bool = typer.Option(False, "--pdf"),
    md: bool = typer.Option(False, "--md"),
    notes: bool = typer.Option(False, "--notes"),
    bib: bool = typer.Option(False, "--bib"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "path.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    selectors = [pdf, md, notes, bib]
    if sum(1 for item in selectors if item) != 1:
        fail(action, "invalid_arguments", "Specify exactly one of --pdf, --md, --notes, --bib", 2, json_output)
    metadata = repo.load_metadata(source_id)
    if pdf:
        result = metadata.managed_pdf_path or metadata.original_pdf_path
    elif md:
        result = metadata.markdown_path
    elif notes:
        result = str(repo.source_dir(source_id) / "notes.md")
    else:
        result = str(repo.source_dir(source_id) / "entry.bib")
    if not result:
        fail(action, "path_not_available", f"No requested artifact exists for {source_id}", 4, json_output)
    emit({"ok": True, "action": action, "source_id": source_id, "path": result, "text": result}, json_output)


@app.command()
def search(
    query: str | None = typer.Argument(None),
    title: str | None = typer.Option(None, "--title"),
    author: str | None = typer.Option(None, "--author"),
    bibtex: str | None = typer.Option(None, "--bibtex"),
    notes: str | None = typer.Option(None, "--notes"),
    fulltext: str | None = typer.Option(None, "--fulltext"),
    status: SourceStatus | None = typer.Option(None, "--status"),
    has_pdf: bool = typer.Option(False, "--has-pdf"),
    has_md: bool = typer.Option(False, "--has-md"),
    linked_to: str | None = typer.Option(None, "--linked-to"),
    link_type: LinkType | None = typer.Option(None, "--link-type"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "search.query"
    repo = load_repo(action, json_output)
    repo.init_index()
    conn = sqlite3.connect(repo.index_db)
    conn.row_factory = sqlite3.Row
    try:
        where = ["1=1"]
        params: list[Any] = []
        fts_source_ids: set[str] | None = None

        def fts_match(expression: str) -> set[str]:
            rows = conn.execute("SELECT source_id FROM source_fts WHERE source_fts MATCH ?", (expression,)).fetchall()
            return {row["source_id"] for row in rows}

        expressions = []
        if query:
            expressions.append(query)
        if title:
            expressions.append(f"title:{title}")
        if author:
            expressions.append(f"author:{author}")
        if bibtex:
            expressions.append(f"bibtex:{bibtex}")
        if notes:
            expressions.append(f"notes:{notes}")
        if fulltext:
            expressions.append(f"markdown:{fulltext}")
        if expressions:
            fts_source_ids = set(repo.list_source_ids())
            for expr in expressions:
                try:
                    fts_source_ids &= fts_match(expr)
                except sqlite3.Error:
                    fts_source_ids &= fts_match(f'"{expr.split(":", 1)[-1]}"')
            if not fts_source_ids:
                payload = {"ok": True, "action": action, "query": _query_payload(query, title, author, bibtex, notes, fulltext, status, has_pdf, has_md, linked_to, link_type), "results": [], "text": ""}
                emit(payload, json_output)
                return
            placeholders = ",".join("?" for _ in fts_source_ids)
            where.append(f"source_id IN ({placeholders})")
            params.extend(sorted(fts_source_ids))
        if status:
            where.append("status = ?")
            params.append(status.value)
        if has_pdf:
            where.append("has_pdf = 1")
        if has_md:
            where.append("has_md = 1")
        if linked_to:
            where.append("source_id IN (SELECT from_id FROM link_index WHERE to_id = ?)")
            params.append(linked_to)
        if link_type:
            where.append("source_id IN (SELECT from_id FROM link_index WHERE type = ?)")
            params.append(link_type.value)
        rows = conn.execute(
            f"SELECT source_id, bibtex_key, title, status, author, bibtex_text, notes_text, markdown_text FROM source_index WHERE {' AND '.join(where)} ORDER BY source_id",
            params,
        ).fetchall()
        results = []
        text_terms = [term for term in [query, title, author, bibtex, notes, fulltext] if term]
        for row in rows:
            results.append(
                {
                    "source_id": row["source_id"],
                    "bibtex_key": row["bibtex_key"],
                    "title": row["title"],
                    "status": row["status"],
                    "matches": build_match_snippets(row, text_terms),
                }
            )
        payload = {
            "ok": True,
            "action": action,
            "query": _query_payload(query, title, author, bibtex, notes, fulltext, status, has_pdf, has_md, linked_to, link_type),
            "results": results,
        }
        if not wants_json(json_output):
            payload["text"] = "\n".join(f"{item['source_id']}\t{item['bibtex_key']}\t{item['title']}" for item in results)
        emit(payload, json_output)
    finally:
        conn.close()


def _query_payload(
    query: str | None,
    title: str | None,
    author: str | None,
    bibtex: str | None,
    notes: str | None,
    fulltext: str | None,
    status: SourceStatus | None,
    has_pdf: bool,
    has_md: bool,
    linked_to: str | None,
    link_type: LinkType | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if query:
        payload["query"] = query
    if title:
        payload["title"] = title
    if author:
        payload["author"] = author
    if bibtex:
        payload["bibtex"] = bibtex
    if notes:
        payload["notes"] = notes
    if fulltext:
        payload["fulltext"] = fulltext
    if status:
        payload["status"] = status.value
    if has_pdf:
        payload["has_pdf"] = True
    if has_md:
        payload["has_md"] = True
    if linked_to:
        payload["linked_to"] = linked_to
    if link_type:
        payload["link_type"] = link_type.value
    return payload


def build_match_snippets(row: sqlite3.Row, terms: list[str]) -> list[dict[str, str]]:
    matches = []
    for field_name, field_text in [("bibtex", row["bibtex_text"]), ("notes", row["notes_text"]), ("markdown", row["markdown_text"])]:
        if not field_text:
            continue
        lower = field_text.lower()
        for term in terms:
            if term.lower() in lower:
                idx = lower.index(term.lower())
                snippet = field_text[max(0, idx - 20) : idx + len(term) + 40].replace("\n", " ")
                matches.append({"field": field_name, "snippet": snippet})
                break
    return matches


@index_app.command("rebuild")
def index_rebuild(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "index.rebuild"
    repo = load_repo(action, json_output)
    repo.rebuild_index()
    repo.append_log(action)
    emit({"ok": True, "action": action, "stats": repo.stats(), "text": "Rebuilt search index"}, json_output)


@index_app.command("stats")
def index_stats(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "index.stats"
    repo = load_repo(action, json_output)
    emit({"ok": True, "action": action, "stats": repo.stats(), "text": json.dumps(repo.stats(), indent=2)}, json_output)


def main() -> None:
    try:
        app()
    except DeweyError as exc:
        if wants_json():
            typer.echo(
                json.dumps(
                    {"ok": False, "action": "command", "error": {"code": exc.code, "message": exc.message}},
                    indent=2,
                )
            )
        else:
            typer.echo(exc.message, err=True)
        raise SystemExit(exc.exit_code)
