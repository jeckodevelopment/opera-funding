const $ = id => document.getElementById(id);
const PAGE_SIZE = 20;
let all = [], visibleCount = PAGE_SIZE;
const safeUrl = value => { try { const u = new URL(value); return u.protocol === "https:" ? u.href : null; } catch { return null; } };
const el = (tag, value, className) => { const e=document.createElement(tag); if(value!==undefined)e.textContent=value; if(className)e.className=className; return e; };
function addLink(parent,label,url) { const safe=safeUrl(url); if(!safe)return; const a=el("a",label); a.href=safe;a.target="_blank";a.rel="noopener noreferrer";parent.append(a); }
function isExpired(o) { if(!/^\d{4}-\d{2}-\d{2}$/.test(o.deadline||""))return false; return o.deadline < new Date().toISOString().slice(0,10); }
function state(o) { if(isExpired(o))return "chiuso"; if(o.status==="chiuso")return "chiuso"; if((o.status||"").startsWith("aperto"))return "aperto"; return "non verificato"; }
function dateLabel(value) { if(!/^\d{4}-\d{2}-\d{2}$/.test(value||""))return "Scadenza da verificare"; const [y,m,d]=value.split("-");return "Scade il "+d+"/"+m+"/"+y; }
function priority(o) { const s=state(o);return s==="aperto"?0:s==="non verificato"?1:2; }
function sortRows(rows,order) {
 const cmp=(a,b)=>Number(b.relevance||0)-Number(a.relevance||0);
 rows.sort((a,b)=>{
   if(order==="relevance")return cmp(a,b);
   if(order==="deadline"){const ad=a.deadline||"9999",bd=b.deadline||"9999";return ad.localeCompare(bd)||cmp(a,b);}
   if(order==="recent")return String(b.first_seen||"").localeCompare(a.first_seen||"")||cmp(a,b);
   return priority(a)-priority(b)||cmp(a,b);
 });return rows;
}
function filteredRows(){
 const q=$("search").value.toLocaleLowerCase("it").trim(),status=$("status").value,kind=$("kind").value,issuer=$("issuer").value,min=Number($("level").value);
 const rows=all.filter(o=>{
   const s=state(o);
   if(status==="active"&&s==="chiuso")return false;
   if(status&&status!=="active"&&s!==status)return false;
   if(kind&&(o.opportunity_type||"non classificato")!==kind)return false;
   if(issuer&&o.issuer!==issuer)return false;
   if(Number(o.relevance||0)<min)return false;
   return !q||[o.title,o.issuer,...(o.themes||[])].join(" ").toLocaleLowerCase("it").includes(q);
 });return sortRows(rows,$("sort").value);
}
function chip(label,type){return el("span",label,"chip "+(type||""));}
function renderItem(o){
 const item=el("article",undefined,"item");const main=el("div",undefined,"item-main"),left=el("div");
 const meta=el("div",undefined,"item-meta");meta.append(el("span",o.issuer||"Ente non specificato"));left.append(meta,el("h3",o.title||"Senza titolo"));
 const badges=el("div",undefined,"item-badges");const st=state(o);
 badges.append(chip(st==="chiuso"?"Chiuso / scaduto":st==="aperto"?"Segnalato aperto":"Stato da verificare",st==="chiuso"?"closed":st==="aperto"?"open":"unknown"));
 badges.append(chip(dateLabel(o.deadline)));
 badges.append(chip(o.opportunity_type||"Tipologia da verificare"));
 left.append(badges);
 const score=el("div",undefined,"item-score");score.append(el("strong",String(o.relevance??0)+"/100"),el("span","Pertinenza"));
 main.append(left,score);item.append(main);
 const actions=el("div",undefined,"item-actions");const broken=o.link_status==="non disponibile";
 if(!broken)addLink(actions,"Consulta la fonte ↗",o.resolved_url||o.url);
 else addLink(actions,"Pagina bandi dell'ente ↗",o.source_url);
 const detail=el("div",undefined,"item-details");detail.hidden=true;
 const detailsButton=el("button","Dettagli +","details-toggle");detailsButton.type="button";detailsButton.setAttribute("aria-expanded","false");
 detailsButton.addEventListener("click",()=>{detail.hidden=!detail.hidden;detailsButton.setAttribute("aria-expanded",String(!detail.hidden));detailsButton.textContent=detail.hidden?"Dettagli +":"Nascondi dettagli −";});
 actions.append(detailsButton);item.append(actions);
 detail.append(el("p","Ammissibilità: "+(o.eligibility||"da verificare")+" · Potenziale progettuale: "+(o.project_potential||"da valutare")));
 if(o.amount)detail.append(el("p","Importo indicativo: "+o.amount));
 if(o.beneficiaries_excerpt)detail.append(el("p","Beneficiari (estratto): "+o.beneficiaries_excerpt));
 if(o.type_reason)detail.append(el("p",o.type_reason));
 if(o.themes?.length)detail.append(el("p","Temi: "+o.themes.join(", ")));
 if(broken)detail.append(el("p","Il collegamento diretto risulta non disponibile (404/410).","linkwarn"));
 if(o.link_status!=="raggiungibile"&&!broken)detail.append(el("p","Collegamento non ancora verificato."));
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
function resetPagination(){visibleCount=PAGE_SIZE;render();}
async function init(){
 try{
  const [resp,report]=await Promise.all([fetch("data/opportunities.json",{cache:"no-store"}),fetch("data/scan-status.json",{cache:"no-store"})]);
  if(!resp.ok||!report.ok)throw Error("Impossibile caricare i dati");
  all=await resp.json();const status=await report.json();
  $("total").textContent=all.length;$("potential").textContent=all.filter(o=>["finanziamento potenziale","call progettuale da verificare"].includes(o.opportunity_type)).length;
  $("high").textContent=all.filter(o=>Number(o.relevance)>=60).length;
  $("sources").textContent=(status.sources||[]).filter(o=>o.ok).length+"/"+(status.sources||[]).length;
  $("scan").textContent=status.checked_at?"Aggiornato il "+new Date(status.checked_at).toLocaleString("it-IT",{dateStyle:"short",timeStyle:"short"})+" · "+(status.sources||[]).filter(o=>!o.ok).length+" fonti con anomalie":"Prima scansione non ancora effettuata";
  for(const name of [...new Set(all.map(o=>o.issuer).filter(Boolean))].sort((a,b)=>a.localeCompare(b,"it"))){const option=el("option",name);option.value=name;$("issuer").append(option);}
  render();
 }catch(err){$("scan").textContent="Dati non disponibili";$("items").replaceChildren(el("p",err.message,"empty"));}
}
for(const id of ["search","status","kind","issuer","level","sort"])$(id).addEventListener(id==="search"?"input":"change",resetPagination);
$("reset").addEventListener("click",()=>{$("search").value="";$("status").value="active";$("kind").value="";$("issuer").value="";$("level").value="0";$("sort").value="priority";resetPagination();});
$("more").addEventListener("click",()=>{visibleCount+=PAGE_SIZE;render();});
init();
