from __future__ import annotations

import re
import uuid
from typing import Any

from dewey.models import DiscoveryCandidate
from dewey.repo import DeweyError, utc_now

WORD_RE = re.compile(r"[a-z0-9]{3,}")
REFERENCE_HEADING_RE = re.compile(
    r"^#{1,6}\s+[*_]*(references|bibliography|works cited|literature cited)[*_]*\s*$",
    re.I | re.M,
)
NEXT_HEADING_RE = re.compile(r"^#{1,6}\s+\S", re.M)
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def candidate_id() -> str:
    return f"cand_{uuid.uuid4().hex[:12]}"


def relevance_score(text: str, topic: str) -> float | None:
    topic_words = set(WORD_RE.findall(topic.casefold()))
    if not topic_words:
        return None
    text_words = set(WORD_RE.findall(text.casefold()))
    return round(len(topic_words & text_words) / len(topic_words), 3)


def extract_reference_entries(markdown: str) -> list[str]:
    heading = REFERENCE_HEADING_RE.search(markdown)
    if not heading:
        raise DeweyError("references_not_found", "No References, Bibliography, or Works Cited section was found")
    section = markdown[heading.end() :]
    next_heading = NEXT_HEADING_RE.search(section)
    if next_heading:
        section = section[: next_heading.start()]
    section = section.strip()
    if not section:
        return []

    numbered = re.split(r"(?m)^\s*(?:\[\d+\]|\d+[.)])\s+", section)
    chunks = numbered[1:] if len(numbered) > 1 else re.split(r"\n\s*\n", section)
    entries = []
    for chunk in chunks:
        cleaned = re.sub(r"\s+", " ", chunk).strip(" -*\t\n")
        if len(cleaned) >= 20:
            entries.append(cleaned)
    return entries


def candidate_from_citation(raw_citation: str, parent_source_id: str, topic: str) -> DiscoveryCandidate:
    doi_match = DOI_RE.search(raw_citation)
    doi = doi_match.group(0).rstrip(".,;)") if doi_match else None
    provisional_title = raw_citation if len(raw_citation) <= 180 else raw_citation[:177] + "..."
    return DiscoveryCandidate(
        candidate_id=candidate_id(),
        title=provisional_title,
        doi=doi,
        raw_citation=raw_citation,
        cited_by_source_id=parent_source_id,
        discovery_method="document_references",
        relevance_score=relevance_score(raw_citation, topic),
        created_at=utc_now(),
    )


def edsl_triage_record(candidate: DiscoveryCandidate, topic: str, research_question: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "question": (
            "Assess whether this candidate should be read for the literature review. "
            "Return JSON with relevant (boolean), score (0-1), and rationale (one sentence)."
        ),
        "context": {
            "topic": topic,
            "research_question": research_question,
            "title": candidate.title,
            "authors": candidate.authors,
            "year": candidate.year,
            "abstract": candidate.abstract,
            "citation_provenance": candidate.cited_by_source_id,
        },
    }
