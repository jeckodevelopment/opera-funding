const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const src=fs.readFileSync("web/app.js","utf8").replace(/\ninit\(\);\s*$/,"\n");
const context={
 document:{getElementById:()=>({addEventListener(){}}),querySelectorAll:()=>[]},
 URL,Date,console
};
vm.runInNewContext(src+"\nglobalThis.exposed={state,dateLabel,sortRows,sourceHealth,opportunitySummary,safeUrl,PAGE_SIZE,statusLabel};",context);
const {state,dateLabel,sortRows,sourceHealth,opportunitySummary,safeUrl,PAGE_SIZE,statusLabel}=context.exposed;
assert.equal(PAGE_SIZE,12);
assert.equal(statusLabel("aperto"),"APERTA");
assert.equal(statusLabel("chiuso"),"SCADUTA");
assert.equal(statusLabel("in arrivo"),"IN ARRIVO");
assert.equal(dateLabel("2027-04-05"),"Scade il 05/04/2027");
assert.equal(state({deadline:"2025-10-05",source_open_confirmed:true,link_status:"raggiungibile"}),"chiuso");
assert.equal(state({deadline:"2027-01-03",source_open_confirmed:true,link_status:"raggiungibile"}),"aperto");
assert.equal(state({deadline:"2027-01-03",source_open_confirmed:false,link_status:"raggiungibile"}),"non verificato");
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
assert.match(html,/data-sort="deadline"/);
assert.match(html,/data-sort="score"/);
assert.match(css,/\.calendar-month/);
assert.match(css,/\.adequacy-track/);
assert.match(css,/\.adequacy-mask/);
assert.match(css,/\.opportunity-dialog/);
assert.match(html,/id="opportunity-dialog"/);
assert.match(html,/id="dialog-close"/);
assert.match(src,/function openDetails/);
assert.match(src,/function makeAdequacy/);
assert.match(css,/\.health-dot\.red/);
assert.doesNotMatch(src,/Controlli prima della candidatura:/);
console.log("Opera+ editorial dashboard tests passed");
