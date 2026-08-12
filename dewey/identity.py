from __future__ import annotations

import re
from difflib import SequenceMatcher

from dewey.models import DiscoveryCandidate

ARXIV_RE = re.compile(r"(?:arxiv[:./]|abs/|pdf/)(\d{4}\.\d{4,5})(?:v\d+)?", re.I)
NON_WORD_RE = re.compile(r"[^a-z0-9]+")
LEADING_REFERENCE_RE = re.compile(r"^\s*(?:\[\d+\]|\d+[.)])\s*")


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().casefold()
    normalized = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", normalized)
    normalized = re.sub(r"^doi:\s*", "", normalized)
    return normalized.rstrip(".,;)") or None


def arxiv_id(candidate: DiscoveryCandidate) -> str | None:
    text = " ".join(filter(None, [candidate.doi, candidate.url, candidate.open_access_url, candidate.raw_citation]))
    match = ARXIV_RE.search(text)
    return match.group(1).casefold() if match else None


def normalize_title(value: str) -> str:
    value = LEADING_REFERENCE_RE.sub("", value).casefold()
    value = value.replace("**", "").replace("_", "")
    return " ".join(NON_WORD_RE.sub(" ", value).split())


def identity_keys(candidate: DiscoveryCandidate) -> list[str]:
    keys = []
    doi = normalize_doi(candidate.doi)
    if doi:
        keys.append(f"doi:{doi}")
    arxiv = arxiv_id(candidate)
    if arxiv:
        keys.append(f"arxiv:{arxiv}")
    title = normalize_title(candidate.title)
    if title:
        keys.append(f"title:{title}")
    return keys


def identity_match(left: DiscoveryCandidate, right: DiscoveryCandidate) -> tuple[str, float] | None:
    left_doi, right_doi = normalize_doi(left.doi), normalize_doi(right.doi)
    if left_doi and right_doi and left_doi == right_doi:
        return "doi", 1.0
    left_arxiv, right_arxiv = arxiv_id(left), arxiv_id(right)
    if left_arxiv and right_arxiv and left_arxiv == right_arxiv:
        return "arxiv", 1.0
    left_title, right_title = normalize_title(left.title), normalize_title(right.title)
    if left_title and left_title == right_title:
        return "title", 1.0
    if min(len(left_title), len(right_title)) < 30:
        return None
    if left.year and right.year and left.year != right.year:
        return None
    score = SequenceMatcher(None, left_title, right_title).ratio()
    if score >= 0.94:
        return "fuzzy_title", round(score, 3)
    return None
