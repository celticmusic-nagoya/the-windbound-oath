// Contract tests prepared before implementation. Real save modules and state machines; only DOM/network/renderers adapted.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {setup}=require('./startup_race.test.cjs'),{deferred,flush}=require('./s2_transition_recovery.test.cjs');
const root=path.join(__dirname,'..'),html=fs.readFileSync(path.join(root,'index.html'),'utf8');
const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/issue54-stage15.json'),'utf8'));
function env(){
 const e=setup(),c=e.c;
 let party=html.slice(html.indexOf('const PartyManager={'),html.indexOf('let gold=0',html.indexOf('const PartyManager={'))).replace('const PartyManager=','window.PartyManager=');vm.runInContext(party,c);
 c.gold=0;c.battleItems={potion:4,ether:2};c.SAVE_KEY='slot';c.oathBound=false;
 for(const file of ['js/data/item-data.js','js/data/equipment-data.js','js/inventory.js','js/equipment.js','js/field/quest-data.js','js/quest.js','js/training-checkpoint.js'])e.load(file);
 c.renderSystemTab=()=>{};c.notice=()=>{}; // DOM-only UI adapters
 const equipStart=html.indexOf('const STARTER_GEAR='),equipEnd=html.indexOf("window.addEventListener('equipment-unlock'",equipStart);assert.ok(equipStart>=0&&equipEnd>equipStart);vm.runInContext(html.slice(equipStart,equipEnd),c);
 const a=html.indexOf('function saveGrowthData()'),b=html.indexOf("$('#menuOpen').onclick",a);vm.runInContext(html.slice(a,b),c);
 c.world=e.node('#world');e.load('js/field/talk-data-attack.js');
 let aScene=html.indexOf('const returnLines='),bScene=html.indexOf('// 襲撃(stage',aScene);assert.ok(aScene>=0&&bScene>aScene);vm.runInContext(html.slice(aScene,bScene),c);
 const aliases=html.indexOf('const atkTalk=');vm.runInContext(html.slice(aliases,html.indexOf('let attackStep=',aliases)),c);
 aScene=html.indexOf('const escapeLinesNow=');bScene=html.indexOf('// Forest field control',aScene);vm.runInContext(html.slice(aScene,bScene),c);
 e.worlds.set('rilde_village_01_peace',JSON.parse(fs.readFileSync(path.join(root,'data/maps/rilde_village_01_peace.json'),'utf8')));
 e.load('js/save-continue.js');return e;
}
function save(stage=0,map='rilde_in_aidan'){
 const d=structuredClone(fixture);d.prologue.storyStage=stage;d.prologue.defeated=stage>=11?['moss_corruption_01','moss_corruption_02','moss_corruption_03']:[];d.prologue.corruptionCount=d.prologue.defeated.length;d.prologue.barrierOpen=stage>=11;d.prologue.louFound=stage>=11;d.prologue.attackStep=stage>=6?2:0;d.prologue.northPhase=stage===8?3:stage===7?2:0;d.prologue.forestStoneSeen=stage>=10;
 d.prologue.moss={map,x:100,y:200,opened:['tr_a1_hollow'],fired:['seen-once'],facing:{dir:'up',flip:false}};d.prologue.position={px:900,py:800};d.talk={seen:[],cycle:{},flags:{test_saved:true}};return d;
}
function put(e,d){const raw=JSON.stringify(d);e.c.localStorage.setItem('slot',raw);return raw;}
let n=0;async function test(name,fn){if(process.env.CONTINUE_TEST_FILTER&&!name.includes(process.env.CONTINUE_TEST_FILTER))return;await fn();n++;console.log('PASS',name)}
if(require.main!==module)module.exports={env,save,put};
else (async()=>{
 await test('no save disables CONTINUE; valid current save enables it without mutation',async()=>{const e=env();assert.equal(e.c.SaveContinue.inspect().ok,false);const raw=put(e,save());assert.equal(e.c.SaveContinue.inspect().ok,true);assert.equal(e.c.localStorage.getItem('slot'),raw)});
 await test('cold CONTINUE restores field coordinates, facing, flags and once-only events; source bytes unchanged',async()=>{const e=env(),raw=put(e,save());assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.M.mapId,'rilde_in_aidan');assert.equal(e.M.feet.x,117);assert.equal(e.M.feet.y,242);assert.equal(e.M.snapshot().facing.dir,'up');assert.equal(e.c.FieldTalk.flag('test_saved'),true);assert.deepEqual(Array.from(e.M.snapshot().fired),['seen-once']);assert.equal(e.c.FieldTalk.active,false);assert.equal(e.c.localStorage.getItem('slot'),raw)});
 for(const stage of [0,1,3])await test('legacy early stage '+stage+' uses explicit safe checkpoint, never guessed legacy coordinates',async()=>{const e=env(),d=save(stage);d.prologue.version=1;delete d.prologue.moss;const raw=put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.storyStage,stage);assert.equal(e.M.mapId,stage===0?'rilde_in_aidan':'rilde_village_01_peace');assert.equal(e.c.localStorage.getItem('slot'),raw)});
 for(const stage of [4,5,6,7,8])await test('story stage '+stage+' restores its defined legacy/atomic scene checkpoint',async()=>{const e=env(),d=save(stage,null);const raw=put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.storyStage,stage);assert.equal(e.c.localStorage.getItem('slot'),raw)});
 await test('current stage2 checkpoint uses actual validated retry; v1 stage2 stays read-only refused',async()=>{const e=env(),d=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/issue54-stage2.json'),'utf8'));await e.complete(e.c.TrainingCheckpoint.ready);put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.storyStage,1);const f=env();d.prologue.version=1;const raw=put(f,d);assert.equal(f.c.SaveContinue.inspect().ok,false);assert.equal(await f.c.SaveContinue.start(),false);assert.equal(f.c.localStorage.getItem('slot'),raw)});
 await test('forest checkpoint restores through existing shared runtime',async()=>{const e=env();put(e,save(9,'moss_forest_01_sunlit_path'));assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.M.mapId,'moss_forest_01_sunlit_path')});
 for(const raw of ['{broken','{}',JSON.stringify({version:99}),JSON.stringify({version:30,prologue:{version:2,storyStage:0}})])await test('invalid/incomplete save is refused safely: '+raw.slice(0,30),async()=>{const e=env();e.c.localStorage.setItem('slot',raw);assert.equal(e.c.SaveContinue.inspect().ok,false);assert.equal(await e.c.SaveContinue.start(),false);assert.equal(e.c.SaveContinue.phase,'TITLE');assert.equal(e.c.localStorage.getItem('slot'),raw)});
 await test('duplicate CONTINUE is rejected while actual map promise is pending',async()=>{const e=env(),d=deferred();put(e,save());e.faults.load.set('rilde_in_aidan',d);const first=e.c.SaveContinue.start();await flush();assert.equal(await e.c.SaveContinue.start(),false);d.resolve(e.map('rilde_in_aidan'));assert.equal(await e.complete(first),true);assert.equal(await e.c.SaveContinue.start(),false)});
 await test('NEW GAME supersedes CONTINUE, rolls back provisional model and rejects the late response',async()=>{const e=env(),d=deferred(),s=save(9,'moss_forest_01_sunlit_path');s.gold=999;const raw=put(e,s);e.faults.load.set(s.prologue.moss.map,d);const old=e.c.SaveContinue.start();await flush();assert.equal(await e.complete(e.c.RildeVillage.startOpening()),true);d.resolve(e.map(s.prologue.moss.map));assert.equal(await e.complete(old),false);assert.equal(e.M.mapId,'rilde_in_aidan');assert.equal(e.c.gold,0);assert.equal(e.c.storyStage,0);assert.equal(e.c.localStorage.getItem('slot'),raw)});
 await test('failure rolls model and map back to title, keeps SAVE bytes, and allows explicit retry',async()=>{const e=env(),s=save();s.gold=999;const raw=put(e,s);e.faults.load.set('rilde_in_aidan',Error('offline'));assert.equal(await e.complete(e.c.SaveContinue.start()),false);assert.equal(e.c.SaveContinue.phase,'TITLE');assert.equal(e.c.gold,0);assert.equal(e.M.active,false);assert.equal(e.c.storyStage,0);assert.equal(e.c.localStorage.getItem('slot'),raw);e.faults.load.delete('rilde_in_aidan');assert.equal(await e.complete(e.c.SaveContinue.start()),true)});
 await test('real SAVE preserves consumed one-time Rilde events across cold CONTINUE',async()=>{
  const e=env();put(e,save());assert.equal(await e.complete(e.c.SaveContinue.start()),true);
  e.c.flags.drawer=true;
  const query=e.c.$;e.c.$=selector=>selector==='#doSave'?null:query(selector);
  e.c.saveGrowthData();const raw=e.c.localStorage.getItem('slot');
  const cold=env();cold.c.localStorage.setItem('slot',raw);assert.equal(await cold.complete(cold.c.SaveContinue.start()),true);
  cold.c.RildeVillage.hook({hook:'rilde_drawer'},cold.M.map);
  assert.equal(cold.c.msg.textContent,'衣類がきれいに畳まれている。','consumed drawer event must not be replayed');
 });
 const eventFlags=(extra={})=>({v:1,drawer:false,pot:false,balloon:false,balloonDone:false,cat:false,catFound:false,catDone:false,...extra});
 for(const event of ['drawer','pot'])for(const consumed of [false,true])await test('new SAVE '+event+' explicit '+consumed+' restores exactly and executes at most once',async()=>{
  const e=env(),d=save();d.prologue.legacyEvents=eventFlags({[event]:consumed});const raw=put(e,d);
  assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.flags[event],consumed);
  e.c.RildeVillage.hook({hook:'rilde_'+event},e.M.map);
  const first=e.c.msg.textContent;e.c.RildeVillage.hook({hook:'rilde_'+event},e.M.map);const second=e.c.msg.textContent;
  assert.equal(e.c.flags[event],true);assert.equal(second,event==='drawer'?'衣類がきれいに畳まれている。':'壺の中は空だ。');
  if(!consumed)assert.ok(first.includes(event==='drawer'?'きずぐすりを1個':'3Gを見つけた'));
  else assert.equal(first,second);
  assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 for(const event of ['drawer','pot'])await test('actual '+event+' acquisition then SAVE/cold CONTINUE never replays its event',async()=>{
  const e=env(),d=save();d.prologue.legacyEvents=eventFlags();put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);
  e.c.RildeVillage.hook({hook:'rilde_'+event},e.M.map);assert.equal(e.c.flags[event],true);
  const query=e.c.$;e.c.$=selector=>selector==='#doSave'?null:query(selector);e.c.saveGrowthData();const raw=e.c.localStorage.getItem('slot');
  assert.equal(JSON.parse(raw).prologue.legacyEvents[event],true);
  const cold=env();cold.c.localStorage.setItem('slot',raw);assert.equal(await cold.complete(cold.c.SaveContinue.start()),true);
  cold.c.RildeVillage.hook({hook:'rilde_'+event},cold.M.map);assert.equal(cold.c.msg.textContent,event==='drawer'?'衣類がきれいに畳まれている。':'壺の中は空だ。');assert.equal(cold.c.localStorage.getItem('slot'),raw);
 });
 await test('old missing history blocks only drawer/pot, preserves inventory/progress/source and does not fabricate quest completion',async()=>{
  const e=env(),d=save(),raw=put(e,d);const baseline=JSON.stringify(d.inventory);
  assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.flags.drawer,true);assert.equal(e.c.flags.pot,true);assert.equal(e.c.storyStage,d.prologue.storyStage);
  assert.equal(e.c.flags.catDone===true,false);assert.equal(e.c.flags.balloonDone===true,false);assert.equal(e.c.localStorage.getItem('slot'),raw);assert.equal(JSON.stringify(JSON.parse(raw).inventory),baseline);
  for(const event of ['drawer','pot']){e.c.RildeVillage.hook({hook:'rilde_'+event},e.M.map);assert.ok(!e.c.msg.textContent.includes('見つけた'));}
 });
 await test('new explicit false survives actual SAVE and incomplete event profile is refused without mutation',async()=>{
  const e=env(),d=save();d.prologue.legacyEvents=eventFlags();put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);
  const query=e.c.$;e.c.$=selector=>selector==='#doSave'?null:query(selector);e.c.saveGrowthData();const raw=e.c.localStorage.getItem('slot');
  assert.equal(JSON.parse(raw).prologue.legacyEvents.drawer,false);assert.equal(JSON.parse(raw).prologue.legacyEvents.pot,false);
  const bad=save();bad.prologue.legacyEvents={v:1,drawer:false};const f=env(),original=put(f,bad);assert.equal(f.c.SaveContinue.inspect().ok,false);assert.equal(await f.c.SaveContinue.start(),false);assert.equal(f.c.localStorage.getItem('slot'),original);
 });
 await test('NEW GAME resets acquisition restrictions to genuinely unclaimed state',async()=>{
  const e=env();put(e,save());assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.flags.drawer,true);assert.equal(e.c.flags.pot,true);
  assert.equal(await e.complete(e.c.RildeVillage.startOpening()),true);assert.equal(e.c.flags.drawer,false);assert.equal(e.c.flags.pot,false);
 });
 await test('failed CONTINUE and normal LOAD never partially commit acquisition flags',async()=>{
  const e=env(),d=save();d.prologue.legacyEvents=eventFlags({drawer:true,pot:true});const raw=put(e,d);e.faults.load.set('rilde_in_aidan',Error('offline'));
  assert.equal(await e.complete(e.c.SaveContinue.start()),false);assert.equal(e.c.flags.drawer===true,false);assert.equal(e.c.flags.pot===true,false);assert.equal(e.c.localStorage.getItem('slot'),raw);
  e.faults.load.delete('rilde_in_aidan');assert.equal(await e.complete(e.c.SaveContinue.start()),true);e.c.flags.drawer=false;e.c.flags.pot=false;
  const forest=save(9,'moss_forest_01_sunlit_path');forest.prologue.legacyEvents=eventFlags({drawer:true,pot:true});const source=put(e,forest);e.faults.load.set(forest.prologue.moss.map,Error('offline'));
  assert.equal(await e.complete(e.c.loadGrowthData()),false);assert.equal(e.c.flags.drawer,false);assert.equal(e.c.flags.pot,false);assert.equal(e.c.localStorage.getItem('slot'),source);
 });
 for(const stage of [1,3])await test('current new-village stage '+stage+' retains its recorded coordinates',async()=>{const e=env(),d=save(stage,'rilde_village_01_peace');put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.storyStage,stage);assert.equal(e.M.feet.x,117);assert.equal(e.M.feet.y,242)});
 await test('unknown map and invalid acquisition boolean are read-only refused',async()=>{for(const modify of [d=>d.prologue.moss.map='unknown_map',d=>{d.prologue.legacyEvents=eventFlags();d.prologue.legacyEvents.drawer='false';}]){const e=env(),d=save();modify(d);const raw=put(e,d);assert.equal(e.c.SaveContinue.inspect().ok,false);assert.equal(await e.c.SaveContinue.start(),false);assert.equal(e.c.localStorage.getItem('slot'),raw);}});
 await test('legitimate old free-roam SAVE retains actual inventory and progression',async()=>{const e=env(),d=save(15,'fort_dunvall_03_keep');d.inventory.claimed=[...d.prologue.moss.opened];const raw=put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.deepEqual(JSON.parse(JSON.stringify(e.c.Inventory.serialize())),d.inventory);assert.equal(e.c.storyStage,15);assert.equal(e.c.PrologueProgress.count(),3);assert.equal(e.c.localStorage.getItem('slot'),raw);});
 await test('only proven old subquest states restore completion, while new flags preserve partial quest state',async()=>{const e=env(),d=save();d.prologue.subQuests={balloon:{state:'done'},cat:{state:'active',objective:'女の子にミルの居場所を知らせよう！'}};put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.flags.balloonDone,true);assert.equal(e.c.flags.catFound,true);assert.equal(e.c.flags.catDone,false);const f=env(),fresh=save();fresh.prologue.legacyEvents=eventFlags({cat:true,catFound:true});put(f,fresh);assert.equal(await f.complete(f.c.SaveContinue.start()),true);assert.equal(f.c.flags.catFound,true);assert.equal(f.c.flags.catDone,false)});
 await test('explicitly saving an old unknown history preserves restriction provenance without inventing collection',async()=>{const e=env(),d=save();put(e,d);assert.equal(await e.complete(e.c.SaveContinue.start()),true);const query=e.c.$;e.c.$=selector=>selector==='#doSave'?null:query(selector);e.c.saveGrowthData();const raw=e.c.localStorage.getItem('slot'),record=JSON.parse(raw);assert.deepEqual(record.prologue.legacyEvents.unknown,['drawer','pot']);const cold=env();cold.c.localStorage.setItem('slot',raw);assert.equal(await cold.complete(cold.c.SaveContinue.start()),true);assert.deepEqual(Array.from(cold.c.PrologueProgress.eventSnapshot().unknown),['drawer','pot']);assert.equal(cold.c.flags.drawer,true);assert.equal(cold.c.flags.pot,true)});
 await test('malformed party, item or map-event records are refused before mutation',async()=>{for(const modify of [d=>d.members.aidan.level='bad',d=>d.active=['unknown'],d=>d.inventory.claimed='bad',d=>d.prologue.moss.fired='bad',d=>d.battleItems.potion=-1,d=>d.prologue.moss.facing.dir='unknown']){const e=env(),d=save();modify(d);const raw=put(e,d);assert.equal(e.c.SaveContinue.inspect().ok,false);assert.equal(await e.c.SaveContinue.start(),false);assert.equal(e.c.localStorage.getItem('slot'),raw);assert.equal(e.c.storyStage,0)}});
 assert.ok(n);console.log(n+' PASS; actual restore modules; simulated DOM/network; browser NOT_RUN');
})().catch(e=>{console.error('FAIL',e.stack);process.exitCode=1});
