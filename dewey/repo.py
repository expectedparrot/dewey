from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import sqlite3
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from dewey.bibtex import BibTeXError, dump_entry, parse_single_entry
from dewey.identity import identity_keys, identity_match, normalize_doi
from dewey.models import (
    BibEntry,
    Config,
    DiscoveryCandidate,
    DiscoveryFile,
    LinksFile,
    MarkdownGenerator,
    MarkdownStatus,
    Metadata,
    ReviewOrder,
    State,
)

REQUIRED_SOURCE_FILES = ("entry.bib", "metadata.json", "state.json", "summary.txt", "notes.md", "links.json")


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
    generator_name: str = "firecrawl"
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
        self.discovery_path = self.dewey_dir / "discovery.json"

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
        atomic_write_json(repo.discovery_path, DiscoveryFile().model_dump())
        atomic_write_text(repo.log_path, "")
        repo.init_index()
        return repo

    def load_config(self) -> Config:
        return Config.model_validate(read_json(self.config_path))

    def write_config(self, config: Config) -> None:
        atomic_write_json(self.config_path, config.model_dump())

    def load_discovery(self) -> DiscoveryFile:
        if not self.discovery_path.exists():
            return DiscoveryFile()
        return DiscoveryFile.model_validate(read_json(self.discovery_path))

    def write_discovery(self, discovery: DiscoveryFile) -> None:
        atomic_write_json(self.discovery_path, discovery.model_dump())

    def add_candidate(self, candidate: DiscoveryCandidate) -> DiscoveryCandidate:
        discovery = self.load_discovery()
        for index, existing in enumerate(discovery.candidates):
            if identity_match(existing, candidate):
                merged = self.merge_candidates(existing, candidate)
                discovery.candidates[index] = merged
                self.write_discovery(discovery)
                return merged
        discovery.candidates.append(candidate)
        self.write_discovery(discovery)
        return candidate

    @staticmethod
    def merge_candidates(existing: DiscoveryCandidate, incoming: DiscoveryCandidate) -> DiscoveryCandidate:
        provenance = list(existing.provenance)
        seen = {(item.source_id, item.method, item.raw_citation) for item in provenance}
        for item in incoming.provenance:
            key = (item.source_id, item.method, item.raw_citation)
            if key not in seen:
                provenance.append(item)
                seen.add(key)
        decisions = list(existing.screening_decisions)
        seen_decisions = {
            (
                item.decision,
                item.stage,
                item.reviewer,
                item.reason_code,
                item.rationale,
                tuple(sorted(item.criteria.items())),
                item.protocol_version,
                item.decided_at,
            )
            for item in decisions
        }
        for item in incoming.screening_decisions:
            key = (
                item.decision,
                item.stage,
                item.reviewer,
                item.reason_code,
                item.rationale,
                tuple(sorted(item.criteria.items())),
                item.protocol_version,
                item.decided_at,
            )
            if key not in seen_decisions:
                decisions.append(item)
                seen_decisions.add(key)
        rank = {"rejected": 0, "candidate": 1, "relevant": 2, "added": 3}
        preferred = incoming if rank[incoming.status.value] > rank[existing.status.value] else existing
        richer = (
            incoming
            if sum(bool(value) for value in (incoming.authors, incoming.year, incoming.abstract))
            > sum(bool(value) for value in (existing.authors, existing.year, existing.abstract))
            else existing
        )
        return existing.model_copy(
            update={
                "title": richer.title,
                "authors": richer.authors or existing.authors,
                "year": richer.year or existing.year,
                "doi": normalize_doi(existing.doi) or normalize_doi(incoming.doi),
                "url": existing.url or incoming.url,
                "open_access_url": existing.open_access_url or incoming.open_access_url,
                "abstract": existing.abstract or incoming.abstract,
                "status": preferred.status,
                "rationale": preferred.rationale or existing.rationale or incoming.rationale,
                "added_source_id": preferred.added_source_id or existing.added_source_id or incoming.added_source_id,
                "provenance": provenance,
                "screening_decisions": decisions,
            }
        )

    def duplicate_candidate_groups(self) -> list[dict[str, Any]]:
        candidates = self.load_discovery().candidates
        components = self._candidate_identity_components(candidates)
        return [
            {
                "candidate_ids": [candidates[index].candidate_id for index in component],
                "title": candidates[component[0]].title,
                "matches": [
                    {"candidate_id": candidates[index].candidate_id, "method": "canonical_identity", "score": 1.0}
                    for index in component[1:]
                ],
            }
            for component in components
            if len(component) > 1
        ]

    @staticmethod
    def _candidate_identity_components(candidates: list[DiscoveryCandidate]) -> list[list[int]]:
        """Return transitively connected groups sharing an exact identity key."""
        parents = list(range(len(candidates)))

        def find(index: int) -> int:
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        def union(left: int, right: int) -> None:
            left_root, right_root = find(left), find(right)
            if left_root != right_root:
                parents[right_root] = left_root

        key_owner: dict[str, int] = {}
        for index, candidate in enumerate(candidates):
            for key in identity_keys(candidate):
                if key in key_owner:
                    union(index, key_owner[key])
                else:
                    key_owner[key] = index
        components: dict[int, list[int]] = {}
        for index in range(len(candidates)):
            components.setdefault(find(index), []).append(index)
        return sorted(components.values(), key=lambda component: component[0])

    def deduplicate_candidates(self) -> dict[str, int]:
        discovery = self.load_discovery()
        unique: list[DiscoveryCandidate] = []
        for component in self._candidate_identity_components(discovery.candidates):
            canonical = discovery.candidates[component[0]]
            for index in component[1:]:
                canonical = self.merge_candidates(canonical, discovery.candidates[index])
            unique.append(canonical)
        before = len(discovery.candidates)
        discovery.candidates = unique
        self.write_discovery(discovery)
        return {"before": before, "after": len(unique), "merged": before - len(unique)}

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
        atomic_write_text(source_dir / "summary.txt", "")
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

    def render_markdown_for_source(self, source_id: str, backend: str = "paper2md") -> RenderResult:
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
            if backend == "firecrawl":
                markdown_text, generator_version = convert_pdf_with_firecrawl(pdf_path)
            elif backend == "paper2md":
                markdown_text, generator_version = convert_pdf_with_paper2md(
                    pdf_path, source_dir / "artifacts" / "paper2md"
                )
            else:
                raise DeweyError("invalid_backend", f"Unknown Markdown backend: {backend}", exit_code=2)
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
            generator_name=backend,
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
        summary_path = self.require_source_dir(source_id) / "summary.txt"
        summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
        indexed_notes = "\n".join(part for part in [summary_text, notes_text] if part)
        md_text = ""
        if metadata.markdown_path:
            md_path = self.root / metadata.markdown_path
            if md_path.exists():
                md_text = md_path.read_text(encoding="utf-8")
        has_pdf = 1 if metadata.managed_pdf_path or metadata.original_pdf_path else 0
        has_md = 1 if metadata.markdown_status == MarkdownStatus.ready and metadata.markdown_path else 0
        all_text = "\n".join(
            part for part in [entry.title(), entry.author(), entry.flattened_fields(), indexed_notes, md_text] if part
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
                    indexed_notes,
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
                (source_id, entry.title(), entry.author(), dump_entry(entry), indexed_notes, md_text, all_text),
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

        try:
            result = convert(pdf_path=pdf_path, output_dir=output_dir, backend="auto")
        except Exception as primary_error:
            try:
                result = convert(pdf_path=pdf_path, output_dir=output_dir, backend="pymupdf")
            except Exception as fallback_error:
                raise DeweyError(
                    "paper2md_failed",
                    f"paper2md marker backend failed ({primary_error}); pymupdf fallback failed ({fallback_error})",
                ) from fallback_error
        version = _paper2md_version()
        backend_used = getattr(result, "backend_used", None)
        generator_version = f"{version} ({backend_used})" if version and backend_used else version
        return result.markdown, generator_version
    except ImportError:
        pass

    cmd = ["paper2md", str(pdf_path), "--output", str(output_dir)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise DeweyError(
            "paper2md_not_found",
            'paper2md is not installed. Install it from GitHub: pip install "paper2md @ git+https://github.com/expectedparrot/paper2md.git"',
            exit_code=1,
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "paper2md failed"
        raise DeweyError("paper2md_failed", stderr, exit_code=1)

    markdown_path = output_dir / "paper.md"
    if not markdown_path.exists():
        raise DeweyError("paper2md_failed", f"paper2md did not produce {markdown_path}", exit_code=1)
    return markdown_path.read_text(encoding="utf-8"), _paper2md_version()


def _firecrawl_api_key() -> str:
    api_key = os.environ.get("FIRECRAWL_API_KEY")
    if not api_key:
        raise DeweyError(
            "firecrawl_api_key_missing",
            "FIRECRAWL_API_KEY is required for the Firecrawl backend",
            exit_code=2,
        )
    return api_key


def convert_url_with_firecrawl(url: str) -> tuple[str, str | None]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DeweyError("invalid_url", f"Expected an HTTP(S) URL, got: {url}", exit_code=2)
    mcp_url = os.environ.get("FIRECRAWL_API_URL")
    if mcp_url:
        return _convert_url_with_firecrawl_mcp(url, mcp_url), "mcp"

    payload = json.dumps(
        {
            "url": url,
            "formats": ["markdown"],
            "parsers": [{"type": "pdf", "mode": "auto"}],
            "timeout": 300000,
        }
    ).encode()
    request = urllib.request.Request(
        "https://api.firecrawl.dev/v2/scrape",
        data=payload,
        headers={
            "Authorization": f"Bearer {_firecrawl_api_key()}",
            "Content-Type": "application/json",
            "User-Agent": "dewey/0.1",
        },
        method="POST",
    )
    markdown = _read_firecrawl_markdown(request, "scrape")
    return markdown, "v2"


def _convert_url_with_firecrawl_mcp(url: str, mcp_url: str) -> str:
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "firecrawl_scrape",
                "arguments": {"url": url, "formats": ["markdown"]},
            },
        }
    ).encode()
    request = urllib.request.Request(
        mcp_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {_firecrawl_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "dewey/0.1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=330) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise DeweyError("firecrawl_failed", f"Firecrawl MCP returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise DeweyError("firecrawl_failed", f"Firecrawl MCP scrape failed: {exc}") from exc

    payloads: list[dict[str, Any]] = []
    for line in body.splitlines():
        candidate = line.removeprefix("data:").strip() if line.startswith("data:") else line.strip()
        if not candidate or candidate == "[DONE]":
            continue
        try:
            decoded = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, dict):
            payloads.append(decoded)
    for response_payload in payloads:
        result = response_payload.get("result", {})
        if result.get("isError"):
            raise DeweyError("firecrawl_failed", _mcp_error_text(result) or "Firecrawl MCP returned an error")
        for block in result.get("content", []):
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            text = block.get("text")
            if not isinstance(text, str):
                continue
            try:
                tool_payload = json.loads(text)
            except json.JSONDecodeError:
                if text.strip():
                    return text
                continue
            markdown = _find_markdown(tool_payload)
            if markdown:
                return markdown
    raise DeweyError("firecrawl_failed", "Firecrawl MCP returned no Markdown")


def _find_markdown(value: Any) -> str | None:
    if isinstance(value, dict):
        markdown = value.get("markdown")
        if isinstance(markdown, str) and markdown.strip():
            return markdown
        for child in value.values():
            found = _find_markdown(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_markdown(child)
            if found:
                return found
    return None


def _mcp_error_text(result: dict[str, Any]) -> str | None:
    for block in result.get("content", []):
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            return block["text"]
    return None


def convert_pdf_with_firecrawl(pdf_path: Path) -> tuple[str, str | None]:
    api_key = _firecrawl_api_key()
    if pdf_path.stat().st_size > 50 * 1024 * 1024:
        raise DeweyError("firecrawl_file_too_large", "Firecrawl Parse accepts files up to 50 MB", exit_code=2)

    boundary = f"----dewey-{uuid.uuid4().hex}"
    options = json.dumps(
        {
            "formats": ["markdown"],
            "parsers": [{"type": "pdf", "mode": "auto"}],
            "timeout": 300000,
        }
    )
    body = bytearray()

    def add_part(name: str, value: bytes, filename: str | None = None, content_type: str | None = None) -> None:
        body.extend(f"--{boundary}\r\n".encode())
        disposition = f'Content-Disposition: form-data; name="{name}"'
        if filename:
            disposition += f'; filename="{filename}"'
        body.extend((disposition + "\r\n").encode())
        if content_type:
            body.extend(f"Content-Type: {content_type}\r\n".encode())
        body.extend(b"\r\n")
        body.extend(value)
        body.extend(b"\r\n")

    add_part("file", pdf_path.read_bytes(), pdf_path.name, "application/pdf")
    add_part("options", options.encode(), content_type="application/json")
    body.extend(f"--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        "https://api.firecrawl.dev/v2/parse",
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "dewey/0.1",
        },
        method="POST",
    )
    return _read_firecrawl_markdown(request, "parse"), "v2"


def _read_firecrawl_markdown(request: urllib.request.Request, operation: str) -> str:
    try:
        with urllib.request.urlopen(request, timeout=330) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise DeweyError("firecrawl_failed", f"Firecrawl returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise DeweyError("firecrawl_failed", f"Firecrawl {operation} failed: {exc}") from exc
    markdown = payload.get("data", {}).get("markdown") if payload.get("success") else None
    if not markdown:
        raise DeweyError("firecrawl_failed", "Firecrawl returned no Markdown")
    return markdown


def _paper2md_version() -> str | None:
    try:
        return importlib.metadata.version("paper2md")
    except importlib.metadata.PackageNotFoundError:
        return None
