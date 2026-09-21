'use strict';
const D = JSON.parse(document.getElementById('dewey-data').textContent);
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const words = value => String(value ?? '').replace(/_/g, ' ');
const nonempty = value => value !== null && value !== undefined && value !== '';
const recorded = value => nonempty(value) ? esc(value) : '<span class="muted">Not recorded</span>';
const empty = message => `<div class="empty">${esc(message)}</div>`;
const safeURL = value => { try { const url = new URL(value); return ['https:','http:'].includes(url.protocol) ? url.href : ''; } catch { return ''; } };
const sources = new Map(D.sources.map(x => [x.source_id, x]));
const studies = new Map(D.studies.map(x => [x.study_id, x]));
const findings = new Map(D.findings.map(x => [x.finding_id, x]));
const themes = new Map(D.themes.map(x => [x.theme_id, x]));
const claims = new Map(D.claims.map(x => [x.claim_id, x]));
const candidateMap = new Map(D.candidates.map(x => [x.candidate_id, x]));
const PAGE_SIZE = 25;
const tabs = ['overview','evidence','sources','graph','candidates'];
const defaults = {tab:'overview',q:'',status:'included',theme:'',yearFrom:'',yearTo:'',design:'',fulltext:'',sort:'review',page:'1',candidateStatus:'',provider:'',via:'',stage:'',reason:'',scope:'focus',focus:'',relation:'',zoom:'1',compare:'',comparison:''};
let state;
let searchTimer;
const byStudy = id => D.findings.filter(x => x.study_id === id);
const studySources = study => (study?.source_ids || []).map(id => sources.get(id)).filter(Boolean);
const sourceStudies = id => D.studies.filter(s => s.source_ids.includes(id));
const appraisalFor = id => D.appraisals.find(x => x.study_id === id);
const themeStudies = id => new Set(D.claims.filter(c => c.theme_ids.includes(id)).flatMap(c => c.evidence.map(e => findings.get(e.finding_id)?.study_id)).filter(Boolean));
const themeSources = id => new Set([...themeStudies(id)].flatMap(id => studies.get(id)?.source_ids || []));
const searchText = value => typeof value === 'string' || typeof value === 'number' ? String(value) : Array.isArray(value) ? value.map(searchText).join(' ') : value && typeof value === 'object' ? Object.values(value).map(searchText).join(' ') : '';
const matches = (value, query = state.q) => !query || searchText(value).toLocaleLowerCase().includes(query.toLocaleLowerCase());
const countBy = values => Object.entries(values.reduce((out, value) => { out[value || 'Not recorded'] = (out[value || 'Not recorded'] || 0) + 1; return out; }, Object.create(null))).sort((a,b) => b[1] - a[1]);
const badge = (value, style='') => `<span class="badge ${esc(style)}">${esc(words(value))}</span>`;
const sourceLabel = id => sources.get(id)?.citation_label || 'Source unavailable';
const selectedStudies = () => [...new Set(state.compare.split(',').filter(id => studies.has(id)))].slice(0,4);

function readState() {
  const params = new URLSearchParams(location.hash.slice(1));
  const value = {...defaults, ...Object.fromEntries(params)};
  // Preserve links in previously published reports.
  const sourceLink = params.get('source');
  if (!params.has('tab') && sourceLink) value.tab = 'sources';
  if (!params.has('tab') && params.has('candidate')) value.tab = 'candidates';
  if (!tabs.includes(value.tab)) value.tab = 'overview';
  value.page = String(Math.max(1, parseInt(value.page) || 1));
  value.zoom = String(Math.min(2, Math.max(.5, Number(value.zoom) || 1)));
  return value;
}
function route(patch={}, base=state) {
  const next = {...base, ...patch};
  const params = new URLSearchParams();
  for (const [key,value] of Object.entries(next)) if (nonempty(value) && (key === 'tab' || value !== defaults[key])) params.set(key, value);
  return '#' + params.toString();
}
function navigate(patch, replace=false, preserveFocus=false) {
  const hash = route(patch);
  if (replace) { history.replaceState(null, '', hash); render(preserveFocus); }
  else if (hash === location.hash) render();
  else location.hash = hash;
}
function link(text, patch, cls='') { return `<a class="${esc(cls)}" href="${esc(route(patch))}">${esc(text)}</a>`; }
const clearDetail = {source:'',candidate:'',claim:'',study:'',finding:''};
const sourceLink = (id,text) => link(text || sourceLabel(id), {...clearDetail,tab:'sources',source:id});
const studyLink = (id,text) => link(text || studies.get(id)?.label || 'Study unavailable', {...clearDetail,tab:'evidence',study:id});
const claimLink = (id,text) => link(text || claims.get(id)?.statement || 'Claim unavailable', {...clearDetail,tab:'overview',claim:id});
const metric = (n,label) => `<div class="metric"><strong>${n}</strong><span>${esc(label)}</span></div>`;
const facts = rows => `<dl class="facts">${rows.map(([label,value])=>`<dt>${esc(label)}</dt><dd>${recorded(value)}</dd>`).join('')}</dl>`;
const pageRows = rows => {state.page=String(Math.min(Number(state.page),Math.max(1,Math.ceil(rows.length/PAGE_SIZE))));return rows.slice((Number(state.page)-1)*PAGE_SIZE,Number(state.page)*PAGE_SIZE);};
function pagination(total) {
  const pages = Math.max(1,Math.ceil(total/PAGE_SIZE)), page = Number(state.page);
  return `<div class="pagination">${page>1?link('← Previous',{page:String(page-1)},'button'):''}<span>Page ${page} of ${pages} · ${total} records</span>${page<pages?link('Next →',{page:String(page+1)},'button'):''}</div>`;
}
function safePDF(source, page) {
  const path = source?.pdf_url || '';
  if (!/^[\w.%~-]+\.assets\/papers\/[\w-]+\.pdf$/.test(path)) return '';
  const first = String(page || '').match(/^\d+/)?.[0];
  return path + (first ? '#page=' + first : '');
}
function externalLink(url, text, cls='button') {
  const safe = safeURL(url);
  return safe ? `<a class="${esc(cls)}" href="${esc(safe)}" target="_blank" rel="noopener noreferrer">${esc(text)} ↗</a>` : '';
}
function inlineMarkdown(text) {
  // Parse only a small safe subset. Raw HTML is always escaped.
  return String(text).split(/(\[[^\]\n]+\]\([^\s)]+\))/g).map(part => {
    const match = part.match(/^\[([^\]]+)\]\(([^\s)]+)\)$/);
    if (match) { const url=safeURL(match[2]); return url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(match[1])}</a>`:esc(match[1]); }
    return esc(part).replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/_([^_\n]+)_/g,'<em>$1</em>').replace(/`([^`]+)`/g,'<code>$1</code>');
  }).join('');
}
function markdown(text) {
  const lines=String(text || '').split(/\r?\n/), out=[];
  let paragraph=[], code=null, list=null;
  const flush = () => { if(paragraph.length){out.push(`<p>${inlineMarkdown(paragraph.join(' '))}</p>`);paragraph=[];} };
  const closeList = () => { if(list){out.push(`</${list}>`);list=null;} };
  for(let i=0;i<lines.length;i++) {
    const line=lines[i];
    if(line.startsWith('```')) {flush();closeList();if(code!==null){out.push(`<pre><code>${esc(code.join('\n'))}</code></pre>`);code=null;}else code=[];continue;}
    if(code!==null){code.push(line);continue;}
    if(!line.trim()){flush();closeList();continue;}
    const heading=line.match(/^(#{1,6})\s+(.+)/), item=line.match(/^\s*(?:([-*+])|\d+[.)])\s+(.+)/);
    if(heading){flush();closeList();const n=Math.min(heading[1].length+1,6);out.push(`<h${n}>${inlineMarkdown(heading[2])}</h${n}>`);}
    else if(item){flush();const tag=item[1]?'ul':'ol';if(list!==tag){closeList();list=tag;out.push(`<${tag}>`);}out.push(`<li>${inlineMarkdown(item[2])}</li>`);}
    else if(line.startsWith('>')){flush();closeList();out.push(`<blockquote>${inlineMarkdown(line.replace(/^>\s?/,''))}</blockquote>`);}
    else if(line.includes('|') && /^\s*\|?\s*:?-{3}/.test(lines[i+1] || '')){
      flush();closeList();const cells=s=>s.trim().replace(/^\||\|$/g,'').split('|').map(x=>inlineMarkdown(x.trim()));
      out.push('<table><thead><tr>'+cells(line).map(x=>`<th>${x}</th>`).join('')+'</tr></thead><tbody>');i++;
      while(lines[i+1]?.includes('|')){i++;out.push('<tr>'+cells(lines[i]).map(x=>`<td>${x}</td>`).join('')+'</tr>');}out.push('</tbody></table>');
    } else {closeList();paragraph.push(line);}
  }
  flush();closeList();if(code!==null)out.push(`<pre><code>${esc(code.join('\n'))}</code></pre>`);
  return out.join('');
}
function filteredSources() {
  const related=state.theme?themeSources(state.theme):null;
  let rows=D.sources.filter(s=>(!state.status || s.status===state.status) && matches(s) && (!related || related.has(s.source_id)) &&
    (!state.yearFrom || Number(s.year)>=Number(state.yearFrom)) && (!state.yearTo || (s.year && Number(s.year)<=Number(state.yearTo))) &&
    (!state.fulltext || (state.fulltext==='yes')===!!(s.has_pdf || s.markdown)) &&
    (!state.design || sourceStudies(s.source_id).some(st=>matches(st.design,state.design))));
  if(state.sort==='title')rows.sort((a,b)=>a.title.localeCompare(b.title));
  if(state.sort.startsWith('year'))rows.sort((a,b)=>a.year&&b.year?(Number(a.year)-Number(b.year))*(state.sort==='year-desc'?-1:1):a.year?-1:b.year?1:0);
  return rows;
}
function filteredStudies() {
  const related=state.theme?themeStudies(state.theme):null;
  const rows=D.studies.filter(s=>(!state.status || studySources(s).some(x=>x.status===state.status)) && (!related || related.has(s.study_id)) &&
    matches([s,byStudy(s.study_id),studySources(s),appraisalFor(s.study_id)]) && (!state.design || matches(s.design,state.design)));
  const year = s=>Math.max(0,...studySources(s).map(x=>Number(x.year)||0));
  if(state.sort.startsWith('year'))rows.sort((a,b)=>year(a)&&year(b)?(year(a)-year(b))*(state.sort==='year-desc'?-1:1):year(a)?-1:year(b)?1:0);
  else if(state.sort==='sample')rows.sort((a,b)=>(b.sample_size ?? -1)-(a.sample_size ?? -1));
  else rows.sort((a,b)=>a.label.localeCompare(b.label));
  return rows;
}
function filteredCandidates() {
  return D.candidates.filter(c=>matches(c) && (!state.candidateStatus || c.status===state.candidateStatus) &&
    (!state.provider || c.provenance.some(p=>p.provider===state.provider)) && (!state.via || c.provenance.some(p=>p.source_id===state.via)) &&
    (!state.stage || c.screening_decisions.some(d=>d.stage===state.stage)) && (!state.reason || c.screening_decisions.some(d=>d.reason_code===state.reason)));
}
function select(id,label,options,value) {
  return `<label>${esc(label)}<select id="${id}" data-filter="${id}" ${state.q&&['scope','focus'].includes(id)?'disabled':''}>${options.map(([key,text])=>`<option value="${esc(key)}" ${value===key?'selected':''}>${esc(text)}</option>`).join('')}</select></label>`;
}
const sourceOptions=[['included','Included papers'],['','All sources'],['unread','Marked unread'],['queued','Queued'],['reading','Reading'],['read','Marked read'],['excluded','Excluded']];
function filters() {
  if(state.source || state.study || state.claim || state.candidate || state.tab==='overview') return '';
  const themeOptions=[['','All themes'],...D.themes.map(t=>[t.theme_id,t.label])];
  const sorts=state.tab==='evidence'?[['title','Study title'],['year-desc','Newest first'],['year-asc','Oldest first'],['sample','Largest recorded sample']]:[['review','Review order'],['title','Title'],['year-desc','Newest first'],['year-asc','Oldest first']];
  let fields='';
  if(['sources','evidence'].includes(state.tab)) {
    fields+=select('status','Collection',sourceOptions,state.status)+select('theme','Theme',themeOptions,state.theme);
    fields+=`<label>Study design contains<input id="design" data-filter="design" value="${esc(state.design)}" placeholder="e.g. randomized"></label>`;
    fields+=select('sort','Sort by',sorts,state.sort==='review'&&state.tab==='evidence'?'title':state.sort);
    if(state.tab==='sources')fields+=`<label>Year from<input id="yearFrom" type="number" data-filter="yearFrom" value="${esc(state.yearFrom)}"></label><label>Year to<input id="yearTo" type="number" data-filter="yearTo" value="${esc(state.yearTo)}"></label>`+select('fulltext','Stored full text',[['','Any availability'],['yes','Available'],['no','Not stored']],state.fulltext);
  } else if(state.tab==='candidates') {
    const unique = values=>[...new Set(values.filter(Boolean))].sort().map(x=>[x,words(x)]);
    fields=select('candidateStatus','Decision',[['','All candidates'],['candidate','Undecided'],['relevant','Relevant, not added'],['added','Added to corpus'],['rejected','Rejected']],state.candidateStatus)+
      select('provider','Provider',[['','All providers'],...unique(D.candidates.flatMap(c=>c.provenance.map(p=>p.provider)))],state.provider)+
      select('via','Found via paper',[['','All origins'],...D.sources.map(s=>[s.source_id,s.citation_label])],state.via)+
      select('stage','Screening stage',[['','All stages'],...unique(D.candidates.flatMap(c=>c.screening_decisions.map(d=>d.stage)))],state.stage)+
      select('reason','Exclusion reason',[['','All reasons'],...unique(D.candidates.flatMap(c=>c.screening_decisions.map(d=>d.reason_code)))],state.reason);
  } else if(state.tab==='graph') {
    fields=select('scope','Network',[['focus','Focused paper and neighbors'],['included','Included papers and neighbors'],['all','Full corpus network']],state.scope)+
      select('focus','Focus paper',D.sources.map(s=>[s.source_id,s.citation_label]),graphFocus())+
      select('relation','Relationship',[['','All relationships'],...countBy(D.links.map(x=>x.type)).map(([x])=>[x,words(x)])],state.relation);
  }
  return `<div class="toolbar"><div class="search-row"><input id="q" type="search" aria-label="Search ${state.tab==='candidates'?'screening records':'literature'}" placeholder="Search titles, authors, findings…" value="${esc(state.q)}"><button data-action="reset">Reset filters</button></div><details class="filter-box" ${innerWidth>600?'open':''}><summary>Filters and sorting${state.theme||state.design||state.provider||state.reason?' · active':''}</summary><div class="filter-grid">${fields}</div>${state.tab==='graph'&&state.q?'<p class="meta filter-note">Search shows matching papers and their neighbors across the corpus. Clear search to use the focus controls.</p>':''}</details></div>`;
}

function overview() {
  const included=D.sources.filter(s=>s.status==='included');
  const completion=(label,n)=>`<div class="completion"><span>${esc(label)}</span><progress max="${Math.max(1,included.length)}" value="${n}" aria-label="${esc(label)}"></progress><span>${n}/${included.length}</span></div>`;
  const cards=D.claims.map(c=>`<article class="card claim-card"><div class="eyebrow">${esc(c.theme_ids.map(id=>themes.get(id)?.label).filter(Boolean).join(' · '))}</div><h3>${claimLink(c.claim_id)}</h3><p class="teaser">${esc(c.scope)}</p>${badge(c.status)}${badge('Recorded confidence: '+c.confidence)}<p class="meta">${c.evidence.filter(e=>e.relationship==='supports').length} supporting · ${c.evidence.filter(e=>e.relationship==='qualifies').length} qualifying · ${c.evidence.filter(e=>e.relationship==='contradicts').length} contradictory findings</p>${claimLink(c.claim_id,'Trace the evidence →')}</article>`).join('');
  return `<div class="section-head"><div><div class="eyebrow">The review at a glance</div><h2 tabindex="-1">What does the evidence suggest?</h2><p class="muted">Recorded conclusions and their evidence. Scope, confidence, and review status come from the research records.</p></div></div>
    <div class="metrics">${metric(included.length,'included papers')}${metric(D.studies.length,'extracted studies')}${metric(D.findings.length,'recorded findings')}${metric(D.themes.length,'themes')}${metric(D.sources.length,'total sources')}</div>
    <div class="grid">${cards || empty('No synthesis claims recorded yet. Explore the papers and evidence table to see the available research.')}</div>
    <div class="section-head"><h2>Coverage and limitations</h2></div><div class="grid"><section class="panel"><h3>Included-paper completeness</h3><div class="completeness">${completion('With a summary',included.filter(s=>s.summary).length)}${completion('With stored full text',included.filter(s=>s.markdown||s.has_pdf).length)}${completion('Full-text reading recorded',included.filter(s=>s.last_read_at&&s.read_depth==='full-text').length)}${completion('With extracted studies',included.filter(s=>sourceStudies(s.source_id).length).length)}</div><p class="meta">Missing reading records mean the reading history is not recorded. They do not establish that a paper was never read.</p></section><section class="panel"><h3>How to interpret this review</h3><p>${D.claims.filter(c=>c.status==='draft').length} of ${D.claims.length} claims are still drafts. Findings retain the authors’ claims, recorded evidence, reviewer interpretation, and source locators separately.</p><p>Sample sizes, measures, and appraisal judgments are shown as recorded; estimates are not pooled across studies.</p>${link('Inspect screening and search coverage →',{...clearDetail,tab:'candidates'})}</section></div>
    <div class="section-head"><h2>Explore by theme</h2></div><ul class="theme-list">${D.themes.map(t=>`<li>${link(t.label,{...clearDetail,tab:'evidence',theme:t.theme_id,page:'1'})}<p>${esc(t.description)}</p></li>`).join('') || '<li>No themes recorded.</li>'}</ul>
    ${D.instructions?`<details class="detail-section"><summary>Review scope and instructions</summary><div class="prose">${markdown(D.instructions)}</div></details>`:''}`;
}
function locators(finding) {
  const linked=studySources(studies.get(finding.study_id));
  return (finding.locators || []).map(loc=>`<div class="locator">${Object.entries(loc).filter(([k,v])=>k!=='passage'&&v).map(([k,v])=>`${esc(words(k))}: ${esc(v)}`).join(' · ')}${loc.passage?`<blockquote>${esc(loc.passage)}</blockquote>`:''}<div>${linked.map(s=>`${sourceLink(s.source_id)} ${safePDF(s,loc.page)?`· <a href="${esc(safePDF(s,loc.page))}" target="_blank" rel="noopener">Open PDF${loc.page?' at locator':''} ↗</a>`:''}`).join(' · ')}</div>${linked.length>1?'<p class="muted">This study links multiple source documents; the recorded locator does not identify which one.</p>':''}</div>`).join('');
}
function findingCard(f, evidenceLink=null) {
  if(!f)return empty('The linked finding is unavailable in this snapshot.');
  return `<article class="finding" id="${esc(f.finding_id)}">${evidenceLink?badge(evidenceLink.relationship,evidenceLink.relationship):''}<h4>${esc(f.outcome)}</h4>${evidenceLink?`<p><strong>Relationship to this claim:</strong> ${esc(evidenceLink.rationale)}</p>`:''}<p><strong>Recorded evidence:</strong> ${esc(f.evidence_statement)}</p><p><strong>Authors’ claim:</strong> ${esc(f.author_claim)}</p><p><strong>Reviewer interpretation:</strong> ${esc(f.reviewer_interpretation)}</p><p class="meta">Certainty: ${esc(f.certainty)}${f.measure?' · Measure: '+esc(f.measure):''}${f.timepoint?' · Timepoint: '+esc(f.timepoint):''}</p>${f.conditions.length?`<p><strong>Conditions:</strong> ${esc(f.conditions.join('; '))}</p>`:''}${locators(f)}<p>${studyLink(f.study_id,'View study design and appraisal →')}</p></article>`;
}
function claimDetail(id) {
  const c=claims.get(id);if(!c)return empty('Claim not found in this snapshot.');
  return `<div class="paper-detail">${link('← Overview',{claim:'',tab:'overview'},'back')}<div class="eyebrow">Synthesis claim · ${esc(c.theme_ids.map(id=>themes.get(id)?.label).filter(Boolean).join(' / '))}</div><h2 tabindex="-1">${esc(c.statement)}</h2>${badge(c.status)}${badge('Recorded confidence: '+c.confidence)}${facts([['Scope',c.scope],['Confidence rationale',c.confidence_rationale]])}<div class="section-head"><h3>Follow the evidence</h3></div>${c.evidence.map(e=>findingCard(findings.get(e.finding_id),e)).join('')}</div>`;
}
function appraisalHTML(a) {
  if(!a)return '<p class="muted">No appraisal recorded for this study.</p>';
  return `<p><strong>${esc(a.overall_judgment)}</strong> · ${esc(a.framework)}${a.framework_version?' ('+esc(a.framework_version)+')':''}</p><p><strong>Applicability:</strong> ${esc(a.applicability)}</p>${a.dimensions.map(d=>`<div class="appraisal"><strong>${esc(d.name)}: ${esc(d.judgment)}</strong><p>${esc(d.rationale)}</p>${d.locators.map(loc=>`<p class="meta">${Object.entries(loc).filter(([,v])=>v).map(([k,v])=>`${esc(k)}: ${esc(v)}`).join(' · ')}</p>`).join('')}</div>`).join('')}<p class="meta">Reviewer: ${esc(a.reviewer)} · ${esc(a.updated_at.slice(0,10))}</p>`;
}
function studyDetail(id) {
  const s=studies.get(id);if(!s)return empty('Study not found in this snapshot.');
  return `<div class="paper-detail">${link('← Evidence table',{...clearDetail,tab:'evidence'},'back')}<h2 tabindex="-1">${esc(s.label)}</h2><p>${studySources(s).map(p=>sourceLink(p.source_id)).join(' · ')}</p>${facts([['Design',s.design],['Population',s.population],['Sample size',s.sample_size],['Setting',s.setting],['Intervention / modality',s.intervention],['Comparator',s.comparator],['Methods',s.methods.join('; ')],['Measures',s.measures.join('; ')]])}<section class="panel"><h3>Appraisal and applicability</h3>${appraisalHTML(appraisalFor(id))}</section><div class="section-head"><h3>Recorded findings</h3></div>${byStudy(id).map(f=>findingCard(f)).join('')||empty('No findings recorded for this study.')}</div>`;
}
function evidenceTable() {
  const rows=filteredStudies(), selected=selectedStudies();
  const comparison=state.comparison&&selected.length>=2?comparisonTable(selected):'';
  return `<div class="section-head"><div><h2 tabindex="-1">Compare the studies</h2><p class="muted">${rows.length} of ${D.studies.length} studies · Each row is a study; a paper can contain more than one.</p></div><div class="actions"><button data-action="csv">Download evidence CSV</button><button data-action="json">Export this view (JSON)</button></div></div>
    <div class="compare-bar"><span>Select 2–4 studies to compare. ${selected.length} selected.</span><div class="actions"><button data-action="compare" ${selected.length<2?'disabled':''}>Compare selected (${selected.length})</button>${selected.length?'<button data-action="clear-compare">Clear selection</button>':''}</div></div>${comparison}
    ${rows.length?`<div class="table-wrap"><table class="evidence-table"><thead><tr><th scope="col">Compare</th><th scope="col">Study / paper</th><th scope="col">Population / sample</th><th scope="col">Design / interview</th><th scope="col">Comparator</th><th scope="col">Outcomes / findings</th><th scope="col">Appraisal / applicability</th></tr></thead><tbody>${pageRows(rows).map(s=>`<tr><td><input type="checkbox" id="select-${esc(s.study_id)}" data-study="${esc(s.study_id)}" aria-label="Compare ${esc(s.label)}" ${selected.includes(s.study_id)?'checked':''} ${selected.length>=4&&!selected.includes(s.study_id)?'disabled':''}></td><td>${studyLink(s.study_id)}<p class="meta">${studySources(s).map(p=>sourceLink(p.source_id)).join('<br>')}</p></td><td>${recorded(s.population)}<p><strong>N = ${nonempty(s.sample_size)?s.sample_size:'not recorded'}</strong></p></td><td><div class="cell-text">${esc(s.design)}<p>${recorded(s.intervention)}</p></div></td><td>${recorded(s.comparator)}</td><td><div class="cell-text">${byStudy(s.study_id).map(f=>`<p>${esc(f.outcome)} ${f.direction?'· '+esc(f.direction):''}</p>`).join('')||'<span class="muted">No findings recorded</span>'}</div>${studyLink(s.study_id,byStudy(s.study_id).length+' findings →')}</td><td><div class="cell-text">${recorded(appraisalFor(s.study_id)?.overall_judgment)}<p>${recorded(appraisalFor(s.study_id)?.applicability)}</p></div></td></tr>`).join('')}</tbody></table></div>${pagination(rows.length)}`:empty('No studies match these filters.')}`;
}
function comparisonTable(ids) {
  const records=ids.map(id=>studies.get(id));
  const fields=[['Design',s=>esc(s.design)],['Population',s=>recorded(s.population)],['Sample size',s=>recorded(s.sample_size)],['Setting',s=>recorded(s.setting)],['Intervention / modality',s=>recorded(s.intervention)],['Comparator',s=>recorded(s.comparator)],['Findings',s=>byStudy(s.study_id).map(f=>`<p><strong>${esc(f.outcome)}:</strong> ${esc(f.evidence_statement)}</p>`).join('')||'No findings recorded'],['Appraisal',s=>recorded(appraisalFor(s.study_id)?.overall_judgment)],['Applicability / limitations',s=>recorded(appraisalFor(s.study_id)?.applicability)]];
  return `<section aria-label="Study comparison"><h3>Side-by-side comparison</h3><p class="muted">These are recorded observations, not pooled estimates. Measures and conditions can differ between studies.</p><div class="table-wrap"><table class="compare-table"><thead><tr><th>Recorded field</th>${records.map(s=>`<th>${studyLink(s.study_id)}</th>`).join('')}</tr></thead><tbody>${fields.map(([label,fn])=>`<tr><th scope="row">${label}</th>${records.map(s=>`<td>${fn(s)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></section>`;
}
function paperList() {
  const rows=filteredSources();
  return `<div class="section-head"><div><h2 tabindex="-1">Papers</h2><p class="muted">${rows.length} of ${D.sources.length} sources · Inclusion and extraction are separate statuses.</p></div><button data-action="bibtex">Download BibTeX</button></div><div class="grid">${pageRows(rows).map(s=>`<article class="card"><div class="eyebrow">${esc(s.citation_label)}</div><h3>${sourceLink(s.source_id,s.title)}</h3><p class="meta">${esc(s.authors)}</p><div>${badge(s.status)}${badge(s.markdown?'Text extracted':s.has_pdf?'PDF stored':'No stored full text')}${s.metadata_incomplete?badge('Incomplete metadata'):''}</div><p class="teaser">${esc(s.summary || 'No summary recorded.')}</p><p class="meta">${sourceStudies(s.source_id).length} extracted studies · ${s.last_read_at?'Reading recorded '+esc(s.last_read_at.slice(0,10)):'Reading history not recorded'}</p>${sourceLink(s.source_id,'Read evidence and paper →')}</article>`).join('')||empty('No papers match these filters.')}</div>${pagination(rows.length)}`;
}
function paperDetail(id) {
  const s=sources.get(id);if(!s)return empty('Paper not found in this snapshot.');
  const ss=sourceStudies(id), findingIds=new Set(ss.flatMap(x=>byStudy(x.study_id).map(f=>f.finding_id)));
  const relatedClaims=D.claims.filter(c=>c.evidence.some(e=>findingIds.has(e.finding_id)));
  const relations=D.links.filter(e=>e.from===id||e.to===id);
  return `<div class="paper-detail">${link('← Papers',{...clearDetail,tab:'sources'},'back')}<div class="eyebrow">${esc(s.citation_label)}</div><h2 tabindex="-1">${esc(s.title)}</h2><p>${esc(s.authors)}</p>${badge(s.status)}${badge(s.markdown?'Text extracted':s.has_pdf?'PDF stored':'No stored full text')}
  <div class="actions">${safePDF(s)?`<a class="button" href="${esc(safePDF(s))}" target="_blank" rel="noopener">Open PDF ↗</a>`:''}${externalLink(s.doi?'https://doi.org/'+s.doi:s.url,'Publisher / source')}<button data-action="citation">Copy citation</button><button data-action="bibtex">Download BibTeX</button><button data-action="share">Copy link</button>${link('Explore connections',{...clearDetail,tab:'graph',focus:id,q:'',scope:'focus'},'button')}</div>
  <section class="prose"><h3>Summary</h3>${s.summary?markdown(s.summary):'<p class="muted">No summary recorded.</p>'}</section>
  <h3>Studies and evidence</h3>${ss.map(st=>`<section class="panel"><h4>${studyLink(st.study_id)}</h4><p>${recorded(st.design)} · N = ${recorded(st.sample_size)}</p>${byStudy(st.study_id).map(f=>findingCard(f)).join('')}<details><summary>Appraisal and applicability</summary>${appraisalHTML(appraisalFor(st.study_id))}</details></section>`).join('')||'<p class="muted">No study extraction recorded for this paper.</p>'}
  <h3>Contributes to synthesis</h3><ul>${relatedClaims.map(c=>`<li>${claimLink(c.claim_id)} ${c.evidence.filter(e=>findingIds.has(e.finding_id)).map(e=>badge(e.relationship,e.relationship)).join(' ')}</li>`).join('')||'<li>No synthesis links recorded.</li>'}</ul>
  <details class="detail-section"><summary>Detailed reviewer notes</summary><div class="prose">${s.notes?markdown(s.notes):'<p>No notes recorded.</p>'}</div></details>
  <details class="detail-section"><summary>Extracted full text${s.markdown?'':' · not stored'}</summary><div class="prose">${s.markdown?markdown(s.markdown):'<p>No extracted full text stored.</p>'}</div></details>
  <details class="detail-section"><summary>Related papers (${relations.length})</summary><ul>${relations.map(e=>`<li>${e.from===id?'This paper '+esc(words(e.type)):'Incoming '+esc(words(e.type))+' from'} ${sourceLink(e.from===id?e.to:e.from)}${e.note?' · '+esc(e.note):''}</li>`).join('')}</ul></details>
  <details class="detail-section"><summary>Bibliography and record details</summary>${facts([['Source ID',s.source_id],['Year',s.year],['DOI',s.doi],['Extraction status',words(s.markdown_status)],['Last recorded reading',s.last_read_at],['Reading depth',s.read_depth]])}<pre>${esc(s.bibtex)}</pre></details></div>`;
}
function searchCoverage() {
  const groups=new Map();
  D.candidates.forEach(c=>c.provenance.forEach(p=>{if(!p.query)return;const key=JSON.stringify([p.provider,p.query]);if(!groups.has(key))groups.set(key,{provider:p.provider,query:p.query,ids:new Set(),seeds:new Set()});const g=groups.get(key);g.ids.add(c.candidate_id);if(p.source_id)g.seeds.add(p.source_id);}));
  const queries=[...groups.values()];
  const queryTable=queries.length?`<h4>Queries preserved in candidate provenance</h4><p class="meta">Counts are distinct candidate records linked to each query, not a provider's total hits. Candidates can appear under multiple queries.</p><div class="table-wrap"><table><thead><tr><th>Provider</th><th>Query</th><th>Candidates</th><th>Seed papers</th></tr></thead><tbody>${queries.map(g=>`<tr><td>${recorded(g.provider)}</td><td>${esc(g.query)}</td><td>${g.ids.size}</td><td>${[...g.seeds].map(id=>sourceLink(id)).join('; ')||'No seed recorded'}</td></tr>`).join('')}</tbody></table></div>`:'<p>No search queries preserved in candidate provenance.</p>';
  const events=D.search_history.length?`<h4>Search and traversal events</h4><p class="meta">These are the events recorded by Dewey. They do not establish that all searches or all provider pages were recorded.</p><div class="table-wrap"><table><thead><tr><th>When / operation</th><th>Query / seed / provider</th><th>Results</th><th>Coverage</th></tr></thead><tbody>${D.search_history.map(h=>`<tr><td>${esc(h.ts||h.timestamp||h.created_at||'Not recorded')}<p>${esc(words(h.action))}</p></td><td>${h.source_id?sourceLink(h.source_id):''}<p>${recorded(h.query)}</p>${h.provider?esc(h.provider):''}</td><td>${facts([['Fetched',h.fetched],['New candidates',h.added]])}</td><td>${h.complete===true?'Marked complete':h.complete===false?'Incomplete':'Completion not recorded'}${h.next_cursor?'<p>Further results available</p>':''}<details><summary>Event record</summary><pre>${esc(JSON.stringify(h,null,2))}</pre></details></td></tr>`).join('')}</tbody></table></div>`:'<p>No search or traversal events recorded.</p>';
  return queryTable+events;
}
function screeningAudit() {
  const rows=filteredCandidates(), counts=countBy(D.candidates.map(c=>c.status));
  const summaries=(title,values)=>`<section class="panel"><h3>${title}</h3><ul class="count-list">${countBy(values).map(([label,n])=>`<li><span>${esc(words(label))}</span><strong>${n}</strong></li>`).join('')||'<li>Not recorded</li>'}</ul></section>`;
  return `<div class="section-head"><div><h2 tabindex="-1">Screening audit</h2><p class="muted">Candidates are possible sources found through searches and citation traversal. They are not evidence until reviewed and added.</p></div><button data-action="json">Export this view (JSON)</button></div><div class="metrics">${counts.map(([label,n])=>metric(n,words(label))).join('')}</div><p class="notice">A completed candidate queue does not establish complete search coverage or finished evidence extraction. “Added” counts candidate records; the corpus can also contain directly imported papers.</p>
  <details class="detail-section"><summary>Search coverage and decision summary</summary><div class="grid">${summaries('Candidate origins (may overlap)',D.candidates.flatMap(c=>[...new Set(c.provenance.map(p=>p.provider||p.method))]))}${summaries('Latest recorded reason',D.candidates.map(c=>c.screening_decisions.at(-1)?.reason_code))}</div><h3>Recorded searches and traversals</h3>${searchCoverage()}</details>
  <div class="section-head"><h3>${rows.length} matching candidates</h3></div><div class="grid">${pageRows(rows).map(c=>`<article class="card"><h3>${link(c.title||'Unresolved citation',{...clearDetail,candidate:c.candidate_id})}</h3><p class="meta">${esc(Array.isArray(c.authors)?c.authors.join('; '):c.authors)} · ${esc(c.year||'Year not recorded')}</p>${badge(c.status)}<p class="teaser">${esc(c.screening_decisions.at(-1)?.rationale||c.rationale||'No screening rationale recorded.')}</p></article>`).join('')||empty('No candidates match these filters.')}</div>${pagination(rows.length)}`;
}
function candidateDetail(id) {
  const c=candidateMap.get(id);if(!c)return empty('Candidate not found in this snapshot.');
  return `<div class="paper-detail">${link('← Screening audit',{...clearDetail,tab:'candidates'},'back')}<h2 tabindex="-1">${esc(c.title||'Unresolved citation')}</h2>${badge(c.status)}<p>${esc(Array.isArray(c.authors)?c.authors.join('; '):c.authors)}</p>${facts([['Year',c.year],['DOI',c.doi]])}${c.added_source_id?sourceLink(c.added_source_id,'Open corpus paper →'):''}${externalLink(c.url,'Source record')}<h3>Screening rationale</h3><p>${recorded(c.rationale)}</p>${c.abstract?`<details class="detail-section"><summary>Abstract</summary><p>${esc(c.abstract)}</p></details>`:''}<h3>Discovery trail</h3>${c.provenance.map(p=>`<section class="panel">${facts([['Method',p.method],['Provider',p.provider],['Query',p.query],['Relationship',p.relation],['Discovered',p.discovered_at],['Raw citation',p.raw_citation]])}${p.source_id?`<p>Found via ${sourceLink(p.source_id)}</p>`:''}</section>`).join('')}<h3>Screening decisions</h3>${c.screening_decisions.map(d=>`<section class="panel">${facts([['Decision',d.decision],['Stage',d.stage],['Reason',d.reason_code],['Rationale',d.rationale],['Reviewer',d.reviewer],['Protocol version',d.protocol_version],['Decided',d.decided_at],['Criteria',searchText(d.criteria)]])}</section>`).join('')||'<p>No decisions recorded.</p>'}<details><summary>Candidate identifier</summary><code>${esc(c.candidate_id)}</code></details></div>`;
}
function graphFocus() {return sources.has(state.focus)?state.focus:(D.sources.find(s=>s.status==='included')||D.sources[0])?.source_id||'';}
function graphData() {
  const eligible=D.links.filter(e=>(!state.relation||e.type===state.relation)&&sources.has(e.from)&&sources.has(e.to));
  let ids=new Set(D.sources.map(s=>s.source_id));
  if(state.q) {
    ids=new Set(D.sources.filter(s=>matches([s.title,s.authors,s.citation_label,s.year,s.source_id])).map(s=>s.source_id));
    const seeds=new Set(ids);eligible.forEach(e=>{if(seeds.has(e.from)||seeds.has(e.to)){ids.add(e.from);ids.add(e.to);}});
  } else if(state.scope!=='all') {
    const seeds=new Set(state.scope==='included'?D.sources.filter(s=>s.status==='included').map(s=>s.source_id):[graphFocus()]);ids=new Set(seeds);
    eligible.forEach(e=>{if(seeds.has(e.from)||seeds.has(e.to)){ids.add(e.from);ids.add(e.to);}});
  }
  return {nodes:D.sources.filter(s=>ids.has(s.source_id)).sort((a,b)=>(Number(a.year)||9999)-(Number(b.year)||9999)||a.title.localeCompare(b.title)),edges:eligible.filter(e=>ids.has(e.from)&&ids.has(e.to))};
}
function graphView() {
  const {nodes,edges}=graphData();
  if(!nodes.length)return '<h2>Citation map</h2>'+empty('No paper matches this search. Try an author surname or title.');
  const width=1050, step=66, height=Math.max(420,nodes.length*step+50), positions=new Map(nodes.map((s,i)=>[s.source_id,{x:40+(i%3)*330,y:45+i*step}]));
  const paths=edges.map(e=>{const a=positions.get(e.from),b=positions.get(e.to),type=e.type==='cites'?'cites':e.type==='version_of'?'version_of':'other';return `<path class="graph-edge ${type}" d="M ${a.x+302} ${a.y-7} C ${width-15} ${a.y-7},${width-15} ${b.y+7},${b.x+304} ${b.y+7}" marker-end="url(#arrow-${type})"><title>${esc(sourceLabel(e.from)+' '+words(e.type)+' '+sourceLabel(e.to))}</title></path>`;}).join('');
  const circles=nodes.map(s=>{const p=positions.get(s.source_id);return `<a class="graph-node ${s.source_id===graphFocus()?'focus':''}" href="${esc(route({...clearDetail,tab:'sources',source:s.source_id}))}" aria-label="${esc(s.title)}"><title>${esc(s.title+' · '+s.authors)}</title><rect x="${p.x-9}" y="${p.y-20}" width="310" height="42" rx="8" fill="${s.source_id===graphFocus()?'#dbe8cb':'#fff'}"/><circle cx="${p.x}" cy="${p.y}" r="5"/><text x="${p.x+13}" y="${p.y+5}">${esc(s.citation_label.length>36?s.citation_label.slice(0,35)+'…':s.citation_label)}</text></a>`;}).join('');
  return `<div class="section-head"><div><h2 tabindex="-1">Chronological citation network</h2><p class="muted">${nodes.length} papers · ${edges.filter(e=>e.type==='cites').length} citation links · ${edges.filter(e=>e.type!=='cites').length} other relationships</p></div><div class="actions"><button data-action="zoom-out" aria-label="Zoom out">−</button><span>${Math.round(Number(state.zoom)*100)}%</span><button data-action="zoom-in" aria-label="Zoom in">+</button></div></div><p class="graph-legend"><span>Green solid → cites</span><span>Purple dashed → version of</span><span>Gray dotted → other relationship</span></p><p class="meta">Arrows run from the citing paper to the cited paper. Other arrows follow the recorded relationship. Papers run from older to newer; scroll within the map. Search matches titles and authors and shows their immediate neighbors.</p><div class="graph-pane" tabindex="0" aria-label="Scrollable citation map"><svg role="img" aria-label="Paper relationships, ordered by year" width="${width*Number(state.zoom)}" height="${height*Number(state.zoom)}" viewBox="0 0 ${width} ${height}"><defs>${['cites','version_of','other'].map((type,i)=>`<marker id="arrow-${type}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="${['#427353','#8462a6','#777'][i]}"/></marker>`).join('')}</defs>${paths}${circles}</svg></div><details class="detail-section"><summary>Accessible relationship list (${edges.length})</summary><ul>${edges.map(e=>`<li>${sourceLink(e.from)} → ${esc(words(e.type))} → ${sourceLink(e.to)}${e.note?' · '+esc(e.note):''}</li>`).join('')||'<li>No recorded connections in this view.</li>'}</ul></details>`;
}
function render(preserveFocus=false) {
  const active=document.activeElement, focusId=preserveFocus?active?.id:null, selection=focusId&&active?.selectionStart;
  state=readState();
  document.querySelectorAll('[data-tab]').forEach(a=>{a.setAttribute('aria-current',a.dataset.tab===state.tab?'page':'false');a.classList.toggle('active',a.dataset.tab===state.tab);});
  $('controls').innerHTML=filters();
  $('content').innerHTML=state.source?paperDetail(state.source):state.study?studyDetail(state.study):state.claim?claimDetail(state.claim):state.candidate?candidateDetail(state.candidate):({overview,evidence:evidenceTable,sources:paperList,candidates:screeningAudit,graph:graphView})[state.tab]();
  if(focusId&&$(focusId)){ $(focusId).focus();try{$(focusId).setSelectionRange(selection,selection);}catch{} }
  $('announcement').textContent=state.q?'Search results updated.':document.querySelector('#content h2')?.textContent||'View updated.';
}
function download(content,name,type) {
  const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text);$('announcement').textContent='Copied to clipboard.'; }
  catch {const area=document.createElement('textarea');area.value=text;document.body.append(area);area.select();const ok=document.execCommand('copy');area.remove();$('announcement').textContent=ok?'Copied to clipboard.':'Copy unavailable in this browser. Use the address bar or bibliography record.';}
}
function exportRows() {return state.tab==='candidates'?filteredCandidates():state.tab==='evidence'?filteredStudies():state.source?[sources.get(state.source)].filter(Boolean):filteredSources();}
function showSource(id) {navigate({...clearDetail,tab:'sources',source:id});}
window.showSource=showSource;
document.addEventListener('input',e=>{
  if(e.target.id==='q'){clearTimeout(searchTimer);searchTimer=setTimeout(()=>navigate({q:e.target.value,page:'1'},true,true),180);}
});
document.addEventListener('change',e=>{
  if(e.target.dataset.filter){clearTimeout(searchTimer);navigate({[e.target.dataset.filter]:e.target.value,page:'1'});}
  if(e.target.dataset.study){const ids=selectedStudies().filter(id=>id!==e.target.dataset.study);if(e.target.checked&&ids.length<4)ids.push(e.target.dataset.study);navigate({compare:ids.join(','),comparison:ids.length<2?'':state.comparison},true,true);}
});
document.addEventListener('click',e=>{
  if(e.target.closest('.skip')){e.preventDefault();$('main').focus();return;}
  const nav=e.target.closest('[data-tab]');if(nav)clearTimeout(searchTimer);
  const button=e.target.closest('[data-action]');if(!button)return;
  const action=button.dataset.action;
  if(action==='reset')navigate({...defaults,tab:state.tab,...clearDetail});
  if(action==='compare')navigate({comparison:'1'});
  if(action==='clear-compare')navigate({compare:'',comparison:''});
  if(action==='share')copy(location.href);
  if(action==='citation'){const s=sources.get(state.source);if(s)copy(`${s.authors} (${s.year||'n.d.'}). ${s.title}.${s.doi?' https://doi.org/'+s.doi:s.url?' '+s.url:''}`);}
  if(action==='bibtex')download(exportRows().map(s=>s.bibtex).filter(Boolean).join('\n'),'papers.bib','application/x-bibtex');
  if(action==='json')download(JSON.stringify(exportRows(),null,2),'review-records.json','application/json');
  if(action==='csv'){
    const columns=['Study','Sources','Design','Population','Sample size','Setting','Intervention','Comparator','Findings','Appraisal','Applicability'];
    const cell=v=>'"'+String(v??'').replace(/^[=+@\-\t\r]/,"'$&").replace(/"/g,'""')+'"';
    const rows=filteredStudies().map(s=>[s.label,studySources(s).map(p=>p.citation_label).join('; '),s.design,s.population,s.sample_size,s.setting,s.intervention,s.comparator,byStudy(s.study_id).map(f=>f.evidence_statement).join('; '),appraisalFor(s.study_id)?.overall_judgment,appraisalFor(s.study_id)?.applicability]);
    download([columns,...rows].map(r=>r.map(cell).join(',')).join('\r\n'),'evidence.csv','text/csv;charset=utf-8');
  }
  if(action.startsWith('zoom-'))navigate({zoom:String(Math.min(2,Math.max(.5,Number(state.zoom)+(action==='zoom-in'?.25:-.25))))},true);
});
window.addEventListener('hashchange',()=>{
  clearTimeout(searchTimer);
  const previous=state;
  render(true);
  if(['tab','source','study','claim','candidate','page'].some(key=>previous[key]!==state[key])) {
    window.scrollTo(0,0);
    document.querySelector('#content h2')?.focus({preventScroll:true});
  }
});
$('question').textContent=D.research_question||D.topic||'';
$('generated').textContent='Snapshot generated '+D.generated_at.slice(0,10);
if(safeURL(D.repository_url)){const a=$('repository');a.href=safeURL(D.repository_url);a.classList.remove('hidden');}
render();
