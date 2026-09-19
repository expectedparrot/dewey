"""Bounded academic discovery pages; callers screen results before accepting them."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from dewey.discovery import candidate_id
from dewey.identity import normalize_doi
from dewey.models import DiscoveryCandidate, DiscoveryProvenance
from dewey.repo import DeweyError, utc_now

PROVIDERS = {"openalex", "semantic-scholar", "firecrawl"}
S2_FIELDS = "title,authors,year,externalIds,url,abstract,openAccessPdf"


@dataclass
class DiscoveryPage:
    candidates: list[DiscoveryCandidate]
    next_cursor: str | None = None
    # None means the provider does not establish exhaustive coverage.
    complete: bool | None = None
    total: int | None = None


def request_json(provider: str, url: str, params: dict[str, Any]) -> dict[str, Any]:
    params = dict(params)
    headers = {"Accept": "application/json", "User-Agent": "dewey/0.1 academic-discovery"}
    if provider == "openalex" and os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    elif provider == "semantic-scholar" and os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = os.environ["SEMANTIC_SCHOLAR_API_KEY"]
    elif provider == "firecrawl":
        if os.environ.get("FIRECRAWL_API_URL"):
            raise DeweyError(
                "provider_unavailable",
                "Use the hosted Firecrawl research MCP tools, then discover add --via-source --relation citations; "
                "the scrape proxy is not a Research REST endpoint.", 2,
            )
        if os.environ.get("FIRECRAWL_API_KEY"):
            headers["Authorization"] = f"Bearer {os.environ['FIRECRAWL_API_KEY']}"
    request = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not echo request URLs or response bodies: either can contain credentials.
        retry = " Respect Retry-After and switch providers if rate limiting persists." if exc.code == 429 else ""
        raise DeweyError("academic_provider_failed", f"{provider} returned HTTP {exc.code}.{retry}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DeweyError("academic_provider_failed", f"{provider} request failed; no discovery results recorded") from exc
    except (ValueError, UnicodeError) as exc:
        raise DeweyError("invalid_provider_response", f"{provider} did not return valid JSON") from exc
    if not isinstance(payload, dict) or payload.get("success") is False or "error" in payload:
        raise DeweyError("academic_provider_failed", f"{provider} returned an error response")
    return payload


def _abstract(index: dict[str, list[int]] | None) -> str | None:
    if not index:
        return None
    return " ".join(word for _, word in sorted((position, word) for word, positions in index.items() for position in positions))


def _firecrawl_url(primary_id: str) -> str | None:
    namespace, _, value = primary_id.partition(":")
    bases = {"doi": "https://doi.org/", "arxiv": "https://arxiv.org/abs/", "pmid": "https://pubmed.ncbi.nlm.nih.gov/", "pmcid": "https://pmc.ncbi.nlm.nih.gov/articles/"}
    return bases[namespace] + value if namespace in bases and value else None


def normalize_paper(paper: dict[str, Any], provider: str, seed: str | None, query: str) -> DiscoveryCandidate:
    title = paper.get("title") or paper.get("display_name")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Paper lacks a title")
    if provider == "openalex":
        authors = [item["author"]["display_name"] for item in (paper.get("authorships") or [])]
        year, doi = paper.get("publication_year"), normalize_doi(paper.get("doi"))
        location = paper.get("best_oa_location") or {}
        url = (paper.get("primary_location") or {}).get("landing_page_url") or paper.get("id")
        oa_url = location.get("pdf_url") or location.get("landing_page_url")
        abstract = _abstract(paper.get("abstract_inverted_index"))
        record_id = paper.get("id")
    elif provider == "semantic-scholar":
        authors = [item["name"] for item in (paper.get("authors") or [])]
        year, doi = paper.get("year"), normalize_doi((paper.get("externalIds") or {}).get("DOI"))
        arxiv = (paper.get("externalIds") or {}).get("ArXiv")
        url = "https://arxiv.org/abs/" + arxiv if arxiv else paper.get("url")
        oa_url = (paper.get("openAccessPdf") or {}).get("url")
        abstract, record_id = paper.get("abstract"), paper.get("paperId")
    else:
        authors = [item if isinstance(item, str) else item["name"] for item in (paper.get("authors") or [])]
        year = paper.get("year")
        ids = paper.get("ids") or {}
        dois = ids.get("doi") or []
        doi = normalize_doi(dois[0]) if dois else None
        primary_id = paper.get("primaryId") or ""
        if primary_id.startswith("doi:"):
            doi = normalize_doi(primary_id)
        url, oa_url = _firecrawl_url(primary_id), None
        abstract, record_id = paper.get("abstract"), primary_id or paper.get("paperId")
    now = utc_now()
    return DiscoveryCandidate(
        candidate_id=candidate_id(), title=title, authors=authors, year=year, doi=doi,
        url=url, open_access_url=oa_url, abstract=abstract, created_at=now,
        discovery_method="forward_citations" if seed else "academic_search",
        provenance=[DiscoveryProvenance(
            source_id=seed, relation="citations" if seed else "related",
            method="forward_citations" if seed else "academic_search", provider=provider,
            query=query, record_id=record_id, discovered_at=now,
        )],
    )


def fetch_page(
    provider: str, query: str, *, seed_source_id: str | None = None,
    paper_id: str | None = None, limit: int = 50, cursor: str | None = None,
) -> DiscoveryPage:
    """Fetch one explicit page. Errors never become an empty successful search."""
    if provider not in PROVIDERS:
        raise DeweyError("invalid_provider", "Choose openalex, semantic-scholar, or firecrawl", 2)
    if not 1 <= limit <= 100:
        raise DeweyError("invalid_limit", "Use a limit between 1 and 100", 2)
    if seed_source_id and not paper_id:
        raise DeweyError("paper_id_required", "Add a verified DOI/URL or pass --paper-id", 2)
    try:
        if provider == "openalex":
            params: dict[str, Any] = {"per_page": limit, "cursor": cursor or "*"}
            if seed_source_id:
                identifier = paper_id or ""
                if identifier.startswith("https://openalex.org/"):
                    identifier = identifier.rsplit("/", 1)[-1]
                if identifier.lower().startswith("doi:") or identifier.startswith("10."):
                    identifier = "https://doi.org/" + (normalize_doi(identifier) or "")
                work = request_json(provider, "https://api.openalex.org/works/" + urllib.parse.quote(identifier, safe=""), {})
                work_id = work["id"].rsplit("/", 1)[-1]
                if not re.fullmatch(r"W\d+", work_id):
                    raise ValueError("Invalid OpenAlex work ID")
                params.update(filter=f"cites:{work_id}", sort="publication_date:desc")
            else:
                params["search"] = query
            payload = request_json(provider, "https://api.openalex.org/works", params)
            papers = payload["results"]
            next_cursor = payload["meta"].get("next_cursor")
            total = payload["meta"].get("count")
            complete = not bool(next_cursor)
        elif provider == "semantic-scholar":
            offset = int(cursor or "0")
            if offset < 0:
                raise ValueError("Negative offset")
            params = {"fields": S2_FIELDS, "limit": limit, "offset": offset}
            if seed_source_id:
                identifier = paper_id or ""
                if identifier.startswith("https://doi.org/") or identifier.startswith("10."):
                    identifier = "DOI:" + (normalize_doi(identifier) or "")
                if identifier.lower().startswith("doi:"):
                    identifier = "DOI:" + identifier[4:]
                endpoint = urllib.parse.quote(identifier, safe="") + "/citations"
            else:
                endpoint = "search"
                params["query"] = query
            payload = request_json(provider, "https://api.semanticscholar.org/graph/v1/paper/" + endpoint, params)
            papers = payload["data"]
            if not isinstance(papers, list):
                raise ValueError("Invalid paper list")
            if seed_source_id:
                papers = [item["citingPaper"] for item in papers]
            next_cursor = str(payload["next"]) if payload.get("next") is not None else None
            total, complete = payload.get("total"), next_cursor is None
            if total is not None and offset + len(papers) < total:
                complete = False
        else:
            if cursor:
                raise DeweyError("unsupported_cursor", "Firecrawl returns ranked results, not paginated citation enumeration", 2)
            endpoint = "https://api.firecrawl.dev/v2/search/research/papers"
            params = {"k": limit}
            if seed_source_id:
                endpoint += "/" + urllib.parse.quote(paper_id or "", safe="") + "/similar"
                params.update(intent=query, mode="citers")
            else:
                params["query"] = query
            payload = request_json(provider, endpoint, params)
            papers = payload["results"]
            # Even a non-truncated candidate pool is not an exhaustive citation census.
            next_cursor, total, complete = None, payload.get("poolSize"), None
        if not isinstance(papers, list):
            raise ValueError("Invalid paper list")
        candidates = [normalize_paper(paper, provider, seed_source_id, query) for paper in papers]
        return DiscoveryPage(candidates, next_cursor, complete, total)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise DeweyError("invalid_provider_response", f"Cannot interpret {provider} response or cursor; no candidates recorded") from exc
