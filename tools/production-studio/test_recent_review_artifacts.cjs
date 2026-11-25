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
