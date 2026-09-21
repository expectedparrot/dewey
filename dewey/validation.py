"""Structural checks shared by doctor and Git synchronization."""
from __future__ import annotations

import sqlite3
from typing import Any

from pydantic import ValidationError

from dewey.bibtex import BibTeXError
from dewey.evidence import EvidenceStore
from dewey.repo import DeweyError, DeweyRepo, sha256_file


def project_issues(repo: DeweyRepo) -> list[dict[str, Any]]:
    try:
        return _project_issues(repo)
    except (DeweyError, ValidationError, OSError, ValueError, TypeError, KeyError) as exc:
        return [{"code": "invalid_project", "message": str(exc)}]


def _project_issues(repo: DeweyRepo) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    top_level = [repo.config_path, repo.instructions_path, repo.order_path, repo.discovery_path, repo.history_path]
    for path in top_level:
        if not path.exists():
            issues.append({"code": "missing_file", "path": str(path)})
    if issues:
        return issues
    repo.load_config()
    source_ids = set(repo.list_source_ids())
    bibtex_keys: dict[str, str] = {}
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
        if entry.key in bibtex_keys:
            issues.append({"code": "duplicate_bibtex_key", "source_id": source_id, "other_source_id": bibtex_keys[entry.key]})
        bibtex_keys[entry.key] = source_id
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
        # Reference-only PDF paths are deliberately local. Their content hash still
        # identifies the input when the extracted Markdown is cloned elsewhere.
        if metadata.markdown_path and not (
            metadata.managed_pdf_path or metadata.original_pdf_path or metadata.content_hash
        ):
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
    if issues:
        return issues
    try:
        repo.rebuild_index()
        repo.stats()
    except sqlite3.Error as exc:
        issues.append({"code": "index_error", "message": str(exc)})
    return issues
