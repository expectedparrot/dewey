"""Macaw plugin registration for dewey."""
from __future__ import annotations

import re
from importlib.metadata import distribution, PackageNotFoundError

import pluggy
import yaml

from dewey.packaged_docs import load_meta, load_readme

hookimpl = pluggy.HookimplMarker("macaw")

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", re.S)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError("META.md is missing a YAML frontmatter block.")
    raw_meta = yaml.safe_load(match.group(1)) or {}
    if not isinstance(raw_meta, dict):
        raise ValueError("META.md frontmatter must be a YAML mapping.")
    return raw_meta, match.group(2)


_metadata, _meta_body = _parse_frontmatter(load_meta())
if _meta_body and _meta_body.strip():
    _metadata["meta_body"] = _meta_body
_metadata.setdefault("name", "dewey")
if not _metadata.get("description"):
    raise ValueError("META.md for dewey is missing required 'description'.")
_metadata.setdefault("invoke", "dewey")
_metadata.setdefault("source_package", "dewey")
try:
    _metadata.setdefault("version", distribution("dewey").version)
except PackageNotFoundError:
    pass


@hookimpl
def macaw_plugin_info() -> dict:
    return dict(_metadata)


@hookimpl
def macaw_plugin_readme() -> str:
    return load_readme()
