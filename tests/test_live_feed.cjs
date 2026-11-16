const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const source=fs.readFileSync("web/app.js","utf8").replace(/\ninit\(\);\s*$/,"\n");
async function scenario(remoteAvailable){
 const calls=[];
 const context={
  URL,Date,console,
  document:{getElementById:()=>({addEventListener(){}}),querySelectorAll:()=>[]},
  fetch:async (url,opts)=>{
   calls.push({url,opts});
   if(url.startsWith("https://raw.githubusercontent.com/")&&!remoteAvailable)throw Error("network/CORS");
   const value=url.endsWith("opportunities.json")?[]:{checked_at:"2026-11-16T19:00:00Z",sources:[]};
   return {ok:true,json:async()=>value};
  }
 };
 vm.runInNewContext(source+"\nglobalThis.getFeed=loadDataset;",context);
 const result=await context.getFeed();
 assert.equal(result.origin,remoteAvailable?"github":"local");
 assert.equal(result.opportunities.length,0);
 assert.equal(result.status.sources.length,0);
 assert.equal(calls.length,remoteAvailable?2:4);
 assert(calls.every(x=>x.opts.credentials==="omit"&&x.opts.cache==="no-store"));
 assert(calls[0].url.startsWith("https://raw.githubusercontent.com/jeckodevelopment/opera-funding/main/data/"));
 if(!remoteAvailable)assert(calls.some(x=>x.url==="data/opportunities.json"));
}
(async()=>{await scenario(true);await scenario(false);console.log("Live GitHub JSON and local fallback tests passed");})().catch(e=>{console.error(e);process.exitCode=1;});
