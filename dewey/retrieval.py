"""Best-effort PDF retrieval from recorded source URLs, without paid services."""
from __future__ import annotations

import http.client
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from dewey.identity import normalize_doi
from dewey.models import MarkdownStatus
from dewey.repo import DeweyError, DeweyRepo, sha256_file, utc_now

MAX_PDF_BYTES = 50 * 1024 * 1024
MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_ATTEMPTS = 8


def http_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urllib.parse.urlparse(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return None
    return urllib.parse.urlunparse(parsed._replace(fragment=""))


class PDFLinks(HTMLParser):
    """Use publisher PDF metadata/alternates; arbitrary cited PDF links are not this paper."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        fields = dict(attrs)
        if tag == "meta" and (fields.get("name") or "").lower() in {"citation_pdf_url", "wkhealth_pdf_url"}:
            if fields.get("content"):
                self.urls.append(fields["content"])
        if tag == "link" and (fields.get("type") or "").lower() == "application/pdf":
            if "alternate" in (fields.get("rel") or "").lower().split() and fields.get("href"):
                self.urls.append(fields["href"])


def source_urls(repo: DeweyRepo, source_id: str, url: str | None = None) -> list[str]:
    metadata = repo.load_metadata(source_id)
    entry = repo.load_entry(source_id)
    candidates = [item for item in repo.load_discovery().candidates if item.added_source_id == source_id]
    values = [url, metadata.open_access_url]
    values.extend(item.open_access_url for item in candidates)
    values.extend([entry.fields.get("url"), metadata.markdown_source, metadata.pdf_source_url])
    values.extend(item.url for item in candidates)
    doi = normalize_doi(entry.fields.get("doi"))
    if doi:
        values.append("https://doi.org/" + doi)
    urls: list[str] = []
    for value in values:
        normalized = http_url(value)
        if not normalized:
            continue
        parsed = urllib.parse.urlparse(normalized)
        # arXiv exposes the same identifier at /abs/ and /pdf/, including version suffixes.
        if parsed.hostname in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"} and parsed.path.startswith("/abs/"):
            pdf_url = urllib.parse.urlunparse(parsed._replace(path=parsed.path.replace("/abs/", "/pdf/", 1)))
            if pdf_url not in urls:
                urls.append(pdf_url)
        if normalized not in urls:
            urls.append(normalized)
    return urls


def _save_pdf(response: Any, prefix: bytes, destination: Path) -> None:
    """Bounded streaming; a failed/truncated response never replaces the stored PDF."""
    fd, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".pdf-download-")
    try:
        total = 0
        tail = b""
        with os.fdopen(fd, "wb") as output:
            chunk = prefix
            while chunk:
                total += len(chunk)
                if total > MAX_PDF_BYTES:
                    raise ValueError("pdf_too_large")
                output.write(chunk)
                tail = (tail + chunk)[-2048:]
                chunk = response.read(65536)
            if b"%%EOF" not in tail:
                raise ValueError("incomplete_pdf")
            length = response.headers.get("Content-Length")
            if length and length.isdigit() and total != int(length):
                raise ValueError("incomplete_pdf")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def fetch_source_pdf(repo: DeweyRepo, source_id: str, url: str | None = None) -> dict[str, Any]:
    """Try one bounded retrieval pass. Existing PDFs are reused, never overwritten."""
    metadata = repo.load_metadata(source_id)
    for stored in (metadata.managed_pdf_path, metadata.original_pdf_path):
        if stored and (repo.root / stored).is_file():
            return {"ok": True, "status": "already_present", "pdf": stored, "attempts": []}
    destination = repo.require_source_dir(source_id) / "source.pdf"
    if destination.exists():
        raise DeweyError("document_exists", "An untracked source.pdf exists; inspect it before retrieving another PDF", 2)
    if url and not http_url(url):
        raise DeweyError("invalid_url", "PDF retrieval requires an HTTP(S) URL", 2)
    queue = source_urls(repo, source_id, url)
    attempted: set[str] = set()
    attempts: list[dict[str, Any]] = []
    downloaded = False
    for _ in range(MAX_ATTEMPTS):
        while queue and queue[0] in attempted:
            queue.pop(0)
        if not queue:
            break
        requested_url = queue.pop(0)
        attempted.add(requested_url)
        attempt: dict[str, Any] = {"url": requested_url}
        attempts.append(attempt)
        request = urllib.request.Request(requested_url, headers={
            "User-Agent": "dewey/0.1 (academic full-text retrieval)",
            "Accept": "application/pdf,text/html;q=0.8,*/*;q=0.1",
        })
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                final_url = response.geturl()
                attempt["resolved_url"] = final_url
                prefix = response.read(1024)
                if prefix.lstrip().startswith(b"%PDF-"):
                    _save_pdf(response, prefix, destination)
                    attempt["outcome"] = "downloaded"
                    downloaded = True
                    break
                content_type = response.headers.get("Content-Type", "").lower()
                if "html" in content_type or prefix.lstrip().lower().startswith((b"<!doctype html", b"<html")):
                    body = prefix + response.read(MAX_HTML_BYTES - len(prefix) + 1)
                    if len(body) > MAX_HTML_BYTES:
                        attempt["outcome"] = "html_too_large"
                        continue
                    parser = PDFLinks()
                    parser.feed(body.decode("utf-8", errors="replace"))
                    links = [http_url(urllib.parse.urljoin(final_url, link)) for link in parser.urls]
                    queue = [link for link in links if link and link not in attempted] + queue
                    attempt["outcome"] = "landing_page" if any(links) else "no_pdf_link"
                else:
                    attempt["outcome"] = "not_pdf"
        except urllib.error.HTTPError as exc:
            attempt.update(outcome="http_error", http_status=exc.code)
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as exc:
            attempt.update(outcome="request_failed", error_type=type(exc).__name__)
        except ValueError as exc:
            attempt.update(outcome="invalid_document", reason=str(exc))
    now = utc_now()
    metadata.pdf_last_attempt_at = now
    metadata.pdf_retrieval_status = "downloaded" if downloaded else "unavailable"
    if downloaded:
        old_hash = metadata.content_hash
        metadata.managed_pdf_path = str(destination.relative_to(repo.root))
        metadata.content_hash = sha256_file(destination)
        metadata.pdf_source_url = attempts[-1]["resolved_url"]
        metadata.pdf_retrieved_at = now
        if old_hash and old_hash != metadata.content_hash:
            metadata.markdown_status = MarkdownStatus.stale if metadata.markdown_path else MarkdownStatus.missing
            state = repo.load_state(source_id)
            state.read_depth = None
            state.last_read_at = None
            repo.write_state(source_id, state)
    metadata.updated_at = now
    repo.write_metadata(source_id, metadata)
    repo.index_source(source_id)
    result = {"ok": downloaded, "status": metadata.pdf_retrieval_status,
              "pdf": metadata.managed_pdf_path if downloaded else None,
              "url": metadata.pdf_source_url if downloaded else None,
              "attempts": attempts, "remaining_urls": len(set(queue) - attempted)}
    repo.append_log("source.fetch_pdf", source_id=source_id, **result)
    return result
