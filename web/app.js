const $ = id => document.getElementById(id);
const PAGE_SIZE = 12;
const DATA_ORIGIN = "https://raw.githubusercontent.com/jeckodevelopment/opera-funding/main/data/";
const FALLBACK_ORIGIN = "data/";
let all=[], visibleCount=PAGE_SIZE;
const el=(tag,text,className)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(className)n.className=className;return n;};
const safeUrl=value=>{try{const u=new URL(value);return u.protocol==="https:"?u.href:null;}catch{return null;}};
function addLink(parent,label,url,className){
 const href=safeUrl(url);if(!href)return;
 const a=el("a",label,className);a.href=href;a.target="_blank";a.rel="noopener noreferrer";parent.append(a);
}
async function fetchDataset(origin){
 const [opResponse,scanResponse]=await Promise.all([
  fetch(origin+"opportunities.json",{cache:"no-store",credentials:"omit"}),
  fetch(origin+"scan-status.json",{cache:"no-store",credentials:"omit"})
 ]);
 if(!opResponse.ok||!scanResponse.ok)throw Error("Could not load funding data");
 const [opportunities,status]=await Promise.all([opResponse.json(),scanResponse.json()]);
 if(!Array.isArray(opportunities)||!status||!Array.isArray(status.sources))throw Error("Invalid funding data");
 return {opportunities,status};
}
async function loadDataset(){
 try{return {...await fetchDataset(DATA_ORIGIN),origin:"github"};}
 catch(e){return {...await fetchDataset(FALLBACK_ORIGIN),origin:"local"};}
}
const validDate=value=>typeof value==="string"&&/^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(Date.parse(value+"T12:00:00Z"));
const today=()=>new Date().toISOString().slice(0,10);
const daysLeft=date=>Math.ceil((Date.parse(date+"T00:00:00Z")-Date.parse(today()+"T00:00:00Z"))/86400000);
function state(o){
 const end=o.deadline,start=o.opening_date;
 if((validDate(end)&&end<today())||o.closure_confirmed||(["chiuso","scaduto"].includes(o.status)&&!o.reopened_confirmed))return "chiuso";
 if(validDate(start)&&start>today()&&o.opening_evidence)return "in arrivo";
 const window=(validDate(end)&&end>=today())||(o.rolling_confirmed===true&&!!o.rolling_evidence);
 if(o.source_open_confirmed===true&&o.link_status==="raggiungibile"&&window&&(!validDate(start)||start<=today()))return "aperto";
 return "non verificato";
}
function dateLabel(value){
 if(!validDate(value))return "Scadenza non indicata";
 const [y,m,d]=value.split("-");return "Scade il "+d+"/"+m+"/"+y;
}
function score(o){return Math.max(0,Math.min(100,Number(o.relevance)||0));}
function groupOrder(o){return {aperto:0,"in arrivo":1,"non verificato":2,chiuso:3}[state(o)];}
function sortRows(rows,order){
 const difference=(a,b)=>score(b)-score(a);
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
  if(stateFilter&&actual!==stateFilter)return false;
  if(kind==="funding"&&!["finanziamento potenziale","call progettuale da verificare"].includes(o.opportunity_type))return false;
  if(kind&&kind!=="funding"&&kind!==o.opportunity_type)return false;
  if(issuer&&issuer!==o.issuer)return false;
  if(score(o)<minimum)return false;
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
function statusLabel(s){return {aperto:"APERTO","in arrivo":"IN ARRIVO","non verificato":"STATO NON CONFERMATO",chiuso:"CHIUSO"}[s];}
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
function makeAdequacy(o){
 const value=score(o);
 const footer=el("div",undefined,"adequacy");
 const heading=el("div",undefined,"adequacy-heading");
 heading.append(el("span","Adeguatezza per Opera+","adequacy-label"),el("strong",value+"/100","adequacy-value"));
 const track=el("div",undefined,"adequacy-track");
 track.style.setProperty("--fit",value+"%");
 track.setAttribute("role","progressbar");
 track.setAttribute("aria-label","Adeguatezza del bando per Opera+");
 track.setAttribute("aria-valuemin","0");track.setAttribute("aria-valuemax","100");track.setAttribute("aria-valuenow",String(value));
 track.append(el("span",undefined,"adequacy-mask"),el("span",undefined,"adequacy-marker"));
 footer.append(heading,track);
 return footer;
}
function dialogField(parent,label,value){
 if(!value)return;
 const field=el("div",undefined,"dialog-field");
 field.append(el("dt",label),el("dd",String(value)));
 parent.append(field);
}
function openDetails(o){
 const dialog=$("opportunity-dialog"),content=$("dialog-content");
 content.replaceChildren();
 content.append(el("h2",o.title||"Opportunità","dialog-title"));
 content.lastChild.id="dialog-title";
 const line=el("div",undefined,"dialog-meta");
 line.append(el("span",statusLabel(state(o)),"chip status "+(state(o)==="aperto"?"open":state(o)==="chiuso"?"closed":state(o)==="in arrivo"?"upcoming":"unknown")));
 line.append(el("span",o.issuer||"Ente non indicato"));
 content.append(line);
 content.append(el("p",opportunitySummary(o),"dialog-summary"));
 const grid=el("dl",undefined,"dialog-grid");
 dialogField(grid,"Scadenza",validDate(o.deadline)?dateLabel(o.deadline).replace("Scade il ",""):"Non indicata");
 dialogField(grid,"Apertura candidature",validDate(o.opening_date)?dateLabel(o.opening_date).replace("Scade il ",""):"");
 dialogField(grid,"Contributo / dotazione",o.amount?String(o.amount).replace(" (da verificare)",""):"Non indicato nella scheda");
 dialogField(grid,"Tipologia candidatura",o.application_type||o.opportunity_type||"");
 dialogField(grid,"Edizione",o.edition_year||"");
 dialogField(grid,"Finestra",o.window_label||"");
 content.append(grid);
 if(o.beneficiaries_excerpt){
  const section=el("section",undefined,"dialog-section");
  section.append(el("h3","Destinatari"),el("p",o.beneficiaries_excerpt));
  content.append(section);
 }
 if(o.application_windows?.length>1){
  const section=el("section",undefined,"dialog-section");
  section.append(el("h3","Finestre di candidatura"),el("p",o.application_windows.filter(validDate).map(d=>dateLabel(d).replace("Scade il ","")).join(" · ")));
  content.append(section);
 }
 if(o.funding_scope_note){
  const section=el("section",undefined,"dialog-section");
  section.append(el("h3","Ambito del bando"),el("p",o.funding_scope_note));
  content.append(section);
 }
 if(o.project_ideas?.length){
  const section=el("section",undefined,"dialog-section");
  section.append(el("h3","Spunti per Opera+"));
  const ideas=el("ul");
  for(const idea of o.project_ideas.slice(0,4))ideas.append(el("li",idea));
  section.append(ideas);content.append(section);
 }
 const links=el("div",undefined,"dialog-links");
 addLink(links,"Apri la scheda ufficiale ↗",o.link_status==="non disponibile"?o.source_url:(o.resolved_url||o.url));
 if(o.deadline_source&&o.deadline_source!==(o.resolved_url||o.url))addLink(links,"Fonte della scadenza ↗",o.deadline_source);
 const used=new Set([o.url,o.resolved_url,o.deadline_source]);
 for(const d of o.documents||[]){
  if(!used.has(d.url)){addLink(links,(d.label||"Documento")+" ↗",d.url);used.add(d.url);}
 }
 content.append(links);
 dialog.showModal();
}
function makeCard(o){
 const article=el("article",undefined,"item");
 const left=el("div",undefined,"item-main"),right=el("aside",undefined,"item-side");
 const tags=el("div",undefined,"item-badges"),st=state(o);
 tags.append(el("span",statusLabel(st),"chip status "+(st==="aperto"?"open":st==="chiuso"?"closed":st==="in arrivo"?"upcoming":"unknown")));
 if(o.application_type)tags.append(el("span",o.application_type+" · "+(o.window_label||"Candidatura"),"chip"));
 left.append(tags,el("h3",o.title||"Opportunità senza titolo","item-title"),el("p",opportunitySummary(o),"item-summary"));
 const meta=el("div",undefined,"item-meta");
 meta.append(el("span",o.issuer||"Ente non indicato","issuer-name"));
 if(o.themes?.length)meta.append(el("span",o.themes[0]));
 left.append(meta);
 const actions=el("div",undefined,"item-actions");
 const button=el("button","Esamina opportunità","details-toggle");button.type="button";
 button.addEventListener("click",()=>openDetails(o));
 actions.append(button);
 if(o.link_status==="non disponibile")addLink(actions,"Sito dell’ente ↗",o.source_url,"source-link");
 else addLink(actions,"Fonte ufficiale ↗",o.resolved_url||o.url,"source-link");
 left.append(actions);
 right.append(makeCalendar(o));
 article.append(left,right,makeAdequacy(o));
 return article;
}
function render(){
 const items=filteredRows(),batch=items.slice(0,visibleCount);
 $("items").replaceChildren(...batch.map(makeCard));
 if(!items.length){
  const empty=$("status").value==="aperto"?"Nessuna candidatura aperta confermata con i filtri selezionati. Esplora le altre opportunità.":"Nessuna opportunità corrisponde ai filtri selezionati.";
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
  incidents:failed.map(x=>({name:x.source_name||names.get(x.source_id)||x.source_id,reason:x.error||"Impossibile completare la lettura della fonte",url:x.source_url||""}))};
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
 const button=$("refresh");button.disabled=true;button.textContent="Aggiornamento…";
 try{
  const dataset=await loadDataset();all=dataset.opportunities;const status=dataset.status;
  $("total").textContent=all.filter(o=>state(o)==="aperto").length;
  $("potential").textContent=all.filter(o=>["finanziamento potenziale","call progettuale da verificare"].includes(o.opportunity_type)).length;
  $("high").textContent=all.filter(o=>state(o)==="aperto"&&score(o)>=60).length;
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
  renderSourceHealth(status,all);syncControls();render();
 }catch(e){
  $("scan").textContent="Dati non disponibili";$("items").replaceChildren(el("p","Impossibile caricare le opportunità. Riprova con Aggiorna.","empty"));
  $("health-dot").className="health-dot red";$("health-label").textContent="Dati non disponibili";
  $("source-incidents").textContent="Il report dell’ultima scansione non è disponibile.";
 }finally{button.disabled=false;button.textContent="Aggiorna ↻";}
}
for(const id of ["search","issuer","kind","level"])$(id).addEventListener(id==="search"?"input":"change",resetPagination);
for(const node of document.querySelectorAll(".quick-tab"))node.addEventListener("click",()=>{$("status").value=node.dataset.value;syncControls();resetPagination();});
for(const node of document.querySelectorAll(".sort-button"))node.addEventListener("click",()=>{$("sort").value=node.dataset.sort;syncControls();resetPagination();});
$("reset").addEventListener("click",()=>{
 $("search").value="";$("issuer").value="";$("kind").value="funding";$("level").value="0";$("status").value="aperto";$("sort").value="deadline";
 syncControls();resetPagination();
});
$("more").addEventListener("click",()=>{visibleCount+=PAGE_SIZE;render();});
$("refresh").addEventListener("click",init);
$("dialog-close").addEventListener("click",()=>$("opportunity-dialog").close());
$("opportunity-dialog").addEventListener("click",event=>{if(event.target===$("opportunity-dialog"))$("opportunity-dialog").close();});
init();
