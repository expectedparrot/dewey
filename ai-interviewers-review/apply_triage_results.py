"""Validate and apply reviewed EDSL title/citation triage decisions to Dewey."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from dewey.models import (
    CandidateStatus,
    ScreeningDecision,
    ScreeningDecisionValue,
    ScreeningStage,
)
from dewey.repo import DeweyRepo, utc_now


INPUT = Path("triage-2026-08-13_decisions.json")
PROTOCOL = "model-title-citation-triage-2026-08-13"
REVIEWER = "openai:gpt-4.1-mini"

rows = json.loads(INPUT.read_text(encoding="utf-8"))
if len(rows) != 871:
    raise ValueError(f"Expected 871 decisions, found {len(rows)}")

repo = DeweyRepo.discover()
discovery = repo.load_discovery()
by_id = {candidate.candidate_id: index for index, candidate in enumerate(discovery.candidates)}
seen: set[str] = set()
counts: Counter[str] = Counter()

status_for = {
    "include": CandidateStatus.relevant,
    "exclude": CandidateStatus.rejected,
    "maybe": CandidateStatus.candidate,
}
decision_for = {
    "include": ScreeningDecisionValue.include,
    "exclude": ScreeningDecisionValue.exclude,
    "maybe": ScreeningDecisionValue.maybe,
}

for row in rows:
    candidate_id = row["scenario.candidate_id"]
    answer = row["answer.triage"]
    decision = answer["decision"]
    score = answer["score"]
    rationale = answer["rationale"].strip()

    if candidate_id in seen:
        raise ValueError(f"Duplicate result for {candidate_id}")
    seen.add(candidate_id)
    if candidate_id not in by_id:
        raise ValueError(f"Unknown candidate {candidate_id}")
    if decision not in status_for:
        raise ValueError(f"Invalid decision {decision!r} for {candidate_id}")
    if not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise ValueError(f"Invalid score {score!r} for {candidate_id}")
    if not rationale:
        raise ValueError(f"Missing rationale for {candidate_id}")

    index = by_id[candidate_id]
    candidate = discovery.candidates[index]
    if candidate.status != CandidateStatus.candidate:
        raise ValueError(f"Candidate {candidate_id} is no longer unresolved: {candidate.status.value}")

    record = ScreeningDecision(
        decision=decision_for[decision],
        stage=ScreeningStage.title_abstract,
        reviewer=REVIEWER,
        reason_code="other" if decision == "exclude" else None,
        rationale=rationale,
        criteria={
            "model_relevance_score": str(score),
            "evidence_available": "title-citation-only",
            "human_review": "include-set-inspected",
        },
        protocol_version=PROTOCOL,
        decided_at=utc_now(),
    )
    discovery.candidates[index] = candidate.model_copy(
        update={
            "status": status_for[decision],
            "relevance_score": float(score),
            "rationale": rationale,
            "screening_decisions": [*candidate.screening_decisions, record],
        }
    )
    counts[decision] += 1

if len(seen) != len(rows):
    raise ValueError("Result IDs were not unique")

repo.write_discovery(discovery)
repo.append_log(
    "screen.batch_apply",
    protocol_version=PROTOCOL,
    reviewer=REVIEWER,
    source_file=str(INPUT),
    records=len(rows),
    counts=dict(counts),
)
print(json.dumps({"applied": len(rows), "counts": dict(counts)}, indent=2))
