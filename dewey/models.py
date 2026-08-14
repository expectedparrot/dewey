from __future__ import annotations

from enum import Enum
from typing import Any, Literal

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


class EvidenceLocator(BaseModel):
    page: str | None = None
    section: str | None = None
    table: str | None = None
    figure: str | None = None
    passage: str | None = None

    @model_validator(mode="after")
    def require_location(self) -> "EvidenceLocator":
        if not any((self.page, self.section, self.table, self.figure, self.passage)):
            raise ValueError("An evidence locator requires a page, section, table, figure, or passage")
        return self


class StudyRecord(BaseModel):
    study_id: str
    source_ids: list[str]
    label: str
    design: str
    population: str | None = None
    sample_size: int | None = Field(default=None, ge=0)
    setting: str | None = None
    intervention: str | None = None
    comparator: str | None = None
    methods: list[str] = Field(default_factory=list)
    measures: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def require_sources(self) -> "StudyRecord":
        if not self.source_ids:
            raise ValueError("A study requires at least one source_id")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("Study source_ids must be unique")
        return self


class FindingRecord(BaseModel):
    finding_id: str
    study_id: str
    question_id: str | None = None
    author_claim: str
    evidence_statement: str
    reviewer_interpretation: str
    outcome: str
    direction: str | None = None
    population: str | None = None
    conditions: list[str] = Field(default_factory=list)
    measure: str | None = None
    timepoint: str | None = None
    certainty: str = "not-assessed"
    locators: list[EvidenceLocator]
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def require_locators(self) -> "FindingRecord":
        if not self.locators:
            raise ValueError("A finding requires at least one evidence locator")
        return self


class AppraisalDimension(BaseModel):
    name: str
    judgment: str
    rationale: str
    locators: list[EvidenceLocator] = Field(default_factory=list)


class AppraisalRecord(BaseModel):
    appraisal_id: str
    study_id: str
    framework: str
    framework_version: str | None = None
    dimensions: list[AppraisalDimension]
    overall_judgment: str
    applicability: str
    reviewer: str
    created_at: str
    updated_at: str


class ThemeRecord(BaseModel):
    theme_id: str
    label: str
    description: str
    question_id: str | None = None
    created_at: str
    updated_at: str


class ClaimEvidenceLink(BaseModel):
    finding_id: str
    relationship: Literal["supports", "contradicts", "qualifies"]
    rationale: str


class ClaimRecord(BaseModel):
    claim_id: str
    theme_ids: list[str]
    statement: str
    scope: str
    evidence: list[ClaimEvidenceLink]
    confidence: str
    confidence_rationale: str
    status: Literal["draft", "reviewed"] = "draft"
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def require_synthesis_links(self) -> "ClaimRecord":
        if not self.theme_ids:
            raise ValueError("A claim requires at least one theme_id")
        if not self.evidence:
            raise ValueError("A claim requires at least one evidence link")
        if not any(link.relationship == "supports" for link in self.evidence):
            raise ValueError("A claim requires at least one supporting finding")
        finding_ids = [link.finding_id for link in self.evidence]
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError("A finding may appear only once in a claim")
        return self


class LiteratureStream(BaseModel):
    stream_id: str
    label: str
    description: str
    source_ids: list[str]
    relationship_to_review: str


class TimelineEntry(BaseModel):
    year: int
    label: str
    significance: str
    source_ids: list[str] = Field(default_factory=list)


class SourcePosition(BaseModel):
    source_id: str
    role: Literal["foundational", "bridge", "evaluation", "counterpoint", "application", "frontier"]
    contribution: str
    claim_ids: list[str] = Field(default_factory=list)
    caveat: str | None = None


class ArticleSection(BaseModel):
    heading: str
    purpose: str
    theme_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)


class ArticleSpec(BaseModel):
    schema_version: str = "1"
    title: str
    subtitle: str | None = None
    audience: str
    genre: str = "economics literature review"
    abstract: str
    keywords: list[str] = Field(default_factory=list)
    jel_codes: list[str] = Field(default_factory=list)
    motivation: list[str]
    field_context: list[str]
    central_question: str
    thesis: str
    contribution: list[str]
    scope_includes: list[str]
    scope_excludes: list[str]
    literatures: list[LiteratureStream]
    source_positions: list[SourcePosition]
    timeline: list[TimelineEntry]
    sections: list[ArticleSection]
    conclusion: list[str]
    updated_at: str

    @model_validator(mode="after")
    def require_article_structure(self) -> "ArticleSpec":
        if not self.motivation or not self.field_context or not self.contribution:
            raise ValueError("An article spec requires motivation, field_context, and contribution")
        if not self.literatures or not self.timeline or not self.sections:
            raise ValueError("An article spec requires literatures, timeline, and sections")
        return self
