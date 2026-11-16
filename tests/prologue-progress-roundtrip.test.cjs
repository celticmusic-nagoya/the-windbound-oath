// AGENTS.md §15/§17: PrologueProgress.serialize -> plan/restoreModel round trip for storyStage 0..15.
// Self-contained (no DEV-block fixture): loads the shipped js/field/moss-forest-story.js and js/prologue-progress.js
// in a vm with minimal stubs, so the real canRestoreEarlyMap / canRestoreFreeRoamMap decide FIELD_MAP routes.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||path.join(__dirname,'..'));
let passed=0;function test(name,f){f();console.log('PASS',name);passed++;}
const plain=x=>JSON.parse(JSON.stringify(x));
const FOREST=['moss_corruption_01','moss_corruption_02','moss_corruption_03'];

function env({rilde=true,moss=null,mossActive=false}={}){
 const el=()=>({style:{},hidden:false,classList:{add(){},remove(){},toggle(){}}});
 const nodes=new Map();
 const document={querySelector:s=>{if(!nodes.has(s))nodes.set(s,el());return nodes.get(s);},querySelectorAll:()=>[],getElementById:id=>document.querySelector('#'+id),body:el()};
 const c={console,JSON,Object,Array,Number,Set,Map,Error,Boolean,String,Math,setTimeout:()=>0,document,
  addEventListener(){},
  flags:{drawer:false,pot:false,balloon:false,balloonDone:false,cat:false,catFound:false,catDone:false},
  forestGobWins:0,louFound:false,storyStage:0,attackStep:0,northPhase:0,forestStoneSeen:false,px:420,py:1160,currentObjective:'',
  subQuests:{balloon:{state:'locked'},cat:{state:'locked'}},
  setObj(){},forestToast(){},
  LoadCoordinator:{assertCurrent(){}},
  RildeVillage:{enabled:()=>rilde},
  MossForest:{map:null,active:mossActive,snapshot:()=>moss?plain(moss):null,setFlag(){},syncSymbols(){}}};
 c.window=c;vm.createContext(c);
 for(const f of ['js/field/moss-forest-story.js','js/prologue-progress.js'])vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),c,{filename:f});
 return c;
}
// Put the model into a given stage through the public restoreModel path (v2 snapshot), then serialize it.
function snapshotAt(c,stage,defeated=[]){
 c.PrologueProgress.restoreModel({version:2,legacyEvents:c.PrologueProgress.eventSnapshot(),defeated,storyStage:stage},stage);
 return plain(c.PrologueProgress.serialize());
}
const EXPECTED={0:'LEGACY_SCENE',1:'LEGACY_SCENE',3:'LEGACY_SCENE',4:'LEGACY_SCENE',5:'LEGACY_SCENE',6:'LEGACY_SCENE',7:'LEGACY_SCENE',8:'LEGACY_SCENE',
 9:'FIELD_MAP',10:'FIELD_MAP',11:'FIELD_MAP',12:'FIELD_MAP',13:'AFTERMATH',14:'FORT_FINALE',15:'PROLOGUE_END'};

test('serialize emits a v2 record whose legacyEvents/defeated/counters are self-consistent and JSON-clean',()=>{
 const c=env(),s=snapshotAt(c,10,[FOREST[0],'attackGob1','not_a_real_id']);
 assert.equal(s.version,2);assert.equal(s.storyStage,10);
 assert.deepEqual(s.defeated.sort(),[FOREST[0],'attackGob1'].sort(),'unknown encounter ids must be dropped on restore');
 assert.equal(s.corruptionCount,1);assert.equal(s.barrierOpen,false);
 assert.equal(s.legacyEvents.v,1);assert.deepEqual(s.legacyEvents.unknown,[]);
 assert.deepEqual(plain(s),s);
});
test('every stage 0..15 (except 2) round-trips through plan with route.stage === storyStage (SaveContinue.inspect contract)',()=>{
 for(let stage=0;stage<=15;stage++){
  if(stage===2)continue;
  const c=env(),s=snapshotAt(c,stage,stage>=11?FOREST:[]);
  const r=c.PrologueProgress.plan(s);
  assert.equal(r.stage,stage,`stage ${stage} must not be rewritten`);
  assert.equal(r.kind,EXPECTED[stage],`stage ${stage} route`);
  assert.ok(Object.isFrozen(r));
 }
});
test('stage 2 (training) is never restored by a plain plan; only the validated TRAINING_RETRY path accepts it',()=>{
 const c=env(),s=snapshotAt(c,2);
 assert.throws(()=>c.PrologueProgress.plan(s),/validated recovery/);
 const t=snapshotAt(c,1);assert.equal(c.PrologueProgress.plan(t,true).kind,'TRAINING_RETRY');
 assert.throws(()=>c.PrologueProgress.plan(s,true),/Invalid training plan/);
 assert.throws(()=>c.PrologueProgress.plan({...t,version:1},true),/Invalid training plan/);
});
test('stages 11..15 without all three forest corruptions demote to 10 in plan and restoreModel (inspect then refuses via stage mismatch)',()=>{
 for(const stage of [11,12,13,14,15]){
  const c=env(),s=snapshotAt(c,stage,FOREST.slice(0,2));
  assert.equal(s.storyStage,10,`restoreModel must demote stage ${stage}`);
  const r=c.PrologueProgress.plan({...s,storyStage:stage});assert.equal(r.stage,10);assert.notEqual(r.stage,stage);
 }
});
test('restoreModel(serialize()) is idempotent: a second serialize is byte-identical',()=>{
 for(const stage of [0,4,8,10,12,15]){
  const c=env();c.subQuests.balloon.state='active';c.attackStep=2;c.northPhase=3;c.forestStoneSeen=true;
  const a=snapshotAt(c,stage,FOREST);c.PrologueProgress.restoreModel(a,a.storyStage);
  const b=plain(c.PrologueProgress.serialize());
  assert.deepEqual(b,a,`stage ${stage}`);
 }
});
test('serialize deep-copies subQuests (later in-game mutation does not alter the saved snapshot)',()=>{
 const c=env(),s=c.PrologueProgress.serialize();c.subQuests.cat.state='done';
 assert.equal(s.subQuests.cat.state,'locked');
});
test('hidden Moss Forest field is not saved as a free-roam checkpoint (map/x/y cleared, level dropped)',()=>{
 const c=env({moss:{map:'moss_forest_02_mossy_ravine',x:100,y:200,level:3,opened:[],fired:[]},mossActive:false});
 const s=plain(c.PrologueProgress.serialize());
 assert.equal(s.moss.map,null);assert.equal(s.moss.x,0);assert.equal(s.moss.y,0);assert.ok(!('level' in s.moss));
 const a=env({moss:{map:'moss_forest_02_mossy_ravine',x:100,y:200,level:3,opened:[],fired:[]},mossActive:true});
 const t=plain(a.PrologueProgress.serialize());assert.equal(t.moss.map,'moss_forest_02_mossy_ravine');assert.equal(t.moss.level,3);
});
test('v2 moss-coordinate stages 0/1/3: early map with finite x/y -> FIELD_MAP; missing coords, v1, unknown map or Rilde off -> LEGACY_SCENE',()=>{
 for(const stage of [0,1,3]){
  const ok={version:2,storyStage:stage,defeated:[],moss:{map:'rilde_village_01_peace',x:10,y:20}};
  assert.equal(env().PrologueProgress.plan(ok).kind,'FIELD_MAP',`stage ${stage}`);
  for(const bad of [{...ok,moss:{...ok.moss,x:NaN}},{...ok,moss:{...ok.moss,y:undefined}},{...ok,version:1},{...ok,moss:{...ok.moss,map:'moss_forest_02_mossy_ravine'}}])
   assert.equal(env().PrologueProgress.plan(bad).kind,'LEGACY_SCENE',`stage ${stage} ${JSON.stringify(bad.moss)} v${bad.version}`);
  assert.equal(env({rilde:false}).PrologueProgress.plan(ok).kind,'LEGACY_SCENE');
 }
});
test('stage 15 free-roam: Dunvar/capital map with finite coords -> FIELD_MAP, otherwise PROLOGUE_END; stage 14 never free-roams',()=>{
 const ok={version:2,storyStage:15,defeated:FOREST,moss:{map:'fort_dunvall_01_courtyard',x:5,y:6}};
 assert.equal(env().PrologueProgress.plan(ok).kind,'FIELD_MAP');
 assert.equal(env().PrologueProgress.plan({...ok,moss:{...ok.moss,x:Infinity}}).kind,'PROLOGUE_END');
 assert.equal(env().PrologueProgress.plan({...ok,moss:{...ok.moss,map:'rilde_village_01_peace'}}).kind,'PROLOGUE_END');
 assert.equal(env().PrologueProgress.plan({...ok,storyStage:14}).kind,'FORT_FINALE');
});
test('unsupported progress versions and malformed legacyEvents are refused by plan',()=>{
 const c=env();
 for(const v of [0,3,'2',undefined])assert.throws(()=>c.PrologueProgress.plan({version:v,storyStage:4}),/Unsupported progress/);
 assert.throws(()=>c.PrologueProgress.plan({version:2,storyStage:4,legacyEvents:{v:2}}),/不完全/);
});
console.log(`${passed} passed`);
