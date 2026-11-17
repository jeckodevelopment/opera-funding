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
 // GitHub raw CDN can serve an older main-branch snapshot despite no-store.
 // Use the same unique token for both resources, so refresh never combines
 // different cached generations of catalog and scan status.
 const revision="v="+Date.now();
 const [opResponse,scanResponse]=await Promise.all([
  fetch(origin+"opportunities.json?"+revision,{cache:"no-store",credentials:"omit"}),
  fetch(origin+"scan-status.json?"+revision,{cache:"no-store",credentials:"omit"})
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
 if(!["finanziamento potenziale","call progettuale da verificare"].includes(o.opportunity_type))return "altro contenuto";
 return "non verificato";
}
function dateLabel(value){
 if(!validDate(value))return "Scadenza non indicata";
 const [y,m,d]=value.split("-");return "Scade il "+d+"/"+m+"/"+y;
}
function score(o){return Math.max(0,Math.min(100,Number(o.relevance)||0));}
function groupOrder(o){return {aperto:0,"in arrivo":1,"non verificato":2,chiuso:3,"altro contenuto":4}[state(o)];}
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
function statusLabel(s){return {aperto:"APERTA","in arrivo":"IN ARRIVO","non verificato":"STATO NON CONFERMATO",chiuso:"SCADUTA","altro contenuto":"ALTRO CONTENUTO"}[s];}
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
function evidenceSection(o){
 const review=reviewSignals(o),section=el("section",undefined,"dialog-section evidence-review");
 section.append(el("h3","Valutazione preliminare"));
 const intro=el("p","Il punteggio indica la coerenza tematica, non l'ammissibilità né le probabilità di ottenere il contributo.");
 section.append(intro);
 const dl=el("dl",undefined,"review-facts");
 dialogField(dl,"Adeguatezza tematica",score(o)+"/100");
 dialogField(dl,"Ammissibilità",review.eligibility);
 dialogField(dl,"Affidabilità della valutazione",review.confidence||"Non documentata");
 dialogField(dl,"Elementi utilizzati",o.score_explanation_basis||"Solo titolo (valutazione preliminare)");
 section.append(dl);
 if(review.explanation){
  section.append(el("h4","Perché questa opportunità può interessare"));
  section.append(el("p",review.explanation));
 }
 if(review.checks.length){
  section.append(el("h4","Verifiche prima di decidere"));
  const list=el("ul");
  for(const check of review.checks)list.append(el("li",check));
  section.append(list);
 }
 if(review.missing.length){
  section.append(el("h4","Informazioni da approfondire"));
  const list=el("ul");
  for(const missing of review.missing)list.append(el("li",missing));
  section.append(list);
 }
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
  fit:score(o)+"/100",
  confidence:review.confidence||"Non documentata",
  basis:String(o.score_explanation_basis||"Titolo e informazioni preliminari"),
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
  ["Tipologia",d.type],["Adeguatezza tematica",d.fit],
  ["Ammissibilità",d.eligibility],["Affidabilità analisi",d.confidence]
 ])addReportFact(facts,label,value);
 sheet.append(facts);
 const summary=el("section",undefined,"print-section");
 summary.append(el("h2","Sintesi dell'opportunità"),el("p",d.summary));
 sheet.append(summary);
 const assessment=el("section",undefined,"print-section");
 assessment.append(el("h2","Motivazione dell'adeguatezza"),el("p",d.reasoning),
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
  el("p","Le informazioni provengono dal catalogo Opera+ Funding e possono essere incomplete o superate. L'adeguatezza tematica non conferma ammissibilità né probabilità di finanziamento. Verificare sempre i documenti ufficiali prima di candidarsi."));
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
function opportunityUrl(id,base=window.location.href){
 const target=new URL(base);
 target.searchParams.set("opportunity",String(id));
 target.hash="";
 return target.href;
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
 const opportunity=all.find(o=>o.id===id);
 if(!opportunity){
  $("dialog-content").replaceChildren(el("h2","Opportunità non trovata","dialog-title"),
   el("p","Questa opportunità non è disponibile nel catalogo attuale. Puoi tornare alla dashboard e cercare altre iniziative."));
  document.title="Opportunità non trovata · Opera+ Funding";
  return;
 }
 renderOpportunity(opportunity);
 document.title=(opportunity.title||"Opportunità")+" · Opera+ Funding";
}
async function copyOpportunityUrl(o,button){
 const url=opportunityUrl(o.id);
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
 content.append(line);
 content.append(el("p",opportunitySummary(o),"dialog-summary"));
 const grid=el("dl",undefined,"dialog-grid");
 dialogField(grid,"Scadenza",validDate(o.deadline)?dateLabel(o.deadline).replace("Scade il ",""):"Non indicata");
 dialogField(grid,"Apertura candidature",validDate(o.opening_date)?dateLabel(o.opening_date).replace("Scade il ",""):"");
 dialogField(grid,"Contributo / dotazione",o.amount?String(o.amount).replace(" (da verificare)",""):"Non indicato nella scheda");
 dialogField(grid,"Natura dell’importo",o.amount_kind||"");
 dialogField(grid,"Tipologia candidatura",o.application_type||o.opportunity_type||"");
 dialogField(grid,"Edizione",o.edition_year||"");
 dialogField(grid,"Finestra",o.window_label||"");
 content.append(grid);
 content.append(evidenceSection(o));
 if(o.rolling_guidance){
  const rolling=el("section",undefined,"dialog-section rolling-guidance");
  rolling.append(el("h3","Possibile opportunità a sportello"));
  rolling.append(el("p",o.rolling_guidance));
  content.append(rolling);
 }
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
 // Link to distinct evidence sources only; avoid repeating the main official page.
 for(const [label,url] of [["Fonte beneficiari ↗",o.beneficiaries_source],
                           ["Fonte importo ↗",o.amount_source],
                           ["Fonte indicazione sportello ↗",o.rolling_guidance_source]]){
  if(url&&![o.url,o.resolved_url,o.deadline_source,o.source_url].includes(url))
   addLink(links,label,url);
 }
 const used=new Set([o.url,o.resolved_url,o.deadline_source]);
 for(const d of o.documents||[]){
  if(!used.has(d.url)){addLink(links,(d.label||"Documento")+" ↗",d.url);used.add(d.url);}
 }
 content.append(links);
 const exportBar=el("div",undefined,"dialog-export");
 const pdfButton=el("button","Esporta scheda PDF","export-pdf-button");
 pdfButton.type="button";
 pdfButton.title="Apri la stampa: seleziona Salva come PDF";
 pdfButton.addEventListener("click",()=>printEvaluation(o));
 exportBar.append(pdfButton,el("span","Si apre la stampa del browser: scegli Salva come PDF.","export-hint"));
 const shareBar=el("div",undefined,"share-opportunity");
 const share=el("button","Copia link della scheda","share-link-button");
 share.type="button";
 share.addEventListener("click",()=>copyOpportunityUrl(o,share));
 shareBar.append(share,el("span","La pagina ha un URL condivisibile e si apre anche direttamente.","export-hint"));
 content.append(shareBar);
 content.append(exportBar);
}
// Subtle recent-change badges only when the scan recorded a material change.
// Never infer novelty from first_seen on the existing catalog.
function changeBadge(o,now=new Date()){
 const labels=[["catalog_new_at","NUOVA","new"],["catalog_updated_at","AGGIORNATA","updated"]];
 for(const [key,label,kind] of labels){
  const value=o[key];
  if(typeof value!=="string"||!/^\d{4}-\d{2}-\d{2}T/.test(value))continue;
  const time=Date.parse(value),age=now.getTime()-time;
  if(Number.isFinite(time)&&age>=0&&age<7*86400000)return {label,kind};
 }
 return null;
}
function makeCard(o){
 const article=el("article",undefined,"item");
 const left=el("div",undefined,"item-main"),right=el("aside",undefined,"item-side");
 const tags=el("div",undefined,"item-badges"),st=state(o);
 tags.append(el("span",statusLabel(st),"chip status "+(st==="aperto"?"open":st==="chiuso"?"closed":st==="in arrivo"?"upcoming":"unknown")));
 const change=changeBadge(o);
 if(change)tags.append(el("span",change.label,"chip change "+change.kind));
 if(o.application_type)tags.append(el("span",o.application_type+" · "+(o.window_label||"Candidatura"),"chip"));
 left.append(tags,el("h3",o.title||"Opportunità senza titolo","item-title"),el("p",opportunitySummary(o),"item-summary"));
 const meta=el("div",undefined,"item-meta");
 meta.append(el("span",o.issuer||"Ente non indicato","issuer-name"));
 if(o.themes?.length)meta.append(el("span",o.themes[0]));
 left.append(meta);
 const actions=el("div",undefined,"item-actions");
 const detailLink=el("a","Esamina opportunità","details-toggle");
 detailLink.href=opportunityUrl(o.id);
 detailLink.addEventListener("click",event=>{
  if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  event.preventDefault();
  navigateOpportunity(o.id);
  window.scrollTo(0,0);
 });
 actions.append(detailLink);
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
  if(!key)continue;
  const title=tab.dataset.label||tab.textContent.replace(/\\s*\\(\\d+\\)$/,"").trim();
  tab.dataset.label=title;
  const number=all.filter(o=>state(o)===key).length;
  tab.textContent=title+" ("+number+")";
 }
}
function render(){
 const items=filteredRows(),batch=items.slice(0,visibleCount);
 $("items").replaceChildren(...batch.map(makeCard));
 if(!items.length){
  const empty=$("status").value==="aperto"?"Nessuna opportunità aperta confermata con i filtri selezionati. Esplora le altre opportunità.":"Nessuna opportunità corrisponde ai filtri selezionati.";
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
  renderSourceHealth(status,all);updateStateCounts();syncControls();render();renderRoute();
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
 $("search").value="";$("issuer").value="";$("kind").value="";$("level").value="0";$("status").value="aperto";$("sort").value="deadline";
 syncControls();resetPagination();
});
$("more").addEventListener("click",()=>{visibleCount+=PAGE_SIZE;render();});
$("refresh").addEventListener("click",init);
$("dialog-close").addEventListener("click",()=>{navigateOpportunity(null);window.scrollTo(0,0);});
window.addEventListener("popstate",renderRoute);
window.addEventListener("afterprint",()=>{$("print-sheet").hidden=true;});
init();
