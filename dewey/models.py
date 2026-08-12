from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class MarkdownStatus(str, Enum):
    missing = "missing"
    ready = "ready"
    failed = "failed"
    stale = "stale"


class SourceStatus(str, Enum):
    unread = "unread"
    queued = "queued"
    reading = "reading"
    read = "read"
    included = "included"
    excluded = "excluded"


class LinkType(str, Enum):
    cites = "cites"
    builds_on = "builds_on"
    contradicts = "contradicts"
    compares_to = "compares_to"
    uses_method = "uses_method"
    uses_dataset = "uses_dataset"
    motivates = "motivates"
    historical_predecessor = "historical_predecessor"
    same_work_as = "same_work_as"
    version_of = "version_of"


class Config(BaseModel):
    version: int = 1
    project_name: str | None = None
    bibtex_encoding: str = "utf-8"
    pdf_copy_mode: str = "copy"
    search_backend: str = "sqlite_fts5"
    default_output: str = "text"
    topic: str | None = None
    research_question: str | None = None


class MarkdownGenerator(BaseModel):
    name: str = "paper2md"
    version: str | None = None


class Metadata(BaseModel):
    source_id: str
    bibtex_key: str
    entry_type: str
    managed_pdf_path: str | None = None
    original_pdf_path: str | None = None
    content_hash: str | None = None
    markdown_path: str | None = None
    markdown_status: MarkdownStatus = MarkdownStatus.missing
    markdown_generator: MarkdownGenerator = Field(default_factory=MarkdownGenerator)
    created_at: str
    updated_at: str
    markdown_source: str | None = None


class State(BaseModel):
    status: SourceStatus = SourceStatus.unread
    added_at: str
    last_read_at: str | None = None
    included: bool | None = None
    priority: int | None = None


class LinkRecord(BaseModel):
    target: str
    type: LinkType
    note: str | None = None
    created_at: str


class LinksFile(BaseModel):
    outgoing: list[LinkRecord] = Field(default_factory=list)


class ReviewOrder(BaseModel):
    strategy: str = "manual"
    order: list[str] = Field(default_factory=list)
    notes: str = ""


class BibEntry(BaseModel):
    entry_type: str
    key: str
    fields: dict[str, str]

    def title(self) -> str:
        return self.fields.get("title", "")

    def author(self) -> str:
        return self.fields.get("author", "")

    def year(self) -> str:
        return self.fields.get("year", "")

    def flattened_fields(self) -> str:
        parts = [self.entry_type, self.key]
        for name, value in self.fields.items():
            parts.append(name)
            parts.append(value)
        return "\n".join(parts)

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_type": self.entry_type,
            "key": self.key,
            "fields": self.fields,
        }


class CandidateStatus(str, Enum):
    candidate = "candidate"
    relevant = "relevant"
    rejected = "rejected"
    added = "added"


class ScreeningStage(str, Enum):
    title_abstract = "title-abstract"
    full_text = "full-text"
    quantitative_eligibility = "quantitative-eligibility"


class ScreeningDecisionValue(str, Enum):
    include = "include"
    exclude = "exclude"
    maybe = "maybe"


class ExclusionReason(str, Enum):
    duplicate = "duplicate"
    not_relevant = "not-relevant"
    wrong_population = "wrong-population"
    wrong_intervention = "wrong-intervention"
    no_comparator = "no-comparator"
    wrong_outcome = "wrong-outcome"
    wrong_design = "wrong-design"
    no_quantitative_data = "no-quantitative-data"
    unavailable_full_text = "unavailable-full-text"
    other = "other"


class ScreeningDecision(BaseModel):
    decision: ScreeningDecisionValue
    stage: ScreeningStage = ScreeningStage.title_abstract
    reviewer: str = "agent"
    reason_code: str | None = None
    rationale: str | None = None
    criteria: dict[str, str] = Field(default_factory=dict)
    protocol_version: str | None = None
    decided_at: str


class DiscoveryProvenance(BaseModel):
    source_id: str | None = None
    method: str = "manual"
    raw_citation: str | None = None
    discovered_at: str


class DiscoveryCandidate(BaseModel):
    candidate_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    url: str | None = None
    open_access_url: str | None = None
    abstract: str | None = None
    raw_citation: str | None = None
    cited_by_source_id: str | None = None
    discovery_method: str = "manual"
    status: CandidateStatus = CandidateStatus.candidate
    relevance_score: float | None = None
    rationale: str | None = None
    added_source_id: str | None = None
    created_at: str
    provenance: list[DiscoveryProvenance] = Field(default_factory=list)
    screening_decisions: list[ScreeningDecision] = Field(default_factory=list)

    @model_validator(mode="after")
    def migrate_legacy_provenance(self) -> "DiscoveryCandidate":
        legacy_key = (self.cited_by_source_id, self.discovery_method, self.raw_citation)
        existing_keys = {(item.source_id, item.method, item.raw_citation) for item in self.provenance}
        if legacy_key not in existing_keys:
            self.provenance.append(
                DiscoveryProvenance(
                    source_id=self.cited_by_source_id,
                    method=self.discovery_method,
                    raw_citation=self.raw_citation,
                    discovered_at=self.created_at,
                )
            )
        return self


class DiscoveryFile(BaseModel):
    candidates: list[DiscoveryCandidate] = Field(default_factory=list)
