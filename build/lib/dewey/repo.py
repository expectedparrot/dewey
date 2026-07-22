from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from dewey.bibtex import BibTeXError, dump_entry, parse_single_entry
from dewey.models import (
    BibEntry,
    Config,
    LinkRecord,
    LinksFile,
    MarkdownGenerator,
    MarkdownStatus,
    Metadata,
    ReviewOrder,
    SourceStatus,
    State,
)


REQUIRED_SOURCE_FILES = ("entry.bib", "metadata.json", "state.json", "notes.md", "links.json")


class DeweyError(Exception):
    def __init__(self, code: str, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code


@dataclass
class RenderResult:
    status: MarkdownStatus
    markdown_path: str | None
    stderr: str | None
    generator_version: str | None = None


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_source_id() -> str:
    return f"src_{uuid.uuid4().hex[:12]}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=False) + "\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".dewey").is_dir():
            return candidate
    raise DeweyError("repo_not_found", "No Dewey repository found in this directory tree", exit_code=3)


class DeweyRepo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.dewey_dir = root / ".dewey"
        self.sources_dir = self.dewey_dir / "sources"
        self.index_db = self.dewey_dir / "indexes" / "search.sqlite"
        self.log_path = self.dewey_dir / "logs" / "activity.jsonl"
        self.instructions_path = self.dewey_dir / "instructions.md"
        self.order_path = self.dewey_dir / "review_order.json"
        self.config_path = self.dewey_dir / "config.json"

    @classmethod
    def discover(cls) -> "DeweyRepo":
        return cls(find_repo_root())

    @classmethod
    def init(cls, root: Path) -> "DeweyRepo":
        repo = cls(root)
        if repo.dewey_dir.exists():
            raise DeweyError("repo_exists", f"Dewey repository already exists at {repo.dewey_dir}", exit_code=2)
        (repo.dewey_dir / "sources").mkdir(parents=True)
        (repo.dewey_dir / "indexes").mkdir(parents=True)
        (repo.dewey_dir / "logs").mkdir(parents=True)
        atomic_write_json(repo.config_path, Config().model_dump())
        atomic_write_text(repo.instructions_path, "")
        atomic_write_json(repo.order_path, ReviewOrder().model_dump())
        atomic_write_text(repo.log_path, "")
        repo.init_index()
        return repo

    def load_config(self) -> Config:
        return Config.model_validate(read_json(self.config_path))

    def source_dir(self, source_id: str) -> Path:
        return self.sources_dir / source_id

    def require_source_dir(self, source_id: str) -> Path:
        path = self.source_dir(source_id)
        if not path.is_dir():
            raise DeweyError("source_not_found", f"No source exists for {source_id}", exit_code=4)
        return path

    def list_source_ids(self) -> list[str]:
        if not self.sources_dir.exists():
            return []
        return sorted(p.name for p in self.sources_dir.iterdir() if p.is_dir())

    def load_entry(self, source_id: str) -> BibEntry:
        path = self.require_source_dir(source_id) / "entry.bib"
        return parse_single_entry(path.read_text(encoding="utf-8"))

    def write_entry(self, source_id: str, entry: BibEntry) -> None:
        atomic_write_text(self.require_source_dir(source_id) / "entry.bib", dump_entry(entry))

    def load_metadata(self, source_id: str) -> Metadata:
        path = self.require_source_dir(source_id) / "metadata.json"
        try:
            return Metadata.model_validate(read_json(path))
        except ValidationError as exc:
            raise DeweyError("invalid_metadata", f"Invalid metadata for {source_id}: {exc}", exit_code=3) from exc

    def write_metadata(self, source_id: str, metadata: Metadata) -> None:
        atomic_write_json(self.require_source_dir(source_id) / "metadata.json", metadata.model_dump())

    def load_state(self, source_id: str) -> State:
        path = self.require_source_dir(source_id) / "state.json"
        try:
            return State.model_validate(read_json(path))
        except ValidationError as exc:
            raise DeweyError("invalid_state", f"Invalid state for {source_id}: {exc}", exit_code=3) from exc

    def write_state(self, source_id: str, state: State) -> None:
        atomic_write_json(self.require_source_dir(source_id) / "state.json", state.model_dump())

    def load_links(self, source_id: str) -> LinksFile:
        path = self.require_source_dir(source_id) / "links.json"
        return LinksFile.model_validate(read_json(path))

    def write_links(self, source_id: str, links: LinksFile) -> None:
        atomic_write_json(self.require_source_dir(source_id) / "links.json", links.model_dump())

    def load_order(self) -> ReviewOrder:
        return ReviewOrder.model_validate(read_json(self.order_path))

    def write_order(self, order: ReviewOrder) -> None:
        atomic_write_json(self.order_path, order.model_dump())

    def append_log(self, action: str, **details: Any) -> None:
        record = {"ts": utc_now(), "action": action, **details}
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")

    def find_by_hash(self, content_hash: str) -> Metadata | None:
        for source_id in self.list_source_ids():
            metadata = self.load_metadata(source_id)
            if metadata.content_hash == content_hash:
                return metadata
        return None

    def existing_bibtex_keys(self, exclude_source_id: str | None = None) -> dict[str, str]:
        result: dict[str, str] = {}
        for source_id in self.list_source_ids():
            if source_id == exclude_source_id:
                continue
            metadata = self.load_metadata(source_id)
            result[metadata.bibtex_key] = source_id
        return result

    def create_source(
        self,
        entry: BibEntry,
        original_pdf_path: str | None = None,
        managed_pdf_path: str | None = None,
        content_hash: str | None = None,
        markdown_status: MarkdownStatus = MarkdownStatus.missing,
        markdown_path: str | None = None,
        markdown_source: str | None = None,
    ) -> str:
        key_map = self.existing_bibtex_keys()
        if entry.key in key_map:
            raise DeweyError(
                "duplicate_bibtex_key",
                f"BibTeX key '{entry.key}' already exists in {key_map[entry.key]}",
                exit_code=2,
            )
        source_id = generate_source_id()
        while self.source_dir(source_id).exists():
            source_id = generate_source_id()
        source_dir = self.source_dir(source_id)
        source_dir.mkdir(parents=True)
        (source_dir / "artifacts").mkdir()
        now = utc_now()
        metadata = Metadata(
            source_id=source_id,
            bibtex_key=entry.key,
            entry_type=entry.entry_type,
            managed_pdf_path=managed_pdf_path,
            original_pdf_path=original_pdf_path,
            content_hash=content_hash,
            markdown_path=markdown_path,
            markdown_status=markdown_status,
            markdown_generator=MarkdownGenerator(),
            created_at=now,
            updated_at=now,
            markdown_source=markdown_source,
        )
        state = State(added_at=now)
        self.write_entry(source_id, entry)
        self.write_metadata(source_id, metadata)
        self.write_state(source_id, state)
        atomic_write_text(source_dir / "notes.md", "")
        self.write_links(source_id, LinksFile())
        return source_id

    def build_placeholder_entry(self, path: Path, bibtex_key: str | None = None) -> BibEntry:
        key = bibtex_key or slugify_key(path.stem or "unknown")
        return BibEntry(
            entry_type="misc",
            key=key,
            fields={
                "title": path.stem or "Unknown Title",
                "note": "Imported from PDF; bibliographic fields incomplete",
            },
        )

    def render_markdown_for_source(self, source_id: str) -> RenderResult:
        metadata = self.load_metadata(source_id)
        source_dir = self.require_source_dir(source_id)
        pdf_path = None
        if metadata.managed_pdf_path:
            pdf_path = self.root / metadata.managed_pdf_path
        elif metadata.original_pdf_path:
            pdf_path = Path(metadata.original_pdf_path)
        if not pdf_path or not pdf_path.exists():
            raise DeweyError("pdf_not_found", f"No PDF exists for {source_id}", exit_code=4)

        stderr_path = source_dir / "artifacts" / "pdf2md.stderr.log"
        try:
            markdown_text, generator_version = convert_pdf_with_paper2md(pdf_path, source_dir / "artifacts" / "paper2md")
        except DeweyError as exc:
            atomic_write_text(stderr_path, exc.message + "\n")
            return RenderResult(status=MarkdownStatus.failed, markdown_path=None, stderr=exc.message)
        except Exception as exc:
            atomic_write_text(stderr_path, str(exc) + "\n")
            return RenderResult(status=MarkdownStatus.failed, markdown_path=None, stderr=str(exc))

        atomic_write_text(stderr_path, "")
        md_path = source_dir / "source.md"
        atomic_write_text(md_path, markdown_text)
        return RenderResult(
            status=MarkdownStatus.ready,
            markdown_path=str(md_path.relative_to(self.root)),
            stderr=None,
            generator_version=generator_version,
        )

    def init_index(self) -> None:
        self.index_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.index_db)
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS source_index (
                  source_id TEXT PRIMARY KEY,
                  bibtex_key TEXT NOT NULL,
                  entry_type TEXT NOT NULL,
                  title TEXT,
                  author TEXT,
                  year TEXT,
                  bibtex_text TEXT,
                  notes_text TEXT,
                  markdown_text TEXT,
                  status TEXT,
                  has_pdf INTEGER NOT NULL,
                  has_md INTEGER NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS source_fts USING fts5(
                  source_id UNINDEXED,
                  title,
                  author,
                  bibtex,
                  notes,
                  markdown,
                  all_text
                );
                CREATE TABLE IF NOT EXISTS link_index (
                  from_id TEXT NOT NULL,
                  to_id TEXT NOT NULL,
                  type TEXT NOT NULL,
                  note TEXT
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def index_source(self, source_id: str) -> None:
        metadata = self.load_metadata(source_id)
        state = self.load_state(source_id)
        entry = self.load_entry(source_id)
        notes_path = self.require_source_dir(source_id) / "notes.md"
        notes_text = notes_path.read_text(encoding="utf-8")
        md_text = ""
        if metadata.markdown_path:
            md_path = self.root / metadata.markdown_path
            if md_path.exists():
                md_text = md_path.read_text(encoding="utf-8")
        has_pdf = 1 if metadata.managed_pdf_path or metadata.original_pdf_path else 0
        has_md = 1 if metadata.markdown_status == MarkdownStatus.ready and metadata.markdown_path else 0
        all_text = "\n".join(
            part for part in [entry.title(), entry.author(), entry.flattened_fields(), notes_text, md_text] if part
        )

        conn = sqlite3.connect(self.index_db)
        try:
            conn.execute("DELETE FROM source_index WHERE source_id = ?", (source_id,))
            conn.execute("DELETE FROM source_fts WHERE source_id = ?", (source_id,))
            conn.execute("DELETE FROM link_index WHERE from_id = ?", (source_id,))
            conn.execute(
                """
                INSERT INTO source_index(
                  source_id, bibtex_key, entry_type, title, author, year, bibtex_text,
                  notes_text, markdown_text, status, has_pdf, has_md
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    metadata.bibtex_key,
                    metadata.entry_type,
                    entry.title(),
                    entry.author(),
                    entry.year(),
                    dump_entry(entry),
                    notes_text,
                    md_text,
                    state.status.value,
                    has_pdf,
                    has_md,
                ),
            )
            conn.execute(
                """
                INSERT INTO source_fts(source_id, title, author, bibtex, notes, markdown, all_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (source_id, entry.title(), entry.author(), dump_entry(entry), notes_text, md_text, all_text),
            )
            links = self.load_links(source_id)
            for link in links.outgoing:
                conn.execute(
                    "INSERT INTO link_index(from_id, to_id, type, note) VALUES (?, ?, ?, ?)",
                    (source_id, link.target, link.type.value, link.note),
                )
            conn.commit()
        finally:
            conn.close()

    def drop_source_from_index(self, source_id: str) -> None:
        conn = sqlite3.connect(self.index_db)
        try:
            conn.execute("DELETE FROM source_index WHERE source_id = ?", (source_id,))
            conn.execute("DELETE FROM source_fts WHERE source_id = ?", (source_id,))
            conn.execute("DELETE FROM link_index WHERE from_id = ? OR to_id = ?", (source_id, source_id))
            conn.commit()
        finally:
            conn.close()

    def rebuild_index(self) -> None:
        self.init_index()
        conn = sqlite3.connect(self.index_db)
        try:
            conn.execute("DELETE FROM source_index")
            conn.execute("DELETE FROM source_fts")
            conn.execute("DELETE FROM link_index")
            conn.commit()
        finally:
            conn.close()
        for source_id in self.list_source_ids():
            self.index_source(source_id)

    def stats(self) -> dict[str, Any]:
        conn = sqlite3.connect(self.index_db)
        try:
            source_count = conn.execute("SELECT COUNT(*) FROM source_index").fetchone()[0]
            link_count = conn.execute("SELECT COUNT(*) FROM link_index").fetchone()[0]
            return {
                "backend": "sqlite_fts5",
                "path": str(self.index_db),
                "sources": source_count,
                "links": link_count,
            }
        finally:
            conn.close()


def slugify_key(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")
    return cleaned or "unknown"


def parse_entry_file(path: Path) -> BibEntry:
    try:
        return parse_single_entry(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DeweyError("file_not_found", f"No file exists at {path}", exit_code=4) from exc
    except BibTeXError as exc:
        raise DeweyError("invalid_bibtex", str(exc), exit_code=2) from exc


def convert_pdf_with_paper2md(pdf_path: Path, output_dir: Path) -> tuple[str, str | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        from paper2md.converter import convert

        result = convert(pdf_path=pdf_path, output_dir=output_dir, backend="auto")
        return result.markdown, _paper2md_version()
    except ImportError:
        pass

    cmd = ["paper2md", str(pdf_path), "--output", str(output_dir)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise DeweyError(
            "paper2md_not_found",
            "paper2md is not installed. Install it from GitHub: pip install \"paper2md @ git+https://github.com/expectedparrot/paper2md.git\"",
            exit_code=1,
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "paper2md failed"
        raise DeweyError("paper2md_failed", stderr, exit_code=1)

    markdown_path = output_dir / "paper.md"
    if not markdown_path.exists():
        raise DeweyError("paper2md_failed", f"paper2md did not produce {markdown_path}", exit_code=1)
    return markdown_path.read_text(encoding="utf-8"), _paper2md_version()


def _paper2md_version() -> str | None:
    try:
        return importlib.metadata.version("paper2md")
    except importlib.metadata.PackageNotFoundError:
        return None
