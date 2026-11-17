const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const src=fs.readFileSync("web/app.js","utf8").replace(/\ninit\(\);\s*$/,"\n");
const context={
 document:{getElementById:()=>({addEventListener(){}}),querySelectorAll:()=>[]},
 URL,Date,console
};
vm.runInNewContext(src+"\nglobalThis.exposed={state,dateLabel,sortRows,sourceHealth,opportunitySummary,safeUrl,PAGE_SIZE,statusLabel,updateStateCounts,reviewSignals,changeBadge};",context);
const {state,dateLabel,sortRows,sourceHealth,opportunitySummary,safeUrl,PAGE_SIZE,statusLabel,updateStateCounts,reviewSignals,changeBadge}=context.exposed;
assert.equal(PAGE_SIZE,12);
const now=new Date("2026-11-20T08:00:00Z");
assert.equal(changeBadge({catalog_new_at:"2026-11-18T07:00:00Z"},now).label,"NUOVA");
assert.equal(changeBadge({catalog_updated_at:"2026-11-18T07:00:00Z"},now).label,"AGGIORNATA");
assert.equal(changeBadge({catalog_new_at:"2026-11-18T07:00:00Z",catalog_updated_at:"2026-11-19T07:00:00Z"},now).label,"NUOVA");
assert.equal(changeBadge({first_seen:"2026-11-18T07:00:00Z"},now),null);
assert.equal(changeBadge({catalog_updated_at:"2026-11-10T07:00:00Z"},now),null);
assert.equal(changeBadge({catalog_new_at:"2026-11-22T07:00:00Z"},now),null);

const incomplete=reviewSignals({title:"Bando culturale",relevance:35,eligibility:"da verificare",
 score_explanation:"Affinità preliminare con formazione",eligibility_checks:["Verificare beneficiari"]});
assert.ok(incomplete.missing.some(x=>x.includes("Beneficiari")));
assert.ok(incomplete.missing.some(x=>x.includes("Scadenza")));
assert.equal(incomplete.eligibility,"da verificare");
assert.equal(incomplete.checks[0],"Verificare beneficiari");
assert.equal(incomplete.explanation,"Affinità preliminare con formazione");
const complete=reviewSignals({beneficiaries_excerpt:"ETS",amount:"10.000 euro",deadline:"2027-04-01",
 link_status:"raggiungibile",eligibility_checks:[]});
assert.equal(complete.missing.length,0);
assert.equal(state({opportunity_type:"finanziamento potenziale",relevance:0}),"non verificato");

assert.equal(statusLabel("aperto"),"APERTA");
assert.equal(statusLabel("chiuso"),"SCADUTA");
assert.equal(statusLabel("in arrivo"),"IN ARRIVO");
assert.equal(statusLabel("altro contenuto"),"ALTRO CONTENUTO");
assert.equal(state({opportunity_type:"altro avviso",title:"Archived news"}),"altro contenuto");
assert.equal(state({opportunity_type:"non classificato",title:"Guidance"}),"altro contenuto");
assert.equal(state({opportunity_type:"finanziamento potenziale",title:"Grant"}),"non verificato");
assert.equal(state({opportunity_type:"call progettuale da verificare",title:"Call"}),"non verificato");

assert.equal(dateLabel("2027-04-05"),"Scade il 05/04/2027");
assert.equal(state({deadline:"2025-10-05",source_open_confirmed:true,link_status:"raggiungibile"}),"chiuso");
assert.equal(state({deadline:"2027-01-03",source_open_confirmed:true,link_status:"raggiungibile"}),"aperto");
assert.equal(state({opportunity_type:"finanziamento potenziale",deadline:"2027-01-03",source_open_confirmed:false,link_status:"raggiungibile"}),"non verificato");
assert.equal(state({opening_date:"2027-02-01",opening_evidence:"https://example.org/call"}),"in arrivo");
const rows=[
 {title:"Tardi",relevance:97,deadline:"2027-06-01",source_open_confirmed:true,link_status:"raggiungibile"},
 {title:"Presto",relevance:70,deadline:"2027-01-02",source_open_confirmed:true,link_status:"raggiungibile"},
 {title:"Alto",relevance:99,deadline:"2027-04-02",source_open_confirmed:true,link_status:"raggiungibile"}
];
assert.deepEqual(Array.from(sortRows([...rows],"deadline"),x=>x.title),["Presto","Alto","Tardi"]);
assert.deepEqual(Array.from(sortRows([...rows],"score"),x=>x.title),["Alto","Tardi","Presto"]);
assert.equal(sourceHealth({sources:[{ok:true,discovered:0},{ok:true,discovered:0}]},[]).level,"green");
assert.equal(sourceHealth({sources:[{ok:false,source_name:"Desk Italia",error:"robots"},{ok:true},{ok:true},{ok:true},{ok:true}]},[]).level,"yellow");
assert.equal(sourceHealth({sources:[{ok:false},{ok:false},{ok:false},{ok:true},{ok:true}]},[]).level,"red");
assert.equal(sourceHealth({sources:[{ok:false,source_name:"Desk Italia",error:"robots"}]},[]).incidents[0].name,"Desk Italia");
assert.equal(safeUrl("javascript:alert(1)"),null);
assert.match(opportunitySummary({title:"X",opportunity_type:"finanziamento potenziale",themes:["musica"]}),/musica/);
const html=fs.readFileSync("web/index.html","utf8");
const css=fs.readFileSync("web/styles.css","utf8");
for(const id of ["status","search","issuer","kind","level","sort","reset","more","items","health-dot","source-incidents","total","potential","high","sources"])assert.match(html,new RegExp('id="'+id+'"'));
assert.match(html,/assets\/operaplus-logo\.png/);
assert.match(html,/>Aperte<\/button>/);
assert.match(html,/>Scadute<\/button>/);
assert.match(html,/data-value="altro contenuto"/);
assert.match(html,/<input id="status" type="hidden" value="aperto">/);
assert.match(html,/<button class="quick-tab active" type="button" data-value="aperto" aria-pressed="true">Aperte<\/button>/);
assert.match(src,/updateStateCounts\(\)/);
assert.match(src,/\$\("status"\)\.value="aperto";\$\("sort"\)\.value="deadline";/);

assert.match(html,/data-sort="deadline"/);
assert.match(html,/data-sort="score"/);
assert.match(html,/<option value="">Tutte le tipologie<\/option>/);
assert.ok(html.indexOf('<option value="">Tutte le tipologie</option>')<html.indexOf('<option value="funding">Finanziamenti e call</option>'));
assert.match(src,/\$\("kind"\)\.value="";/);
assert.match(css,/\.calendar-month/);
assert.match(css,/\.adequacy-track/);
assert.match(css,/\.adequacy-mask/);
assert.match(css,/\.opportunity-dialog/);
assert.match(css,/\.evidence-review/);
assert.match(src,/content.append\(evidenceSection\(o\)\)/);
assert.match(html,/id="opportunity-dialog"/);
assert.match(html,/id="dialog-close"/);
assert.match(src,/function openDetails/);
assert.match(src,/Possibile opportunità a sportello/);
assert.match(src,/Natura dell’importo/);
assert.match(css,/\.rolling-guidance/);
assert.match(css,/\.chip\.change/);
assert.match(src,/changeBadge\(o\)/);
assert.match(src,/function makeAdequacy/);
assert.match(css,/\.health-dot\.red/);
assert.doesNotMatch(src,/Controlli prima della candidatura:/);
console.log("Opera+ editorial dashboard tests passed");
