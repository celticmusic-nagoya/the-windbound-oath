// AGENTS.md §17: versioned save data, migration/default handling, never silently destroy an older save.
// Self-contained (no DEV-block fixture): loads the shipped js/equipment.js and js/save-continue.js in a vm with minimal stubs.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||path.join(__dirname,'..'));
let passed=0;function test(name,f){f();console.log('PASS',name);passed++;}
function env(){
 const store=new Map(),writes=[];
 const localStorage={getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>{writes.push(k);store.set(k,String(v));},removeItem:k=>{writes.push(k);store.delete(k);}};
 const c={localStorage,console,JSON,Object,Array,Number,Set,Error,CustomEvent:class{constructor(t,o){this.type=t;this.detail=o&&o.detail;}},dispatchEvent(){},
  EquipmentData:{items:{}},
  PartyManager:{members:{aidan:{},liam:{}},maxActive:4},
  TrainingCheckpoint:{prepare:(saved)=>({data:saved,restoreVillage:false})},
  MossForestStory:{canRestoreEarlyMap:()=>true,canRestoreFreeRoamMap:()=>true,MAP_IDS:{}},
  PrologueProgress:{plan:p=>({stage:p.storyStage})}};
 c.window=c;vm.createContext(c);
 for(const f of ['js/equipment.js','js/save-continue.js'])vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),c,{filename:f});
 return {c,store,writes};
}
const base=(over={})=>({version:30,prologue:{version:1,storyStage:4},inventory:{gear:{}},members:{aidan:{joined:true,level:3,exp:10}},active:['aidan'],...over});
const plain=x=>JSON.parse(JSON.stringify(x));

// --- EquipmentManager.migrateStarterSword: proposal-only migration ---
const {c:E}=env(),M=E.EquipmentManager.migrateStarterSword;
test('legacy wooden_sword migrates to father_sword (bag and equipped) without mutating the source save',()=>{
 const src=base({inventory:{gear:{wooden_sword:1,leather_cap:2}},equipment:{v:1,state:{aidan:{weapon:'wooden_sword'}}}}),snap=plain(src);
 const out=plain(M(src));
 assert.deepEqual(src,snap,'source save must be untouched');
 assert.deepEqual(out.inventory.gear,{leather_cap:2,father_sword:1});
 assert.equal(out.equipment.state.aidan.weapon,'father_sword');
 assert.equal(out.version,30);assert.deepEqual(out.prologue,snap.prologue);
});
test('migration merges into an existing father_sword count and is idempotent',()=>{
 const once=plain(M(base({inventory:{gear:{wooden_sword:2,father_sword:1}}})));
 assert.deepEqual(once.inventory.gear,{father_sword:3});
 assert.deepEqual(plain(M(once)),once);
});
test('overflow or invalid counts refuse migration (throw) and leave the source save intact',()=>{
 for(const gear of [{wooden_sword:50,father_sword:50},{wooden_sword:1,father_sword:-1},{wooden_sword:1,father_sword:1.5}]){
  const src=base({inventory:{gear}}),snap=plain(src);
  assert.throws(()=>M(src),/manual review/);assert.deepEqual(src,snap);
 }
});
test('saves without gear/equipment or with out-of-range wooden_sword counts pass through unchanged',()=>{
 for(const src of [base({inventory:{}}),base({inventory:{gear:{wooden_sword:0}}}),base({inventory:{gear:{wooden_sword:100}}}),base({inventory:{gear:[]}}),base()]){
  const snap=plain(src);assert.deepEqual(plain(M(src)),snap);assert.deepEqual(src,snap);
 }
});

// --- SaveContinue.inspect: version gate is read-only ---
function inspect(record){const e=env(),raw=JSON.stringify(record);e.store.set('windbound_oath_v028',raw);const r=e.c.SaveContinue.inspect();
 assert.equal(e.store.get('windbound_oath_v028'),raw,'inspect must not rewrite the stored bytes');assert.deepEqual(e.writes,[],'inspect must not write storage');return r;}
test('accepted save versions: v30 with prologue v1/v2, and legacy unversioned prologue v1',()=>{
 for(const [sv,pv] of [[30,1],[30,2],[undefined,1]]){
  const d=base();if(sv===undefined)delete d.version;else d.version=sv;d.prologue.version=pv;
  const r=inspect(d);assert.equal(r.ok,true,`version ${sv}/${pv}: ${r.error}`);assert.equal(r.route.stage,4);
 }
});
test('accepted legacy save with wooden_sword is migrated in the inspected data, raw bytes preserved',()=>{
 const d=base({inventory:{gear:{wooden_sword:1}}});delete d.version;const r=inspect(d);
 assert.equal(r.ok,true,r.error);assert.equal(JSON.parse(r.raw).inventory.gear.wooden_sword,1);assert.deepEqual(plain(r.data.inventory.gear),{father_sword:1});
});
test('unknown or inconsistent versions are rejected without touching storage',()=>{
 const cases=[[29,1],[31,1],['30',1],[undefined,2],[30,0],[30,3],[30,undefined]];
 for(const [sv,pv] of cases){const d=base();if(sv===undefined)delete d.version;else d.version=sv;if(pv===undefined)delete d.prologue.version;else d.prologue.version=pv;
  const r=inspect(d);assert.equal(r.ok,false,`version ${sv}/${pv} must be rejected`);assert.match(r.error,/未対応|不完全/);}
});
test('storyStage outside 0..15 or non-integer is rejected; 0 and 15 boundaries accepted',()=>{
 for(const s of [-1,16,1.5,'4',null]){const d=base();d.prologue.storyStage=s;assert.equal(inspect(d).ok,false,`stage ${s}`);}
 for(const s of [0,15]){const d=base();d.prologue.storyStage=s;const r=inspect(d);assert.equal(r.ok,true,`stage ${s}: ${r.error}`);}
});
test('missing save and corrupt JSON report errors without writing storage',()=>{
 const e=env();assert.equal(e.c.SaveContinue.inspect().ok,false);
 e.store.set('windbound_oath_v028','{broken');const r=e.c.SaveContinue.inspect();assert.equal(r.ok,false);assert.equal(e.store.get('windbound_oath_v028'),'{broken');assert.deepEqual(e.writes,[]);
});
test('migration overflow surfaces as a refused restore, original bytes kept',()=>{
 const r=inspect(base({inventory:{gear:{wooden_sword:60,father_sword:60}}}));assert.equal(r.ok,false);assert.match(r.error,/manual review/);
});
console.log(`${passed} PASS; save version/migration non-destructive`);
