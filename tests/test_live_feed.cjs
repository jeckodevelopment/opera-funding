const fs=require("node:fs");
const vm=require("node:vm");
const assert=require("node:assert/strict");
const source=fs.readFileSync("web/app.js","utf8").replace(/\ninit\(\);\s*$/,"\n");
async function scenario(remoteAvailable){
 const calls=[];
 const context={
  URL,Date,console,window:{addEventListener(){}},
  setTimeout,clearTimeout,AbortController,
  document:{getElementById:()=>({addEventListener(){}}),querySelectorAll:()=>[]},
  fetch:async (url,opts)=>{
   calls.push({url,opts});
   if(url.startsWith("https://raw.githubusercontent.com/")&&!remoteAvailable)throw Error("network/CORS");
   const value=url.includes("opportunities.json?")?[]:{checked_at:"2026-11-16T19:00:00Z",sources:[]};
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
 assert(calls.every(x=>x.opts.signal instanceof AbortSignal));
 assert(calls[0].url.startsWith("https://raw.githubusercontent.com/jeckodevelopment/opera-funding/main/data/"));
 const versions=calls.map(x=>new URL(x.url,"https://local.example/dev/funding/").searchParams.get("v"));
 assert(versions.every(v=>v&&/^\d+$/.test(v)));
 assert.equal(versions[0],versions[1]);
 if(!remoteAvailable){
   assert(calls.some(x=>x.url.startsWith("data/opportunities.json?v=")));
   assert.equal(versions[2],versions[3]);
 }
 
}

async function timeoutScenario(){
 const calls=[];
 const context={
  URL,Date,console,window:{addEventListener(){}},setTimeout,clearTimeout,AbortController,
  document:{getElementById:()=>({addEventListener(){}}),querySelectorAll:()=>[]},
  fetch:(url,opts)=>{
   calls.push(url);
   if(url.startsWith("https://raw.githubusercontent.com/"))return new Promise(()=>{});
   return Promise.resolve({ok:true,json:async()=>url.includes("opportunities.json?")?[]:{checked_at:"2026-11-18T08:00:00Z",sources:[]}});
  }
 };
 // Remote request stalls; shorten the production deadline inside this VM
 // to verify that the dashboard falls back to its local snapshot promptly.
 const original=fs.readFileSync("web/app.js","utf8")
   .replace(/fetchWithDeadline\(DATA_ORIGIN\)/g,"fetchWithDeadline(DATA_ORIGIN,80)")
   .replace(/fetchWithDeadline\(FALLBACK_ORIGIN\)/g,"fetchWithDeadline(FALLBACK_ORIGIN,80)")
   .replace(/\ninit\(\);\s*$/,"\n");
 vm.runInNewContext(original+"\nglobalThis.getFeed=loadDataset;",context);
 const result=await context.getFeed();
 assert.equal(result.origin,"local");
 assert(calls.some(url=>url.startsWith("data/opportunities.json?")));
}

(async()=>{await scenario(true);await scenario(false);await timeoutScenario();console.log("Live GitHub JSON and local fallback tests passed");})().catch(e=>{console.error(e);process.exitCode=1;});
