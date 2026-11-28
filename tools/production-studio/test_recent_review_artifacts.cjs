const test=require("node:test"),assert=require("node:assert/strict");
const fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const context={module:{exports:{}}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,"recent-review-artifacts.js"),"utf8"),context);
const {selectRecentArtifacts}=context.module.exports;
const art=(id,branch,name,extra={})=>({id,name,expired:false,size_in_bytes:100,created_at:"2026-11-25T12:00:00Z",digest:"sha256:"+"a".repeat(64),workflow_run:{id:100+id,head_branch:branch,head_sha:"b".repeat(40),repository_id:1408120919,head_repository_id:1408120919},...extra});
test("recognizes live face, wardrobe, textile, blueprint and HOME receipts",()=>{
 const rows=selectRecentArtifacts({artifacts:[art(1,"main","morwen-isolated-vroid-reopen-review"),art(2,"main","morwen-parallel-C-wardrobe"),art(3,"asset/morwen-measured-textile-20261125","morwen-measured-textile-not-adopted"),art(4,"feature/lind-village-world-integration-plan-01","aidan-measured-blueprint"),art(5,"feature/lind-village-world-integration-plan-01","home-cross-run-qa-45607836766")]});
 assert.deepEqual(Array.from(rows,x=>x.id),[5,4,3,2,1]);assert.match(rows[4].filter,/mouth-reopened/);
});
test("rejects expired, wrong repository, fork, malformed and duplicate; same-repo unknown sources are metadata only",()=>{
 const a=art(1,"main","morwen-isolated-vroid-reopen-review");
 const rows=selectRecentArtifacts({artifacts:[a,a,art(2,"main","unrelated"),art(3,"evil","morwen-isolated-vroid-reopen-review"),art(4,"main",a.name,{expired:true}),art(5,"main",a.name,{workflow_run:{...a.workflow_run,head_repository_id:2}}),art(6,"main",a.name,{workflow_run:{...a.workflow_run,head_sha:"bad"}}),art(7,"main",a.name,{workflow_run:{...a.workflow_run,repository_id:2,head_repository_id:2}}),null]});
 assert.deepEqual(Array.from(rows,x=>x.id),[3,2,1]);assert.ok(rows[0].metadataOnly&&rows[1].metadataOnly&&!rows[2].metadataOnly);
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
 const sandbox={document:doc,AbortSignal,fetch:async url=>{calls++;return {ok:!fail,status:403,json:async()=>url.includes("/issues/comments?")?[report(71,427),report(72,421)]:url.includes("/workflows/")?{workflow_runs:[run(45710690152)]}:url.includes("/actions/runs?")?{workflow_runs:[]}:{artifacts:[art(1,"main","morwen-isolated-vroid-reopen-review"),art(2,"feature/lind-ecology-01","lind-eco-53-candidate-evidence")]}}},setTimeout:(fn,ms)=>{timer={id:++serial,fn,ms};return serial},clearTimeout:()=>{timer=null}};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,"recent-review-artifacts.js"),"utf8"),sandbox);
 const flush=()=>new Promise(resolve=>setImmediate(resolve));await flush();
 assert.equal(calls,4);assert.equal(ids["recent-review-artifacts"].children.length,2);
 const category=ids["refresh-recent-review"].afterItems[2];category.value="リルド村・植生";category.events.change();assert.equal(calls,4);assert.equal(ids["recent-review-artifacts"].children.length,1);assert.equal(ids["recent-review-artifacts"].children[0].dataset.artifactId,"2");
 const buttons=ids["refresh-recent-review"].afterItems[4];const search=ids["refresh-recent-review"].afterItems[6];
 const allButton=buttons.children.find(e=>e.dataset.category==="");allButton.events.click();assert.equal(ids["recent-review-artifacts"].children.length,2);
 search.value="eco";search.events.input();assert.equal(ids["recent-review-artifacts"].children.length,1);assert.equal(ids["recent-review-artifacts"].children[0].dataset.artifactId,"2");
 search.value="";search.events.input();category.value="リルド村・植生";category.events.change();assert.equal(calls,4);
 const preservation=ids["recent-review-title"].beforeItems[3];assert.equal(preservation.children.length,1);
 const reports=ids["recent-review-artifacts"].beforeItems[3];assert.equal(reports.children.length,2);assert.equal(reports.children[0].dataset.reportId,"72");
 assert.ok(timer.ms>=299000&&timer.ms<=300000);
 doc.hidden=true;doc.events.visibilitychange();assert.equal(timer,null);
 doc.hidden=false;doc.events.visibilitychange();assert.ok(timer);
 fail=true;timer.fn();ids["refresh-recent-review"].events.click();await flush();
 assert.equal(calls,7);assert.equal(ids["recent-review-artifacts"].children.length,1);assert.equal(preservation.children.length,1);assert.equal(reports.children.length,2);
 assert.match(ids["recent-review-status"].textContent,/前回取得分を保持/);assert.ok(timer.ms>=899000&&timer.ms<=900000);
 category.value="";category.events.change();assert.equal(calls,7);assert.equal(ids["recent-review-artifacts"].children.length,2);assert.match(ids["recent-review-status"].textContent,/前回取得分を保持/);
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
 assert.deepEqual(Array.from(selectRecentArtifacts(data,"リルド村・植生"),x=>x.id),[6,2,1]);
 assert.deepEqual(Array.from(selectRecentArtifacts(data,"モルウェン・材質研究"),x=>x.id),[5,4,3]);
 assert.equal(selectRecentArtifacts(data,"unknown").length,0);
});

test("observed current hero-tree and native forest evidence is discoverable, with branch and name constraints",()=>{
 const branch="docs/ireland-world-source-grounded-plan-20261123";
 const rows=selectRecentArtifacts({artifacts:[art(15073087704,branch,"two-hero-tree-v55-island-source"),art(15072796460,branch,"two-forest-v52-native-virtual-qa"),art(9,"other", "two-hero-tree-v55-island-source"),art(8,branch,"two-forest-unknown")]});
 assert.deepEqual(Array.from(rows,x=>x.category),["世界・樹木","世界・森林","世界・森林","世界・森林"]);assert.equal(rows.find(x=>x.id===9).metadataOnly,true);
});

test("sanctuary and future versioned world evidence are visible without weakening branch boundaries",()=>{
 const branch="docs/ireland-world-source-grounded-plan-20261123";
 const data={artifacts:[art(15075315647,branch,"two-sanctuary-v57-native-composition"),art(15073087704,branch,"two-hero-tree-v55-island-source"),art(15072796460,branch,"two-forest-v52-native-virtual-qa"),art(11,branch,"two-river-v99-native-review"),art(12,"other","two-river-v99-native-review"),art(13,branch,"two-forest-unknown"),art(14,branch,"two-river-v99-native-review",{expired:true})]};
 assert.deepEqual(Array.from(selectRecentArtifacts(data),x=>x.id),[15075315647,15073087704,15072796460,13,12,11]);
 assert.equal(selectRecentArtifacts(data,"世界・聖域")[0].id,15075315647);assert.equal(selectRecentArtifacts(data).find(x=>x.id===12).metadataOnly,true);
 assert.deepEqual(Array.from(selectRecentArtifacts(data,"世界・河川／水辺"),x=>x.id),[11]);
});

test("world namespace catches actual new naming orders and unversioned candidates without crossing branches",()=>{
 const branch="docs/ireland-world-source-grounded-plan-20261123";
 const data={artifacts:[art(15076007596,branch,"two-v59-ruin-2d-references"),art(15075731907,branch,"two-sanctuary-v58-native-scenery"),art(31,branch,"two-unversioned-prototype"),art(32,"other","two-v59-ruin-2d-references"),art(33,branch,"two-../unsafe"),art(34,branch,"two-"+'a'.repeat(161)),art(35,branch,"two-fork",{workflow_run:{...art(35,branch,"two-fork").workflow_run,head_repository_id:2}})]};
 assert.deepEqual(Array.from(selectRecentArtifacts(data),x=>x.id),[15076007596,15075731907,31]);
 assert.equal(selectRecentArtifacts(data,"世界・聖域")[0].id,15075731907);
 assert.deepEqual(Array.from(selectRecentArtifacts(data,"世界・遺跡"),x=>x.id),[15076007596]);
 assert.deepEqual(Array.from(selectRecentArtifacts(data,"世界・新規制作証跡（未分類）"),x=>x.id),[31]);
});

test("actual river and DEM sources and botanical candidates remain distinct",()=>{
 const branch="docs/ireland-world-source-grounded-plan-20261123";
 const rows=selectRecentArtifacts({artifacts:[art(15036275709,branch,"two-ireland-river-reference-v26"),art(15033082981,branch,"two-ireland-dem-v24-southwest"),art(1,branch,"two-fern-v65-candidate")]});
 assert.deepEqual(Array.from(rows,x=>x.category),["世界・河川／水辺","世界・地形","世界・植物／草花"]);
});

const {selectLiveRuns,swipeDirection,inferCategory}=context.module.exports;
test("actual repository fallback retains new WIP metadata without allowing arbitrary forks",()=>{
 const branch="feature/new-battle-ui";
 const real=art(201,branch,"battle-ui-wip",{workflow_run:{...art(201,branch,"battle-ui-wip").workflow_run,repository_id:1408120919,head_repository_id:1408120919}});
 const unknown=art(202,"feature/new","fresh-candidate",{workflow_run:{...real.workflow_run,id:302,head_branch:"feature/new"}});
 const fork={...real,id:203,workflow_run:{...real.workflow_run,head_repository_id:2}};
 const unsafe={...real,id:204,name:"../private"};
 const rows=selectRecentArtifacts({artifacts:[real,unknown,fork,unsafe]},"",100);
 assert.equal(rows.length,2);assert.equal(rows[0].category,"その他・未分類");assert.equal(rows[1].category,"ゲーム・UI／実装");assert.ok(rows.every(x=>x.metadataOnly));
});
test("active and completed public runs classified, no fork/no-op or invalid path",()=>{
 const rows=selectLiveRuns({workflow_runs:[run(21,{name:"Morwen VRoid / vrm_export",path:".github/workflows/morwen-vroid-macos-probe.yml",status:"in_progress",conclusion:null}),run(22,{name:"Forest render",path:".github/workflows/forest.yml"}),run(23,{status:"queued",conclusion:null,name:"World terrain",path:".github/workflows/terrain.yml"}),run(24,{head_repository:{full_name:"other/repo"}}),run(25,{name:"Morwen scoped comment launch",conclusion:"skipped"}),run(26,{path:"../invalid.yml"})]});
 assert.deepEqual(Array.from(rows,x=>x.id),[23,21,22]);assert.equal(rows[1].category,"モルウェン・Blender移行／造形");assert.equal(rows[2].category,"世界・森林");
 assert.throws(()=>selectLiveRuns({artifacts:[]}));
});
test("swipe threshold preserves vertical scroll, tiny gestures and both directions",()=>{
 assert.equal(swipeDirection(-80,10),1);assert.equal(swipeDirection(80,10),-1);assert.equal(swipeDirection(30,0),0);assert.equal(swipeDirection(60,80),0);assert.equal(swipeDirection(-60,55),0);
});

const {selectProductionReports,mergeProductionReports}=context.module.exports;
function report(id,pr,extra={}){
 return {id,issue_url:"https://api.github.com/repos/"+REPO+"/issues/"+pr,html_url:"https://github.com/"+REPO+"/pull/"+pr+"#issuecomment-"+id,user:{login:"celticmusic-nagoya"},updated_at:"2026-11-27T06:00:00Z",body:"公開制作報告・画像未登録",...extra};
}
test("reports include actual owning PR sources; exclude untrusted links, other authors, invalid dates and duplicates",()=>{
 const a=report(7211450119,540),b=report(7211532848,482);
 const rows=selectProductionReports([a,b,a,report(1,999),report(2,427,{user:{login:"other"}}),report(3,427,{html_url:"https://example.com"}),report(4,427,{updated_at:"bad"}),report(5,427,{issue_url:"https://api.github.com/repos/other/repo/issues/427"}),null]);
 assert.deepEqual(Array.from(rows,x=>x.id),[7211532848,7211450119]);
 assert.equal(rows[0].category,"世界・エリア制作");assert.throws(()=>selectProductionReports({comments:[]}));
});
test("report snapshot keeps bounded prior records when recent 100 are dominated by another domain",()=>{
 const prior=selectProductionReports([report(10,421),report(11,427),report(12,427),report(13,427)]);
 const current=selectProductionReports([report(14,427),report(12,427,{body:"edited"}),report(15,482)]);
 const rows=mergeProductionReports(prior,current);
 assert.deepEqual(Array.from(rows,x=>x.id),[15,14,13,12,10]);assert.equal(rows.find(x=>x.id===12).excerpt,"edited");
});

const {expiryState,expirySummary,orderExpiry,recoveryLocator}=context.module.exports;
test("expiry boundary, stale snapshot and priority never imply durable preservation",()=>{
 const now=Date.parse("2026-11-28T12:00:00Z");
 const make=(id,offset)=>({id,expires:offset===null?"":new Date(now+offset*3600000).toISOString()});
 const rows=[make(1,169),make(2,168),make(3,48),make(4,0),make(5,-1),make(6,null),make(7,1),make(8,48.1)];
 assert.deepEqual(Array.from(rows,x=>expiryState(x,now)),["later","soon","urgent","elapsed","elapsed","unknown","urgent","soon"]);
 assert.deepEqual(JSON.parse(JSON.stringify(expirySummary(rows,now))),{elapsed:2,urgent:2,soon:2,later:1,unknown:1});
 assert.deepEqual(Array.from(orderExpiry(rows,now),x=>x.id),[7,3,8,2,6,5,4]);
 assert.equal(expiryState({expires:"bad"},now),"unknown");
});
test("locator binds same repository identity, exact digest and source metadata without claiming backup",()=>{
 const a=art(15261507321,"studio/rilde-day-expression-a02-20261128","two-audio-rilde-day-a02-review",{expires_at:"2026-12-01T11:29:44Z",digest:"sha256:"+"9".repeat(64)});
 const row=selectRecentArtifacts({artifacts:[a]})[0];
 const receipt=recoveryLocator(row,"2026-11-28T12:00:00Z");
 assert.equal(row.category,"音楽・音響");
 assert.equal(receipt.repository,REPO);assert.equal(receipt.artifact_id,a.id);assert.equal(receipt.run_id,a.workflow_run.id);assert.equal(receipt.head_sha,a.workflow_run.head_sha);assert.equal(receipt.head_branch,a.workflow_run.head_branch);
 assert.equal(receipt.archive_digest,a.digest);assert.equal(receipt.archive_bytes,a.size_in_bytes);assert.equal(receipt.expires_at,a.expires_at);
 assert.equal(receipt.preservation_status,"UNVERIFIED");assert.equal(receipt.byte_verification,"NOT_RUN");assert.equal(receipt.adoption,"UNDETERMINED");
 assert.equal(recoveryLocator({...row,digest:"",expires:"bad"},"2026-11-28T12:00:00Z").archive_digest,null);
 assert.throws(()=>recoveryLocator({...row,head:"bad"},"2026-11-28T12:00:00Z"));
 assert.throws(()=>recoveryLocator(row,"bad"));
});
