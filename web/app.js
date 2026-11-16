const $=id=>document.getElementById(id);
let all=[];
const safeUrl=v=>{try{const u=new URL(v);return u.protocol==="https:"?u.href:null}catch{return null}};
function textNode(tag,content,cls){const e=document.createElement(tag);e.textContent=content??"";if(cls)e.className=cls;return e}
function render(){
 const q=$("search").value.toLowerCase().trim(),min=Number($("level").value),issuer=$("issuer").value,kind=$("kind").value,status=$("status").value;
 const rows=all.filter(x=>(!issuer||x.issuer===issuer)&&(!kind||(x.opportunity_type||"non classificato")===kind)&&(!status||(x.status||"non verificato").startsWith(status))&&Number(x.relevance||0)>=min&&[x.title,x.issuer,...(x.themes||[])].join(" ").toLowerCase().includes(q));
 $("items").replaceChildren();
 if(!rows.length){$("items").append(textNode("p",all.length?"Nessun risultato per i filtri selezionati.":"Nessuna opportunità rilevata: controlla lo stato delle fonti.","hint"));return}
 for(const o of rows){
  const card=textNode("article","","item"),top=textNode("div","","itemtop"),left=textNode("div");
  left.append(textNode("h2",o.title||"Senza titolo"),textNode("div",o.issuer||"Ente sconosciuto","meta"));
  top.append(left,textNode("span",String(o.relevance??0)+"/100","score"));card.append(top);
  const tags=textNode("div","","tags");
  const fields=["Tipologia: "+(o.opportunity_type||"da classificare"),"Stato: "+(o.status||"non verificato"),"Scadenza: "+(o.deadline?new Date(o.deadline+"T12:00:00").toLocaleDateString("it-IT"):"da verificare"),"Ammissibilità: "+(o.eligibility||"da verificare"),...(o.amount?["Importo: "+o.amount]:[]),...(o.themes||[])];
  for(const tag of fields)tags.append(textNode("span",tag,"tag"));card.append(tags);
  card.append(textNode("p",(o.type_reason||"Tipologia da verificare")+" · Pertinenza preliminare, non probabilità di finanziamento","warn"));
  const broken=o.link_status==="non disponibile";
  const url=!broken&&safeUrl(o.resolved_url||o.url);
  if(url){const a=textNode("a","Consulta la fonte ↗");a.href=url;a.target="_blank";a.rel="noopener noreferrer";card.append(a)}
  if(broken){card.append(textNode("p","Il collegamento diretto restituisce 404/410: consulta l'ente o la pagina indice.","linkwarn"));
    const fallback=safeUrl(o.source_url);if(fallback){const link=textNode("a","Pagina bandi dell'ente ↗","sourcefallback");link.href=fallback;link.target="_blank";link.rel="noopener noreferrer";card.append(link)}
  }
  if(Array.isArray(o.documents)&&o.documents.length>1){const docs=textNode("div","","docs");for(const d of o.documents.slice(1,8)){const link=safeUrl(d.url);if(!link)continue;const a=textNode("a",(d.label||"Documento")+" ↗");a.href=link;a.target="_blank";a.rel="noopener noreferrer";docs.append(a)}card.append(docs)}
  $("items").append(card);
 }
}
async function init(){
 try{
  const [a,b]=await Promise.all([fetch("data/opportunities.json",{cache:"no-store"}),fetch("data/scan-status.json",{cache:"no-store"})]);
  if(!a.ok||!b.ok)throw Error("Dati non disponibili");
  all=await a.json();const status=await b.json();
  $("total").textContent=all.length;$("high").textContent=all.filter(x=>x.relevance>=60).length;
  $("sources").textContent=(status.sources||[]).filter(x=>x.ok).length+"/"+(status.sources||[]).length;
  $("scan").textContent=status.checked_at?"Ultima scansione: "+new Date(status.checked_at).toLocaleString("it-IT")+" · "+(status.sources||[]).filter(x=>!x.ok).length+" fonti con anomalie":"Prima scansione non ancora eseguita";
  for(const name of [...new Set(all.map(o=>o.issuer))].sort()){const opt=document.createElement("option");opt.value=name;opt.textContent=name;$("issuer").append(opt)}
  render();
 }catch(e){$("scan").textContent="Errore nel caricamento: "+e.message;$("items").replaceChildren(textNode("p","La dashboard non può mostrare dati aggiornati.","warn"))}
}
for(const id of ["search","level","issuer","kind","status"])$(id).addEventListener(id==="search"?"input":"change",render);
init();
