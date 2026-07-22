from __future__ import annotations

from importlib.resources import files


def _read_doc(name: str) -> str:
    return files(__package__).joinpath(name).read_text(encoding="utf-8").strip() + "\n"


def meta() -> str:
    return _read_doc("META.md")


def agent() -> str:
    return _read_doc("AGENT.md")


def readme() -> str:
    return _read_doc("README.md")

# Compatibility aliases for the macaw plugin loader (load_* convention)
load_meta = meta
load_agent = agent
load_readme = readme
