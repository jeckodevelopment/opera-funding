const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const src = fs.readFileSync("web/app.js","utf8");
const context = {
  document: {getElementById:()=>({addEventListener(){}}),querySelectorAll:()=>[]},
  URL, Date, console
};
vm.runInNewContext(src.replace(/\ninit\(\);\s*$/, "\n") + "\nglobalThis.exposed = {state, dateLabel, sortRows, safeUrl, PAGE_SIZE, sourceHealth};", context);
const {state, dateLabel, sortRows, safeUrl, PAGE_SIZE, sourceHealth} = context.exposed;
assert.equal(state({status:"aperto (fonte indice)",deadline:"2025-05-01"}),"chiuso");
assert.equal(state({status:"non verificato"}),"non verificato");
assert.equal(state({status:"aperto (fonte indice)",deadline:"2027-02-15",source_open_confirmed:true,link_status:"raggiungibile"}),"aperto");
assert.equal(state({status:"aperto (fonte indice)",deadline:"2027-02-15",source_open_confirmed:false,link_status:"raggiungibile"}),"non verificato");
assert.equal(state({status:"aperto (fonte indice)",deadline:"2027-02-15",source_open_confirmed:true,link_status:"da verificare"}),"non verificato");
assert.equal(state({opening_date:"2027-03-01",opening_evidence:"https://example.org/bando"}),"in arrivo");
assert.equal(dateLabel("2027-04-05"),"Scade il 05/04/2027");
assert.equal(PAGE_SIZE,20);
const records = [{title:"older",relevance:99,status:"chiuso",deadline:"2025-05-01"}, {title:"current",relevance:60,status:"non verificato"}];
assert.equal(sortRows(records,"priority")[0].title,"current");
const upcoming=[
 {title:"later",source_open_confirmed:true,deadline:"2027-05-20",link_status:"raggiungibile",relevance:95},
 {title:"earlier",source_open_confirmed:true,deadline:"2027-01-05",link_status:"raggiungibile",relevance:30},
 {title:"unknown",relevance:100,status:"non verificato"},
 {title:"closed",relevance:100,deadline:"2025-01-01"}
];
assert.deepEqual(Array.from(sortRows(upcoming,"priority"),x=>x.title),["earlier","later","unknown","closed"]);
assert.equal(safeUrl("javascript:alert(1)"),null);
const html=fs.readFileSync("web/index.html","utf8");
const css=fs.readFileSync("web/styles.css","utf8");
for (const key of ["search","status","kind","issuer","level","sort","reset","more","items"]) {
  assert.match(html,new RegExp('id="'+key+'"'));
}
assert.match(html,/operaplus-logo\.png/);
assert.match(css,/color-scheme:light/);
assert.match(css,/\.chip\.status\.open\{/);
assert.match(css,/\.chip\.status\.closed\{/);
assert.match(css,/\.chip\.status\.unknown\{/);
assert.match(css,/\.chip\.status\.upcoming\{/);
assert.match(css,/max-width:102px!important/);
assert.match(html,/data-value="aperto"/);
assert.match(html,/data-value="chiuso"/);
assert.match(html,/aria-pressed="true"/);
assert.match(html,/id="health-dot"/);
assert.match(html,/id="source-incidents"/);
assert.equal(sourceHealth({sources:[{ok:true},{ok:true}]},[]).level,"green");
assert.equal(sourceHealth({sources:[{ok:false,source_id:"a",error:"HTTP 500"},{ok:true},{ok:true},{ok:true}]},[]).level,"red"); // 25% missing
assert.equal(sourceHealth({sources:[{ok:false,source_id:"a",error:"HTTP 500"},...Array(5).fill({ok:true})]},[]).level,"yellow");
assert.equal(sourceHealth({sources:[{ok:false},{ok:false},{ok:false},{ok:true}]},[]).level,"red");
assert.equal(sourceHealth({sources:[{ok:false,source_id:"piemonte",source_name:"Regione Piemonte",error:"Errore"}]},[]).incidents[0].name,"Regione Piemonte");
assert.equal(sourceHealth({sources:[{ok:true,source_id:"eufunding",discovered:0},{ok:true,discovered:3},{ok:true,discovered:7},{ok:true,discovered:2},{ok:true,discovered:6}]},[]).level,"yellow");
assert.equal(sourceHealth({sources:[{ok:true,source_id:"eufunding",discovered:0},{ok:true,discovered:0},{ok:true,discovered:0},{ok:true,discovered:0},{ok:true,discovered:2}]},[]).level,"red");
assert.match(sourceHealth({sources:[{ok:true,source_id:"eufunding",discovered:0}]},[]).incidents[0].reason,/Nessuna opportunità/);
assert.doesNotMatch(src,/Controlli prima della candidatura:/);
assert.doesNotMatch(html,/DA VERIFICARE/);
console.log("Dashboard UX regression checks passed");
