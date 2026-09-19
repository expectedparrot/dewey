from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

from dewey.bibtex import dump_entry
from dewey.identity import normalize_doi
from dewey.models import ArticleSpec
from dewey.repo import DeweyError, DeweyRepo, atomic_write_text


ARTICLE_CSS = """
:root { --ink:#202020; --muted:#666; --green:#428a5f; --rule:#d9d9d9; --paper:#fff; }
* { box-sizing:border-box; }
html { background:#f5f5f3; font-size:17px; -webkit-font-smoothing:antialiased; }
body { max-width:900px; margin:0 auto; padding:64px 76px 96px; color:var(--ink); background:var(--paper); font:1rem/1.65 Georgia,'Times New Roman',serif; box-shadow:0 0 40px rgba(0,0,0,.07); }
h1,h2,h3 { line-height:1.2; color:#161616; font-weight:600; }
h1 { font-size:2.45rem; letter-spacing:-.025em; margin-bottom:.25rem; }
h2 { font-size:1.55rem; margin-top:2.5rem; padding-top:.45rem; border-top:2px solid var(--green); }
h3 { font-size:1.18rem; margin-top:1.8rem; }
.subtitle { color:var(--muted); font-size:1.25rem; margin-top:0; }
.abstract { margin:2rem 0; padding:1rem 1.25rem; border-left:4px solid var(--green); background:#f4f8f5; }
.abstract-title { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-weight:700; text-transform:uppercase; letter-spacing:.08em; font-size:.75rem; color:var(--green); }
.related-resource { margin:1.5rem 0 2.25rem; padding:.85rem 1rem; border:1px solid #bad4c3; border-radius:4px; background:#f4f8f5; font:0.92rem/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
.related-resource p { margin:0; }
.explorer-panel { margin:2rem 0 2.5rem; }
.explorer-panel iframe { width:100%; height:560px; border:1px solid var(--rule); border-radius:6px; background:#f5f1e8; }
.explorer-panel figcaption { margin-top:.5rem; color:var(--muted); font:0.84rem/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
.reference, .csl-entry { scroll-margin-top:1rem; }
.source-links { font-size:.85rem; margin:.25rem 0 1rem; }
nav#TOC { margin:2rem 0; padding:1rem 1.25rem; border:1px solid var(--rule); background:#fafafa; }
nav#TOC:before { content:'Contents'; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; font-weight:700; }
nav#TOC ul { margin-bottom:0; }
table { width:100%; border-collapse:collapse; margin:1.4rem 0; font-size:.9rem; }
th { text-align:left; border-bottom:2px solid var(--ink); padding:.5rem; }
td { vertical-align:top; border-bottom:1px solid var(--rule); padding:.5rem; }
a { color:#286f49; text-underline-offset:2px; }
.article-meta { color:var(--muted); font:0.86rem/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
@media(max-width:760px){ body{padding:32px 22px 64px;box-shadow:none} h1{font-size:2rem} }
@media print{ html,body{background:#fff} body{padding:0;box-shadow:none;font-size:11pt} nav#TOC{break-after:page} }
""".strip() + "\n"


def article_brief(spec: ArticleSpec, bundle: dict[str, Any]) -> str:
    claims = {claim["claim_id"]: claim for claim in bundle["claims"]}
    themes = {theme["theme_id"]: theme for theme in bundle["themes"]}
    lines = [
        f"# Article brief: {spec.title}",
        "",
        "> This is a writing brief, not manuscript prose. Use it to write an economics literature review",
        "> organized around an argument, intellectual development, and evidence-weighted claims.",
        "",
        "## Positioning",
        "",
        f"- **Audience:** {spec.audience}",
        f"- **Genre:** {spec.genre}",
        f"- **Central question:** {spec.central_question}",
        f"- **Thesis:** {spec.thesis}",
        f"- **Abstract:** {spec.abstract}",
        f"- **Keywords:** {', '.join(spec.keywords)}",
        f"- **JEL codes:** {', '.join(spec.jel_codes)}",
        "",
        "## Motivation and context",
        "",
    ]
    lines.extend(f"- {item}" for item in spec.motivation)
    lines.extend(["", "### Field context", ""])
    lines.extend(f"- {item}" for item in spec.field_context)
    lines.extend(["", "### Contribution", ""])
    lines.extend(f"- {item}" for item in spec.contribution)
    lines.extend(["", "## Scope", "", "### Include", ""])
    lines.extend(f"- {item}" for item in spec.scope_includes)
    lines.extend(["", "### Exclude or treat as boundary evidence", ""])
    lines.extend(f"- {item}" for item in spec.scope_excludes)
    lines.extend(["", "## Literature map", ""])
    for stream in spec.literatures:
        lines.extend(
            [
                f"### {stream.label} (`{stream.stream_id}`)",
                "",
                stream.description,
                "",
                f"**Relationship to review:** {stream.relationship_to_review}",
                "",
                f"**Sources:** {', '.join(stream.source_ids)}",
                "",
            ]
        )
    source_by_id = {source["source_id"]: source for source in bundle["sources"]}
    lines.extend(["## Study map", "", "| Study | Role | Contribution | Claims | Caveat |", "|---|---|---|---|---|"])
    for item in spec.source_positions:
        source = source_by_id[item.source_id]
        lines.append(
            "| "
            + " | ".join(
                value.replace("|", "\\|")
                for value in (
                    f"@{source['bibtex_key']}: {source['title']}",
                    item.role,
                    item.contribution,
                    ", ".join(item.claim_ids) or "context only",
                    item.caveat or "—",
                )
            )
            + " |"
        )
    lines.extend(["## Timeline", "", "| Year | Development | Why it matters | Sources |", "|---:|---|---|---|"])
    for item in sorted(spec.timeline, key=lambda value: value.year):
        lines.append(f"| {item.year} | {item.label} | {item.significance} | {', '.join(item.source_ids)} |")
    lines.extend(["", "## Planned argument", ""])
    for number, section in enumerate(spec.sections, 1):
        lines.extend([f"### {number}. {section.heading}", "", f"**Purpose:** {section.purpose}", ""])
        if section.theme_ids:
            lines.append("**Themes:** " + "; ".join(themes[item]["label"] for item in section.theme_ids))
        for claim_id in section.claim_ids:
            claim = claims[claim_id]
            lines.extend(
                [
                    "",
                    f"#### Claim: {claim['statement']}",
                    "",
                    f"- Scope: {claim['scope']}",
                    f"- Confidence: {claim['confidence']} — {claim['confidence_rationale']}",
                ]
            )
            for evidence in claim["evidence"]:
                finding = evidence["finding"]
                sources = ", ".join(source["bibtex_key"] for source in evidence["sources"])
                locators = json.dumps(finding["locators"], ensure_ascii=False)
                lines.append(
                    f"- **{evidence['relationship']}** ({sources}): {finding['evidence_statement']} "
                    f"Locator: `{locators}`. Appraisal: {evidence['appraisal']['overall_judgment'] if evidence['appraisal'] else 'not appraised'}."
                )
        lines.append("")
    lines.extend(["## Intended conclusion", ""])
    lines.extend(f"- {item}" for item in spec.conclusion)
    lines.extend(["", "## Citation workflow", "",
                  "Use `dewey report citations --status included --json` for citation keys and paper links.",
                  "Write Pandoc citations such as `[@key, p. 7]` or narrative `@key`. Render with",
                  "`dewey report render article.md --output article.html --json` to generate linked references.",
                  "Deliver the returned PDF assets beside the HTML, preserving relative paths.",
                  "", "## Source metadata", ""])
    for source in bundle["sources"]:
        lines.append(
            f"- `{source['source_id']}` / `@{source['bibtex_key']}` — {source['author']} ({source['year']}), "
            f"*{source['title']}*. DOI: {source['doi'] or 'none'}"
        )
    return "\n".join(lines) + "\n"


def local_pdf(repo: DeweyRepo, source_id: str) -> Path | None:
    metadata = repo.load_metadata(source_id)
    for value in (metadata.managed_pdf_path, metadata.original_pdf_path):
        if value:
            path = repo.root / value
            if path.is_file():
                return path
    return None


def report_citations(repo: DeweyRepo) -> list[dict[str, Any]]:
    """Citation instructions and available paper links; discovery leads are excluded."""
    records = []
    keys: set[str] = set()
    for source_id in repo.list_source_ids():
        entry = repo.load_entry(source_id)
        if entry.key in keys:
            raise DeweyError("duplicate_citation_key", f"Duplicate citation key: {entry.key}", exit_code=2)
        keys.add(entry.key)
        metadata = repo.load_metadata(source_id)
        doi = normalize_doi(entry.fields.get("doi"))
        links = []
        for label, url in (
            ("DOI", f"https://doi.org/{quote(doi, safe='/():')}" if doi else None),
            ("Source page", entry.fields.get("url")),
            ("Open access", metadata.open_access_url),
            ("PDF online", metadata.pdf_source_url),
        ):
            if url and urlsplit(url).scheme in {"http", "https"} and urlsplit(url).netloc:
                links.append({"label": label, "url": url})
        records.append({
            "source_id": source_id, "bibtex_key": entry.key,
            "title": entry.fields.get("title", ""), "status": repo.load_state(source_id).status.value,
            "citation": f"[@{entry.key}]", "narrative_citation": f"@{entry.key}",
            "reference_id": f"ref-{entry.key}", "links": links,
            "has_local_pdf": local_pdf(repo, source_id) is not None,
        })
    return sorted(records, key=lambda record: record["bibtex_key"])


def pandoc_nodes(value: Any):
    """Walk parsed nodes, so citation-like text in code is never treated as a citation."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from pandoc_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from pandoc_nodes(child)


def run_pandoc(command: list[str], input_text: str | None = None) -> subprocess.CompletedProcess:
    completed = subprocess.run(command, input=input_text, text=True, capture_output=True)
    if completed.returncode != 0:
        raise DeweyError("pandoc_failed", completed.stderr.strip() or "pandoc rendering failed", exit_code=3)
    return completed


def linked_report_document(
    pandoc: str, markdown_path: Path, output_path: Path, repo: DeweyRepo, csl_path: Path | None,
) -> tuple[str, dict[str, Any]]:
    records = {record["bibtex_key"]: record for record in report_citations(repo)}
    with tempfile.TemporaryDirectory(prefix="dewey-report-") as temporary:
        bibliography = Path(temporary) / "references.bib"
        bibliography.write_text("\n".join(
            dump_entry(repo.load_entry(record["source_id"])) for record in records.values()
        ), encoding="utf-8")
        command = [pandoc, str(markdown_path), "--from=markdown", "--to=json", "--citeproc",
                   "--metadata=link-citations:true", "--metadata=reference-section-title:References"]
        if records:
            command.extend(["--bibliography", str(bibliography)])
        if csl_path:
            command.extend(["--csl", str(csl_path)])
        completed = run_pandoc(command)
        document = json.loads(completed.stdout)
    nodes = list(pandoc_nodes(document))
    cited = {citation["citationId"] for node in nodes if node.get("t") == "Cite"
             for citation in node["c"][0]} - {"*"}
    unknown = cited - records.keys()
    if unknown:
        raise DeweyError("unknown_citation", "Citation keys absent from the Dewey corpus: "
                         + ", ".join(sorted(unknown)), exit_code=2)
    references = {node["c"][0][0][4:]: node for node in nodes
                  if node.get("t") == "Div" and "csl-entry" in node["c"][0][1]
                  and node["c"][0][0].startswith("ref-")}
    missing = cited - references.keys()
    if missing:
        raise DeweyError("missing_references", "No reference entries for: " + ", ".join(sorted(missing))
                         + ". Remove suppress-bibliography or use a CSL style with a bibliography.", exit_code=2)
    assets = []
    for key, node in references.items():
        if key not in records:
            raise DeweyError("unknown_citation", f"Reference absent from the Dewey corpus: {key}", exit_code=2)
        record = records[key]
        links = list(record["links"])
        pdf = local_pdf(repo, record["source_id"])
        if pdf:
            relative = Path(output_path.stem + ".assets") / "papers" / (record["source_id"] + ".pdf")
            destination = output_path.parent / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if pdf.resolve() != destination.resolve():
                shutil.copyfile(pdf, destination)
            assets.append(str(destination))
            links.append({"label": "PDF (local copy)", "url": quote(relative.as_posix(), safe="/")})
        inlines: list[dict[str, Any]] = []
        for link in links:
            if inlines:
                inlines.extend([{"t": "Space"}, {"t": "Str", "c": "·"}, {"t": "Space"}])
            inlines.append({"t": "Link", "c": [["", [], []], [{"t": "Str", "c": link["label"]}],
                                                   [link["url"], ""]]})
        if inlines:
            node["c"][1].append({"t": "Div", "c": [["", ["source-links"], []],
                                                        [{"t": "Para", "c": inlines}]]})
    return json.dumps(document), {"citation_keys": sorted(references), "pdf_assets": assets,
                                  "warnings": completed.stderr.strip().splitlines()}


def render_with_pandoc(
    markdown_path: Path, output_path: Path, css_path: Path | None = None,
    *, repo: DeweyRepo | None = None, csl_path: Path | None = None,
) -> dict[str, Any]:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise DeweyError("pandoc_not_found", "pandoc is required for HTML rendering", exit_code=4)
    if markdown_path.resolve() == output_path.resolve():
        raise DeweyError("invalid_output", "HTML output must differ from the Markdown manuscript", exit_code=2)
    document = None
    result: dict[str, Any] = {"citation_keys": [], "pdf_assets": [], "warnings": []}
    if repo is not None:
        document, result = linked_report_document(pandoc, markdown_path, output_path, repo, csl_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stylesheet = css_path or output_path.with_suffix(".css")
    if css_path is None:
        atomic_write_text(stylesheet, ARTICLE_CSS)
    command = [
        pandoc,
        *(["--from=json"] if document is not None else [str(markdown_path)]),
        "--to=html5",
        "--resource-path", os.pathsep.join([str(markdown_path.resolve().parent), str(Path.cwd())]),
        "--standalone",
        "--toc",
        "--toc-depth=2",
        "--metadata",
        "lang=en",
        "--css",
        str(stylesheet.resolve()),
        "--embed-resources",
        "--output",
        str(output_path),
    ]
    completed = run_pandoc(command, document)
    result["warnings"].extend(completed.stderr.strip().splitlines())
    return result


def embed_explorer(output_path: Path, explorer_path: Path) -> None:
    if not explorer_path.exists():
        raise DeweyError("file_not_found", f"No explorer exists at {explorer_path}", exit_code=4)
    report = output_path.read_text(encoding="utf-8")
    explorer = explorer_path.read_text(encoding="utf-8")
    iframe_pattern = re.compile(
        r'<iframe(?P<attrs>[^>]*\bid="literature-explorer"[^>]*)\bsrc="[^"]+"(?P<rest>[^>]*)>.*?</iframe>',
        re.DOTALL,
    )
    match = iframe_pattern.search(report)
    if match is None:
        raise DeweyError(
            "explorer_iframe_not_found",
            'The rendered report requires an iframe with id="literature-explorer"',
            exit_code=3,
        )
    embedded_iframe = (
        f'<iframe{match.group("attrs")} srcdoc="{html.escape(explorer, quote=True)}"'
        f'{match.group("rest")}></iframe>'
    )
    report = report[: match.start()] + embedded_iframe + report[match.end() :]
    report = re.sub(
        r'href="\.\./ai-interviewers-explorer\.html#source=([^"]+)"',
        r'href="#explorer-embed" data-explorer-source="\1"',
        report,
    )
    report = report.replace(
        "</body>",
        """<script>
document.querySelectorAll('[data-explorer-source]').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();
    const frame = document.getElementById('literature-explorer');
    frame.contentWindow.showSource(link.dataset.explorerSource);
    document.getElementById('explorer-embed').scrollIntoView({behavior: 'smooth'});
  });
});
</script></body>""",
    )
    atomic_write_text(output_path, report)
