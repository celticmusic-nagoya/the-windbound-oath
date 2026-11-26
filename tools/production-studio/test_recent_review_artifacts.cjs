const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const context={module:{exports:{}}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,"recent-review-artifacts.js"),"utf8"),context);
const {selectRecentArtifacts}=context.module.exports;
const art=(id,branch,name,extra={})=>({id,name,expired:false,size_in_bytes:100,created_at:"2026-11-25T12:00:00Z",digest:"sha256:"+"a".repeat(64),workflow_run:{id:100+id,head_branch:branch,head_sha:"b".repeat(40),repository_id:1,head_repository_id:1},...extra});
test("recognizes live face, wardrobe, textile, blueprint and HOME receipts",()=>{
 const rows=selectRecentArtifacts({artifacts:[art(1,"main","morwen-isolated-vroid-reopen-review"),art(2,"main","morwen-parallel-C-wardrobe"),art(3,"asset/morwen-measured-textile-20261125","morwen-measured-textile-not-adopted"),art(4,"feature/lind-village-world-integration-plan-01","aidan-measured-blueprint"),art(5,"feature/lind-village-world-integration-plan-01","home-cross-run-qa-45607836766")]});
 assert.deepEqual(Array.from(rows,x=>x.id),[5,4,3,2,1]);assert.match(rows[4].filter,/mouth-reopened/);
});
test("rejects expired, unrelated, fork, malformed, duplicate and unknown-source records",()=>{
 const a=art(1,"main","morwen-isolated-vroid-reopen-review");
 const rows=selectRecentArtifacts({artifacts:[a,a,art(2,"main","unrelated"),art(3,"evil","morwen-isolated-vroid-reopen-review"),art(4,"main",a.name,{expired:true}),art(5,"main",a.name,{workflow_run:{...a.workflow_run,head_repository_id:2}}),art(6,"main",a.name,{workflow_run:{...a.workflow_run,head_sha:"bad"}}),null]});
 assert.equal(rows.length,1);assert.equal(rows[0].id,1);
});
test("invalid API shape and bounded result",()=>{assert.throws(()=>selectRecentArtifacts({workflow_runs:[]}));assert.equal(selectRecentArtifacts({artifacts:Array.from({length:60},(_,i)=>art(i+1,"main","morwen-isolated-vroid-reopen-review"))}).length,30);});

const {selectPreservationRuns,refreshDelay}=context.module.exports;
const REPO="celticmusic-nagoya/the-windbound-oath";
const run=(id,extra={})=>({id,path:".github/workflows/public-preservation-pilot.yml",head_branch:"main",head_sha:"a".repeat(40),repository:{full_name:REPO},head_repository:{full_name:REPO},status:"completed",conclusion:"success",updated_at:"2026-11-25T22:09:30Z",...extra});
test("preservation list accepts only the exact public workflow and separates known operation labels",()=>{
 const rows=selectPreservationRuns({workflow_runs:[run(45706894871),run(45710690152),run(45710690152),run(99,{status:"waiting",conclusion:null}),run(1,{head_repository:{full_name:"other/repo"}}),run(2,{head_branch:"feature/test"}),run(3,{path:".github/workflows/other.yml"}),run(4,{status:"unknown"}),null]});
 assert.deepEqual(Array.from(rows,x=>x.id),[45710690152,45706894871,99]);assert.equal(rows[0].label,"独立復元");assert.equal(rows[1].label,"自動保全");assert.equal(rows[2].conclusion,null);
 assert.throws(()=>selectPreservationRuns({artifacts:[]}));
 assert.equal(refreshDelay(true),300000);assert.equal(refreshDelay(false),900000);
});
test("visible automatic refresh, hidden pause, no overlap, error retains prior cards",async()=>{
 class El{constructor(){this.children=[];this.dataset={};this.style={};this.events={};this.textContent="";}setAttribute(){}append(...x){this.children.push(...x)}replaceChildren(){this.children=[]}before(...x){this.beforeItems=x}after(...x){this.afterItems=x}addEventListener(k,f){this.events[k]=f}}
 const ids=Object.fromEntries(["recent-review-artifacts","recent-review-status","refresh-recent-review","recent-review-title"].map(k=>[k,new El()]));
 const doc={hidden:false,events:{},getElementById:k=>ids[k],createElement:()=>new El(),addEventListener(k,f){this.events[k]=f}};
 let calls=0,fail=false,timer=null,serial=0;
 const sandbox={document:doc,AbortSignal,fetch:async url=>{calls++;return {ok:!fail,status:403,json:async()=>url.includes("/workflows/")?{workflow_runs:[run(45710690152)]}:{artifacts:[art(1,"main","morwen-isolated-vroid-reopen-review"),art(2,"feature/lind-ecology-01","lind-eco-53-candidate-evidence")]}}},setTimeout:(fn,ms)=>{timer={id:++serial,fn,ms};return serial},clearTimeout:()=>{timer=null}};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,"recent-review-artifacts.js"),"utf8"),sandbox);
 const flush=()=>new Promise(resolve=>setImmediate(resolve));await flush();
 assert.equal(calls,2);assert.equal(ids["recent-review-artifacts"].children.length,2);
 const category=ids["refresh-recent-review"].afterItems[2];category.value="リルド村・植生";category.events.change();assert.equal(calls,2);assert.equal(ids["recent-review-artifacts"].children.length,1);assert.equal(ids["recent-review-artifacts"].children[0].dataset.artifactId,"2");
 const preservation=ids["recent-review-title"].beforeItems[3];assert.equal(preservation.children.length,1);
 assert.ok(timer.ms>=299000&&timer.ms<=300000);
 doc.hidden=true;doc.events.visibilitychange();assert.equal(timer,null);
 doc.hidden=false;doc.events.visibilitychange();assert.ok(timer);
 fail=true;timer.fn();ids["refresh-recent-review"].events.click();await flush();
 assert.equal(calls,4);assert.equal(ids["recent-review-artifacts"].children.length,1);assert.equal(preservation.children.length,1);
 assert.match(ids["recent-review-status"].textContent,/前回取得分を保持/);assert.ok(timer.ms>=899000&&timer.ms<=900000);
 category.value="";category.events.change();assert.equal(calls,4);assert.equal(ids["recent-review-artifacts"].children.length,2);assert.match(ids["recent-review-status"].textContent,/前回取得分を保持/);
});

test("ECO and measured material sources are recognized; filter before 30-row limit",()=>{
 const eco=art(1,"feature/lind-ecology-01","lind-eco-53-candidate-evidence");
 const pkg=art(2,"feature/lind-ecology-01","lind-eco-integration-v2-package");
 const brass=art(3,"asset/morwen-measured-textile-20261125","morwen-brass-source-maps-not-adopted");
 const gold=art(4,"asset/morwen-measured-textile-20261125","morwen-met-gold-thread-oa-sources-not-adopted");
 const photo=art(5,"asset/morwen-measured-textile-20261125","morwen-photo-textile-comparison-not-adopted");
 const unrelated=art(6,"feature/lind-ecology-01","unknown-source");
 const data={artifacts:[eco,pkg,brass,gold,photo,unrelated,...Array.from({length:40},(_,i)=>art(100+i,"main","morwen-isolated-vroid-reopen-review"))]};
 assert.equal(selectRecentArtifacts(data).length,30);
 assert.deepEqual(Array.from(selectRecentArtifacts(data,"リルド村・植生"),x=>x.id),[2,1]);
 assert.deepEqual(Array.from(selectRecentArtifacts(data,"モルウェン・材質研究"),x=>x.id),[5,4,3]);
 assert.equal(selectRecentArtifacts(data,"unknown").length,0);
});

test("observed current hero-tree and native forest evidence is discoverable, with branch and name constraints",()=>{
 const branch="docs/ireland-world-source-grounded-plan-20261123";
 const rows=selectRecentArtifacts({artifacts:[art(15073087704,branch,"two-hero-tree-v55-island-source"),art(15072796460,branch,"two-forest-v52-native-virtual-qa"),art(9,"other", "two-hero-tree-v55-island-source"),art(8,branch,"two-forest-unknown")]}, "世界・樹木／森林");
 assert.deepEqual(Array.from(rows,x=>x.id),[15073087704,15072796460]);
});
