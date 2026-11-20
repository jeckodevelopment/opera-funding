const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const src=fs.readFileSync("web/app.js","utf8").replace(/\ninit\(\);\s*$/,"\n");
const context={
 document:{getElementById:()=>({addEventListener(){}}),querySelectorAll:()=>[]},
 URL,Date,console,window:{addEventListener(){}}
};
vm.runInNewContext(src+"\nglobalThis.exposed={state,dateLabel,sortRows,sourceHealth,opportunitySummary,safeUrl,PAGE_SIZE,statusLabel,updateStateCounts,reviewSignals,changeBadge,evaluationData,opportunityRequirementFacts,opportunityUrl,requestedOpportunity,findOpportunity,readWatchlist,isFollowed,cleanWorkflow,assessmentLabel,adequacyLevel,adequacyLabel,makeAdequacy,requirementChecklist,isRolling,matchesCatalogStatus};",context);
const {state,dateLabel,sortRows,sourceHealth,opportunitySummary,safeUrl,PAGE_SIZE,statusLabel,updateStateCounts,reviewSignals,changeBadge,evaluationData,opportunityRequirementFacts,opportunityUrl,requestedOpportunity,findOpportunity,readWatchlist,isFollowed,cleanWorkflow,assessmentLabel,adequacyLevel,adequacyLabel,makeAdequacy,requirementChecklist,isRolling,matchesCatalogStatus}=context.exposed;
assert.equal(PAGE_SIZE,12);
const sportello={opportunity_type:"finanziamento potenziale",rolling_confirmed:true,
 rolling_evidence:"https://example.org/call",source_open_confirmed:true,link_status:"raggiungibile"};
assert.equal(isRolling(sportello),true);
assert.equal(state(sportello),"aperto");
assert.equal(matchesCatalogStatus(sportello,"sportello"),true);
assert.equal(matchesCatalogStatus(sportello,"aperto"),true);
assert.equal(isRolling({...sportello,rolling_evidence:null}),false);
assert.equal(isRolling({...sportello,rolling_confirmed:false}),false);
assert.equal(isRolling({...sportello,opportunity_type:"altro avviso"}),false);
assert.equal(isRolling({...sportello,rolling_evidence:"javascript:alert(1)"}),false);
assert.equal(isRolling({...sportello,closure_confirmed:true}),true);
assert.equal(matchesCatalogStatus({...sportello,closure_confirmed:true},"sportello"),true);
assert.equal(matchesCatalogStatus({...sportello,closure_confirmed:true},"aperto"),false);
assert.match(src,/if\\(!matchesCatalogStatus\\(o,stateFilter\\)\\)return false;/);
assert.doesNotMatch(src,/stateFilter&&stateFilter!=="followed"&&actual!==stateFilter/);
assert.deepEqual(["aperto","sportello","chiuso"].map(filter=>
  matchesCatalogStatus(sportello,filter)),[true,true,false]);


assert.equal(assessmentLabel({assessment_label:"ALTA AFFINITÀ"}),"ALTA AFFINITÀ");
assert.equal(assessmentLabel({relevance:65,opportunity_type:"finanziamento potenziale"}),"MEDIA AFFINITÀ");
assert.equal(assessmentLabel({relevance:9,opportunity_type:"call progettuale da verificare"}),"BASSA AFFINITÀ");
assert.equal(assessmentLabel({relevance:90,opportunity_type:"altro avviso"}),"INFORMATIVA");
const workflowInput={phase:"Presentata",owner:"A".repeat(180),next_step:"Inviare allegati",due:"2027-02-28",notes:"Nota"}; 
const workflowClean=cleanWorkflow(workflowInput);
assert.equal(workflowClean.phase,"Presentata");
assert.equal(workflowClean.owner.length,120);
assert.equal(workflowClean.due,"2027-02-28");
assert.equal(cleanWorkflow({phase:"Impossibile",due:"non valido"}).phase,"Da esaminare");
assert.equal(cleanWorkflow({phase:"Da valutare"}).phase,"Da esaminare");
assert.equal(cleanWorkflow({due:"non valido"}).due,"");

const short=opportunityUrl({id:"https://volontariatotorino.it/bandi/dora",public_id:143},"https://jeckodevelopment.com/dev/funding/");
assert.equal(short,"https://jeckodevelopment.com/dev/funding/?opportunity=143");
assert.equal(requestedOpportunity(short),"143");
const catalog=[{id:"https://volontariatotorino.it/bandi/dora",public_id:143,title:"Dora"},
 {id:"https://example.org/other",public_id:144,alternative_urls:["https://example.org/old"]}];
assert.equal(findOpportunity("143",catalog).title,"Dora");
assert.equal(findOpportunity("https://volontariatotorino.it/bandi/dora",catalog).public_id,143);
assert.equal(findOpportunity("https://example.org/old",catalog).public_id,144);
assert.equal(findOpportunity("9999999",catalog),null);
assert.equal(findOpportunity("147",[{id:"official",public_id:32,public_id_aliases:[147],title:"Culture Moves"}]).title,"Culture Moves");
assert.equal(findOpportunity("143foo",catalog),null);

assert.equal(readWatchlist().size,0);
assert.equal(isFollowed({id:"https://example.org/call"}),false);

const id="https://example.org/call?id=32&mode=it#window=1";
const shared=opportunityUrl(id,"https://jeckodevelopment.com/dev/funding/?campaign=old");
assert.equal(requestedOpportunity(shared),id);
assert.ok(shared.startsWith("https://jeckodevelopment.com/dev/funding/?"));
assert.equal(new URL(shared).searchParams.get("campaign"),"old");
assert.equal(requestedOpportunity("https://jeckodevelopment.com/dev/funding/"),null);
assert.equal(requestedOpportunity("https://jeckodevelopment.com/dev/funding/?opportunity="+"x".repeat(2501)),null);

const evaluation=evaluationData({
 title:"Contributo educativo",issuer:"Fondazione Esempio",relevance:72,
 opportunity_type:"finanziamento potenziale",eligibility:"da verificare",
 deadline:"2027-03-12",amount:"€ 50.000 (da verificare)",amount_kind:"dotazione finanziaria",
 beneficiaries_excerpt:"ETS iscritti al registro",
 score_explanation:"Coerenza con formazione e giovani (scheda).",
 score_confidence:"indicativa",score_explanation_basis:"titolo e scheda",
 eligibility_checks:["Verificare sede legale"],
 documents:[
  {label:"Avviso",url:"https://example.org/bando.pdf"},
  {label:"Link malevolo",url:"javascript:alert(1)"},
  {label:"Duplicato",url:"https://example.org/bando.pdf"}
 ],
 url:"https://example.org/opportunita"
},new Date("2026-11-17T12:00:00Z"));
assert.equal(evaluation.fit,"64%");
assert.equal(evaluation.deadline,"12/03/2027");
assert.equal(evaluation.eligibility,"da verificare");
assert.equal(evaluation.amountKind,"dotazione finanziaria");
assert.equal(evaluation.checks[0],"Verificare sede legale");
assert.equal(evaluation.reasoning,"Coerenza con formazione e giovani (scheda).");
const detailInput={
 title:"Bando pilota",url:"https://example.org/opportunity",relevance:62,
 opportunity_type:"finanziamento potenziale",
 programme_objectives_excerpt:"Sostenere la cultura nelle scuole",
 funded_activities_excerpt:"Laboratori e attività musicali",
 beneficiaries_excerpt:"Associazioni culturali",
 requirements_excerpt:"Partenariato scolastico obbligatorio",
 funding_scope_note:"Progetti con impatto regionale",
 opening_date:"2026-11-15",amount_kind:"contributo massimo",
 edition_year:"2027",window_label:"Prima finestra",
 application_windows:["2027-03-01","2027-05-15"],
 rolling_guidance:"Presentazione continuativa",
 assessment_review_status:"PARZIALE",
 assessment_method:"Revisione documentale automatica",
 adequacy_reason:"Compatibile, con partenariato richiesto",
 assessment_gaps:["Confermare la sede del partner"]
};
const detailFacts=opportunityRequirementFacts(detailInput);
const fullReport=evaluationData(detailInput,new Date("2026-11-18T12:00:00Z"));
assert.equal(fullReport.requirementFacts.length,detailFacts.length);
for(const [label,value] of detailFacts){
 const fact=fullReport.requirementFacts.find(x=>x.label===label);
 assert.ok(fact,"Campo mancante nel PDF: "+label);
 assert.equal(fact.value,String(value));
}
assert.equal(fullReport.requirementFacts.find(x=>x.label==="Attività finanziabili").value,"Laboratori e attività musicali");
assert.equal(fullReport.requirementFacts.find(x=>x.label==="Vincoli e requisiti").value,"Partenariato scolastico obbligatorio");
assert.ok(fullReport.requirementFacts.some(x=>x.label==="Finestre successive"&&x.value.includes("15/05/2027")));
assert.equal(fullReport.adequacyReason,"Compatibile, con partenariato richiesto");
assert.equal(fullReport.assessmentGaps[0],"Confermare la sede del partner");
assert.equal(evaluationData({title:"Incomplete"},new Date("2026-11-18T12:00:00Z")).requirementFacts.length,0);
assert.match(src,/for\(const fact of d\.requirementFacts\)addReportFact\(detailFacts,fact\.label,fact\.value\)/);
assert.match(src,/print-conditions/);
assert.match(fs.readFileSync("web/styles.css","utf8"),/\.print-detail-facts/);

assert.equal(evaluation.links.length,2);
assert.ok(evaluation.links.every(x=>x.href.startsWith("https://")));
const incompleteEvaluation=evaluationData({title:"Avviso",opportunity_type:"call progettuale da verificare",relevance:10},new Date("2026-11-17T12:00:00Z"));
assert.equal(incompleteEvaluation.deadline,"Non indicata");
assert.ok(incompleteEvaluation.missing.some(x=>x.includes("Beneficiari")));
assert.equal(incompleteEvaluation.eligibility,"da verificare");
assert.equal(incompleteEvaluation.fit,"5%");

const now=new Date("2026-11-20T08:00:00Z");
assert.equal(changeBadge({catalog_new_at:"2026-11-18T07:00:00Z"},now).label,"NUOVA");
assert.equal(changeBadge({catalog_updated_at:"2026-11-18T07:00:00Z",catalog_tracking_version:3},now).label,"AGGIORNATA");
assert.equal(changeBadge({catalog_updated_at:"2026-11-18T07:00:00Z",catalog_tracking_version:1},now),null);
assert.equal(changeBadge({catalog_updated_at:"2026-11-18T07:00:00Z",catalog_tracking_version:2},now),null);
assert.equal(changeBadge({catalog_new_at:"2026-11-18T07:00:00Z",catalog_updated_at:"2026-11-19T07:00:00Z",catalog_tracking_version:3},now).label,"NUOVA");
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
assert.equal(statusLabel("non verificato"),"APERTURA DA VERIFICARE");
assert.equal(state({opportunity_type:"altro avviso",title:"Archived news"}),"altro contenuto");
assert.equal(state({opportunity_type:"non classificato",title:"Guidance"}),"non verificato");
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
assert.deepEqual(Array.from(sortRows([...rows],"score"),x=>x.title),["Presto","Alto","Tardi"]);
assert.equal(sourceHealth({sources:[{ok:true,discovered:0},{ok:true,discovered:0}]},[]).level,"green");
assert.equal(sourceHealth({sources:[{ok:false,source_name:"Desk Italia",error:"robots"},{ok:true},{ok:true},{ok:true},{ok:true}]},[]).level,"yellow");
assert.equal(sourceHealth({sources:[{ok:false},{ok:false},{ok:false},{ok:true},{ok:true}]},[]).level,"red");
assert.equal(sourceHealth({sources:[{ok:false,source_name:"Desk Italia",error:"robots"}]},[]).incidents[0].name,"Desk Italia");
const blocked=sourceHealth({sources:[{ok:false,source_id:"alcotra",source_name:"Interreg ALCOTRA",error:"robots.txt non raggiungibile; verifica automatica non disponibile",institutional_reference_url:"https://www.regione.piemonte.it/alcotra",institutional_reference_label:"Regione Piemonte",coverage_note:"Storico conservato"}]},[]);
assert.equal(blocked.incidents[0].referenceLabel,"Regione Piemonte");
assert.equal(blocked.incidents[0].coverageNote,"Storico conservato");
assert.equal(safeUrl("javascript:alert(1)"),null);
assert.match(opportunitySummary({title:"X",opportunity_type:"finanziamento potenziale",themes:["musica"]}),/musica/);
const html=fs.readFileSync("web/index.html","utf8");
const css=fs.readFileSync("web/styles.css","utf8");
for(const id of ["status","search","issuer","kind","level","sort","reset","more","items","health-dot","source-incidents","total","potential","high","sources"])assert.match(html,new RegExp('id="'+id+'"'));
assert.match(html,/assets\/operaplus-logo\.png/);
for(const view of ["dashboard","finanziatori","monitoraggio"])assert.match(html,new RegExp('data-view="'+view+'"'));
assert.match(src,/function renderMainView\(href\)/);
assert.match(src,/function activeView\(href\)/);
assert.match(html,/<section class="funding-registry" id="finanziatori"[^>]*hidden/);
assert.match(html,/<section class="funding-registry" id="monitoraggio-programmi"[^>]*hidden/);
for(const id of ["finanziatori","monitoraggio-programmi","funder-search","funder-list","programme-list"])assert.match(html,new RegExp('id="'+id+'"'));
assert.match(src,/function renderFundingRegistry\(status\)/);
assert.match(src,/function registryTable\(headers\)/);
assert.match(src,/registryTable\(\["Finanziatore","Tipologia","Territorio","Programmi","Fonte"\]\)/);
assert.match(src,/registryTable\(\["Programma","Finanziatore","Stato","Ultima verifica","Fonte"\]\)/);
assert.match(src,/reference_only:"Solo riferimento"/);
assert.match(css,/\.registry-table/);
assert.doesNotMatch(css,/\.registry-scroll\{[^}]*overflow-x:auto/);
assert.match(css,/\.registry-table-wrap/);
assert.match(css,/@media\(max-width:640px\)/);
assert.match(css,/\.registry-table tbody tr\{display:block/);
assert.match(css,/overflow-wrap:anywhere/);
assert.match(src,/registry\.funders/);
assert.match(src,/not_configured/);
assert.match(css,/\.registry-list/);
assert.match(html,/app\.js\?v=20261120-rolling/);
assert.match(html,/styles\.css\?v=20261118-11/);
assert.match(src,/function fetchWithDeadline/);
assert.match(src,/loadSequence/);
assert.match(html,/>Aperte<\/button>/);
assert.match(html,/>Scadute<\/button>/);
assert.match(html,/data-value="altro contenuto"/);
assert.match(html,/<input id="status" type="hidden" value="aperto">/);
assert.match(html,/<button class="quick-tab active" type="button" data-value="aperto" aria-pressed="true">Aperte<\/button>/);
assert.match(src,/updateStateCounts\(\)/);
assert.match(src,/tab\.hidden=number===0/);
assert.match(src,/tab\.hidden=false/);
assert.match(css,/\.quick-tab\[hidden\]/);
assert.match(src,/\$\("status"\)\.value="aperto";\$\("sort"\)\.value="deadline";/);

assert.match(html,/data-sort="deadline"/);
assert.match(html,/data-sort="score"/);
assert.match(html,/<option value="">Tutte le tipologie<\/option>/);
assert.ok(html.indexOf('<option value="">Tutte le tipologie</option>')<html.indexOf('<option value="funding">Finanziamenti e call</option>'));
assert.match(src,/\$\("kind"\)\.value="";/);
assert.match(css,/\.calendar-month/);
assert.match(css,/\.adequacy-track/);
assert.match(css,/\.adequacy-fill/);
assert.match(css,/\.opportunity-page/);
assert.match(css,/\.evidence-review/);
assert.match(src,/content.append\(evidenceSection\(o\)\)/);
assert.match(html,/id="opportunity-page"/);
assert.match(html,/data-value="followed"/);
assert.match(html,/>Apertura da verificare<\/button>/);
assert.doesNotMatch(html,/>Da approfondire<\/button>/);
assert.match(src,/function workflowForm\(o\)/);
assert.match(src,/function saveWorkflow\(o,record\)/);
assert.match(src,/WORKFLOW_PHASES/);
assert.match(src,/localStorage\.setItem\(WORKFLOW_KEY/);
assert.match(css,/\.workflow-form/);
assert.match(css,/\.chip\.assessment/);

assert.match(html,/id="followed-note"/);
assert.match(src,/function toggleFollowed/);
assert.match(src,/WATCHLIST_KEY/);
assert.match(src,/localStorage\.setItem/);
assert.match(css,/\.follow-button/);

assert.match(html,/id="dialog-close"/);
assert.match(src,/function renderOpportunity/);
assert.match(src,/window\.history\.pushState/);
assert.match(src,/popstate/);
assert.match(src,/Copia link della scheda/);
assert.match(src,/titleLink\.href=opportunityUrl\(o\)/);
assert.match(src,/detailLink\.href=opportunityUrl\(o\)/);
assert.match(src,/window\.history\.replaceState/);
assert.match(css,/\.item-title-link/);

assert.match(src,/detailLink\.href=opportunityUrl\(o\)/);
assert.doesNotMatch(src,/detailLink\.addEventListener\("click"/);
assert.match(css,/\.item-actions a\.details-toggle\{display:inline-flex/);

assert.match(src,/Procedura a sportello/);
assert.match(src,/Natura dell’importo/);
assert.match(css,/\.rolling-guidance/);
assert.match(css,/\.chip\.change/);
assert.match(html,/id="print-sheet"/);
assert.match(src,/function prepareEvaluationSheet/);
assert.match(src,/window.print\(\)/);
assert.match(src,/afterprint/);
assert.match(src,/Esporta PDF/);
assert.match(css,/@page\{size:A4/);
assert.match(css,/@media print/);
assert.match(css,/#print-sheet:not\(\[hidden\]\)/);

assert.match(src,/changeBadge\(o\)/);
assert.equal(adequacyLevel({assessment_label:"ALTA AFFINITÀ"}),2);
assert.equal(adequacyLevel({adequacy_level:3}),3);
assert.equal(adequacyLabel({adequacy_level:1}),"BASSA");
assert.equal(adequacyLabel({adequacy_level:0}),"INFORMATIVA");
assert.doesNotMatch(src,/tags\.append\(el\("span",assessmentLabel\(o\)/);
assert.doesNotMatch(src,/line\.append\(el\("span",assessmentLabel\(o\)/);
assert.match(src,/section\.append\(el\("h3","Adeguatezza per Opera\+"\),makeAdequacy\(o\)\)/);
assert.match(src,/Adeguatezza per Opera\+/);
assert.match(src,/detailDisclosure\("Documenti e fonti ufficiali"/);
assert.match(src,/detailDisclosure\("Come è stata calcolata l’adeguatezza\?"/);
assert.doesNotMatch(src,/dialogField\(dl,"Vincoli dell’adeguatezza"/);
assert.doesNotMatch(src,/dialogField\(dl,"Motivo della valutazione"/);
assert.match(src,/article\.append\(left,right,makeAdequacy\(o\)\)/);
assert.doesNotMatch(src,/dialogField\(dl,"Adeguatezza tematica"/);
assert.match(src,/function makeAdequacy/);
assert.match(src,/function requirementChecklist\(o\)/);
assert.match(src,/function requirementAccordion\(o\)/);
assert.match(src,/content\.append\(requirementAccordion\(o\),actions,workflowForm\(o\)\)/);
assert.match(css,/\.requirements-checklist/);
assert.match(css,/\.requirement-item\.risk/);
const evidenceCases=[
 {input:{applicant_requirement_comparison:[
  {category:"territorio",status:"compatibile",requirement:"Sede in Piemonte",source:"https://example.org/a",reason:"Sede verificata"},
  {category:"anzianita",status:"potenzialmente_incompatibile",requirement:"Almeno tre anni",reason:"Data da controllare"},
  {category:"partenariato",status:"da_verificare",source:"javascript:alert(1)",reason:"Partner da trovare"}
 ]},expected:{verified:1,risk:1,pending:1}},
 {input:{direct_application_blocker:"RUNTS richiesto per capofila"},expected:{verified:0,risk:1,pending:0}},
 {input:{},expected:{verified:0,risk:0,pending:0}}
];
for(const entry of evidenceCases){
 const result=requirementChecklist(entry.input);
 assert.equal(result.counts.verified,entry.expected.verified);
 assert.equal(result.counts.risk,entry.expected.risk);
 assert.equal(result.counts.pending,entry.expected.pending);
 if(entry.input.applicant_requirement_comparison){
  assert.equal(result.items[2].source,null);
 }
}

assert.match(css,/\.health-dot\.red/);
assert.doesNotMatch(src,/Controlli prima della candidatura:/);
console.log("Opera+ editorial dashboard tests passed");

// The public PDF must not expose internal method/coverage metadata.
const printableSource=src.slice(src.indexOf("function prepareEvaluationSheet(o){"),src.indexOf("function printEvaluation(o){"));
assert.doesNotMatch(printableSource,/Copertura documentale:/);
assert.doesNotMatch(printableSource,/Elementi utilizzati:/);
assert.doesNotMatch(printableSource,/d\.methodology|d\.coverage|d\.basis/);
assert.match(printableSource,/d\.adequacyReason/);
assert.match(printableSource,/print-disclaimer/);
