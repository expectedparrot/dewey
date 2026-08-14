"""Apply human-reviewed second-pass adjudication to unresolved Dewey candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from dewey.models import CandidateStatus, ScreeningDecision, ScreeningDecisionValue, ScreeningStage
from dewey.repo import DeweyRepo, utc_now


INPUT = Path("triage-maybes-2026-08-13_decisions.json")
PROTOCOL = "human-reviewed-gpt41-adjudication-2026-08-13"

# Every model-proposed retrieval was inspected. These are the distinct leads that
# remain sufficiently relevant to retrieve; repeated citations and false matches
# from truncated records are excluded below with an explicit human-review marker.
RETRIEVE = {
    "cand_4e20f503aaf2",  # Collecting Social Data with LLMs
    "cand_6aa2462b723f",  # social presence in web/IVR surveys
    "cand_b6097aaf7bb1",  # reciprocal disclosure with virtual interviewer
    "cand_45516c617b14",  # conversational interviewing and measurement error
    "cand_32e0bb40f433",  # interactive feedback in web surveys
    "cand_8d5d24d2f6e6",  # SimSensei
    "cand_485594b69eef",  # virtual humans and disclosure
    "cand_7e449874a0bf",  # personification/interactivity and disclosure
    "cand_2cdb0d799a36",  # virtual interviewer comprehension/engagement
    "cand_01a1e66a334d",  # interviewer style and reporting quality
    "cand_edced7d9ce37",  # disclosure to computers
    "cand_81593808773d",  # conversational survey interface
    "cand_a91e234c20f0",  # chatbot and deep self-disclosure
    "cand_801adc5bb7a7",  # embodiment/relevance and social desirability
    "cand_55b79011571b",  # conversational course evaluations
    "cand_3b9bf78d8487",  # bots and experimenter effects
    "cand_3216a2724232",  # human dialogue features in web surveys
    "cand_268f9746fc0a",  # interactional trouble benchmark
    "cand_a37d1c46a28d",  # chatbot formality and disclosure
    "cand_88ab07f22fe4",  # follow-up question generation
    "cand_d88d82836fd8",  # conversational survey frontends
    "cand_f632e43ef07a",  # AI interviewer landscape
    "cand_1003fdf1c722",  # conversational survey UX
    "cand_4f2abcf90382",  # avatar interview feedback benchmark
    "cand_caf578362d03",  # LLM child witness interview
    "cand_3c651d0b595e",  # avatar interview mega-analysis
    "cand_be916390f50e",  # child-avatar chatbot training
    "cand_771f9ed5290f",  # AI talking avatar for child interviews
    "cand_ab635eb5057c",  # computer-generated security interviewer
    "cand_d12262f5f694",  # AI in police interrogations
}

rows = json.loads(INPUT.read_text(encoding="utf-8"))
repo = DeweyRepo.discover()
discovery = repo.load_discovery()
by_id = {candidate.candidate_id: index for index, candidate in enumerate(discovery.candidates)}
counts: Counter[str] = Counter()

for row in rows:
    candidate_id = row["scenario.candidate_id"]
    answer = row["answer.adjudication"]
    model_decision = answer["decision"]
    if model_decision not in {"retrieve", "exclude", "duplicate"}:
        raise ValueError(f"Invalid model decision for {candidate_id}: {model_decision}")
    if candidate_id not in by_id:
        raise ValueError(f"Unknown candidate: {candidate_id}")
    candidate = discovery.candidates[by_id[candidate_id]]
    if candidate.status != CandidateStatus.candidate:
        raise ValueError(f"Candidate no longer unresolved: {candidate_id}")

    retained = candidate_id in RETRIEVE
    if retained:
        final_status = CandidateStatus.relevant
        final_decision = ScreeningDecisionValue.include
        rationale = answer["rationale"].strip()
        review_outcome = "retrieve-confirmed"
        reason_code = None
    else:
        final_status = CandidateStatus.rejected
        final_decision = ScreeningDecisionValue.exclude
        review_outcome = "duplicate" if model_decision == "duplicate" else "exclude-confirmed"
        if model_decision == "retrieve":
            review_outcome = "retrieve-overruled"
            rationale = (
                "Human review overruled model retrieval: the record is a repeated citation, "
                "a false match from truncated metadata, or outside the focused review scope."
            )
        else:
            rationale = answer["rationale"].strip()
        reason_code = "duplicate" if model_decision == "duplicate" else "not-relevant"

    record = ScreeningDecision(
        decision=final_decision,
        stage=ScreeningStage.title_abstract,
        reviewer="codex-human-review",
        reason_code=reason_code,
        rationale=rationale,
        criteria={
            "model": "openai:gpt-4.1",
            "model_decision": model_decision,
            "model_category": answer["category"],
            "human_review_outcome": review_outcome,
            "evidence_available": "title-citation-only",
        },
        protocol_version=PROTOCOL,
        decided_at=utc_now(),
    )
    discovery.candidates[by_id[candidate_id]] = candidate.model_copy(
        update={
            "status": final_status,
            "rationale": rationale,
            "screening_decisions": [*candidate.screening_decisions, record],
        }
    )
    counts["retrieve" if retained else "exclude"] += 1
    if model_decision == "retrieve" and not retained:
        counts["model_retrievals_overruled"] += 1

repo.write_discovery(discovery)
repo.append_log(
    "screen.batch_adjudicate",
    protocol_version=PROTOCOL,
    records=len(rows),
    counts=dict(counts),
    source_file=str(INPUT),
)
print(json.dumps({"applied": len(rows), "counts": dict(counts)}, indent=2))
