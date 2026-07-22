from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
