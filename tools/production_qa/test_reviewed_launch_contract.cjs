"use strict";
const test=require("node:test"), assert=require("node:assert/strict"), crypto=require("node:crypto");
const {verifyContract,selectPrior,ACTIVE,PATH,DEPENDENCIES}=require("./reviewed_launch_contract.cjs");
const blob="a".repeat(40), profile=Buffer.from("test profile");
const contract={schema:"two-reviewed-launch-v1",review_state:"REVIEWED_FOR_OWNER_LAUNCH",
 asset_id:"MORWEN",worker_path:PATH,worker_blob:blob,profile_sha256:crypto.createHash("sha256").update(profile).digest("hex"),restore_source:"actions_artifact",dependency_blobs:Object.fromEntries(DEPENDENCIES.map(p=>[p,blob]))};
const blobFor=()=>blob;
const prior={id:123,workflow_id:424712879,path:PATH,head_branch:"main",event:"workflow_dispatch",
 repository:{id:1408120919},head_repository:{id:1408120919},actor:{id:41898282,login:"github-actions[bot]"},
 run_attempt:1,head_sha:"b".repeat(40),display_title:"Morwen VRoid / vrm_export request:456",status:"completed",conclusion:"failure"};
const jobnames=["VRM export and private transfer (reopen)","matrix.lane","blender-transfer-protected","complete-morwen-transfer"];
function fixture(){return [{workflow_runs:[structuredClone(prior)]},structuredClone(prior),
 {total_count:4,jobs:jobnames.map(name=>({name,run_id:123,run_attempt:1,status:"completed",conclusion:"skipped"}))},
 Object.fromEntries(ACTIVE.map(s=>[s,{total_count:0,workflow_runs:[]}]))];}
test("reviewed exact worker and profile",()=>verifyContract(contract,blob,profile,"MORWEN",blobFor));
for(const [name,change,b,p,a] of [
 ["candidate not reviewed",{review_state:"CANDIDATE_REVIEW_REQUIRED"},blob,profile,"MORWEN"],
 ["wrong worker",{},"c".repeat(40),profile,"MORWEN"],
 ["wrong profile",{},blob,Buffer.from("changed"),"MORWEN"],
 ["wrong asset",{},blob,profile,"OTHER"],
 ["wrong path",{worker_path:"other"},blob,profile,"MORWEN"]
])test(name,()=>assert.throws(()=>verifyContract({...contract,...change},b,p,a,blobFor)));
test("latest terminated run selected automatically",()=>assert.equal(selectPrior(...fixture()),123));
for(const [name,mutate] of [
 ["latest changed",f=>f[1].id++],["missing prior",f=>f[0].workflow_runs=[]],
 ["active previous",f=>f[1].status="in_progress"],["wrong mode",f=>f[1].display_title="other"],
 ["wrong actor",f=>f[1].actor.id=1],["wrong repository",f=>f[1].repository.id=1],
 ["rerun attempt",f=>f[1].run_attempt=2],["job incomplete",f=>f[2].jobs[0].status="in_progress"],
 ["job missing",f=>f[2].jobs.pop()],["wrong job identity",f=>f[2].jobs[0].run_id=124],
 ["wrong workflow",f=>f[1].workflow_id=1],["changed revision",f=>f[1].head_sha="d".repeat(40)],
 ["malformed active inventory",f=>delete f[3].waiting]
])test(name,()=>{const f=fixture();mutate(f);assert.throws(()=>selectPrior(...f));});
for(const status of ACTIVE)test("reject "+status,()=>{const f=fixture();f[3][status]={total_count:1,workflow_runs:[{id:999}]};assert.throws(()=>selectPrior(...f));});

test("private explicit source supported",()=>verifyContract({...contract,restore_source:"private_release"},blob,profile,"MORWEN",blobFor));
test("no automatic fallback",()=>assert.throws(()=>verifyContract({...contract,restore_source:"auto"},blob,profile,"MORWEN",blobFor)));
test("missing dependency",()=>{const deps={...contract.dependency_blobs};delete deps[DEPENDENCIES[0]];assert.throws(()=>verifyContract({...contract,dependency_blobs:deps},blob,profile,"MORWEN",blobFor));});
test("changed dependency",()=>assert.throws(()=>verifyContract(contract,blob,profile,"MORWEN",p=>p===DEPENDENCIES[0]?"c".repeat(40):blob)));
test("extra dependency",()=>assert.throws(()=>verifyContract({...contract,dependency_blobs:{...contract.dependency_blobs,unexpected:blob}},blob,profile,"MORWEN",blobFor)));
