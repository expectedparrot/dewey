from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from dewey.models import ArticleSpec
from dewey.repo import DeweyError, atomic_write_text


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
.reference { scroll-margin-top:1rem; }
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
    lines.extend(["", "## Source metadata", ""])
    for source in bundle["sources"]:
        lines.append(
            f"- `{source['source_id']}` / `@{source['bibtex_key']}` — {source['author']} ({source['year']}), "
            f"*{source['title']}*. DOI: {source['doi'] or 'none'}"
        )
    return "\n".join(lines) + "\n"


def render_with_pandoc(markdown_path: Path, output_path: Path, css_path: Path | None = None) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        raise DeweyError("pandoc_not_found", "pandoc is required for HTML rendering", exit_code=4)
    stylesheet = css_path or output_path.with_suffix(".css")
    if css_path is None:
        atomic_write_text(stylesheet, ARTICLE_CSS)
    command = [
        pandoc,
        str(markdown_path),
        "--standalone",
        "--toc",
        "--toc-depth=2",
        "--metadata",
        "lang=en",
        "--css",
        str(stylesheet),
        "--embed-resources",
        "--output",
        str(output_path),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode != 0:
        raise DeweyError("pandoc_failed", completed.stderr.strip() or "pandoc rendering failed", exit_code=3)


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
