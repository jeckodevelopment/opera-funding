const $ = id => document.getElementById(id);
const PAGE_SIZE = 20;
const DATA_ORIGIN = "https://raw.githubusercontent.com/jeckodevelopment/opera-funding/main/data/";
const FALLBACK_ORIGIN = "data/";
async function fetchDataset(origin) {
 const [opportunitiesResponse,statusResponse]=await Promise.all([
  fetch(origin+"opportunities.json",{cache:"no-store",credentials:"omit"}),
  fetch(origin+"scan-status.json",{cache:"no-store",credentials:"omit"})
 ]);
 if(!opportunitiesResponse.ok||!statusResponse.ok)throw Error("HTTP error loading dataset");
 const [opportunities,status]=await Promise.all([opportunitiesResponse.json(),statusResponse.json()]);
 if(!Array.isArray(opportunities)||!status||typeof status!=="object"||!Array.isArray(status.sources))
  throw Error("Invalid funding JSON schema");
 return {opportunities,status};
}
async function loadDataset() {
 try {return {...await fetchDataset(DATA_ORIGIN),origin:"github"};}
 catch(error) {
  const fallback=await fetchDataset(FALLBACK_ORIGIN);
  return {...fallback,origin:"local",reason:error.message};
 }
}

let all = [], visibleCount = PAGE_SIZE;
const safeUrl = value => { try { const u = new URL(value); return u.protocol === "https:" ? u.href : null; } catch { return null; } };
const el = (tag, value, className) => { const e=document.createElement(tag); if(value!==undefined)e.textContent=value; if(className)e.className=className; return e; };
function addLink(parent,label,url) { const safe=safeUrl(url); if(!safe)return; const a=el("a",label); a.href=safe;a.target="_blank";a.rel="noopener noreferrer";parent.append(a); }
function isExpired(o) { if(!/^\d{4}-\d{2}-\d{2}$/.test(o.deadline||""))return false; return o.deadline < new Date().toISOString().slice(0,10); }
function state(o) {
 if(isExpired(o)||o.closure_confirmed||((o.status==="chiuso"||o.status==="scaduto")&&!o.reopened_confirmed))return "chiuso";
 const now=new Date().toISOString().slice(0,10), end=o.deadline, start=o.opening_date;
 if(start&&start>now&&o.opening_evidence)return "in arrivo";
 const openEvidence=o.source_open_confirmed===true && o.link_status==="raggiungibile";
 const validWindow=(end&&/^\d{4}-\d{2}-\d{2}$/.test(end)&&end>=now)||(o.rolling_confirmed===true&&!!o.rolling_evidence);
 if(openEvidence&&validWindow&&(!start||start<=now))return "aperto";
 return "non verificato";
}
function dateLabel(value) { if(!/^\d{4}-\d{2}-\d{2}$/.test(value||""))return "Scadenza non disponibile"; const [y,m,d]=value.split("-");return "Scade il "+d+"/"+m+"/"+y; }
function priority(o) {const st=state(o);return st==="aperto"?0:st==="non verificato"?1:st==="in arrivo"?2:3;}
function deadlineKey(o) {return o.deadline||"9999-12-31";}
function sortRows(rows,order) {
 const relevance=(a,b)=>Number(b.relevance||0)-Number(a.relevance||0);
 rows.sort((a,b)=>{
   if(order==="relevance")return relevance(a,b);
   if(order==="deadline")return deadlineKey(a).localeCompare(deadlineKey(b))||relevance(a,b);
   if(order==="recent")return String(b.first_seen||"").localeCompare(a.first_seen||"")||relevance(a,b);
   const group=priority(a)-priority(b);
   if(group)return group;
   if(priority(a)===0)return deadlineKey(a).localeCompare(deadlineKey(b))||relevance(a,b);
   if(priority(a)===2)return String(a.opening_date||"9999").localeCompare(String(b.opening_date||"9999"))||relevance(a,b);
   return relevance(a,b);
 });return rows;
}
function filteredRows(){
 const q=$("search").value.toLocaleLowerCase("it").trim(),status=$("status").value,kind=$("kind").value,issuer=$("issuer").value,min=Number($("level").value);
 const rows=all.filter(o=>{
   const s=state(o);
   if(status==="active"&&!(s==="aperto"||s==="in arrivo") )return false;
   if(status&&status!=="active"&&s!==status)return false;
   if(kind==="funding"&&!["finanziamento potenziale","call progettuale da verificare"].includes(o.opportunity_type))return false;
   if(kind&&kind!=="funding"&&(o.opportunity_type||"non classificato")!==kind)return false;
   if(issuer&&o.issuer!==issuer)return false;
   if(Number(o.relevance||0)<min)return false;
   return !q||[o.title,o.issuer,...(o.themes||[])].join(" ").toLocaleLowerCase("it").includes(q);
 });return sortRows(rows,$("sort").value);
}
function chip(label,type){return el("span",label,"chip "+(type||""));}
function renderItem(o){
 const item=el("article",undefined,"item");const main=el("div",undefined,"item-main"),left=el("div");
 const meta=el("div",undefined,"item-meta");meta.append(el("span",o.issuer||"Ente non specificato"));
 const badges=el("div",undefined,"item-badges");const st=state(o);
 badges.append(chip(st==="chiuso"?"CHIUSO":st==="aperto"?"APERTO":st==="in arrivo"?"IN ARRIVO":"STATO NON CONFERMATO","status "+(st==="chiuso"?"closed":st==="aperto"?"open":st==="in arrivo"?"upcoming":"unknown")));
 badges.append(chip(dateLabel(o.deadline),"deadline"));
 badges.append(chip(o.opportunity_type==="call progettuale da verificare"?"Call progettuale":o.opportunity_type==="finanziamento potenziale"?"Finanziamento potenziale":(o.opportunity_type||"Tipologia da definire")));
 left.append(badges,el("h3",o.title||"Senza titolo"),meta);
 const score=el("div",undefined,"item-score");score.append(el("strong",String(o.relevance??0)+"/100"),el("span","Pertinenza"));
 main.append(left,score);item.append(main);
 const actions=el("div",undefined,"item-actions");const broken=o.link_status==="non disponibile";
 if(!broken)addLink(actions,"Consulta la fonte ↗",o.resolved_url||o.url);
 else addLink(actions,"Pagina bandi dell'ente ↗",o.source_url);
 const detail=el("div",undefined,"item-details");detail.hidden=true;
 const detailsButton=el("button","Dettagli +","details-toggle");detailsButton.type="button";detailsButton.setAttribute("aria-expanded","false");
 detailsButton.addEventListener("click",()=>{detail.hidden=!detail.hidden;detailsButton.setAttribute("aria-expanded",String(!detail.hidden));detailsButton.textContent=detail.hidden?"Dettagli +":"Nascondi dettagli −";});
 actions.append(detailsButton);item.append(actions);
 

 if(o.deadline_source)addLink(detail,"Fonte della scadenza ↗",o.deadline_source);
 if(o.amount)detail.append(el("p","Importo indicativo: "+String(o.amount).split(" (da verificare)")[0]));
 if(o.beneficiaries_excerpt)detail.append(el("p","Destinatari: "+o.beneficiaries_excerpt));


 if(Array.isArray(o.project_ideas)&&o.project_ideas.length)detail.append(el("p","Possibili progetti per Opera+: "+o.project_ideas.join("; ")));


 if(broken)detail.append(el("p","Il collegamento diretto risulta non disponibile (404/410).","linkwarn"));

 const docs=el("div",undefined,"documents");
 if(Array.isArray(o.documents)){for(const d of o.documents.slice(1,8))addLink(docs,(d.label||"Documento")+" ↗",d.url);}
 if(docs.childNodes.length)detail.append(docs);
 item.append(detail);return item;
}
function render(){
 const rows=filteredRows(),displayed=rows.slice(0,visibleCount);
 $("items").replaceChildren(...displayed.map(renderItem));
 if(!rows.length)$("items").append(el("p",all.length?"Nessun risultato: prova a modificare i filtri.":"Non ci sono ancora opportunità disponibili.","empty"));
 $("count").textContent=rows.length+" risultati"+(rows.length>PAGE_SIZE?" · visualizzati "+displayed.length:"");
 $("more").hidden=visibleCount>=rows.length;
}
function syncTabs(){const value=$("status").value;for(const tab of document.querySelectorAll(".quick-tab")){const active=tab.dataset.value===value;tab.classList.toggle("active",active);tab.setAttribute("aria-pressed",String(active));}}
function sourceHealth(status,opportunities){
 const sources=status.sources||[];
 const failures=sources.filter(x=>x.ok!==true);
 const ratio=sources.length?failures.length/sources.length:1;
 const level=!sources.length?"red":!failures.length?"green":failures.length>=3||ratio>=.25?"red":"yellow";
 const map=new Map(opportunities.map(o=>[o.source_id,o.issuer]));
 const incidents=failures.map(x=>({name:x.source_name||map.get(x.source_id)||x.source_id,reason:x.error||"Il portale non ha restituito risultati utilizzabili",id:x.source_id,url:x.source_url||""}));
 return {level,incidents,ok:sources.length-failures.length,total:sources.length};
}
function renderSourceHealth(status,opportunities){
 const health=sourceHealth(status,opportunities);
 const dot=$("health-dot"),label=$("health-label"),count=$("health-count"),list=$("source-incidents");
 dot.className="health-dot "+health.level;
 const headline=health.level==="green"?"Tutte le fonti raggiunte":health.level==="yellow"?"Alcune fonti non raggiungibili":"Aggiornamento incompleto";
 label.textContent=headline;
 count.textContent=health.ok+"/"+health.total+" fonti";
 list.replaceChildren();
 if(!health.incidents.length){list.append(el("p","Nessuna anomalia segnalata nell’ultimo aggiornamento.","health-ok"));return;}
 for(const issue of health.incidents){
  const row=el("div",undefined,"source-incident");
  const head=el("strong",issue.name);
  if(issue.url)addLink(row,issue.name+" ↗",issue.url);
  else row.append(head);
  row.append(el("span",issue.reason));
  list.append(row);
 }
}
function resetPagination(){visibleCount=PAGE_SIZE;render();}
async function init(){
 const button=$("refresh");if(button){button.disabled=true;button.textContent="Aggiornamento…";}
 try{
  const dataset=await loadDataset();all=dataset.opportunities;const status=dataset.status;
  $("total").textContent=all.filter(o=>state(o)==="aperto").length;
  $("potential").textContent=all.filter(o=>["finanziamento potenziale","call progettuale da verificare"].includes(o.opportunity_type)).length;
  $("high").textContent=all.filter(o=>state(o)==="non verificato").length;
  $("sources").textContent=all.filter(o=>state(o)==="chiuso").length;
  const timestamp=status.checked_at?new Date(status.checked_at).toLocaleString("it-IT",{dateStyle:"short",timeStyle:"short"}):"non disponibile";
  const failures=(status.sources||[]).filter(o=>!o.ok).length;
  const source=dataset.origin==="github"?"Dati live da GitHub":"Copia locale di riserva (GitHub non raggiungibile)";
  $("scan").textContent=source+" · Ultima scansione: "+timestamp+" · "+failures+" fonti con anomalie";
  $("scan").classList.toggle("fallback-data",dataset.origin==="local");
  const issuer=$("issuer");const oldIssuer=issuer.value;issuer.replaceChildren(el("option","Tutti"));
  issuer.firstChild.value="";
  for(const name of [...new Set(all.map(o=>o.issuer).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"it"))){
   const option=el("option",name);option.value=name;issuer.append(option);
  }
  issuer.value=Array.from(issuer.options).some(x=>x.value===oldIssuer)?oldIssuer:"";
  renderSourceHealth(status,all);syncTabs();render();
 }catch(err){
  $("scan").textContent="Impossibile caricare i dati da GitHub o dalla copia locale";
  $("health-dot").className="health-dot red";$("health-label").textContent="Dati non disponibili";
  $("source-incidents").textContent="Non è stato possibile consultare il report delle fonti.";
  $("items").replaceChildren(el("p","Dati temporaneamente non disponibili. Riprova con Aggiorna.","empty"));
 }finally{if(button){button.disabled=false;button.textContent="Aggiorna dati ↻";}}
}
for(const id of ["search","status","kind","issuer","level","sort"])$(id).addEventListener(id==="search"?"input":"change",resetPagination);
$("reset").addEventListener("click",()=>{$("search").value="";$("status").value="active";$("kind").value="funding";$("issuer").value="";$("level").value="0";$("sort").value="priority";syncTabs();resetPagination();});
for(const tab of document.querySelectorAll(".quick-tab"))tab.addEventListener("click",()=>{$("status").value=tab.dataset.value;syncTabs();resetPagination();});
$("refresh").addEventListener("click",init);
$("more").addEventListener("click",()=>{visibleCount+=PAGE_SIZE;render();});
init();
