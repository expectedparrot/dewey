from __future__ import annotations

import re

from dewey.models import BibEntry

ENTRY_RE = re.compile(r"^\s*@(?P<type>[A-Za-z]+)\s*\{\s*(?P<key>[^,\s]+)\s*,(?P<body>.*)\}\s*$", re.S)


class BibTeXError(ValueError):
    pass


def parse_single_entry(text: str) -> BibEntry:
    match = ENTRY_RE.match(text.strip())
    if not match:
        raise BibTeXError("Expected exactly one BibTeX entry")
    entry_type = match.group("type").lower()
    key = match.group("key").strip()
    body = match.group("body").strip()
    fields: dict[str, str] = {}
    i = 0
    while i < len(body):
        while i < len(body) and body[i] in " \t\r\n,":
            i += 1
        if i >= len(body):
            break
        name_start = i
        while i < len(body) and re.match(r"[A-Za-z0-9_\-]", body[i]):
            i += 1
        name = body[name_start:i].strip().lower()
        if not name:
            raise BibTeXError("Malformed field name")
        while i < len(body) and body[i].isspace():
            i += 1
        if i >= len(body) or body[i] != "=":
            raise BibTeXError(f"Expected '=' after field '{name}'")
        i += 1
        while i < len(body) and body[i].isspace():
            i += 1
        value, i = _parse_value(body, i)
        fields[name] = value
        while i < len(body) and body[i].isspace():
            i += 1
        if i < len(body) and body[i] == ",":
            i += 1
    return BibEntry(entry_type=entry_type, key=key, fields=fields)


def _parse_value(text: str, i: int) -> tuple[str, int]:
    if i >= len(text):
        raise BibTeXError("Missing field value")
    if text[i] == "{":
        depth = 0
        start = i + 1
        i += 1
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                if depth == 0:
                    return text[start:i].strip(), i + 1
                depth -= 1
            i += 1
        raise BibTeXError("Unterminated brace value")
    if text[i] == '"':
        start = i + 1
        i += 1
        escaped = False
        while i < len(text):
            ch = text[i]
            if ch == '"' and not escaped:
                return text[start:i], i + 1
            escaped = ch == "\\" and not escaped
            if ch != "\\":
                escaped = False
            i += 1
        raise BibTeXError("Unterminated quoted value")
    start = i
    while i < len(text) and text[i] not in ",\n\r":
        i += 1
    return text[start:i].strip(), i


def dump_entry(entry: BibEntry) -> str:
    lines = [f"@{entry.entry_type}{{{entry.key},"]
    field_items = list(entry.fields.items())
    for index, (name, value) in enumerate(field_items):
        suffix = "," if index < len(field_items) - 1 else ""
        lines.append(f"  {name}={{{value}}}{suffix}")
    lines.append("}")
    return "\n".join(lines) + "\n"
