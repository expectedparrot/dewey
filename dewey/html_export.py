from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from dewey.repo import DeweyRepo, atomic_write_text, utc_now


def explorer_payload(repo: DeweyRepo) -> dict[str, Any]:
    config = repo.load_config()
    order = repo.load_order().order
    positions = {source_id: index for index, source_id in enumerate(order)}
    sources = []
    links = []
    for source_id in repo.list_source_ids():
        entry = repo.load_entry(source_id)
        metadata = repo.load_metadata(source_id)
        state = repo.load_state(source_id)
        source_dir = repo.source_dir(source_id)
        summary_path = source_dir / "summary.txt"
        notes_path = source_dir / "notes.md"
        markdown = ""
        if metadata.markdown_path:
            markdown_path = repo.root / metadata.markdown_path
            if markdown_path.exists():
                markdown = markdown_path.read_text(encoding="utf-8")
        outgoing = [item.model_dump(mode="json") for item in repo.load_links(source_id).outgoing]
        for item in outgoing:
            links.append({"from": source_id, "to": item["target"], "type": item["type"], "note": item["note"]})
        sources.append(
            {
                "source_id": source_id,
                "bibtex_key": entry.key,
                "entry_type": entry.entry_type,
                "title": entry.title(),
                "authors": entry.author(),
                "year": entry.year(),
                "doi": entry.fields.get("doi"),
                "url": entry.fields.get("url"),
                "status": state.status.value,
                "priority": state.priority,
                "markdown_status": metadata.markdown_status.value,
                "generator": metadata.markdown_generator.model_dump(mode="json"),
                "summary": summary_path.read_text(encoding="utf-8").strip() if summary_path.exists() else "",
                "notes": notes_path.read_text(encoding="utf-8").strip() if notes_path.exists() else "",
                "markdown": markdown,
                "outgoing": outgoing,
                "order": positions.get(source_id),
            }
        )
    sources.sort(key=lambda item: (item["order"] is None, item["order"] or 0, item["title"].casefold()))
    return {
        "generated_at": utc_now(),
        "project_name": config.project_name or repo.root.name,
        "topic": config.topic,
        "research_question": config.research_question,
        "instructions": repo.instructions_path.read_text(encoding="utf-8").strip(),
        "sources": sources,
        "candidates": [item.model_dump(mode="json") for item in repo.load_discovery().candidates],
        "links": links,
    }


def build_explorer_html(payload: dict[str, Any], title: str) -> str:
    safe_title = html.escape(title)
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title>
<style>
:root{{--paper:#f5f1e8;--card:#fffdf8;--ink:#26251f;--muted:#6f6b60;--line:#d8d0bf;--green:#406d4a;--red:#a44b3f;--blue:#456b8c;--gold:#b88a31}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,sans-serif}}
header{{padding:28px clamp(18px,4vw,60px);background:#263b2b;color:white}} h1{{margin:0;font:700 clamp(25px,4vw,42px)/1.1 Georgia,serif}}
.question{{max-width:980px;margin:10px 0 0;color:#e4eddf;font-size:17px}} .shell{{display:grid;grid-template-columns:310px minmax(0,1fr);min-height:calc(100vh - 130px)}}
aside{{border-right:1px solid var(--line);padding:18px;position:sticky;top:0;height:100vh;overflow:auto;background:#eee8dc}} main{{padding:24px clamp(18px,4vw,52px);min-width:0}}
.tabs{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px}} button,.button{{border:1px solid var(--line);background:var(--card);color:var(--ink);padding:8px 12px;border-radius:999px;cursor:pointer}}
button.active{{background:var(--green);color:white;border-color:var(--green)}} input,select{{width:100%;padding:10px;border:1px solid var(--line);border-radius:8px;background:white;margin:0 0 9px}}
.stats{{display:grid;grid-template-columns:repeat(4,minmax(100px,1fr));gap:10px;margin-bottom:18px}} .stat,.card,.detail{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px}}
.stat strong{{display:block;font-size:25px}} .list{{display:grid;gap:10px}} .card{{cursor:pointer}} .card:hover{{border-color:var(--green)}} .card h3{{margin:0 0 4px;font:700 18px/1.3 Georgia,serif}}
.meta,.muted{{color:var(--muted);font-size:13px}} .badge{{display:inline-block;border-radius:999px;padding:2px 8px;background:#e7e0d3;margin:2px 3px 2px 0;font-size:12px}}
.badge.included,.badge.added{{background:#d9eadb;color:#285833}} .badge.relevant{{background:#fff0bd;color:#745500}} .badge.rejected,.badge.excluded{{background:#f4d6d2;color:#792e28}}
.detail h2{{font:700 28px/1.2 Georgia,serif;margin-top:0}} .summary{{font-size:17px;border-left:4px solid var(--gold);padding-left:14px}} pre{{white-space:pre-wrap;word-break:break-word;max-height:65vh;overflow:auto;background:#f3eee4;padding:16px;border-radius:8px}}
.hidden{{display:none}} a{{color:var(--blue)}} .edge{{padding:10px 0;border-bottom:1px solid var(--line)}} .empty{{padding:40px;text-align:center;color:var(--muted)}}
@media(max-width:800px){{.shell{{display:block}} aside{{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}} .stats{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body>
<header><h1>{safe_title}</h1><div id="topic" class="question"></div></header>
<div class="shell"><aside><div class="tabs"><button data-tab="sources" class="active">Corpus</button><button data-tab="candidates">Discovery</button><button data-tab="graph">Citations</button></div>
<input id="search" type="search" placeholder="Search titles, authors, summaries…"><select id="filter"><option value="">All states</option></select>
<button id="download">Download filtered JSON</button><p class="muted" id="generated"></p><details><summary>Review instructions</summary><p id="instructions"></p></details></aside>
<main><div id="stats" class="stats"></div><section id="list" class="list"></section><section id="detail" class="detail hidden"></section></main></div>
<script id="dewey-data" type="application/json">{data}</script><script>
const D=JSON.parse(document.getElementById('dewey-data').textContent); let tab='sources', selected=null;
const q=document.getElementById('search'), filter=document.getElementById('filter'), list=document.getElementById('list'), detail=document.getElementById('detail');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
document.getElementById('topic').textContent=[D.topic,D.research_question].filter(Boolean).join(' — '); document.getElementById('instructions').textContent=D.instructions||'No review instructions.'; document.getElementById('generated').textContent='Generated '+D.generated_at;
function states(){{return tab==='sources'?['unread','queued','reading','read','included','excluded']:tab==='candidates'?['candidate','relevant','rejected','added']:[]}}
function resetFilter(){{filter.innerHTML='<option value="">All states</option>'+states().map(x=>`<option>${{x}}</option>`).join(''); filter.disabled=tab==='graph';}}
function searchable(x){{return Object.values(x).filter(v=>typeof v==='string').join(' ').toLowerCase()}}
function filtered(){{const term=q.value.toLowerCase(), state=filter.value; const rows=tab==='sources'?D.sources:tab==='candidates'?D.candidates:D.links; return rows.filter(x=>(!term||searchable(x).includes(term))&&(!state||x.status===state));}}
function stats(){{const cs=D.candidates.reduce((a,x)=>(a[x.status]=(a[x.status]||0)+1,a),{{}}); document.getElementById('stats').innerHTML=`<div class="stat"><strong>${{D.sources.length}}</strong>sources</div><div class="stat"><strong>${{D.sources.filter(x=>x.status==='included').length}}</strong>included</div><div class="stat"><strong>${{cs.candidate||0}}</strong>undecided</div><div class="stat"><strong>${{D.links.length}}</strong>links</div>`}}
function sourceCard(x){{return `<article class="card" data-id="${{esc(x.source_id)}}"><h3>${{esc(x.title||x.bibtex_key)}}</h3><div class="meta">${{esc(x.authors)}} ${{esc(x.year)}}</div><span class="badge ${{x.status}}">${{x.status}}</span><span class="badge">${{x.markdown_status}}</span><p>${{esc(x.summary||'No summary yet.')}}</p></article>`}}
function candidateCard(x){{return `<article class="card" data-id="${{esc(x.candidate_id)}}"><h3>${{esc(x.title)}}</h3><span class="badge ${{x.status}}">${{x.status}}</span>${{x.relevance_score==null?'':`<span class="badge">score ${{x.relevance_score}}</span>`}}<p>${{esc(x.rationale||x.raw_citation||x.abstract||'No rationale.')}}</p></article>`}}
function renderList(){{detail.classList.add('hidden'); const rows=filtered(); list.innerHTML=rows.length?(tab==='sources'?rows.map(sourceCard).join(''):tab==='candidates'?rows.map(candidateCard).join(''):rows.map(x=>`<article class="card edge"><strong>${{esc(label(x.from))}}</strong> → <span class="badge">${{esc(x.type)}}</span> → <strong>${{esc(label(x.to))}}</strong><div class="muted">${{esc(x.note||'')}}</div></article>`).join('')):'<div class="empty">No matching records.</div>'; if(tab!=='graph') document.querySelectorAll('.card[data-id]').forEach(el=>el.onclick=()=>show(el.dataset.id));}}
function label(id){{return D.sources.find(x=>x.source_id===id)?.title||id}}
function show(id){{selected=id; const x=(tab==='sources'?D.sources:D.candidates).find(x=>(x.source_id||x.candidate_id)===id); if(!x)return; list.innerHTML=''; detail.classList.remove('hidden'); if(tab==='sources')detail.innerHTML=`<button id="back">← Back</button><h2>${{esc(x.title)}}</h2><p class="meta">${{esc(x.authors)}} · ${{esc(x.year)}} · ${{esc(x.bibtex_key)}} · ${{esc(x.source_id)}}</p><p><span class="badge ${{x.status}}">${{x.status}}</span> ${{x.doi?`<a href="https://doi.org/${{esc(x.doi)}}">DOI</a>`:''}} ${{x.url?`<a href="${{esc(x.url)}}">Source page</a>`:''}}</p><h3>Summary</h3><p class="summary">${{esc(x.summary||'No summary yet.')}}</p><details><summary>Notes</summary><pre>${{esc(x.notes)}}</pre></details><details><summary>Full Markdown</summary><pre>${{esc(x.markdown)}}</pre></details>`; else detail.innerHTML=`<button id="back">← Back</button><h2>${{esc(x.title)}}</h2><p><span class="badge ${{x.status}}">${{x.status}}</span> discovered by ${{esc(x.discovery_method)}}</p><h3>Screening rationale</h3><p>${{esc(x.rationale||'Not screened.') }}</p><h3>Raw citation / abstract</h3><pre>${{esc(x.raw_citation||x.abstract||'')}}</pre><p>${{x.doi?`DOI: ${{esc(x.doi)}}`:''}} ${{x.cited_by_source_id?`Cited by: ${{esc(label(x.cited_by_source_id))}}`:''}}</p>`; document.getElementById('back').onclick=renderList;}}
function render(){{stats();renderList()}} document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{{tab=b.dataset.tab;selected=null;document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));resetFilter();render()}}); q.oninput=renderList;filter.onchange=renderList;
document.getElementById('download').onclick=()=>{{const blob=new Blob([JSON.stringify(filtered(),null,2)],{{type:'application/json'}}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`dewey-${{tab}}.json`;a.click();URL.revokeObjectURL(a.href)}}; resetFilter();render();
</script></body></html>'''


def write_explorer(repo: DeweyRepo, output: Path, title: str | None = None) -> dict[str, Any]:
    payload = explorer_payload(repo)
    resolved_title = title or f"{payload['project_name']} · literature explorer"
    target = output if output.is_absolute() else repo.root / output
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(target, build_explorer_html(payload, resolved_title))
    return {"path": str(target), "sources": len(payload["sources"]), "candidates": len(payload["candidates"]), "links": len(payload["links"])}
