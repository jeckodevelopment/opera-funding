const $ = id => document.getElementById(id);
const PAGE_SIZE = 12;
const DATA_ORIGIN = "https://raw.githubusercontent.com/jeckodevelopment/opera-funding/main/data/";
const FALLBACK_ORIGIN = "data/";
let all=[], visibleCount=PAGE_SIZE,loadSequence=0;
const WATCHLIST_KEY="opera-funding-watchlist-v1";
function readWatchlist(){
 try{
  if(typeof localStorage==="undefined")return new Set();
  const raw=JSON.parse(localStorage.getItem(WATCHLIST_KEY)||"[]");
  return new Set(Array.isArray(raw)?raw.filter(x=>typeof x==="string"&&x.length<2500):[]);
 }catch{return new Set();}
}
const WORKFLOW_KEY="opera-funding-follow-workflow-v1";
const WORKFLOW_PHASES=["Da valutare","Interessante","Candidatura in preparazione","Presentata","Non pertinente"];
function cleanWorkflow(record){
 const entry=record&&typeof record==="object"?record:{};
 return {
  phase:WORKFLOW_PHASES.includes(entry.phase)?entry.phase:WORKFLOW_PHASES[0],
  owner:typeof entry.owner==="string"?entry.owner.slice(0,120):"",
  next_step:typeof entry.next_step==="string"?entry.next_step.slice(0,300):"",
  due:validLocalDate(entry.due)?entry.due:"",
  notes:typeof entry.notes==="string"?entry.notes.slice(0,3000):""
 };
}
function validLocalDate(value){return typeof value==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value+"T12:00:00Z"));}
function readWorkflow(){
 try{
  const raw=JSON.parse(localStorage.getItem(WORKFLOW_KEY)||"{}");
  if(!raw||typeof raw!=="object"||Array.isArray(raw))return Object.create(null);
  const result=Object.create(null);
  for(const [id,value] of Object.entries(raw)){
   if(typeof id==="string"&&id.length<2500)result[id]=cleanWorkflow(value);
  }
  return result;
 }catch{return Object.create(null);}
}
let followed=readWatchlist();
let workflow=readWorkflow();
function workflowRecord(o){return workflow[o.id]||cleanWorkflow({});}
function persistWorkflow(){
 try{
  if(typeof localStorage==="undefined")return false;
  localStorage.setItem(WATCHLIST_KEY,JSON.stringify([...followed]));
  localStorage.setItem(WORKFLOW_KEY,JSON.stringify(workflow));
  return true;
 }catch{return false;}
}
function isFollowed(o){return followed.has(o.id);}
function saveWorkflow(o,record){
 followed.add(o.id);
 workflow[o.id]=cleanWorkflow(record);
 const persisted=persistWorkflow();
 updateStateCounts();
 render();
 return persisted;
}
function toggleFollowed(o){
 if(isFollowed(o)){
  followed.delete(o.id);
  delete workflow[o.id];
 }else followed.add(o.id);
 persistWorkflow();
 updateStateCounts();
 render();
}
function workflowForm(o){
 const record=workflowRecord(o),section=el("section",undefined,"dialog-section workflow-section");
 section.append(el("h3","Gestione personale dell'opportunità"));
 section.append(el("p","Stato, responsabile, note e prossima attività restano soltanto in questo browser: non sono visibili agli altri volontari.","workflow-disclaimer"));
 const form=el("form",undefined,"workflow-form");
 function field(label,control){
  const wrap=el("label",undefined,"workflow-field");
  wrap.append(el("span",label),control);
  form.append(wrap);
  return control;
 }
 const stage=el("select");stage.name="phase";
 for(const phase of WORKFLOW_PHASES){const option=el("option",phase);option.value=phase;stage.append(option);}
 stage.value=record.phase;field("Stato di lavorazione",stage);
 const owner=el("input");owner.type="text";owner.maxLength=120;owner.value=record.owner;
 owner.placeholder="Responsabile (facoltativo)";field("Responsabile",owner);
 const step=el("input");step.type="text";step.maxLength=300;step.value=record.next_step;
 step.placeholder="Prossima attività (facoltativa)";field("Prossima attività",step);
 const due=el("input");due.type="date";due.value=record.due;field("Scadenza interna",due);
 const notes=el("textarea");notes.maxLength=3000;notes.rows=4;notes.value=record.notes;
 notes.placeholder="Appunti riservati su questo dispositivo";field("Note operative",notes);
 const save=el("button","Salva valutazione personale","workflow-save");save.type="submit";
 const feedback=el("span",undefined,"workflow-feedback");feedback.setAttribute("role","status");
 form.append(save,feedback);
 form.addEventListener("submit",event=>{
  event.preventDefault();
  const persistent=saveWorkflow(o,{phase:stage.value,owner:owner.value,next_step:step.value,due:due.value,notes:notes.value});
  feedback.textContent=persistent?"Salvato su questo browser.":"Salvataggio non persistente: spazio del browser non disponibile.";
 });
 section.append(form);
 return section;
}
function followButton(o){
 const button=el("button",isFollowed(o)?"✓ Da seguire":"Segui opportunità","follow-button"+(isFollowed(o)?" selected":""));
 button.type="button";
 button.setAttribute("aria-pressed",String(isFollowed(o)));
 button.addEventListener("click",()=>{
  toggleFollowed(o);
  button.textContent=isFollowed(o)?"✓ Da seguire":"Segui opportunità";
  button.classList.toggle("selected",isFollowed(o));
  button.setAttribute("aria-pressed",String(isFollowed(o)));
 });
 return button;
}

const el=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;};
const safeUrl=value=>{try{const u=new URL(value);return u.protocol==="https:"?u.href:null;}catch{return null;}};
function addLink(parent,label,url,className){
 const href=safeUrl(url);if(!href)return;
 const a=el("a",label,className);a.href=href;a.target="_blank";a.rel="noopener noreferrer";parent.append(a);
}
async function fetchDataset(origin,signal){
 // A unique token prevents the GitHub CDN from returning an older catalog.
 const revision="v="+Date.now();
 const opts={cache:"no-store",credentials:"omit",signal};
 const [opResponse,scanResponse]=await Promise.all([
  fetch(origin+"opportunities.json?"+revision,opts),
  fetch(origin+"scan-status.json?"+revision,opts)
 ]);
 if(!opResponse.ok||!scanResponse.ok)throw Error("Could not load funding data");
 const [opportunities,status]=await Promise.all([opResponse.json(),scanResponse.json()]);
 if(!Array.isArray(opportunities)||!status||!Array.isArray(status.sources))throw Error("Invalid funding data");
 return {opportunities,status};
}
// Do not leave the dashboard indefinitely in "Caricamento" if GitHub Raw
// stalls or is blocked by a browser/network extension.
async function fetchWithDeadline(origin,timeoutMs=6500){
 const aborter=typeof AbortController!=="undefined"?new AbortController():null;
 let timeoutId;
 try{
  return await Promise.race([
   fetchDataset(origin,aborter?.signal),
   new Promise((_,reject)=>{timeoutId=setTimeout(()=>{
    aborter?.abort();
    reject(new Error("Funding data request timed out"));
   },timeoutMs);})
  ]);
 }finally{clearTimeout(timeoutId);}
}
async function loadDataset(){
 try{return {...await fetchWithDeadline(DATA_ORIGIN),origin:"github"};}
 catch(e){return {...await fetchWithDeadline(FALLBACK_ORIGIN),origin:"local"};}
}
const validDate=value=>typeof value==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value+"T12:00:00Z"));
const today=()=>new Date().toISOString().slice(0,10);
const daysLeft=date=>Math.ceil((Date.parse(date+"T00:00:00Z")-Date.parse(today()+"T00:00:00Z"))/86400000);
function state(o){
 if(o.opportunity_type==="altro avviso")return "altro contenuto";
 const end=o.deadline,start=o.opening_date;
 if((validDate(end)&&end<today())||o.closure_confirmed||(["chiuso","scaduto"].includes(o.status)&&!o.reopened_confirmed))return "chiuso";
 if(validDate(start)&&start>today()&&o.opening_evidence)return "in arrivo";
 const window=(validDate(end)&&end>=today())||(o.rolling_confirmed===true&&!!o.rolling_evidence);
 if(o.source_open_confirmed===true&&o.link_status==="raggiungibile"&&window&&(!validDate(start)||start<=today()))return "aperto";
 if(!["finanziamento potenziale","call progettuale da verificare","non classificato"].includes(o.opportunity_type))return "altro contenuto";
 return "non verificato";
}
function dateLabel(value){
 if(!validDate(value))return "Scadenza non indicata";
 const [y,m,d]=value.split("-");return "Scade il "+d+"/"+m+"/"+y;
}
function score(o){return Math.max(0,Math.min(100,Number(o.relevance)||0));}
function adequacyLevel(o){
 if(Number.isInteger(o.adequacy_level))return Math.max(0,Math.min(3,o.adequacy_level));
 const grade=assessmentLabel(o);
 if(grade==="INFORMATIVA")return 0;
 let level=grade==="ALTA AFFINITÀ"?3:grade==="MEDIA AFFINITÀ"?2:1;
 if(!o.assessment_source && !o.assessment_evidence_source)level=Math.min(level,2);
 if(!o.funded_activities_excerpt || !o.beneficiaries_excerpt)level=Math.min(level,2);
 const terms=String(o.beneficiaries_excerpt||"")+" "+String(o.requirements_excerpt||"");
 if(/(?:solo|esclusivamente|only)\\s+(?:persone fisiche|singoli artisti|individual artists|individual applicants|imprese|companies|businesses)/i.test(terms))level=1;
 return level;
}
function adequacyLabel(o){return ["INFORMATIVA","BASSA","MEDIA","ALTA"][adequacyLevel(o)];}
function adequacyPercent(o){
 const level=adequacyLevel(o);
 if(level===0)return 0;
 const value=Number(o.adequacy_score ?? o.relevance);
 const fraction=Number.isFinite(value)?Math.max(0,Math.min(100,value))/100:0.5;
 const bands={1:[1,39],2:[40,74],3:[75,100]};
 const [minimum,maximum]=bands[level];
 return Math.round(minimum+(maximum-minimum)*fraction);
}
function affinityRank(o){return adequacyPercent(o);}
function makeAdequacy(o){
 const percent=adequacyPercent(o);
 const surface=el("div",undefined,"adequacy");
 const heading=el("div",undefined,"adequacy-heading");
 heading.append(el("span","Adeguatezza per Opera+","adequacy-label"),el("strong",percent+"%","adequacy-value"));
 const track=el("div",undefined,"adequacy-track");
 track.style.setProperty("--adequacy-percent",percent+"%");
 track.setAttribute("role","progressbar");
 track.setAttribute("aria-label","Adeguatezza per Opera+");
 track.setAttribute("aria-valuemin","0");
 track.setAttribute("aria-valuemax","100");
 track.setAttribute("aria-valuenow",String(percent));
 const fill=el("div",undefined,"adequacy-fill");
 fill.style.width=percent+"%";
 track.append(fill);
 surface.append(heading,track);
 return surface;
}
function groupOrder(o){return {aperto:0,"in arrivo":1,"non verificato":2,chiuso:3,"altro contenuto":4}[state(o)];}
function sortRows(rows,order){
 const difference=(a,b)=>affinityRank(b)-affinityRank(a);
 rows.sort((a,b)=>{
  const group=groupOrder(a)-groupOrder(b);if(group)return group;
  if(order==="score")return difference(a,b)||String(a.deadline||"9999").localeCompare(String(b.deadline||"9999"));
  if(state(a)==="chiuso")return String(b.deadline||"0000").localeCompare(String(a.deadline||"0000"))||difference(a,b);
  return String(a.deadline||"9999").localeCompare(String(b.deadline||"9999"))||difference(a,b);
 });
 return rows;
}
function filteredRows(){
 const term=$("search").value.trim().toLocaleLowerCase("it"),stateFilter=$("status").value,issuer=$("issuer").value,kind=$("kind").value,minimum=Number($("level").value);
 return sortRows(all.filter(o=>{
  const actual=state(o);
  if(stateFilter==="followed"&&!isFollowed(o))return false;
  if(stateFilter&&stateFilter!=="followed"&&actual!==stateFilter)return false;
  if(kind==="funding"&&!["finanziamento potenziale","call progettuale da verificare"].includes(o.opportunity_type))return false;
  if(kind&&kind!=="funding"&&kind!==o.opportunity_type)return false;
  if(issuer&&issuer!==o.issuer)return false;
  if(affinityRank(o)<minimum)return false;
  if(!term)return true;
  return [o.title,o.issuer,o.beneficiaries_excerpt,...(o.themes||[])].filter(Boolean).join(" ").toLocaleLowerCase("it").includes(term);
 }),$("sort").value);
}
function opportunitySummary(o){
 if(o.summary&&typeof o.summary==="string")return o.summary;
 const themes=(o.themes||[]).slice(0,2);
 if(themes.length){
  const kind=o.opportunity_type==="finanziamento potenziale"?"Finanziamento":"Call progettuale";
  return kind+" con temi legati a "+themes.join(" e ")+". Consulta la scheda ufficiale per destinatari e condizioni.";
 }
 if(o.opportunity_type==="finanziamento potenziale")return "Opportunità di sostegno economico: requisiti, destinatari e modalità di partecipazione sono nella scheda ufficiale.";
 if(o.opportunity_type==="call progettuale da verificare")return "Invito a presentare progetti. Consulta la fonte per approfondire obiettivi, finanziamento e destinatari.";
 return "Avviso pubblicato dall’ente promotore. Consulta la fonte originale per conoscere il contenuto.";
}
function statusLabel(s){return {aperto:"APERTA","in arrivo":"IN ARRIVO","non verificato":"APERTURA DA VERIFICARE",chiuso:"SCADUTA","altro contenuto":"ALTRO CONTENUTO"}[s];}
function makeCalendar(o){
 const date=o.deadline;const calendar=el("div",undefined,"calendar"+(!validDate(date)?" unknown-date":""));
 calendar.setAttribute("role","img");
 calendar.setAttribute("aria-label",dateLabel(date));
 if(!validDate(date)){calendar.append(el("span","DATA","calendar-month"),el("span","—","calendar-day"),el("span","Non indicata","calendar-year"));return calendar;}
 const [year,month,day]=date.split("-");
 const monthName=["GEN","FEB","MAR","APR","MAG","GIU","LUG","AGO","SET","OTT","NOV","DIC"][Number(month)-1];
 if(state(o)==="aperto"&&daysLeft(date)<=10)calendar.classList.add("urgent");
 calendar.append(el("span",monthName,"calendar-month"),el("span",String(Number(day)),"calendar-day"),el("span",year,"calendar-year"));
 return calendar;
}
function dialogField(parent,label,value){
 if(!value)return;
 const field=el("div",undefined,"dialog-field");
 field.append(el("dt",label),el("dd",String(value)));
 parent.append(field);
}
// Display evidence without affecting discovery, status, sorting or filtering.
function reviewSignals(o){
 const checks=Array.isArray(o.eligibility_checks)?o.eligibility_checks.filter(x=>typeof x==="string"&&x.trim()):[];
 const missing=[];
 if(!o.beneficiaries_excerpt)missing.push("Beneficiari ammessi non documentati");
 if(!o.amount)missing.push("Importo o dotazione non indicati");
 if(!validDate(o.deadline)&&o.rolling_confirmed!==true)missing.push("Scadenza o apertura a sportello da verificare");
 if(o.link_status!=="raggiungibile")missing.push("Collegamento alla fonte da verificare");
 return {checks,missing,explanation:typeof o.score_explanation==="string"?o.score_explanation.trim():"",
  confidence:typeof o.score_confidence==="string"?o.score_confidence.trim():"",
  eligibility:typeof o.eligibility==="string"?o.eligibility.trim():"da verificare"};
}
function uniqueStatements(values){
 const seen=new Set(),result=[];
 for(const entry of values){
  if(typeof entry!=="string"||!entry.trim())continue;
  const value=entry.trim(),key=value.toLocaleLowerCase("it").replace(/\\s+/g," ");
  if(!seen.has(key)){seen.add(key);result.push(value);}
 }
 return result;
}
function detailDisclosure(title,body,extraClass=""){
 const details=el("details",undefined,"detail-disclosure "+extraClass);
 details.append(el("summary",title),body);
 return details;
}
function evidenceSection(o){
 const review=reviewSignals(o),section=el("section",undefined,"dialog-section evidence-review");
 section.append(el("h3","Adeguatezza per Opera+"),makeAdequacy(o));
 const reasons=uniqueStatements([o.adequacy_reason,o.assessment_reason,review.explanation]);
 if(reasons.length){
  section.append(el("h4","Perché questo giudizio"));
  section.append(el("p",reasons[0],"assessment-rationale"));
 }
 const notes=uniqueStatements([
  ...reasons.slice(1),
  ...(Array.isArray(o.assessment_gaps)?o.assessment_gaps:[]),
  ...(Array.isArray(o.assessment_missing_fields)?o.assessment_missing_fields:[]),
  ...review.checks,...review.missing
 ]).filter(note=>!reasons[0]||note!==reasons[0]);
 if(notes.length){
  const noteBox=el("div",undefined,"assessment-notes");
  noteBox.append(el("h4","Criticità e verifiche"));
  const list=el("ul");
  for(const note of notes)list.append(el("li",note));
  noteBox.append(list);section.append(noteBox);
 }
 const technical=el("dl",undefined,"review-facts");
 dialogField(technical,"Ammissibilità",review.eligibility);
 dialogField(technical,"Copertura documentale",o.assessment_review_status||"Non determinata");
 dialogField(technical,"Affidabilità",o.assessment_confidence||review.confidence||"Non documentata");
 dialogField(technical,"Metodo",o.assessment_method||"Valutazione preliminare");
 dialogField(technical,"Evidenze utilizzate",o.assessment_basis||o.score_explanation_basis||"Informazioni preliminari");
 if(o.assessment_checked_at)dialogField(technical,"Ultima verifica",String(o.assessment_checked_at).slice(0,10));
 section.append(detailDisclosure("Come è stata calcolata l’adeguatezza?",technical,"assessment-method"));
 section.append(el("p","La valutazione è indicativa: non certifica l’ammissibilità né garantisce il contributo.","assessment-disclaimer"));
 return section;
}
// Evaluation handout is built with text nodes and HTTPS-only links to avoid
// interpreting text supplied by external funding sites as HTML.
function evaluationData(o,issued=new Date()){
 const review=reviewSignals(o),links=[];
 const seen=new Set();
 const candidates=[
  ["Scheda del bando",o.link_status==="non disponibile"?o.source_url:(o.resolved_url||o.url)],
  ["Fonte della scadenza",o.deadline_source],
  ["Fonte dei beneficiari",o.beneficiaries_source],
  ["Fonte dell'importo",o.amount_source],
  ["Fonte della procedura a sportello",o.rolling_guidance_source],
  ...(Array.isArray(o.documents)?o.documents.map(d=>[d.label||"Documento",d.url]):[])
 ];
 for(const [label,url] of candidates){
  const href=safeUrl(url);
  if(!href||seen.has(href))continue;
  seen.add(href);links.push({label:String(label),href});
 }
 return {
  title:String(o.title||"Opportunità senza titolo"),
  issuer:String(o.issuer||"Ente non indicato"),
  status:statusLabel(state(o)),
  date:issued.toLocaleDateString("it-IT",{year:"numeric",month:"long",day:"numeric"}),
  deadline:validDate(o.deadline)?dateLabel(o.deadline).replace("Scade il ",""):"Non indicata",
  opening:validDate(o.opening_date)?dateLabel(o.opening_date).replace("Scade il ",""):"Non indicata",
  amount:String(o.amount||"Non indicato"),
  amountKind:String(o.amount_kind||"Da verificare"),
  type:String(o.application_type||o.opportunity_type||"Non indicata"),
  fit:adequacyPercent(o)+"%",
  editorialAssessment:adequacyPercent(o)+"%",
  editorialReason:String(o.assessment_reason||"Classificazione tematica preliminare; apertura e ammissibilità richiedono evidenze."),
  confidence:o.assessment_confidence||review.confidence||"Non documentata",
  basis:String(o.assessment_basis||o.score_explanation_basis||"Titolo e informazioni preliminari"),
  reasoning:review.explanation||"Motivazione non disponibile",
  eligibility:review.eligibility,
  beneficiaries:String(o.beneficiaries_excerpt||"Non documentati"),
  rolling:String(o.rolling_guidance||""),
  summary:opportunitySummary(o),
  checks:review.checks,
  missing:review.missing,
  ideas:Array.isArray(o.project_ideas)?o.project_ideas.slice(0,4).filter(x=>typeof x==="string"):[],
  links
 };
}
function appendReportList(parent,title,values){
 if(!values.length)return;
 const section=el("section",undefined,"print-section");
 section.append(el("h2",title));
 const ul=el("ul");
 for(const value of values)ul.append(el("li",value));
 section.append(ul);parent.append(section);
}
function addReportFact(parent,label,value){
 const item=el("div",undefined,"print-fact");
 item.append(el("dt",label),el("dd",value));
 parent.append(item);
}
function prepareEvaluationSheet(o){
 const d=evaluationData(o),sheet=$("print-sheet");
 sheet.replaceChildren();
 const heading=el("header",undefined,"print-head");
 const logo=el("img");logo.src="assets/operaplus-logo.png";logo.alt="Opera+";logo.width=133;
 heading.append(logo,el("p","FUNDING · SCHEDA DI VALUTAZIONE","print-kicker"));
 sheet.append(heading);
 sheet.append(el("h1",d.title));
 const meta=el("p",d.issuer+" · "+d.status+" · Scheda generata il "+d.date,"print-meta");
 sheet.append(meta);
 const facts=el("dl",undefined,"print-facts");
 for(const [label,value] of [
  ["Scadenza",d.deadline],["Apertura candidature",d.opening],
  ["Contributo / dotazione",d.amount],["Natura dell'importo",d.amountKind],
  ["Tipologia",d.type],["Adeguatezza per Opera+",d.editorialAssessment],
  ["Ammissibilità",d.eligibility],["Affidabilità analisi",d.confidence]
 ])addReportFact(facts,label,value);
 sheet.append(facts);
 const summary=el("section",undefined,"print-section");
 summary.append(el("h2","Sintesi dell'opportunità"),el("p",d.summary));
 sheet.append(summary);
 const assessment=el("section",undefined,"print-section");
 assessment.append(el("h2","Motivazione dell'adeguatezza"),el("p",d.editorialReason),el("p",d.reasoning),
  el("p","Elementi utilizzati: "+d.basis,"print-muted"));
 sheet.append(assessment);
 const beneficiaries=el("section",undefined,"print-section");
 beneficiaries.append(el("h2","Destinatari / beneficiari"),el("p",d.beneficiaries));
 sheet.append(beneficiaries);
 if(d.rolling){
  const rolling=el("section",undefined,"print-section");
  rolling.append(el("h2","Possibile procedura a sportello"),el("p",d.rolling));
  sheet.append(rolling);
 }
 appendReportList(sheet,"Verifiche prima della decisione",d.checks);
 appendReportList(sheet,"Informazioni mancanti o da approfondire",d.missing);
 appendReportList(sheet,"Spunti progettuali",d.ideas);
 if(d.links.length){
  const sources=el("section",undefined,"print-section print-sources");
  sources.append(el("h2","Fonti e documentazione"));
  const ol=el("ol");
  for(const link of d.links){
   const li=el("li");
   li.append(el("span",link.label+" — "));
   const a=el("a",link.href);a.href=link.href;a.rel="noopener noreferrer";
   li.append(a);ol.append(li);
  }
  sources.append(ol);sheet.append(sources);
 }
 const disclaimer=el("footer",undefined,"print-disclaimer");
 disclaimer.append(el("strong","Valutazione preliminare, non decisione di candidatura."),
  el("p","Le informazioni provengono dal catalogo Opera+ Funding e possono essere incomplete o superate. L'adeguatezza progettuale non conferma ammissibilità né probabilità di finanziamento. Verificare sempre i documenti ufficiali prima di candidarsi."));
 sheet.append(disclaimer);
 return sheet;
}
function printEvaluation(o){
 const sheet=prepareEvaluationSheet(o);
 // Keep print content separate from the interactive dialog and dashboard.

 sheet.hidden=false;
 window.print();
}

// Static-hosting-friendly deep links: the same index.html serves every page.
// Numeric public_id is permanent; internal id remains the source URL for
// scanner identity, legacy shared links and browser-only saved opportunities.
function opportunityUrl(row,base=window.location.href){
 const target=new URL(base);
 const id=(row&&typeof row==="object")?row.public_id:row;
 if(Number.isSafeInteger(id)&&id>0)
  target.searchParams.set("opportunity",String(id));
 else
  target.searchParams.set("opportunity",String(row?.id||id));
 target.hash="";
 return target.href;
}
function findOpportunity(key,rows){
 if(typeof key!=="string")return null;
 if(/^[1-9]\d*$/.test(key)){
  const numeric=Number(key);
  if(!Number.isSafeInteger(numeric))return null;
  return rows.find(row=>row.public_id===numeric)||
   rows.find(row=>Array.isArray(row.public_id_aliases)&&row.public_id_aliases.includes(numeric))||null;
 }
 // Preserve links shared before numeric identifiers were introduced.
 return rows.find(row=>row.id===key||(Array.isArray(row.alternative_urls)&&row.alternative_urls.includes(key)))||null;
}
function requestedOpportunity(href){
 const id=new URL(href).searchParams.get("opportunity");
 return id&&id.length<=2500?id:null;
}
function navigateOpportunity(id){
 const target=id?opportunityUrl(id):new URL(window.location.href);
 if(!id)target.searchParams.delete("opportunity");
 window.history.pushState(null,"",target.href);
 renderRoute();
}
function renderRoute(){
 const id=requestedOpportunity(window.location.href);
 const page=$("opportunity-page");
 page.hidden=!id;
 document.body.classList.toggle("detail-view",!!id);
 if(!id){
  document.title="Opera+ Funding · Opportunità per la cultura";
  return;
 }
 const opportunity=findOpportunity(id,all);
 if(!opportunity){
  $("dialog-content").replaceChildren(el("h2","Opportunità non trovata","dialog-title"),
   el("p","Questa opportunità non è disponibile nel catalogo attuale. Puoi tornare alla dashboard e cercare altre iniziative."));
  document.title="Opportunità non trovata · Opera+ Funding";
  return;
 }
 // A legacy shared URL still resolves, then silently becomes the concise URL.
 if(opportunity.public_id&&id!==String(opportunity.public_id)){
  window.history.replaceState(null,"",opportunityUrl(opportunity));
 }
 renderOpportunity(opportunity);
 document.title=(opportunity.title||"Opportunità")+" · Opera+ Funding";
}
async function copyOpportunityUrl(o,button){
 const url=opportunityUrl(o);
 try{
  await navigator.clipboard.writeText(url);
  button.textContent="Link copiato";
 }catch{
  // Always expose the shareable URL without relying on clipboard permissions.
  button.textContent="Copia il link dalla barra degli indirizzi";
 }
}
function renderOpportunity(o){
 const content=$("dialog-content");
 content.replaceChildren();
 content.append(el("h2",o.title||"Opportunità","dialog-title"));
 content.lastChild.id="dialog-title";
 const line=el("div",undefined,"dialog-meta");
 line.append(el("span",statusLabel(state(o)),"chip status "+(state(o)==="aperto"?"open":state(o)==="chiuso"?"closed":state(o)==="in arrivo"?"upcoming":"unknown")));
 const change=changeBadge(o);
 if(change)line.append(el("span",change.label,"chip change "+change.kind));
 line.append(el("span",o.issuer||"Ente non indicato"));
 content.append(line,el("p",opportunitySummary(o),"dialog-summary"));
 const grid=el("dl",undefined,"dialog-grid detail-highlights");
 dialogField(grid,"Scadenza",validDate(o.deadline)?dateLabel(o.deadline).replace("Scade il ",""):o.rolling_confirmed===true?"A sportello":"Non indicata");
 dialogField(grid,"Contributo / dotazione",o.amount?String(o.amount).replace(" (da verificare)",""):"Non indicato");
 dialogField(grid,"Beneficiari",o.beneficiaries_excerpt||"Da verificare nella documentazione");
 dialogField(grid,"Tipologia",o.application_type||o.opportunity_type||"Non indicata");
 content.append(grid);
 const actions=el("div",undefined,"detail-primary-actions");
 addLink(actions,"Apri il bando ufficiale ↗",o.link_status==="non disponibile"?o.source_url:(o.resolved_url||o.url),"detail-official-link");
 actions.append(followButton(o));
 content.append(actions);
 content.append(evidenceSection(o));

 const information=el("section",undefined,"dialog-section detail-information");
 information.append(el("h3","Informazioni sul bando"));
 const requirementFacts=el("dl",undefined,"detail-facts");
 for(const [label,value] of [
  ["Finalità del programma",o.programme_objectives_excerpt],
  ["Attività finanziabili",o.funded_activities_excerpt],
  ["Destinatari e beneficiari",o.beneficiaries_excerpt],
  ["Vincoli e requisiti",o.requirements_excerpt],
  ["Ambito del bando",o.funding_scope_note],
  ["Apertura candidature",validDate(o.opening_date)?dateLabel(o.opening_date).replace("Scade il ",""):""],
  ["Natura dell’importo",o.amount_kind],
  ["Edizione",o.edition_year],
  ["Finestra di candidatura",o.window_label],
  ["Finestre successive",Array.isArray(o.application_windows)&&o.application_windows.length>1?o.application_windows.filter(validDate).map(d=>dateLabel(d).replace("Scade il ","")).join(" · "):""],
  ["Procedura a sportello",o.rolling_guidance]
 ])dialogField(requirementFacts,label,value);
 information.append(detailDisclosure("Requisiti, condizioni e informazioni aggiuntive",requirementFacts,"requirements-disclosure"));
 const documents=el("div",undefined,"dialog-links detail-document-links"),used=new Set();
 const appendDocument=(label,url)=>{
  const href=safeUrl(url);
  if(href&&!used.has(href)){used.add(href);addLink(documents,label,href);}
 };
 appendDocument("Scheda ufficiale ↗",o.link_status==="non disponibile"?o.source_url:(o.resolved_url||o.url));
 for(const [label,url] of [
  ["Fonte scadenza ↗",o.deadline_source],
  ["Fonte beneficiari ↗",o.beneficiaries_source],
  ["Fonte importo ↗",o.amount_source],
  ["Fonte sportello ↗",o.rolling_guidance_source]
 ])appendDocument(label,url);
 for(const document of o.documents||[])appendDocument((document.label||"Documento")+" ↗",document.url);
 if(documents.childElementCount)information.append(detailDisclosure("Documenti e fonti ufficiali",documents,"sources-disclosure"));
 if(Array.isArray(o.project_ideas)&&o.project_ideas.length){
  const ideas=el("ul");
  for(const idea of uniqueStatements(o.project_ideas).slice(0,4))ideas.append(el("li",idea));
  if(ideas.childElementCount)information.append(detailDisclosure("Spunti progettuali per Opera+",ideas,"ideas-disclosure"));
 }
 content.append(information);
 content.append(workflowForm(o));
 const utilities=el("div",undefined,"detail-utilities");
 const pdfButton=el("button","Esporta PDF","export-pdf-button");
 pdfButton.type="button";pdfButton.title="Stampa o salva come PDF";
 pdfButton.addEventListener("click",()=>printEvaluation(o));
 const share=el("button","Copia link della scheda","share-link-button");
 share.type="button";share.addEventListener("click",()=>copyOpportunityUrl(o,share));
 utilities.append(pdfButton,share);
 content.append(utilities);
}
// Subtle recent-change badges only when the scan recorded a material change.
// Never infer novelty from first_seen on the existing catalog.
function changeBadge(o,now=new Date()){
 const labels=[["catalog_new_at","NUOVA","new"],["catalog_updated_at","AGGIORNATA","updated"]];
 // Versions 1 and 2 flagged harmless extraction enrichment on many records.
 // Never show those obsolete update badges, even before the next catalog scan.
 if(o.catalog_tracking_version!==3){
  const fresh={...o};delete fresh.catalog_updated_at;
  o=fresh;
 }
 for(const [key,label,kind] of labels){
  const value=o[key];
  if(typeof value!=="string"||!/^\d{4}-\d{2}-\d{2}T/.test(value))continue;
  const time=Date.parse(value),age=now.getTime()-time;
  if(Number.isFinite(time)&&age>=0&&age<7*86400000)return {label,kind};
 }
 return null;
}
function assessmentLabel(o){
 if(typeof o.assessment_label==="string"&&o.assessment_label.trim())return o.assessment_label;
 if(!["finanziamento potenziale","call progettuale da verificare","non classificato"].includes(o.opportunity_type))return "INFORMATIVA";
 return score(o)>=70?"ALTA AFFINITÀ":score(o)>=45?"MEDIA AFFINITÀ":"BASSA AFFINITÀ";
}
function makeCard(o){
 const article=el("article",undefined,"item");
 const left=el("div",undefined,"item-main"),right=el("aside",undefined,"item-side");
 const tags=el("div",undefined,"item-badges"),st=state(o);
 tags.append(el("span",statusLabel(st),"chip status "+(st==="aperto"?"open":st==="chiuso"?"closed":st==="in arrivo"?"upcoming":"unknown")));
 const change=changeBadge(o);
 if(change)tags.append(el("span",change.label,"chip change "+change.kind));
 if(o.assessment_review_status && o.assessment_review_status!=="REVISIONE DOCUMENTALE"){
  tags.append(el("span",o.assessment_review_status==="EVIDENZE RACCOLTE"?"Evidenze raccolte":"Verifica documentale parziale","chip"));
 }
 if(isFollowed(o))tags.append(el("span",workflowRecord(o).phase,"chip personal-phase"));
 if(o.application_type)tags.append(el("span",o.application_type+" · "+(o.window_label||"Candidatura"),"chip"));
 const title=el("h3",undefined,"item-title");
 const titleLink=el("a",o.title||"Opportunità senza titolo","item-title-link");
 titleLink.href=opportunityUrl(o);
 title.append(titleLink);
 left.append(tags,title,el("p",opportunitySummary(o),"item-summary"));
 const meta=el("div",undefined,"item-meta");
 meta.append(el("span",o.issuer||"Ente non indicato","issuer-name"));
 if(o.themes?.length)meta.append(el("span",o.themes[0]));
 left.append(meta);
 const actions=el("div",undefined,"item-actions");
 const detailLink=el("a","Esamina opportunità","details-toggle");
 detailLink.href=opportunityUrl(o);
 // Use native anchor navigation for reliable click, keyboard and new-tab behavior.
 detailLink.setAttribute("aria-label","Esamina opportunità: "+(o.title||"scheda"));
 actions.append(detailLink,followButton(o));
 if(o.link_status==="non disponibile")addLink(actions,"Sito dell’ente ↗",o.source_url,"source-link");
 else addLink(actions,"Fonte ufficiale ↗",o.resolved_url||o.url,"source-link");
 left.append(actions);
 right.append(makeCalendar(o));
 article.append(left,right,makeAdequacy(o));
 return article;
}
function updateStateCounts(){
 for(const tab of document.querySelectorAll(".quick-tab")){
  const key=tab.dataset.value;
  if(!key){tab.textContent="Tutti ("+all.length+")";continue;}
  const title=tab.dataset.label||tab.textContent.replace(/\\s*\\(\\d+\\)$/,"").trim();
  tab.dataset.label=title;
  const number=all.filter(o=>key==="followed"?isFollowed(o):state(o)===key).length;
  tab.textContent=title+" ("+number+")";
 }
}
function render(){
 const items=filteredRows(),batch=items.slice(0,visibleCount);
 $("followed-note").hidden=$("status").value!=="followed";
 $("items").replaceChildren(...batch.map(makeCard));
 if(!items.length){
  const empty=$("status").value==="followed"?"Non hai ancora salvato opportunità da seguire su questo browser.":$("status").value==="aperto"?"Nessuna opportunità aperta confermata con i filtri selezionati. Esplora le altre opportunità.":"Nessuna opportunità corrisponde ai filtri selezionati.";
  $("items").append(el("p",empty,"empty"));
 }
 $("count").textContent=items.length+" opportunità"+(items.length>PAGE_SIZE?" · "+batch.length+" visualizzate":"");
 $("more").hidden=visibleCount>=items.length;
}
function sourceHealth(status,opportunities){
 const sources=status.sources||[],failed=sources.filter(o=>o.ok!==true),ratio=sources.length?failed.length/sources.length:1;
 const level=!sources.length?"red":!failed.length?"green":failed.length>=3||ratio>=.25?"red":"yellow";
 const names=new Map(opportunities.map(x=>[x.source_id,x.issuer]));
 return {level,ok:sources.length-failed.length,total:sources.length,
  incidents:failed.map(x=>({name:x.source_name||names.get(x.source_id)||x.source_id,reason:x.error||"Impossibile completare la lettura della fonte",url:x.source_url||"",referenceUrl:x.institutional_reference_url||"",referenceLabel:x.institutional_reference_label||"Fonte istituzionale integrativa",coverageNote:x.coverage_note||""}))};
}
function renderSourceHealth(status,opportunities){
 const h=sourceHealth(status,opportunities);
 $("health-dot").className="health-dot "+h.level;
 $("health-label").textContent=h.level==="green"?"Fonti operative":h.level==="yellow"?"Anomalie sulle fonti":"Problemi di aggiornamento";
 $("health-count").textContent=h.ok+" / "+h.total+" fonti raggiunte";
 const list=$("source-incidents");list.replaceChildren();
 if(!h.incidents.length){list.append(el("p","Nessuna anomalia tecnica riscontrata nell’ultima scansione.","health-ok"));return;}
 for(const issue of h.incidents){
  const row=el("div",undefined,"source-incident");
  if(issue.url)addLink(row,issue.name,issue.url);else row.append(el("strong",issue.name));
  row.append(el("span",issue.reason));
  if(issue.coverageNote)row.append(el("span",issue.coverageNote));
  if(issue.referenceUrl)addLink(row,issue.referenceLabel,issue.referenceUrl,"source-link");
  list.append(row);
 }
}
function syncControls(){
 for(const node of document.querySelectorAll(".quick-tab")){
  const active=node.dataset.value===$("status").value;
  node.classList.toggle("active",active);node.setAttribute("aria-pressed",String(active));
 }
 for(const node of document.querySelectorAll(".sort-button")){
  const active=node.dataset.sort===$("sort").value;
  node.classList.toggle("active",active);node.setAttribute("aria-pressed",String(active));
 }
}
function resetPagination(){visibleCount=PAGE_SIZE;render();}
async function init(){
 const sequence=++loadSequence;
 const button=$("refresh");button.disabled=true;button.textContent="Aggiornamento…";
 try{
  const dataset=await loadDataset();
  if(sequence!==loadSequence)return;
  all=dataset.opportunities;const status=dataset.status;
  $("total").textContent=all.filter(o=>state(o)==="aperto").length;
  $("potential").textContent=all.length;
  $("high").textContent=all.filter(o=>state(o)==="aperto"&&adequacyLevel(o)===3).length;
  $("sources").textContent=status.sources.length;
  const stamp=status.checked_at?new Date(status.checked_at).toLocaleString("it-IT",{dateStyle:"short",timeStyle:"short"}):"non disponibile";
  $("scan").textContent=(dataset.origin==="github"?"Ultima scansione: ":"Copia locale · Ultima scansione: ")+stamp;
  $("scan").classList.toggle("fallback-data",dataset.origin==="local");
  const selector=$("issuer"),oldValue=selector.value;selector.replaceChildren();
  const allOption=el("option","Tutti gli enti");allOption.value="";selector.append(allOption);
  for(const name of [...new Set(all.map(o=>o.issuer).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"it"))){
   const option=el("option",name);option.value=name;selector.append(option);
  }
  selector.value=[...selector.options].some(x=>x.value===oldValue)?oldValue:"";
  renderSourceHealth(status,all);updateStateCounts();syncControls();render();renderRoute();
 }catch(e){
  if(sequence!==loadSequence)return;
  $("scan").textContent="Dati non disponibili";$("items").replaceChildren(el("p","Impossibile caricare le opportunità. Riprova con Aggiorna.","empty"));
  $("health-dot").className="health-dot red";$("health-label").textContent="Dati non disponibili";
  $("source-incidents").textContent="Il report dell’ultima scansione non è disponibile.";
 }finally{if(sequence===loadSequence){button.disabled=false;button.textContent="Aggiorna ↻";}}
}
for(const id of ["search","issuer","kind","level"])$(id).addEventListener(id==="search"?"input":"change",resetPagination);
for(const node of document.querySelectorAll(".quick-tab"))node.addEventListener("click",()=>{$("status").value=node.dataset.value;syncControls();resetPagination();});
for(const node of document.querySelectorAll(".sort-button"))node.addEventListener("click",()=>{$("sort").value=node.dataset.sort;syncControls();resetPagination();});
$("reset").addEventListener("click",()=>{
 $("search").value="";$("issuer").value="";$("kind").value="";$("level").value="0";$("status").value="aperto";$("sort").value="deadline";
 syncControls();resetPagination();
});
$("more").addEventListener("click",()=>{visibleCount+=PAGE_SIZE;render();});
$("refresh").addEventListener("click",init);
$("dialog-close").addEventListener("click",()=>{navigateOpportunity(null);window.scrollTo(0,0);});
window.addEventListener("popstate",renderRoute);
window.addEventListener("afterprint",()=>{$("print-sheet").hidden=true;});
init();
