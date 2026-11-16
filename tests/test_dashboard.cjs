const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const src = fs.readFileSync("web/app.js","utf8");
const context = {
  document: {getElementById:()=>({addEventListener(){}})},
  URL, Date, console
};
vm.runInNewContext(src.replace(/\ninit\(\);\s*$/, "\n") + "\nglobalThis.exposed = {state, dateLabel, sortRows, safeUrl, PAGE_SIZE};", context);
const {state, dateLabel, sortRows, safeUrl, PAGE_SIZE} = context.exposed;
assert.equal(state({status:"aperto (fonte indice)",deadline:"2025-05-01"}),"chiuso");
assert.equal(state({status:"non verificato"}),"non verificato");
assert.equal(dateLabel("2027-04-05"),"Scade il 05/04/2027");
assert.equal(PAGE_SIZE,20);
const records = [{title:"older",relevance:99,status:"chiuso",deadline:"2025-05-01"}, {title:"current",relevance:60,status:"non verificato"}];
assert.equal(sortRows(records,"priority")[0].title,"current");
assert.equal(safeUrl("javascript:alert(1)"),null);
const html=fs.readFileSync("web/index.html","utf8");
const css=fs.readFileSync("web/styles.css","utf8");
for (const key of ["search","status","kind","issuer","level","sort","reset","more","items"]) {
  assert.match(html,new RegExp('id="'+key+'"'));
}
assert.match(html,/operaplus-logo\.png/);
assert.match(css,/max-width:104px!important/);
console.log("Dashboard UX regression checks passed");
