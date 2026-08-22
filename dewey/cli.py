from __future__ import annotations

import csv
import io
import json
import shutil
import sqlite3
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv

from dewey.archive import write_project_archive
from dewey.bibtex import BibTeXError, dump_entry
from dewey.evidence import EvidenceStore
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
    ExclusionReason,
    LinkRecord,
    LinkType,
    MarkdownStatus,
    ReadDepth,
    ScreeningDecision,
    ScreeningDecisionValue,
    ScreeningStage,
    SourceStatus,
)
from dewey.repo import (
    DeweyError,
    DeweyRepo,
    atomic_write_text,
    convert_url_with_firecrawl,
    parse_entry_file,
    sha256_file,
    slugify_key,
    utc_now,
)
from dewey.reporting import article_brief, embed_explorer, render_with_pandoc

app = typer.Typer(no_args_is_help=True)
load_dotenv()
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
screen_app = typer.Typer(no_args_is_help=True)
traverse_app = typer.Typer(no_args_is_help=True)
export_app = typer.Typer(no_args_is_help=True)
study_app = typer.Typer(no_args_is_help=True)
finding_app = typer.Typer(no_args_is_help=True)
appraisal_app = typer.Typer(no_args_is_help=True)
matrix_app = typer.Typer(no_args_is_help=True)
synthesis_app = typer.Typer(no_args_is_help=True)
theme_app = typer.Typer(no_args_is_help=True)
claim_app = typer.Typer(no_args_is_help=True)
report_app = typer.Typer(no_args_is_help=True)

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
app.add_typer(screen_app, name="screen")
app.add_typer(traverse_app, name="traverse")
app.add_typer(export_app, name="export")
app.add_typer(study_app, name="study")
app.add_typer(finding_app, name="finding")
app.add_typer(appraisal_app, name="appraisal")
app.add_typer(matrix_app, name="matrix")
app.add_typer(synthesis_app, name="synthesis")
app.add_typer(theme_app, name="theme")
app.add_typer(claim_app, name="claim")
app.add_typer(report_app, name="report")


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


def load_json_object(path: Path, action: str, json_output: bool = False) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(action, "file_not_found", f"No file exists at {path}", 4, json_output)
    except json.JSONDecodeError as exc:
        fail(action, "invalid_json", f"Invalid JSON in {path}: {exc}", 2, json_output)
    if not isinstance(payload, dict):
        fail(action, "invalid_json", f"Expected a JSON object in {path}", 2, json_output)
    return payload


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
    read_depth_counts = {depth.value: 0 for depth in ReadDepth}
    read_depth_counts["unspecified"] = 0
    for source_id in source_ids:
        metadata = repo.load_metadata(source_id)
        state = repo.load_state(source_id)
        counts[state.status.value] += 1
        if state.last_read_at is not None:
            key = state.read_depth.value if state.read_depth is not None else "unspecified"
            read_depth_counts[key] += 1
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
    discovery_sightings = sum(len(candidate.provenance) for candidate in discovery.candidates)
    index_health = {"exists": repo.index_db.exists(), "stats": repo.stats() if repo.index_db.exists() else None}
    text = (
        f"Sources: {len(source_ids)} | PDFs: {pdf_count} | Markdown ready: {md_ready} | "
        f"Summarized: {summarized} | Candidates: {candidate_counts['candidate']} "
        f"({discovery_sightings} sightings) | "
        f"Full-text read: {read_depth_counts['full-text']} | Abstract read: {read_depth_counts['abstract']} | "
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
                "by_read_depth": read_depth_counts,
                "ordered_sources": len(order.order),
                "total_links": count_total_links(repo),
                "stale_or_failed_markdown": stale_or_failed,
                "summarized": summarized,
                "candidates_by_status": candidate_counts,
                "discovery_sightings": discovery_sightings,
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
    for group in repo.duplicate_candidate_groups():
        issues.append({"code": "duplicate_candidates", **group})
    evidence = EvidenceStore(repo.root)
    try:
        studies = evidence.studies()
        findings = evidence.findings()
        appraisals = evidence.appraisals()
        themes = evidence.themes()
        claims = evidence.claims()
    except DeweyError as exc:
        issues.append({"code": exc.code, "message": exc.message})
        studies, findings, appraisals, themes, claims = [], [], [], [], []
    study_ids = {study.study_id for study in studies}
    for study in studies:
        for source_id in study.source_ids:
            if source_id not in source_ids:
                issues.append({"code": "missing_study_source", "study_id": study.study_id, "source_id": source_id})
    for finding in findings:
        if finding.study_id not in study_ids:
            issues.append(
                {"code": "missing_finding_study", "finding_id": finding.finding_id, "study_id": finding.study_id}
            )
    appraisal_study_ids: set[str] = set()
    for appraisal in appraisals:
        if appraisal.study_id not in study_ids:
            issues.append(
                {
                    "code": "missing_appraisal_study",
                    "appraisal_id": appraisal.appraisal_id,
                    "study_id": appraisal.study_id,
                }
            )
        if appraisal.study_id in appraisal_study_ids:
            issues.append({"code": "duplicate_study_appraisal", "study_id": appraisal.study_id})
        appraisal_study_ids.add(appraisal.study_id)
    theme_ids = {theme.theme_id for theme in themes}
    finding_ids = {finding.finding_id for finding in findings}
    for claim in claims:
        for theme_id in claim.theme_ids:
            if theme_id not in theme_ids:
                issues.append({"code": "missing_claim_theme", "claim_id": claim.claim_id, "theme_id": theme_id})
        for link in claim.evidence:
            if link.finding_id not in finding_ids:
                issues.append(
                    {"code": "missing_claim_finding", "claim_id": claim.claim_id, "finding_id": link.finding_id}
                )
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


def synthesis_coverage(repo: DeweyRepo) -> dict[str, Any]:
    store = EvidenceStore(repo.root)
    studies = store.studies()
    findings = store.findings()
    appraisals = store.appraisals()
    themes = store.themes()
    claims = store.claims()
    included_source_ids = {
        source_id
        for source_id in repo.list_source_ids()
        if repo.load_state(source_id).status == SourceStatus.included
    }
    represented_source_ids = {source_id for study in studies for source_id in study.source_ids}
    study_ids_with_findings = {finding.study_id for finding in findings}
    study_ids_with_appraisals = {appraisal.study_id for appraisal in appraisals}
    missing_study_sources = sorted(included_source_ids - represented_source_ids)
    missing_finding_studies = sorted(
        study.study_id for study in studies if study.study_id not in study_ids_with_findings
    )
    missing_appraisal_studies = sorted(
        study.study_id for study in studies if study.study_id not in study_ids_with_appraisals
    )
    used_finding_ids = {link.finding_id for claim in claims for link in claim.evidence}
    unused_findings = sorted(finding.finding_id for finding in findings if finding.finding_id not in used_finding_ids)
    used_theme_ids = {theme_id for claim in claims for theme_id in claim.theme_ids}
    themes_without_claims = sorted(theme.theme_id for theme in themes if theme.theme_id not in used_theme_ids)
    return {
        "included_sources": len(included_source_ids),
        "studies": len(studies),
        "findings": len(findings),
        "appraisals": len(appraisals),
        "themes": len(themes),
        "claims": len(claims),
        "represented_included_sources": len(included_source_ids & represented_source_ids),
        "missing_study_sources": missing_study_sources,
        "missing_finding_studies": missing_finding_studies,
        "missing_appraisal_studies": missing_appraisal_studies,
        "unused_findings": unused_findings,
        "themes_without_claims": themes_without_claims,
    }


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
    missing_documents = [
        source_id
        for source_id in unsummarized
        if not repo.load_metadata(source_id).managed_pdf_path
        and not repo.load_metadata(source_id).original_pdf_path
    ]
    coverage = synthesis_coverage(repo)
    included_unsummarized = [
        source_id for source_id in unsummarized if repo.load_state(source_id).status == SourceStatus.included
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
        recommendations = [
            f"dewey discover accept {relevant[0].candidate_id}",
            f"Accept or reject {len(relevant)} relevant candidate(s)",
        ]
    elif not source_ids:
        phase = "seed"
        recommendations = ["The last candidate set yielded no sources; broaden or revise the search"]
    elif included_unsummarized and included_unsummarized[0] in missing_documents:
        phase = "retrieve"
        recommendations = [
            f"dewey add document {included_unsummarized[0]} <paper.pdf>",
            f"Retrieve full text for {len([source_id for source_id in included_unsummarized if source_id in missing_documents])} included source(s) before summarizing",
        ]
    elif included_unsummarized:
        phase = "read"
        recommendations = [
            f"dewey summary set {included_unsummarized[0]} --text <summary>",
            f"Summarize {len(included_unsummarized)} included source(s)",
        ]
    elif coverage["missing_study_sources"]:
        phase = "extract"
        recommendations = [
            f"dewey study template --output study.json",
            f"dewey study create {coverage['missing_study_sources'][0]} --file study.json",
            f"Create study records for {len(coverage['missing_study_sources'])} included source(s)",
        ]
    elif coverage["missing_finding_studies"]:
        phase = "extract"
        recommendations = [
            "dewey finding template --output finding.json",
            f"dewey finding add {coverage['missing_finding_studies'][0]} --file finding.json",
            f"Extract findings for {len(coverage['missing_finding_studies'])} study record(s)",
        ]
    elif coverage["missing_appraisal_studies"]:
        phase = "appraise"
        recommendations = [
            "dewey appraisal template --output appraisal.json",
            f"dewey appraisal set {coverage['missing_appraisal_studies'][0]} --file appraisal.json",
            f"Appraise {len(coverage['missing_appraisal_studies'])} study record(s)",
        ]
    elif coverage["findings"] and not coverage["themes"]:
        phase = "synthesize"
        recommendations = [
            "dewey theme template --output theme.json",
            "dewey theme create --file theme.json",
            "Create themes that organize the extracted findings",
        ]
    elif coverage["unused_findings"]:
        phase = "synthesize"
        recommendations = [
            "dewey claim template --output claim.json",
            "dewey claim create --file claim.json",
            f"Connect {len(coverage['unused_findings'])} unused finding(s) to evidence-weighted claims",
        ]
    elif coverage["claims"] and EvidenceStore(repo.root).article_spec() is None:
        phase = "position"
        recommendations = [
            "dewey report article-template --output article.json",
            "Curate the field context, thesis, literature streams, study roles, timeline, and section logic",
            "dewey report article-set --file article.json",
        ]
    elif coverage["claims"] and not (repo.root / ".dewey" / "synthesis" / "article-brief.md").exists():
        phase = "report"
        recommendations = [
            "dewey report audit",
            "dewey report brief --output .dewey/synthesis/article-brief.md",
            "Use the brief to write the substantive Markdown article, then render it with Pandoc",
        ]
    elif coverage["claims"] and not (repo.root / ".dewey" / "synthesis" / "report-context.json").exists():
        phase = "report"
        recommendations = [
            "dewey report audit",
            "dewey report context --output .dewey/synthesis/report-context.json",
            "Use the report bundle to draft a traceable thematic report",
        ]
    elif unsummarized and unsummarized[0] in missing_documents:
        phase = "retrieve"
        recommendations = [
            f"dewey add document {unsummarized[0]} <paper.pdf>",
            f"Retrieve and screen {len(missing_documents)} metadata-only source(s)",
        ]
    elif unsummarized:
        phase = "read"
        recommendations = [
            f"dewey summary set {unsummarized[0]} --text <summary>",
            f"Summarize {len(unsummarized)} remaining source(s)",
        ]
    else:
        phase = "expand"
        recommendations = ["Traverse citations from a strong included source", "dewey traverse references <source-id>"]
    emit(
        {
            "ok": True,
            "action": action,
            "phase": phase,
            "next_steps": recommendations,
            "text": "\n".join(recommendations),
        },
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
    emit(
        {
            "ok": True,
            "action": action,
            "topic": config.topic,
            "research_question": config.research_question,
            "text": f"Topic: {config.topic}\nQuestion: {config.research_question}",
        },
        json_output,
    )


@topic_app.command("show")
def topic_show(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "topic.show"
    repo = load_repo(action, json_output)
    config = repo.load_config()
    emit(
        {
            "ok": True,
            "action": action,
            "topic": config.topic,
            "research_question": config.research_question,
            "text": f"Topic: {config.topic or '(unset)'}\nQuestion: {config.research_question or '(unset)'}",
        },
        json_output,
    )


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
    emit(
        {"ok": True, "action": action, "source_id": source_id, "summary": summary.rstrip(), "text": summary.rstrip()},
        json_output,
    )


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
        candidate_id=candidate_id(),
        title=title.strip(),
        authors=author,
        year=year,
        doi=doi,
        url=url,
        abstract=abstract,
        relevance_score=relevance_score(
            " ".join([title, abstract or ""]), config.topic or config.research_question or ""
        ),
        created_at=utc_now(),
    )
    stored = repo.add_candidate(candidate)
    repo.append_log(action, candidate_id=stored.candidate_id)
    emit(
        {
            "ok": True,
            "action": action,
            "candidate": stored.model_dump(mode="json"),
            "text": f"{stored.candidate_id}\t{stored.title}",
        },
        json_output,
    )


@discover_app.command("list")
def discover_list(
    status: CandidateStatus | None = typer.Option(None, "--status"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.list"
    repo = load_repo(action, json_output)
    candidates = [item for item in repo.load_discovery().candidates if status is None or item.status == status]
    candidates.sort(
        key=lambda item: (item.relevance_score is None, -(item.relevance_score or 0), item.title.casefold())
    )
    data = [item.model_dump(mode="json") for item in candidates]
    text_value = "\n".join(
        f"{item.candidate_id}\t{item.status.value}\t{item.relevance_score if item.relevance_score is not None else '-'}\t{item.title}"
        for item in candidates
    )
    emit({"ok": True, "action": action, "candidates": data, "text": text_value}, json_output)


@discover_app.command("dedupe")
def discover_dedupe(
    apply: bool = typer.Option(False, "--apply", help="Merge duplicate records; without this flag, only report them."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.dedupe"
    repo = load_repo(action, json_output)
    groups = repo.duplicate_candidate_groups()
    if not apply:
        emit(
            {
                "ok": True,
                "action": action,
                "applied": False,
                "groups": groups,
                "duplicates": sum(len(group["candidate_ids"]) - 1 for group in groups),
                "text": f"Found {len(groups)} duplicate group(s); rerun with --apply to merge them",
            },
            json_output,
        )
        return
    result = repo.deduplicate_candidates()
    repo.append_log(action, **result)
    emit(
        {
            "ok": True,
            "action": action,
            "applied": True,
            **result,
            "text": f"Merged {result['merged']} duplicate candidate(s); {result['after']} unique candidates remain",
        },
        json_output,
    )


def _candidate(repo: DeweyRepo, candidate_id_value: str) -> DiscoveryCandidate:
    for item in repo.load_discovery().candidates:
        if item.candidate_id == candidate_id_value:
            return item
    raise DeweyError("candidate_not_found", f"No discovery candidate exists for {candidate_id_value}", exit_code=4)


def add_discovery_citation_links(repo: DeweyRepo, candidate: DiscoveryCandidate, source_id: str, note: str) -> int:
    added = 0
    for provenance in candidate.provenance:
        parent = provenance.source_id
        if not parent or parent not in repo.list_source_ids():
            continue
        links = repo.load_links(parent)
        if any(link.target == source_id and link.type == LinkType.cites for link in links.outgoing):
            continue
        links.outgoing.append(LinkRecord(target=source_id, type=LinkType.cites, note=note, created_at=utc_now()))
        repo.write_links(parent, links)
        repo.index_source(parent)
        added += 1
    return added


@discover_app.command("decide")
def discover_decide(
    candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"),
    status: CandidateStatus = typer.Option(..., "--status"),
    rationale: str | None = typer.Option(None, "--rationale"),
    reviewer: str = typer.Option("agent", "--reviewer"),
    stage: ScreeningStage = typer.Option(ScreeningStage.title_abstract, "--stage"),
    criterion: list[str] = typer.Option([], "--criterion", help="Criterion as NAME=VALUE; repeat as needed."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.decide"
    repo = load_repo(action, json_output)
    if status == CandidateStatus.added:
        fail(action, "invalid_status", "Use discover accept to add a candidate", 2, json_output)
    criteria: dict[str, str] = {}
    for value in criterion:
        if "=" not in value or not value.split("=", 1)[0].strip():
            fail(action, "invalid_criterion", f"Expected NAME=VALUE, got {value!r}", 2, json_output)
        name, answer = value.split("=", 1)
        criteria[name.strip()] = answer.strip()
    discovery = repo.load_discovery()
    for index, item in enumerate(discovery.candidates):
        if item.candidate_id == candidate_id_value:
            decision = ScreeningDecision(
                decision={
                    CandidateStatus.relevant: ScreeningDecisionValue.include,
                    CandidateStatus.rejected: ScreeningDecisionValue.exclude,
                    CandidateStatus.candidate: ScreeningDecisionValue.maybe,
                }[status],
                stage=stage,
                reviewer=reviewer,
                rationale=rationale,
                criteria=criteria,
                decided_at=utc_now(),
            )
            discovery.candidates[index] = item.model_copy(
                update={
                    "status": status,
                    "rationale": rationale,
                    "screening_decisions": [*item.screening_decisions, decision],
                }
            )
            repo.write_discovery(discovery)
            repo.append_log(
                action,
                candidate_id=candidate_id_value,
                status=status.value,
                reviewer=reviewer,
                stage=stage.value,
                criteria=criteria,
            )
            emit(
                {
                    "ok": True,
                    "action": action,
                    "candidate": discovery.candidates[index].model_dump(mode="json"),
                    "text": f"{candidate_id_value}: {status.value}",
                },
                json_output,
            )
            return
    fail(action, "candidate_not_found", f"No discovery candidate exists for {candidate_id_value}", 4, json_output)


@discover_app.command("history")
def discover_history(
    candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.history"
    repo = load_repo(action, json_output)
    candidate = _candidate(repo, candidate_id_value)
    decisions = [item.model_dump(mode="json") for item in candidate.screening_decisions]
    text_value = "\n".join(
        f"{item.decided_at}\t{item.stage.value}\t{item.decision.value}\t{item.reviewer}\t{item.rationale or ''}"
        for item in candidate.screening_decisions
    )
    emit(
        {
            "ok": True,
            "action": action,
            "candidate_id": candidate_id_value,
            "decisions": decisions,
            "text": text_value or "No recorded screening decisions",
        },
        json_output,
    )


@screen_app.command("decide")
def screen_decide(
    candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"),
    stage: ScreeningStage = typer.Option(..., "--stage"),
    decision: ScreeningDecisionValue = typer.Option(..., "--decision"),
    reason: ExclusionReason | None = typer.Option(None, "--reason"),
    rationale: str | None = typer.Option(None, "--rationale"),
    reviewer: str = typer.Option("agent", "--reviewer"),
    protocol_version: str | None = typer.Option(None, "--protocol-version"),
    criterion: list[str] = typer.Option([], "--criterion", help="Criterion as NAME=VALUE; repeat as needed."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "screen.decide"
    repo = load_repo(action, json_output)
    if decision == ScreeningDecisionValue.exclude and reason is None:
        fail(action, "missing_reason", "Excluded records require --reason", 2, json_output)
    if decision != ScreeningDecisionValue.exclude and reason is not None:
        fail(action, "unexpected_reason", "--reason is only valid for an exclude decision", 2, json_output)
    criteria: dict[str, str] = {}
    for value in criterion:
        if "=" not in value or not value.split("=", 1)[0].strip():
            fail(action, "invalid_criterion", f"Expected NAME=VALUE, got {value!r}", 2, json_output)
        name, answer = value.split("=", 1)
        criteria[name.strip()] = answer.strip()
    discovery = repo.load_discovery()
    for index, candidate in enumerate(discovery.candidates):
        if candidate.candidate_id != candidate_id_value:
            continue
        record = ScreeningDecision(
            decision=decision,
            stage=stage,
            reviewer=reviewer,
            reason_code=reason.value if reason else None,
            rationale=rationale,
            criteria=criteria,
            protocol_version=protocol_version,
            decided_at=utc_now(),
        )
        current_status = candidate.status
        if current_status != CandidateStatus.added:
            current_status = {
                ScreeningDecisionValue.include: CandidateStatus.relevant,
                ScreeningDecisionValue.exclude: CandidateStatus.rejected,
                ScreeningDecisionValue.maybe: CandidateStatus.candidate,
            }[decision]
        updated = candidate.model_copy(
            update={
                "status": current_status,
                "rationale": rationale,
                "screening_decisions": [*candidate.screening_decisions, record],
            }
        )
        discovery.candidates[index] = updated
        repo.write_discovery(discovery)
        repo.append_log(
            action,
            candidate_id=candidate_id_value,
            stage=stage.value,
            decision=decision.value,
            reason=reason.value if reason else None,
            reviewer=reviewer,
            protocol_version=protocol_version,
        )
        emit(
            {
                "ok": True,
                "action": action,
                "candidate": updated.model_dump(mode="json"),
                "decision": record.model_dump(mode="json"),
                "text": f"{candidate_id_value}: {stage.value} {decision.value}",
            },
            json_output,
        )
        return
    fail(action, "candidate_not_found", f"No discovery candidate exists for {candidate_id_value}", 4, json_output)


@screen_app.command("history")
def screen_history(
    candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    discover_history(candidate_id_value, json_output)


def screening_conflicts(repo: DeweyRepo) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for candidate in repo.load_discovery().candidates:
        latest: dict[tuple[ScreeningStage, str], ScreeningDecision] = {}
        for decision in candidate.screening_decisions:
            latest[(decision.stage, decision.reviewer)] = decision
        for stage in ScreeningStage:
            stage_decisions = [record for (record_stage, _), record in latest.items() if record_stage == stage]
            values = {record.decision for record in stage_decisions}
            if len(values) > 1:
                conflicts.append(
                    {
                        "candidate_id": candidate.candidate_id,
                        "stage": stage.value,
                        "decisions": [record.model_dump(mode="json") for record in stage_decisions],
                    }
                )
    return conflicts


@screen_app.command("conflicts")
def screen_conflicts(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "screen.conflicts"
    repo = load_repo(action, json_output)
    conflicts = screening_conflicts(repo)
    emit(
        {
            "ok": True,
            "action": action,
            "conflicts": conflicts,
            "text": f"Found {len(conflicts)} unresolved screening conflict(s)",
        },
        json_output,
    )


@screen_app.command("audit")
def screen_audit(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "screen.audit"
    repo = load_repo(action, json_output)
    issues: list[dict[str, Any]] = []
    for candidate in repo.load_discovery().candidates:
        for decision in candidate.screening_decisions:
            if decision.decision == ScreeningDecisionValue.exclude and not decision.reason_code:
                issues.append(
                    {
                        "code": "exclusion_without_reason",
                        "candidate_id": candidate.candidate_id,
                        "stage": decision.stage.value,
                    }
                )
            if decision.reason_code == ExclusionReason.other.value and not decision.rationale:
                issues.append(
                    {
                        "code": "other_without_rationale",
                        "candidate_id": candidate.candidate_id,
                        "stage": decision.stage.value,
                    }
                )
    issues.extend({"code": "reviewer_conflict", **conflict} for conflict in screening_conflicts(repo))
    emit(
        {
            "ok": not issues,
            "action": action,
            "issues": issues,
            "text": f"Screening audit found {len(issues)} issue(s)",
        },
        json_output,
    )


@discover_app.command("accept")
def discover_accept(
    candidate_id_value: str = typer.Argument(..., metavar="CANDIDATE_ID"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "discovery.accept"
    repo = load_repo(action, json_output)
    discovery = repo.load_discovery()
    for index, item in enumerate(discovery.candidates):
        if item.candidate_id != candidate_id_value:
            continue
        if item.status == CandidateStatus.added:
            fail(
                action, "candidate_already_added", f"Candidate already added as {item.added_source_id}", 2, json_output
            )
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
        add_discovery_citation_links(repo, item, source_id, "Discovered from bibliography")
        repo.index_source(source_id)
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
                "text": f"Added {source_id}: {item.title}",
            },
            json_output,
        )
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
            fail(
                action,
                "candidate_already_added",
                f"Candidate already resolved as {item.added_source_id}",
                2,
                json_output,
            )
        add_discovery_citation_links(repo, item, source_id, "Resolved from bibliography")
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
def discover_export_triage(
    output: Path = typer.Option(..., "--output"), json_output: bool = typer.Option(False, "--json")
) -> None:
    action = "discovery.export_triage"
    repo = load_repo(action, json_output)
    config = repo.load_config()
    records = [
        edsl_triage_record(item, config.topic or "", config.research_question or "")
        for item in repo.load_discovery().candidates
        if item.status == CandidateStatus.candidate
    ]
    atomic_write_text(output, "".join(json.dumps(record) + "\n" for record in records))
    emit(
        {
            "ok": True,
            "action": action,
            "output": str(output),
            "records": len(records),
            "text": f"Wrote {len(records)} triage records to {output}",
        },
        json_output,
    )


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
        fail(
            action,
            "markdown_required",
            f"Render {source_id} to Markdown before traversing its references",
            2,
            json_output,
        )
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
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "extracted": len(fetched),
            "added": added,
            "text": f"Extracted {len(fetched)} references from the document; added {added} new candidates",
        },
        json_output,
    )


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
    emit(
        {"ok": True, "action": action, **result, "text": f"Wrote literature explorer to {result['path']}"}, json_output
    )


@export_app.command("zip")
def export_zip(
    output: Path | None = typer.Option(None, "--output", "-o"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "export.zip"
    repo = load_repo(action, json_output)
    try:
        result = write_project_archive(repo, output)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    repo.append_log(action, path=result["path"], files=result["files"], bytes=result["bytes"])
    emit(
        {
            "ok": True,
            "action": action,
            **result,
            "text": f"Wrote portable Dewey project ({result['files']} files) to {result['path']}",
        },
        json_output,
    )


@add_app.command("source")
def add_source(
    source: str,
    bibtex_key: str | None = typer.Option(None, "--bibtex-key"),
    no_md: bool = typer.Option(False, "--no-md"),
    force_duplicate: bool = typer.Option(False, "--force-duplicate"),
    copy_mode: bool = typer.Option(False, "--copy"),
    reference_mode: bool = typer.Option(False, "--reference"),
    backend: str = typer.Option("firecrawl", "--backend", help="Markdown backend: firecrawl or paper2md"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "source.add"
    repo = load_repo(action, json_output)
    parsed_source = urllib.parse.urlparse(source)
    is_url = parsed_source.scheme in {"http", "https"} and bool(parsed_source.netloc)
    if is_url:
        if backend != "firecrawl":
            fail(action, "invalid_backend", "URL sources require the firecrawl backend", 2, json_output)
        for existing_id in repo.list_source_ids():
            if repo.load_metadata(existing_id).markdown_source == source and not force_duplicate:
                emit(
                    {
                        "ok": True,
                        "action": action,
                        "source_id": existing_id,
                        "duplicate": True,
                        "reused_source_id": existing_id,
                        "text": f"Reused existing source {existing_id}",
                    },
                    json_output,
                )
                return
        name = Path(parsed_source.path).stem or parsed_source.netloc
        key = bibtex_key or slugify_key(name)
        entry = BibEntry(entry_type="misc", key=key, fields={"title": name, "url": source})
        try:
            source_id = repo.create_source(entry, markdown_source=source)
            if not no_md:
                markdown, version = convert_url_with_firecrawl(source)
                source_dir = repo.require_source_dir(source_id)
                markdown_path = source_dir / "source.md"
                atomic_write_text(markdown_path, markdown)
                metadata = repo.load_metadata(source_id)
                metadata.markdown_status = MarkdownStatus.ready
                metadata.markdown_path = str(markdown_path.relative_to(repo.root))
                metadata.markdown_generator.name = "firecrawl"
                metadata.markdown_generator.version = version
                metadata.updated_at = utc_now()
                repo.write_metadata(source_id, metadata)
            update_source_index(repo, source_id)
            repo.append_log(action, source_id=source_id, duplicate=False, input_type="url", url=source)
            emit(
                {
                    "ok": True,
                    "action": action,
                    "source_id": source_id,
                    "duplicate": False,
                    "input_type": "url",
                    "text": f"Added source {source_id}",
                },
                json_output,
            )
        except DeweyError as exc:
            fail(action, exc.code, exc.message, exc.exit_code, json_output)
        return

    path = Path(source).resolve()
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


@add_app.command("document")
def add_document(
    source_id: str,
    path: Path,
    replace: bool = typer.Option(False, "--replace"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Attach a retrieved PDF to an existing metadata-only source."""
    action = "source.attach_document"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    if not path.exists() or not path.is_file():
        fail(action, "file_not_found", f"No file exists at {path}", 4, json_output)
    if path.suffix.casefold() != ".pdf":
        fail(action, "invalid_document", "Attached documents must be PDFs", 2, json_output)
    metadata = repo.load_metadata(source_id)
    destination = repo.source_dir(source_id) / "source.pdf"
    if (metadata.managed_pdf_path or destination.exists()) and not replace:
        fail(action, "document_exists", f"A PDF already exists for {source_id}; use --replace", 2, json_output)
    resolved_input = path.resolve()
    if resolved_input != destination.resolve():
        shutil.copy2(resolved_input, destination)
    metadata.managed_pdf_path = str(destination.relative_to(repo.root))
    metadata.original_pdf_path = str(resolved_input)
    metadata.content_hash = sha256_file(destination)
    metadata.markdown_status = MarkdownStatus.missing
    metadata.markdown_path = None
    metadata.markdown_source = None
    metadata.updated_at = utc_now()
    repo.write_metadata(source_id, metadata)
    repo.index_source(source_id)
    repo.append_log(action, source_id=source_id, path=str(resolved_input), replaced=replace)
    emit({"ok": True, "action": action, "source_id": source_id, "pdf": metadata.managed_pdf_path, "text": f"Attached PDF to {source_id}"}, json_output)


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
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "raw": raw,
            "parsed": entry.as_dict(),
            "text": raw.rstrip(),
        },
        json_output,
    )


@bib_app.command("set")
def bib_set(
    source_id: str, file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")
) -> None:
    action = "bib.set"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    try:
        entry = parse_entry_file(file.resolve())
        existing = repo.existing_bibtex_keys(exclude_source_id=source_id)
        if entry.key in existing:
            raise DeweyError(
                "duplicate_bibtex_key", f"BibTeX key '{entry.key}' already exists in {existing[entry.key]}", 2
            )
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
            raise DeweyError(
                "duplicate_bibtex_key", f"BibTeX key '{updated.key}' already exists in {existing[updated.key]}", 2
            )
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
def cite(
    source_id: str, format: str = typer.Option("bibtex", "--format"), json_output: bool = typer.Option(False, "--json")
) -> None:
    action = "cite.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    entry = repo.load_entry(source_id)
    if format == "bibtex":
        text = dump_entry(entry).rstrip()
        payload = {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "format": format,
            "citation": text,
            "text": text,
        }
    elif format == "key":
        payload = {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "format": format,
            "citation": entry.key,
            "text": entry.key,
        }
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
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "status": status.value,
            "text": f"Set {source_id} to {status.value}",
        },
        json_output,
    )


@state_app.command("show")
def state_show(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "state.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    state = repo.load_state(source_id)
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "state": state.model_dump(),
            "text": json.dumps(state.model_dump(), indent=2),
        },
        json_output,
    )


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
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "priority": priority,
            "text": f"Set priority for {source_id} to {priority}",
        },
        json_output,
    )


@state_app.command("mark-read")
def state_mark_read(
    source_id: str,
    depth: ReadDepth = typer.Option(ReadDepth.full_text, "--depth"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "state.mark_read"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    metadata = repo.load_metadata(source_id)
    has_pdf = bool(metadata.managed_pdf_path or metadata.original_pdf_path)
    has_markdown = metadata.markdown_status == MarkdownStatus.ready
    if depth == ReadDepth.full_text and not (has_pdf or has_markdown):
        fail(
            action,
            "full_text_unavailable",
            (
                f"Cannot mark {source_id} full-text read: it has no PDF or ready Markdown. "
                "Retrieve the document first, or use --depth abstract for abstract-only screening."
            ),
            2,
            json_output,
        )
    state = repo.load_state(source_id)
    state.status = SourceStatus.read
    state.last_read_at = utc_now()
    state.read_depth = depth
    repo.write_state(source_id, state)
    update_source_index(repo, source_id)
    repo.append_log(action, source_id=source_id, read_depth=depth.value)
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "read_depth": depth.value,
            "text": f"Marked {source_id} as read ({depth.value})",
        },
        json_output,
    )


@notes_app.command("show")
def notes_show(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "notes.show"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    text = (repo.source_dir(source_id) / "notes.md").read_text(encoding="utf-8")
    emit({"ok": True, "action": action, "source_id": source_id, "notes": text, "text": text.rstrip()}, json_output)


@notes_app.command("set")
def notes_set(
    source_id: str, file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")
) -> None:
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
def notes_edit(
    source_id: str, append: str = typer.Option(..., "--append"), json_output: bool = typer.Option(False, "--json")
) -> None:
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
            emit(
                {
                    "ok": True,
                    "action": action,
                    "from": from_id,
                    "to": to_id,
                    "duplicate": True,
                    "text": "Link already exists",
                },
                json_output,
            )
            return
    links.outgoing.append(LinkRecord(target=to_id, type=type, note=note, created_at=utc_now()))
    repo.write_links(from_id, links)
    update_source_index(repo, from_id)
    repo.append_log(action, **{"from": from_id, "to": to_id, "type": type.value})
    emit(
        {
            "ok": True,
            "action": action,
            "from": from_id,
            "to": to_id,
            "type": type.value,
            "text": f"Linked {from_id} -> {to_id}",
        },
        json_output,
    )


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
    emit(
        {
            "ok": True,
            "action": action,
            "from": from_id,
            "to": to_id,
            "type": type.value,
            "text": f"Removed link {from_id} -> {to_id}",
        },
        json_output,
    )


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
    emit(
        {"ok": True, "action": action, "order": source_ids, "text": f"Set order for {len(source_ids)} source(s)"},
        json_output,
    )


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
    emit(
        {"ok": True, "action": action, "order": order.order, "text": f"Placed {source_id} in review order"}, json_output
    )


@order_app.command("remove")
def order_remove(source_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "order.remove"
    repo = load_repo(action, json_output)
    order = repo.load_order()
    order.order = [item for item in order.order if item != source_id]
    repo.write_order(order)
    repo.append_log(action, source_id=source_id)
    emit(
        {"ok": True, "action": action, "order": order.order, "text": f"Removed {source_id} from review order"},
        json_output,
    )


@instructions_app.command("show")
def instructions_show(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "instructions.show"
    repo = load_repo(action, json_output)
    text = repo.instructions_path.read_text(encoding="utf-8")
    emit({"ok": True, "action": action, "instructions": text, "text": text.rstrip()}, json_output)


@instructions_app.command("set")
def instructions_set(
    file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")
) -> None:
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
    backend: str = typer.Option("firecrawl", "--backend", help="Markdown backend: firecrawl or paper2md"),
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
        emit(
            {
                "ok": True,
                "action": action,
                "results": results,
                "text": f"Rendered Markdown for {len(results)} source(s)",
            },
            json_output,
        )
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
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "markdown_status": result.status.value,
            "text": f"Rendered Markdown for {source_id}",
        },
        json_output,
    )


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
    emit(
        {
            "ok": True,
            "action": action,
            "source_id": source_id,
            "representation": "md",
            "content": text,
            "text": text.rstrip(),
        },
        json_output,
    )


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
                payload = {
                    "ok": True,
                    "action": action,
                    "query": _query_payload(
                        query, title, author, bibtex, notes, fulltext, status, has_pdf, has_md, linked_to, link_type
                    ),
                    "results": [],
                    "text": "",
                }
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
            "query": _query_payload(
                query, title, author, bibtex, notes, fulltext, status, has_pdf, has_md, linked_to, link_type
            ),
            "results": results,
        }
        if not wants_json(json_output):
            payload["text"] = "\n".join(
                f"{item['source_id']}\t{item['bibtex_key']}\t{item['title']}" for item in results
            )
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
    for field_name, field_text in [
        ("bibtex", row["bibtex_text"]),
        ("notes", row["notes_text"]),
        ("markdown", row["markdown_text"]),
    ]:
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


def emit_template(action: str, template: dict[str, Any], output: Path | None, json_output: bool) -> None:
    rendered = json.dumps(template, indent=2) + "\n"
    if output:
        atomic_write_text(output, rendered)
    emit(
        {
            "ok": True,
            "action": action,
            "template": template,
            "output": str(output) if output else None,
            "text": f"Wrote template to {output}" if output else rendered.rstrip(),
        },
        json_output,
    )


@study_app.command("template")
def study_template(
    output: Path | None = typer.Option(None, "--output"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit_template(
        "study.template",
        {
            "label": "Short study label",
            "design": "Study design",
            "population": "Population",
            "sample_size": 0,
            "setting": "Setting",
            "intervention": "Intervention or exposure",
            "comparator": "Comparator",
            "methods": ["Method detail"],
            "measures": ["Outcome measure"],
        },
        output,
        json_output,
    )


@study_app.command("create")
def study_create(
    source_id: str,
    file: Path = typer.Option(..., "--file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "study.create"
    repo = load_repo(action, json_output)
    ensure_source_exists(repo, source_id, action, json_output)
    try:
        record = EvidenceStore(repo.root).create_study(load_json_object(file, action, json_output), source_id)
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_study"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, study_id=record.study_id, source_ids=record.source_ids)
    emit(
        {
            "ok": True,
            "action": action,
            "study": record.model_dump(mode="json"),
            "text": f"Created {record.study_id}: {record.label}",
        },
        json_output,
    )


@study_app.command("list")
def study_list(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "study.list"
    repo = load_repo(action, json_output)
    records = EvidenceStore(repo.root).studies()
    emit(
        {
            "ok": True,
            "action": action,
            "studies": [record.model_dump(mode="json") for record in records],
            "text": "\n".join(f"{record.study_id}\t{record.design}\t{record.label}" for record in records),
        },
        json_output,
    )


@study_app.command("show")
def study_show(study_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "study.show"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).study(study_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit({"ok": True, "action": action, "study": record.model_dump(mode="json"), "text": record.model_dump_json(indent=2)}, json_output)


@study_app.command("update")
def study_update(
    study_id: str,
    file: Path = typer.Option(..., "--file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "study.update"
    repo = load_repo(action, json_output)
    try:
        payload = load_json_object(file, action, json_output)
        source_ids = payload.get("source_ids")
        if source_ids is not None:
            for source_id in source_ids:
                ensure_source_exists(repo, source_id, action, json_output)
        record = EvidenceStore(repo.root).update_study(study_id, payload)
    except (TypeError, ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_study"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, study_id=study_id)
    emit({"ok": True, "action": action, "study": record.model_dump(mode="json"), "text": f"Updated {study_id}"}, json_output)


@study_app.command("delete")
def study_delete(
    study_id: str,
    cascade: bool = typer.Option(False, "--cascade"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "study.delete"
    repo = load_repo(action, json_output)
    try:
        deleted = EvidenceStore(repo.root).delete_study(study_id, cascade=cascade)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    repo.append_log(action, study_id=study_id, cascade=cascade, deleted=deleted)
    emit({"ok": True, "action": action, "deleted": deleted, "text": f"Deleted {study_id}"}, json_output)


@finding_app.command("template")
def finding_template(
    output: Path | None = typer.Option(None, "--output"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit_template(
        "finding.template",
        {
            "author_claim": "Authors' claim",
            "evidence_statement": "Result actually reported",
            "reviewer_interpretation": "Reviewer's bounded interpretation",
            "outcome": "Outcome",
            "direction": "positive, negative, mixed, or null",
            "population": "Population if finding-specific",
            "conditions": ["Relevant condition"],
            "measure": "Measure",
            "timepoint": "Timepoint",
            "certainty": "not-assessed",
            "locators": [{"page": "1", "section": "Results", "table": "Table 1"}],
        },
        output,
        json_output,
    )


@finding_app.command("add")
def finding_add(
    study_id: str,
    file: Path = typer.Option(..., "--file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "finding.add"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).create_finding(load_json_object(file, action, json_output), study_id)
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_finding"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, finding_id=record.finding_id, study_id=study_id)
    emit(
        {
            "ok": True,
            "action": action,
            "finding": record.model_dump(mode="json"),
            "text": f"Created {record.finding_id}: {record.outcome}",
        },
        json_output,
    )


@finding_app.command("list")
def finding_list(
    study_id: str | None = typer.Option(None, "--study"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "finding.list"
    repo = load_repo(action, json_output)
    records = [item for item in EvidenceStore(repo.root).findings() if study_id is None or item.study_id == study_id]
    emit(
        {
            "ok": True,
            "action": action,
            "findings": [record.model_dump(mode="json") for record in records],
            "text": "\n".join(f"{record.finding_id}\t{record.study_id}\t{record.outcome}" for record in records),
        },
        json_output,
    )


@finding_app.command("show")
def finding_show(finding_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "finding.show"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).finding(finding_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit({"ok": True, "action": action, "finding": record.model_dump(mode="json"), "text": record.model_dump_json(indent=2)}, json_output)


@finding_app.command("update")
def finding_update(
    finding_id: str,
    file: Path = typer.Option(..., "--file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "finding.update"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).update_finding(
            finding_id, load_json_object(file, action, json_output)
        )
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_finding"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, finding_id=finding_id)
    emit({"ok": True, "action": action, "finding": record.model_dump(mode="json"), "text": f"Updated {finding_id}"}, json_output)


@finding_app.command("delete")
def finding_delete(finding_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "finding.delete"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).delete_finding(finding_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    repo.append_log(action, finding_id=finding_id, study_id=record.study_id)
    emit({"ok": True, "action": action, "finding_id": finding_id, "text": f"Deleted {finding_id}"}, json_output)


@appraisal_app.command("template")
def appraisal_template(
    output: Path | None = typer.Option(None, "--output"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    emit_template(
        "appraisal.template",
        {
            "framework": "Appraisal framework",
            "framework_version": "1",
            "dimensions": [
                {
                    "name": "internal validity",
                    "judgment": "low, moderate, or high concern",
                    "rationale": "Reason for judgment",
                    "locators": [{"page": "1", "section": "Methods"}],
                }
            ],
            "overall_judgment": "Overall confidence",
            "applicability": "Applicability to the review question",
            "reviewer": "Reviewer name or process",
        },
        output,
        json_output,
    )


@appraisal_app.command("set")
def appraisal_set(
    study_id: str,
    file: Path = typer.Option(..., "--file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "appraisal.set"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).set_appraisal(load_json_object(file, action, json_output), study_id)
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_appraisal"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, appraisal_id=record.appraisal_id, study_id=study_id)
    emit(
        {
            "ok": True,
            "action": action,
            "appraisal": record.model_dump(mode="json"),
            "text": f"Set appraisal for {study_id}: {record.overall_judgment}",
        },
        json_output,
    )


@appraisal_app.command("show")
def appraisal_show(study_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "appraisal.show"
    repo = load_repo(action, json_output)
    record = EvidenceStore(repo.root).appraisal_for(study_id)
    if record is None:
        fail(action, "appraisal_not_found", f"No appraisal exists for {study_id}", 4, json_output)
    emit({"ok": True, "action": action, "appraisal": record.model_dump(mode="json"), "text": record.model_dump_json(indent=2)}, json_output)


@appraisal_app.command("list")
def appraisal_list(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "appraisal.list"
    repo = load_repo(action, json_output)
    records = EvidenceStore(repo.root).appraisals()
    emit(
        {
            "ok": True,
            "action": action,
            "appraisals": [record.model_dump(mode="json") for record in records],
            "text": "\n".join(
                f"{record.study_id}\t{record.overall_judgment}\t{record.framework}" for record in records
            ),
        },
        json_output,
    )


@appraisal_app.command("delete")
def appraisal_delete(study_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "appraisal.delete"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).delete_appraisal(study_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    repo.append_log(action, appraisal_id=record.appraisal_id, study_id=study_id)
    emit({"ok": True, "action": action, "study_id": study_id, "text": f"Deleted appraisal for {study_id}"}, json_output)


@synthesis_app.command("coverage")
def synthesis_coverage_command(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "synthesis.coverage"
    repo = load_repo(action, json_output)
    coverage = synthesis_coverage(repo)
    gaps = (
        len(coverage["missing_study_sources"])
        + len(coverage["missing_finding_studies"])
        + len(coverage["missing_appraisal_studies"])
    )
    text = (
        f"Included sources: {coverage['included_sources']} | represented: "
        f"{coverage['represented_included_sources']} | studies: {coverage['studies']} | "
        f"findings: {coverage['findings']} | appraisals: {coverage['appraisals']}\n"
        f"Missing study records: {len(coverage['missing_study_sources'])} | "
        f"studies without findings: {len(coverage['missing_finding_studies'])} | "
        f"studies without appraisals: {len(coverage['missing_appraisal_studies'])}"
    )
    emit({"ok": gaps == 0, "action": action, "coverage": coverage, "text": text}, json_output)


@theme_app.command("template")
def theme_template(output: Path | None = typer.Option(None, "--output"), json_output: bool = typer.Option(False, "--json")) -> None:
    emit_template(
        "theme.template",
        {"label": "Theme label", "description": "What this theme includes and excludes", "question_id": None},
        output,
        json_output,
    )


@theme_app.command("create")
def theme_create(file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "theme.create"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).create_theme(load_json_object(file, action, json_output))
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_theme"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, theme_id=record.theme_id)
    emit({"ok": True, "action": action, "theme": record.model_dump(mode="json"), "text": f"Created {record.theme_id}: {record.label}"}, json_output)


@theme_app.command("list")
def theme_list(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "theme.list"
    repo = load_repo(action, json_output)
    records = EvidenceStore(repo.root).themes()
    emit({"ok": True, "action": action, "themes": [item.model_dump(mode="json") for item in records], "text": "\n".join(f"{item.theme_id}\t{item.label}" for item in records)}, json_output)


@theme_app.command("show")
def theme_show(theme_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "theme.show"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).theme(theme_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit({"ok": True, "action": action, "theme": record.model_dump(mode="json"), "text": record.model_dump_json(indent=2)}, json_output)


@theme_app.command("update")
def theme_update(theme_id: str, file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "theme.update"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).update_theme(theme_id, load_json_object(file, action, json_output))
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_theme"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, theme_id=theme_id)
    emit({"ok": True, "action": action, "theme": record.model_dump(mode="json"), "text": f"Updated {theme_id}"}, json_output)


@theme_app.command("delete")
def theme_delete(theme_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "theme.delete"
    repo = load_repo(action, json_output)
    try:
        EvidenceStore(repo.root).delete_theme(theme_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    repo.append_log(action, theme_id=theme_id)
    emit({"ok": True, "action": action, "theme_id": theme_id, "text": f"Deleted {theme_id}"}, json_output)


@claim_app.command("template")
def claim_template(output: Path | None = typer.Option(None, "--output"), json_output: bool = typer.Option(False, "--json")) -> None:
    emit_template(
        "claim.template",
        {
            "theme_ids": ["theme_id"],
            "statement": "Bounded synthesis claim",
            "scope": "Population, setting, intervention, and limits",
            "evidence": [
                {"finding_id": "finding_id", "relationship": "supports", "rationale": "Why this finding bears on the claim"}
            ],
            "confidence": "low, moderate, or high",
            "confidence_rationale": "Evidence-weighted reason for confidence",
            "status": "draft",
        },
        output,
        json_output,
    )


@claim_app.command("create")
def claim_create(file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "claim.create"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).create_claim(load_json_object(file, action, json_output))
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_claim"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, claim_id=record.claim_id, theme_ids=record.theme_ids)
    emit({"ok": True, "action": action, "claim": record.model_dump(mode="json"), "text": f"Created {record.claim_id}: {record.statement}"}, json_output)


@claim_app.command("list")
def claim_list(theme_id: str | None = typer.Option(None, "--theme"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "claim.list"
    repo = load_repo(action, json_output)
    records = [item for item in EvidenceStore(repo.root).claims() if theme_id is None or theme_id in item.theme_ids]
    emit({"ok": True, "action": action, "claims": [item.model_dump(mode="json") for item in records], "text": "\n".join(f"{item.claim_id}\t{item.confidence}\t{item.statement}" for item in records)}, json_output)


@claim_app.command("show")
def claim_show(claim_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "claim.show"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).claim(claim_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit({"ok": True, "action": action, "claim": record.model_dump(mode="json"), "text": record.model_dump_json(indent=2)}, json_output)


@claim_app.command("update")
def claim_update(claim_id: str, file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")) -> None:
    action = "claim.update"
    repo = load_repo(action, json_output)
    try:
        record = EvidenceStore(repo.root).update_claim(claim_id, load_json_object(file, action, json_output))
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_claim"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, claim_id=claim_id)
    emit({"ok": True, "action": action, "claim": record.model_dump(mode="json"), "text": f"Updated {claim_id}"}, json_output)


@claim_app.command("delete")
def claim_delete(claim_id: str, json_output: bool = typer.Option(False, "--json")) -> None:
    action = "claim.delete"
    repo = load_repo(action, json_output)
    try:
        EvidenceStore(repo.root).delete_claim(claim_id)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    repo.append_log(action, claim_id=claim_id)
    emit({"ok": True, "action": action, "claim_id": claim_id, "text": f"Deleted {claim_id}"}, json_output)


@claim_app.command("audit")
def claim_audit(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "claim.audit"
    repo = load_repo(action, json_output)
    coverage = synthesis_coverage(repo)
    claims = EvidenceStore(repo.root).claims()
    issues: list[dict[str, Any]] = []
    for claim in claims:
        relationships = {link.relationship for link in claim.evidence}
        if "contradicts" not in relationships and "qualifies" not in relationships:
            issues.append({"code": "unqualified_claim", "claim_id": claim.claim_id})
    for finding_id in coverage["unused_findings"]:
        issues.append({"code": "unused_finding", "finding_id": finding_id})
    for theme_id in coverage["themes_without_claims"]:
        issues.append({"code": "theme_without_claims", "theme_id": theme_id})
    emit({"ok": not issues, "action": action, "issues": issues, "text": f"Claim audit found {len(issues)} issue(s)"}, json_output)


def report_readiness_issues(repo: DeweyRepo) -> list[dict[str, Any]]:
    store = EvidenceStore(repo.root)
    coverage = synthesis_coverage(repo)
    issues: list[dict[str, Any]] = []
    for source_id in coverage["missing_study_sources"]:
        issues.append({"code": "included_source_without_study", "source_id": source_id})
    for study_id in coverage["missing_finding_studies"]:
        issues.append({"code": "study_without_findings", "study_id": study_id})
    for study_id in coverage["missing_appraisal_studies"]:
        issues.append({"code": "study_without_appraisal", "study_id": study_id})
    for finding_id in coverage["unused_findings"]:
        issues.append({"code": "unused_finding", "finding_id": finding_id})
    for theme_id in coverage["themes_without_claims"]:
        issues.append({"code": "theme_without_claims", "theme_id": theme_id})
    for claim in store.claims():
        if claim.status != "reviewed":
            issues.append({"code": "draft_claim", "claim_id": claim.claim_id})
        relationships = {link.relationship for link in claim.evidence}
        if "contradicts" not in relationships and "qualifies" not in relationships:
            issues.append({"code": "unqualified_claim", "claim_id": claim.claim_id})
    return issues


def report_context_bundle(repo: DeweyRepo) -> dict[str, Any]:
    store = EvidenceStore(repo.root)
    config = repo.load_config()
    studies = {item.study_id: item for item in store.studies()}
    findings = {item.finding_id: item for item in store.findings()}
    appraisals = {item.study_id: item for item in store.appraisals()}
    claims = store.claims()
    source_ids = sorted({source_id for study in studies.values() for source_id in study.source_ids})
    sources: dict[str, dict[str, Any]] = {}
    for source_id in source_ids:
        entry = repo.load_entry(source_id)
        state = repo.load_state(source_id)
        sources[source_id] = {
            "source_id": source_id,
            "bibtex_key": entry.key,
            "title": entry.title(),
            "author": entry.fields.get("author"),
            "year": entry.year(),
            "doi": entry.fields.get("doi"),
            "url": entry.fields.get("url"),
            "status": state.status.value,
        }

    expanded_claims: dict[str, dict[str, Any]] = {}
    for claim in claims:
        evidence: list[dict[str, Any]] = []
        for link in claim.evidence:
            finding = findings[link.finding_id]
            study = studies[finding.study_id]
            appraisal = appraisals.get(study.study_id)
            evidence.append(
                {
                    "relationship": link.relationship,
                    "rationale": link.rationale,
                    "finding": finding.model_dump(mode="json"),
                    "study": study.model_dump(mode="json"),
                    "appraisal": appraisal.model_dump(mode="json") if appraisal else None,
                    "sources": [sources[source_id] for source_id in study.source_ids],
                }
            )
        expanded_claims[claim.claim_id] = {**claim.model_dump(mode="json"), "evidence": evidence}

    themes = []
    for theme in store.themes():
        themes.append(
            {
                **theme.model_dump(mode="json"),
                "claim_ids": [claim.claim_id for claim in claims if theme.theme_id in claim.theme_ids],
            }
        )
    issues = report_readiness_issues(repo)
    article = store.article_spec()
    return {
        "schema_version": "1",
        "generated_at": utc_now(),
        "review": {"topic": config.topic, "research_question": config.research_question},
        "readiness": {"ready": not issues, "issues": issues},
        "coverage": synthesis_coverage(repo),
        "writing_instructions": [
            "Organize the report by themes and claims, not by paper.",
            "Treat claim statements as bounded synthesis propositions, not immutable conclusions.",
            "Weight evidence using appraisal and applicability; do not count findings as equal votes.",
            "Represent supporting, contradicting, and qualifying evidence fairly.",
            "Preserve source locators for every substantive empirical statement.",
            "Do not infer that unused or unavailable evidence is negative evidence.",
        ],
        "themes": themes,
        "claims": [expanded_claims[claim.claim_id] for claim in claims],
        "sources": list(sources.values()),
        "article": article.model_dump(mode="json") if article else None,
    }


def validate_article_references(repo: DeweyRepo, payload: dict[str, Any]) -> None:
    store = EvidenceStore(repo.root)
    source_ids = set(repo.list_source_ids())
    theme_ids = {item.theme_id for item in store.themes()}
    claim_ids = {item.claim_id for item in store.claims()}
    referenced_sources = {
        source_id
        for group in payload.get("literatures", [])
        for source_id in group.get("source_ids", [])
    }
    referenced_sources.update(
        source_id for item in payload.get("timeline", []) for source_id in item.get("source_ids", [])
    )
    referenced_sources.update(item.get("source_id") for item in payload.get("source_positions", []))
    referenced_themes = {
        theme_id for section in payload.get("sections", []) for theme_id in section.get("theme_ids", [])
    }
    referenced_claims = {
        claim_id for section in payload.get("sections", []) for claim_id in section.get("claim_ids", [])
    }
    referenced_claims.update(
        claim_id for item in payload.get("source_positions", []) for claim_id in item.get("claim_ids", [])
    )
    missing = {
        "sources": sorted(referenced_sources - source_ids),
        "themes": sorted(referenced_themes - theme_ids),
        "claims": sorted(referenced_claims - claim_ids),
    }
    if any(missing.values()):
        raise DeweyError("invalid_article_references", f"Unknown article references: {json.dumps(missing)}", exit_code=2)


def render_report_markdown(bundle: dict[str, Any]) -> str:
    review = bundle["review"]
    lines = [
        f"# {review['topic'] or 'Literature review'}",
        "",
        f"**Research question:** {review['research_question'] or 'Not specified'}",
        "",
        "## Evidence status",
        "",
        f"Report-ready: **{'yes' if bundle['readiness']['ready'] else 'no'}**  ",
        f"Studies: {bundle['coverage']['studies']} · Findings: {bundle['coverage']['findings']} · "
        f"Appraisals: {bundle['coverage']['appraisals']} · Claims: {bundle['coverage']['claims']}",
        "",
        "## Drafting instructions",
        "",
    ]
    lines.extend(f"- {item}" for item in bundle["writing_instructions"])
    claims = {claim["claim_id"]: claim for claim in bundle["claims"]}
    rendered_claim_ids: set[str] = set()
    for theme in bundle["themes"]:
        lines.extend(["", f"## {theme['label']}", "", theme["description"]])
        for claim_id in theme["claim_ids"]:
            if claim_id in rendered_claim_ids:
                lines.extend(["", f"_Cross-theme claim: see `{claim_id}` above._"])
                continue
            rendered_claim_ids.add(claim_id)
            claim = claims[claim_id]
            lines.extend(
                [
                    "",
                    f"### Claim: {claim['statement']}",
                    "",
                    f"- **Scope:** {claim['scope']}",
                    f"- **Confidence:** {claim['confidence']}",
                    f"- **Rationale:** {claim['confidence_rationale']}",
                    "",
                    "| Relationship | Study | Finding | Locator | Appraisal |",
                    "|---|---|---|---|---|",
                ]
            )
            for item in claim["evidence"]:
                finding = item["finding"]
                study = item["study"]
                locators = "; ".join(
                    ", ".join(f"{key}: {value}" for key, value in locator.items() if value)
                    for locator in finding["locators"]
                )
                appraisal = item["appraisal"]["overall_judgment"] if item["appraisal"] else "not appraised"
                values = [item["relationship"], study["label"], finding["evidence_statement"], locators, appraisal]
                lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |")
    lines.extend(["", "## Reporting gaps", ""])
    if bundle["readiness"]["issues"]:
        lines.extend(f"- `{item['code']}`: {json.dumps(item, ensure_ascii=False)}" for item in bundle["readiness"]["issues"])
    else:
        lines.append("- No structural reporting gaps detected.")
    lines.extend(["", "## Sources", ""])
    for source in bundle["sources"]:
        citation = ", ".join(str(value) for value in (source["author"], source["year"], source["title"]) if value)
        lines.append(f"- `{source['source_id']}` — {citation}")
    return "\n".join(lines) + "\n"


@report_app.command("context")
def report_context(
    output: Path | None = typer.Option(None, "--output"),
    format: str = typer.Option("json", "--format"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "report.context"
    repo = load_repo(action, json_output)
    bundle = report_context_bundle(repo)
    if format == "json":
        rendered = json.dumps(bundle, indent=2, ensure_ascii=False) + "\n"
    elif format == "markdown":
        rendered = render_report_markdown(bundle)
    else:
        fail(action, "invalid_format", "--format must be json or markdown", 2, json_output)
    if output:
        atomic_write_text(output, rendered)
    emit(
        {
            "ok": True,
            "action": action,
            "bundle": bundle,
            "output": str(output) if output else None,
            "format": format,
            "text": f"Wrote report context to {output}" if output else rendered.rstrip(),
        },
        json_output,
    )


@report_app.command("audit")
def report_audit(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "report.audit"
    repo = load_repo(action, json_output)
    issues = report_readiness_issues(repo)
    emit({"ok": not issues, "action": action, "issues": issues, "text": f"Report audit found {len(issues)} issue(s)"}, json_output)


@report_app.command("article-template")
def report_article_template(
    output: Path = typer.Option(Path("article.json"), "--output"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "report.article-template"
    payload = {
        "title": "Article title",
        "subtitle": None,
        "audience": "Economists and adjacent social scientists",
        "genre": "economics literature review",
        "abstract": "One-paragraph statement of the question, synthesis, and contribution.",
        "keywords": ["keyword"],
        "jel_codes": ["C83"],
        "motivation": ["Why the topic matters before discussing individual studies."],
        "field_context": ["The established tradeoff or intellectual problem that organizes the field."],
        "central_question": "What does this literature establish, and what remains unresolved?",
        "thesis": "The review's bounded answer to the central question.",
        "contribution": ["How this review reorganizes or connects existing literatures."],
        "scope_includes": ["Included populations, technologies, outcomes, or periods."],
        "scope_excludes": ["Adjacent evidence outside the review's inferential scope."],
        "literatures": [{"stream_id": "stream_1", "label": "Literature stream", "description": "Its question and methods.", "source_ids": ["src_id"], "relationship_to_review": "How it contributes to the article's argument."}],
        "source_positions": [{"source_id": "src_id", "role": "foundational", "contribution": "What this study adds.", "claim_ids": ["claim_id"], "caveat": "What it cannot establish."}],
        "timeline": [{"year": 2020, "label": "Intellectual or empirical development", "significance": "Why this changes the field.", "source_ids": ["src_id"]}],
        "sections": [{"heading": "Introduction", "purpose": "Motivate the problem, state the thesis, and preview the argument.", "theme_ids": [], "claim_ids": []}],
        "conclusion": ["The main implication and research agenda."],
    }
    atomic_write_text(output, json.dumps(payload, indent=2) + "\n")
    emit({"ok": True, "action": action, "output": str(output), "text": f"Wrote article template to {output}"}, json_output)


@report_app.command("article-set")
def report_article_set(
    file: Path = typer.Option(..., "--file"), json_output: bool = typer.Option(False, "--json")
) -> None:
    action = "report.article-set"
    repo = load_repo(action, json_output)
    payload = load_json_object(file, action, json_output)
    try:
        validate_article_references(repo, payload)
        record = EvidenceStore(repo.root).set_article_spec(payload)
    except (ValueError, DeweyError) as exc:
        fail(action, getattr(exc, "code", "invalid_article_spec"), str(exc), getattr(exc, "exit_code", 2), json_output)
    repo.append_log(action, title=record.title)
    emit({"ok": True, "action": action, "article": record.model_dump(mode="json"), "text": f"Set article specification: {record.title}"}, json_output)


@report_app.command("article-show")
def report_article_show(json_output: bool = typer.Option(False, "--json")) -> None:
    action = "report.article-show"
    repo = load_repo(action, json_output)
    record = EvidenceStore(repo.root).article_spec()
    if record is None:
        fail(action, "article_spec_not_found", "No article specification exists; run report article-template and article-set", 4, json_output)
    emit({"ok": True, "action": action, "article": record.model_dump(mode="json"), "text": json.dumps(record.model_dump(mode="json"), indent=2)}, json_output)


@report_app.command("brief")
def report_brief(
    output: Path = typer.Option(Path("article-brief.md"), "--output"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "report.brief"
    repo = load_repo(action, json_output)
    spec = EvidenceStore(repo.root).article_spec()
    if spec is None:
        fail(action, "article_spec_not_found", "No article specification exists; run report article-template and article-set", 4, json_output)
    rendered = article_brief(spec, report_context_bundle(repo))
    atomic_write_text(output, rendered)
    emit({"ok": True, "action": action, "output": str(output), "text": f"Wrote article brief to {output}"}, json_output)


@report_app.command("render")
def report_render(
    markdown: Path,
    output: Path = typer.Option(..., "--output"),
    css: Path | None = typer.Option(None, "--css"),
    embed_explorer_path: Path | None = typer.Option(None, "--embed-explorer"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "report.render"
    load_repo(action, json_output)
    if not markdown.exists():
        fail(action, "file_not_found", f"No file exists at {markdown}", 4, json_output)
    try:
        render_with_pandoc(markdown, output, css)
        if embed_explorer_path is not None:
            embed_explorer(output, embed_explorer_path)
    except DeweyError as exc:
        fail(action, exc.code, exc.message, exc.exit_code, json_output)
    emit({"ok": True, "action": action, "input": str(markdown), "output": str(output), "text": f"Rendered {output} from {markdown}"}, json_output)


def evidence_matrix_rows(repo: DeweyRepo) -> list[dict[str, Any]]:
    store = EvidenceStore(repo.root)
    studies = {item.study_id: item for item in store.studies()}
    appraisals = {item.study_id: item for item in store.appraisals()}
    rows: list[dict[str, Any]] = []
    for finding in store.findings():
        study = studies.get(finding.study_id)
        if study is None:
            continue
        appraisal = appraisals.get(study.study_id)
        rows.append(
            {
                "study_id": study.study_id,
                "finding_id": finding.finding_id,
                "source_ids": study.source_ids,
                "study": study.label,
                "design": study.design,
                "population": finding.population or study.population,
                "sample_size": study.sample_size,
                "setting": study.setting,
                "intervention": study.intervention,
                "comparator": study.comparator,
                "outcome": finding.outcome,
                "direction": finding.direction,
                "measure": finding.measure,
                "author_claim": finding.author_claim,
                "evidence_statement": finding.evidence_statement,
                "reviewer_interpretation": finding.reviewer_interpretation,
                "certainty": finding.certainty,
                "locators": [item.model_dump(mode="json", exclude_none=True) for item in finding.locators],
                "appraisal_framework": appraisal.framework if appraisal else None,
                "overall_judgment": appraisal.overall_judgment if appraisal else None,
                "applicability": appraisal.applicability if appraisal else None,
            }
        )
    return rows


@matrix_app.command("evidence")
def matrix_evidence(
    output: Path | None = typer.Option(None, "--output"),
    format: str = typer.Option("json", "--format"),
    study_id: str | None = typer.Option(None, "--study"),
    source_id: str | None = typer.Option(None, "--source"),
    outcome: str | None = typer.Option(None, "--outcome"),
    design: str | None = typer.Option(None, "--design"),
    judgment: str | None = typer.Option(None, "--judgment"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    action = "matrix.evidence"
    repo = load_repo(action, json_output)
    rows = evidence_matrix_rows(repo)
    if study_id:
        rows = [row for row in rows if row["study_id"] == study_id]
    if source_id:
        rows = [row for row in rows if source_id in row["source_ids"]]
    if outcome:
        rows = [row for row in rows if outcome.lower() in row["outcome"].lower()]
    if design:
        rows = [row for row in rows if design.lower() in row["design"].lower()]
    if judgment:
        rows = [
            row
            for row in rows
            if row["overall_judgment"] and judgment.lower() in row["overall_judgment"].lower()
        ]
    if format not in {"json", "csv", "markdown"}:
        fail(action, "invalid_format", "--format must be json, csv, or markdown", 2, json_output)
    if format == "json":
        rendered = json.dumps(rows, indent=2) + "\n"
    elif format == "csv":
        buffer = io.StringIO()
        fieldnames = list(rows[0]) if rows else ["study_id", "finding_id"]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
                    for key, value in row.items()
                }
            )
        rendered = buffer.getvalue()
    else:
        fields = ("study", "outcome", "direction", "certainty", "overall_judgment")
        rendered = "| " + " | ".join(fields) + " |\n"
        rendered += "| " + " | ".join("---" for _ in fields) + " |\n"
        for row in rows:
            rendered += "| " + " | ".join(str(row[field] or "").replace("|", "\\|") for field in fields) + " |\n"
    if output:
        atomic_write_text(output, rendered)
    emit(
        {
            "ok": True,
            "action": action,
            "rows": rows,
            "output": str(output) if output else None,
            "format": format,
            "text": f"Wrote {len(rows)} evidence row(s) to {output}" if output else rendered.rstrip(),
        },
        json_output,
    )


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
