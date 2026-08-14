from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from dewey.models import AppraisalRecord, ArticleSpec, ClaimRecord, FindingRecord, StudyRecord, ThemeRecord
from dewey.repo import DeweyError, atomic_write_json, read_json, utc_now


Record = TypeVar("Record", bound=BaseModel)


def evidence_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EvidenceStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.base = root / ".dewey" / "synthesis"
        self.studies_dir = self.base / "studies"
        self.findings_dir = self.base / "findings"
        self.appraisals_dir = self.base / "appraisals"
        self.themes_dir = self.base / "themes"
        self.claims_dir = self.base / "claims"
        self.article_spec_path = self.base / "article.json"

    def ensure(self) -> None:
        for path in (self.studies_dir, self.findings_dir, self.appraisals_dir, self.themes_dir, self.claims_dir):
            path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _load(path: Path, model: type[Record], kind: str) -> Record:
        try:
            return model.model_validate(read_json(path))
        except ValidationError as exc:
            raise DeweyError(f"invalid_{kind}", f"Invalid {kind} record at {path}: {exc}", exit_code=3) from exc

    @staticmethod
    def _list(directory: Path, model: type[Record], kind: str) -> list[Record]:
        if not directory.exists():
            return []
        return [EvidenceStore._load(path, model, kind) for path in sorted(directory.glob("*.json"))]

    def studies(self) -> list[StudyRecord]:
        return self._list(self.studies_dir, StudyRecord, "study")

    def findings(self) -> list[FindingRecord]:
        return self._list(self.findings_dir, FindingRecord, "finding")

    def appraisals(self) -> list[AppraisalRecord]:
        return self._list(self.appraisals_dir, AppraisalRecord, "appraisal")

    def themes(self) -> list[ThemeRecord]:
        return self._list(self.themes_dir, ThemeRecord, "theme")

    def claims(self) -> list[ClaimRecord]:
        return self._list(self.claims_dir, ClaimRecord, "claim")

    def study(self, study_id: str) -> StudyRecord:
        path = self.studies_dir / f"{study_id}.json"
        if not path.exists():
            raise DeweyError("study_not_found", f"No study exists for {study_id}", exit_code=4)
        return self._load(path, StudyRecord, "study")

    def finding(self, finding_id: str) -> FindingRecord:
        path = self.findings_dir / f"{finding_id}.json"
        if not path.exists():
            raise DeweyError("finding_not_found", f"No finding exists for {finding_id}", exit_code=4)
        return self._load(path, FindingRecord, "finding")

    def appraisal_for(self, study_id: str) -> AppraisalRecord | None:
        return next((item for item in self.appraisals() if item.study_id == study_id), None)

    def theme(self, theme_id: str) -> ThemeRecord:
        path = self.themes_dir / f"{theme_id}.json"
        if not path.exists():
            raise DeweyError("theme_not_found", f"No theme exists for {theme_id}", exit_code=4)
        return self._load(path, ThemeRecord, "theme")

    def claim(self, claim_id: str) -> ClaimRecord:
        path = self.claims_dir / f"{claim_id}.json"
        if not path.exists():
            raise DeweyError("claim_not_found", f"No claim exists for {claim_id}", exit_code=4)
        return self._load(path, ClaimRecord, "claim")

    def article_spec(self) -> ArticleSpec | None:
        if not self.article_spec_path.exists():
            return None
        return self._load(self.article_spec_path, ArticleSpec, "article_spec")

    def set_article_spec(self, payload: dict[str, Any]) -> ArticleSpec:
        self.ensure()
        data = {key: value for key, value in payload.items() if key != "updated_at"}
        record = ArticleSpec.model_validate({**data, "updated_at": utc_now()})
        atomic_write_json(self.article_spec_path, record.model_dump(mode="json"))
        return record

    def create_study(self, payload: dict[str, Any], source_id: str) -> StudyRecord:
        self.ensure()
        now = utc_now()
        data = dict(payload)
        source_ids = list(data.pop("source_ids", []))
        if source_id not in source_ids:
            source_ids.insert(0, source_id)
        record = StudyRecord.model_validate(
            {**data, "study_id": evidence_id("study"), "source_ids": source_ids, "created_at": now, "updated_at": now}
        )
        atomic_write_json(self.studies_dir / f"{record.study_id}.json", record.model_dump(mode="json"))
        return record

    def update_study(self, study_id: str, payload: dict[str, Any]) -> StudyRecord:
        existing = self.study(study_id)
        data = existing.model_dump(mode="json")
        data.update({key: value for key, value in payload.items() if key not in {"study_id", "created_at", "updated_at"}})
        data.update({"study_id": study_id, "created_at": existing.created_at, "updated_at": utc_now()})
        record = StudyRecord.model_validate(data)
        atomic_write_json(self.studies_dir / f"{study_id}.json", record.model_dump(mode="json"))
        return record

    def delete_study(self, study_id: str, cascade: bool = False) -> dict[str, int]:
        self.study(study_id)
        findings = [item for item in self.findings() if item.study_id == study_id]
        appraisals = [item for item in self.appraisals() if item.study_id == study_id]
        if (findings or appraisals) and not cascade:
            raise DeweyError(
                "study_has_evidence",
                f"{study_id} has {len(findings)} finding(s) and {len(appraisals)} appraisal(s); use --cascade",
                exit_code=2,
            )
        for finding in findings:
            (self.findings_dir / f"{finding.finding_id}.json").unlink()
        for appraisal in appraisals:
            (self.appraisals_dir / f"{appraisal.appraisal_id}.json").unlink()
        (self.studies_dir / f"{study_id}.json").unlink()
        return {"studies": 1, "findings": len(findings), "appraisals": len(appraisals)}

    def create_finding(self, payload: dict[str, Any], study_id: str) -> FindingRecord:
        self.ensure()
        self.study(study_id)
        now = utc_now()
        data = {key: value for key, value in payload.items() if key not in {"finding_id", "study_id", "created_at", "updated_at"}}
        record = FindingRecord.model_validate(
            {**data, "finding_id": evidence_id("finding"), "study_id": study_id, "created_at": now, "updated_at": now}
        )
        atomic_write_json(self.findings_dir / f"{record.finding_id}.json", record.model_dump(mode="json"))
        return record

    def update_finding(self, finding_id: str, payload: dict[str, Any]) -> FindingRecord:
        existing = self.finding(finding_id)
        data = existing.model_dump(mode="json")
        data.update(
            {
                key: value
                for key, value in payload.items()
                if key not in {"finding_id", "study_id", "created_at", "updated_at"}
            }
        )
        data.update(
            {
                "finding_id": finding_id,
                "study_id": existing.study_id,
                "created_at": existing.created_at,
                "updated_at": utc_now(),
            }
        )
        record = FindingRecord.model_validate(data)
        atomic_write_json(self.findings_dir / f"{finding_id}.json", record.model_dump(mode="json"))
        return record

    def delete_finding(self, finding_id: str) -> FindingRecord:
        record = self.finding(finding_id)
        (self.findings_dir / f"{finding_id}.json").unlink()
        return record

    def set_appraisal(self, payload: dict[str, Any], study_id: str) -> AppraisalRecord:
        self.ensure()
        self.study(study_id)
        existing = self.appraisal_for(study_id)
        now = utc_now()
        data = {key: value for key, value in payload.items() if key not in {"appraisal_id", "study_id", "created_at", "updated_at"}}
        record = AppraisalRecord.model_validate(
            {
                **data,
                "appraisal_id": existing.appraisal_id if existing else evidence_id("appraisal"),
                "study_id": study_id,
                "created_at": existing.created_at if existing else now,
                "updated_at": now,
            }
        )
        if existing:
            (self.appraisals_dir / f"{existing.appraisal_id}.json").unlink(missing_ok=True)
        atomic_write_json(self.appraisals_dir / f"{record.appraisal_id}.json", record.model_dump(mode="json"))
        return record

    def delete_appraisal(self, study_id: str) -> AppraisalRecord:
        record = self.appraisal_for(study_id)
        if record is None:
            raise DeweyError("appraisal_not_found", f"No appraisal exists for {study_id}", exit_code=4)
        (self.appraisals_dir / f"{record.appraisal_id}.json").unlink()
        return record

    def create_theme(self, payload: dict[str, Any]) -> ThemeRecord:
        self.ensure()
        now = utc_now()
        data = {key: value for key, value in payload.items() if key not in {"theme_id", "created_at", "updated_at"}}
        record = ThemeRecord.model_validate(
            {**data, "theme_id": evidence_id("theme"), "created_at": now, "updated_at": now}
        )
        atomic_write_json(self.themes_dir / f"{record.theme_id}.json", record.model_dump(mode="json"))
        return record

    def update_theme(self, theme_id: str, payload: dict[str, Any]) -> ThemeRecord:
        existing = self.theme(theme_id)
        data = existing.model_dump(mode="json")
        data.update({key: value for key, value in payload.items() if key not in {"theme_id", "created_at", "updated_at"}})
        data.update({"theme_id": theme_id, "created_at": existing.created_at, "updated_at": utc_now()})
        record = ThemeRecord.model_validate(data)
        atomic_write_json(self.themes_dir / f"{theme_id}.json", record.model_dump(mode="json"))
        return record

    def delete_theme(self, theme_id: str) -> ThemeRecord:
        record = self.theme(theme_id)
        used_by = [claim.claim_id for claim in self.claims() if theme_id in claim.theme_ids]
        if used_by:
            raise DeweyError("theme_has_claims", f"{theme_id} is used by claim(s): {', '.join(used_by)}", exit_code=2)
        (self.themes_dir / f"{theme_id}.json").unlink()
        return record

    def create_claim(self, payload: dict[str, Any]) -> ClaimRecord:
        self.ensure()
        now = utc_now()
        data = {key: value for key, value in payload.items() if key not in {"claim_id", "created_at", "updated_at"}}
        for theme_id in data.get("theme_ids", []):
            self.theme(theme_id)
        for link in data.get("evidence", []):
            self.finding(link.get("finding_id", ""))
        record = ClaimRecord.model_validate(
            {**data, "claim_id": evidence_id("claim"), "created_at": now, "updated_at": now}
        )
        atomic_write_json(self.claims_dir / f"{record.claim_id}.json", record.model_dump(mode="json"))
        return record

    def update_claim(self, claim_id: str, payload: dict[str, Any]) -> ClaimRecord:
        existing = self.claim(claim_id)
        data = existing.model_dump(mode="json")
        data.update({key: value for key, value in payload.items() if key not in {"claim_id", "created_at", "updated_at"}})
        for theme_id in data.get("theme_ids", []):
            self.theme(theme_id)
        for link in data.get("evidence", []):
            self.finding(link.get("finding_id", ""))
        data.update({"claim_id": claim_id, "created_at": existing.created_at, "updated_at": utc_now()})
        record = ClaimRecord.model_validate(data)
        atomic_write_json(self.claims_dir / f"{claim_id}.json", record.model_dump(mode="json"))
        return record

    def delete_claim(self, claim_id: str) -> ClaimRecord:
        record = self.claim(claim_id)
        (self.claims_dir / f"{claim_id}.json").unlink()
        return record
