from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from dewey.bibtex import dump_entry
from dewey.repo import DeweyRepo, atomic_write_text, utc_now


def author_surname(author: str) -> str:
    author = author.strip()
    if not author:
        return "Unknown"
    if "," in author:
        return author.split(",", maxsplit=1)[0].strip()
    return author.split()[-1]


def citation_label(authors: str, year: str, title: str = "") -> str:
    surnames = [author_surname(author) for author in authors.split(" and ") if author.strip()]
    if not surnames:
        words = title.replace("[", "").replace("]", "").split()
        names = " ".join(words[:6]) + ("…" if len(words) > 6 else "") if words else "Unresolved citation"
    elif len(surnames) == 1:
        names = surnames[0]
    elif len(surnames) == 2:
        names = f"{surnames[0]} & {surnames[1]}"
    else:
        names = f"{surnames[0]} et al."
    return f"{names} ({year})" if year else names


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
                "bibtex": dump_entry(entry),
                "entry_type": entry.entry_type,
                "title": entry.title(),
                "authors": entry.author(),
                "year": entry.year(),
                "citation_label": citation_label(entry.author(), entry.year(), entry.title()),
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
    label_groups: dict[str, list[dict[str, Any]]] = {}
    for source in sources:
        label_groups.setdefault(source["citation_label"], []).append(source)
    for group in label_groups.values():
        if len(group) < 2:
            continue
        for index, source in enumerate(sorted(group, key=lambda item: item["title"].casefold())):
            label = source["citation_label"]
            source["citation_label"] = (
                label.removesuffix(")") + f"{chr(97 + index)})"
                if label.endswith(")")
                else f"{label} [{chr(97 + index)}]"
            )
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
    return f"""<!doctype html>
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
.stats{{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin:0 0 14px;color:var(--muted);font-size:13px}} .stats strong{{color:var(--ink);font-size:15px}} .stats .sep{{color:#aaa18f}} .card,.detail{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px}}
.list{{display:grid;gap:10px}} .card{{cursor:pointer}} .card:hover{{border-color:var(--green)}} .card h3{{margin:0 0 4px;font:700 18px/1.3 Georgia,serif}}
.meta,.muted{{color:var(--muted);font-size:13px}} .badge{{display:inline-block;border-radius:999px;padding:2px 8px;background:#e7e0d3;margin:2px 3px 2px 0;font-size:12px}}
.badge.included,.badge.added{{background:#d9eadb;color:#285833}} .badge.relevant{{background:#fff0bd;color:#745500}} .badge.rejected,.badge.excluded{{background:#f4d6d2;color:#792e28}}
.detail h2{{font:700 28px/1.2 Georgia,serif;margin-top:0}} .summary{{font-size:17px;border-left:4px solid var(--gold);padding-left:14px}} pre{{white-space:pre-wrap;word-break:break-word;max-height:65vh;overflow:auto;background:#f3eee4;padding:16px;border-radius:8px}}
.hidden{{display:none!important}} a{{color:var(--blue)}} .edge{{padding:10px 0;border-bottom:1px solid var(--line)}} .empty{{padding:40px;text-align:center;color:var(--muted)}}
.graph-scope{{display:flex;gap:8px;align-items:flex-start;margin:0 0 12px;color:var(--muted);font-size:13px}} .graph-scope input{{width:auto;margin:3px 0 0}}
.tab-note{{margin:-4px 0 16px;padding:11px 14px;border-left:4px solid var(--blue);background:#e8eef2;color:#344b5c}} .downloads{{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}}
.graph-wrap{{overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px}} .citation-graph{{display:block;width:100%;min-width:650px;height:auto}}
.citation-graph .link{{stroke:#9a917f;stroke-width:1.5;fill:none;marker-end:url(#arrow);transition:opacity .15s,stroke .15s}} .citation-graph .node{{cursor:pointer;transition:opacity .15s}} .citation-graph .node rect{{fill:#fdfaf3;stroke:var(--green);stroke-width:2}} .citation-graph .node:hover rect,.citation-graph .node.active rect{{fill:#e5efe4;stroke-width:3}} .citation-graph text{{font:600 13px ui-sans-serif,system-ui,sans-serif;fill:var(--ink);stroke:none;pointer-events:none}} .citation-graph .dim{{opacity:.14}} .citation-graph .link.active{{stroke:var(--gold);stroke-width:2.5;opacity:1}}
@media(max-width:800px){{.shell{{display:block}} aside{{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line)}}}}
</style></head><body>
<header><h1>{safe_title}</h1><div id="topic" class="question"></div></header>
<div class="shell"><aside><div class="tabs"><button data-tab="sources" class="active">Corpus</button><button data-tab="candidates">Discovery</button><button data-tab="graph">Citations</button></div>
<input id="search" type="search" placeholder="Search titles, authors, summaries…"><select id="filter"><option value="">All states</option></select>
<label id="graph-scope" class="graph-scope hidden"><input id="show-all-citations" type="checkbox"> Show the full traversal network</label>
<div class="downloads"><button id="download">Download JSON</button><button id="bibtex">Download BibTeX</button></div><p class="muted" id="generated"></p><details><summary>Review instructions</summary><p id="instructions"></p></details></aside>
<main><div id="stats" class="stats"></div><div id="tab-note" class="tab-note hidden"></div><section id="list" class="list"></section><section id="detail" class="detail hidden"></section></main></div>
<script id="dewey-data" type="application/json">{data}</script><script>
const D=JSON.parse(document.getElementById('dewey-data').textContent); let tab='sources', selected=null;
const q=document.getElementById('search'), filter=document.getElementById('filter'), list=document.getElementById('list'), detail=document.getElementById('detail'), note=document.getElementById('tab-note'), bibButton=document.getElementById('bibtex'), graphScope=document.getElementById('graph-scope'), showAllCitations=document.getElementById('show-all-citations');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
const inline=s=>esc(s).replace(/\\*\\*([^*]+)\\*\\*/g,'<strong>$1</strong>').replace(/_([^_]+)_/g,'<em>$1</em>');
document.getElementById('topic').textContent=[D.topic,D.research_question].filter(Boolean).join(' — '); document.getElementById('instructions').textContent=D.instructions||'No review instructions.'; document.getElementById('generated').textContent='Generated '+D.generated_at;
function states(){{return tab==='sources'?['unread','queued','reading','read','included','excluded']:tab==='candidates'?['candidate','relevant','rejected','added']:[]}}
function resetFilter(){{filter.innerHTML='<option value="">All states</option>'+states().map(x=>`<option>${{x}}</option>`).join(''); filter.disabled=tab==='graph'; graphScope.classList.toggle('hidden',tab!=='graph'); bibButton.classList.toggle('hidden',tab!=='sources'); note.classList.toggle('hidden',tab!=='candidates'); note.textContent=tab==='candidates'?'Discovery contains possible sources found through searches or extracted from papers’ references. Candidates stay outside the reviewed corpus until screened and added.':'';}}
function searchable(x){{return Object.values(x).filter(v=>typeof v==='string').join(' ').toLowerCase()}}
function filtered(){{const term=q.value.toLowerCase(), state=filter.value; let rows=tab==='sources'?D.sources:tab==='candidates'?D.candidates:D.links; if(tab==='graph'&&!showAllCitations.checked){{const included=new Set(D.sources.filter(x=>x.status==='included').map(x=>x.source_id));rows=rows.filter(x=>included.has(x.from)||included.has(x.to))}} return rows.filter(x=>(!term||searchable(x).includes(term))&&(!state||x.status===state));}}
function stats(){{const cs=D.candidates.reduce((a,x)=>(a[x.status]=(a[x.status]||0)+1,a),{{}}), item=(n,s)=>`<span><strong>${{n}}</strong> ${{s}}</span>`; document.getElementById('stats').innerHTML=[item(D.sources.length,'sources'),item(D.sources.filter(x=>x.status==='included').length,'included'),item(cs.candidate||0,'undecided'),item(D.links.length,'citation links')].join('<span class="sep">·</span>')}}
function sourceCard(x){{return `<article class="card" data-id="${{esc(x.source_id)}}"><h3>${{inline(x.title||x.bibtex_key)}}</h3><div class="meta">${{esc(x.authors)}} ${{esc(x.year)}}</div><span class="badge ${{x.status}}">${{x.status}}</span><span class="badge">${{x.markdown_status}}</span><p>${{inline(x.summary||'No summary yet.')}}</p></article>`}}
function sightings(x){{return x.provenance?.length||1}}
function candidateCard(x){{const n=sightings(x);return `<article class="card" data-id="${{esc(x.candidate_id)}}"><h3>${{inline(x.title)}}</h3><span class="badge ${{x.status}}">${{x.status}}</span>${{x.relevance_score==null?'':`<span class="badge">score ${{x.relevance_score}}</span>`}}<span class="badge">${{n}} sighting${{n===1?'':'s'}}</span><p>${{inline(x.rationale||x.raw_citation||x.abstract||'No rationale.')}}</p></article>`}}
function renderList(){{detail.classList.add('hidden'); const rows=filtered(); list.innerHTML=rows.length?(tab==='sources'?rows.map(sourceCard).join(''):tab==='candidates'?rows.map(candidateCard).join(''):citationGraph(rows)):'<div class="empty">No matching records.</div>'; if(tab!=='graph') document.querySelectorAll('.card[data-id]').forEach(el=>el.onclick=()=>show(el.dataset.id)); else activateGraph();}}
function label(id){{const x=D.sources.find(x=>x.source_id===id); return x?.citation_label||id}}
function citationGraph(edges){{
  const ids=[...new Set([...D.sources.filter(x=>x.status==='included').map(x=>x.source_id),...edges.flatMap(x=>[x.from,x.to])])], source=id=>D.sources.find(x=>x.source_id===id), year=id=>parseInt(source(id)?.year)||9999;
  const years=[...new Set(ids.map(year))].sort((a,b)=>a-b), w=900, maxCols=4, positions={{}}; let y=72;
  years.forEach(value=>{{const group=ids.filter(id=>year(id)===value).sort((a,b)=>label(a).localeCompare(label(b))), rowCount=Math.ceil(group.length/maxCols), perRow=Math.ceil(group.length/rowCount); for(let start=0;start<group.length;start+=perRow){{const row=group.slice(start,start+perRow); row.forEach((id,col)=>positions[id]={{x:w*(col+1)/(row.length+1),y}}); y+=112}} y+=24}});
  const h=Math.max(250,y+8);
  const lines=edges.map(e=>{{const a=positions[e.to],b=positions[e.from], starts=edges.filter(x=>x.to===e.to),ends=edges.filter(x=>x.from===e.from),x1=a.x+(starts.indexOf(e)-(starts.length-1)/2)*13,x2=b.x+(ends.indexOf(e)-(ends.length-1)/2)*13,y1=a.y+29,y2=b.y-29,mid=y1+(y2-y1)*.5; return `<path class="link" data-a="${{esc(e.from)}}" data-b="${{esc(e.to)}}" d="M ${{x1}} ${{y1}} C ${{x1}} ${{mid}}, ${{x2}} ${{mid}}, ${{x2}} ${{y2}}"><title>${{esc(label(e.to))}} → ${{esc(label(e.from))}} (cited by)</title></path>`}}).join('');
  const nodes=ids.map(id=>{{const p=positions[id], words=label(id).split(' '), mid=Math.ceil(words.length/2), l1=words.slice(0,mid).join(' '),l2=words.slice(mid).join(' ');return `<g class="node" data-id="${{esc(id)}}"><rect x="${{p.x-82}}" y="${{p.y-28}}" width="164" height="56" rx="12"/><text x="${{p.x}}" y="${{p.y-(l2?5:-1)}}" text-anchor="middle">${{esc(l1)}}</text>${{l2?`<text x="${{p.x}}" y="${{p.y+14}}" text-anchor="middle">${{esc(l2)}}</text>`:''}}<title>${{esc(D.sources.find(x=>x.source_id===id)?.title||id)}}</title></g>`}}).join('');
  const edgeList=edges.map(x=>`<div class="edge"><strong>${{esc(label(x.from))}}</strong> → <span class="badge">${{esc(x.type)}}</span> → <strong>${{esc(label(x.to))}}</strong></div>`).join('');
  return `<p class="muted">The default view shows reviewed papers and their directly connected citation context. Earlier work appears at the top; arrows show influence from a cited paper to the later paper citing it. Hover to isolate a citation neighborhood.</p><div class="graph-wrap"><svg class="citation-graph" viewBox="0 0 ${{w}} ${{h}}" role="img" aria-label="Chronological citation network"><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#9a917f"/></marker></defs>${{lines}}${{nodes}}</svg></div><details><summary>Citation edge list (citing → cited)</summary>${{edgeList}}</details>`
}}
function activateGraph(){{const svg=document.querySelector('.citation-graph'),nodes=[...document.querySelectorAll('.node')],links=[...document.querySelectorAll('.link')]; nodes.forEach(node=>{{node.onclick=()=>showSource(node.dataset.id); node.onmouseenter=()=>{{const id=node.dataset.id, related=new Set([id]); links.forEach(link=>{{const active=link.dataset.a===id||link.dataset.b===id; link.classList.toggle('active',active); link.classList.toggle('dim',!active); if(active){{related.add(link.dataset.a);related.add(link.dataset.b)}}}}); nodes.forEach(n=>{{n.classList.toggle('active',n.dataset.id===id);n.classList.toggle('dim',!related.has(n.dataset.id))}})}}; node.onmouseleave=()=>{{links.forEach(x=>x.classList.remove('active','dim'));nodes.forEach(x=>x.classList.remove('active','dim'))}}}})}}
function showSource(id){{tab='sources'; document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x.dataset.tab==='sources')); resetFilter(); show(id)}}
function show(id,updateHash=true){{selected=id; const x=(tab==='sources'?D.sources:D.candidates).find(x=>(x.source_id||x.candidate_id)===id); if(!x)return; if(updateHash)history.replaceState(null,'',`#${{tab==='sources'?'source':'candidate'}}=${{encodeURIComponent(id)}}`); list.innerHTML=''; detail.classList.remove('hidden'); if(tab==='sources')detail.innerHTML=`<button id="back">← Back</button><h2>${{esc(x.title)}}</h2><p class="meta">${{esc(x.authors)}} · ${{esc(x.year)}} · ${{esc(x.bibtex_key)}} · ${{esc(x.source_id)}}</p><p><span class="badge ${{x.status}}">${{x.status}}</span> ${{x.doi?`<a href="https://doi.org/${{esc(x.doi)}}">DOI</a>`:''}} ${{x.url?`<a href="${{esc(x.url)}}">Source page</a>`:''}}</p><h3>Summary</h3><p class="summary">${{esc(x.summary||'No summary yet.')}}</p><details><summary>Notes</summary><pre>${{esc(x.notes)}}</pre></details><details><summary>Full Markdown</summary><pre>${{esc(x.markdown)}}</pre></details>`; else {{const provenance=x.provenance?.length?x.provenance:[{{source_id:x.cited_by_source_id,method:x.discovery_method,raw_citation:x.raw_citation,discovered_at:x.created_at}}], trails=provenance.map(p=>`<li>${{p.source_id?`<strong>${{esc(label(p.source_id))}}</strong> · `:''}}${{esc(p.method)}}${{p.discovered_at?` · ${{esc(p.discovered_at.slice(0,10))}}`:''}}</li>`).join(''); detail.innerHTML=`<button id="back">← Back</button><h2>${{esc(x.title)}}</h2><p><span class="badge ${{x.status}}">${{x.status}}</span> ${{sightings(x)}} discovery sighting${{sightings(x)===1?'':'s'}}</p><h3>Discovery provenance</h3><ul>${{trails}}</ul><h3>Screening rationale</h3><p>${{esc(x.rationale||'Not screened.') }}</p><h3>Raw citation / abstract</h3><pre>${{esc(x.raw_citation||x.abstract||'')}}</pre><p>${{x.doi?`DOI: ${{esc(x.doi)}}`:''}}</p>`}} document.getElementById('back').onclick=()=>{{history.replaceState(null,'',location.pathname+location.search);renderList()}};}}
function render(){{stats();renderList()}} document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{{tab=b.dataset.tab;selected=null;document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));resetFilter();render()}}); q.oninput=renderList;filter.onchange=renderList;showAllCitations.onchange=renderList;
document.getElementById('download').onclick=()=>{{const blob=new Blob([JSON.stringify(filtered(),null,2)],{{type:'application/json'}}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`dewey-${{tab}}.json`;a.click();URL.revokeObjectURL(a.href)}}; resetFilter();render();
bibButton.onclick=()=>{{const text=filtered().map(x=>x.bibtex).filter(Boolean).join('\\n'),blob=new Blob([text],{{type:'application/x-bibtex'}}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='dewey-corpus.bib';a.click();URL.revokeObjectURL(a.href)}};
const deepLink=new URLSearchParams(location.hash.slice(1)); const sourceLink=deepLink.get('source'),candidateLink=deepLink.get('candidate'); if(sourceLink)show(sourceLink,false); else if(candidateLink){{tab='candidates';document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x.dataset.tab==='candidates'));resetFilter();show(candidateLink,false)}};
</script></body></html>"""


def write_explorer(repo: DeweyRepo, output: Path, title: str | None = None) -> dict[str, Any]:
    payload = explorer_payload(repo)
    resolved_title = title or f"{payload['project_name']} · literature explorer"
    target = output if output.is_absolute() else repo.root / output
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(target, build_explorer_html(payload, resolved_title))
    return {
        "path": str(target),
        "sources": len(payload["sources"]),
        "candidates": len(payload["candidates"]),
        "links": len(payload["links"]),
    }
