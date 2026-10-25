// Real coordinator, RildeVillage, S2 runtime, FieldTalk, HTML say/dev/LOAD. Network/rendering adapters only.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const {environment,deferred,flush}=require('./s2_transition_recovery.test.cjs');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
function extractDevBlock(source){
 const start=/^function devResetScreens\s*\(/m.exec(source);
 assert.ok(start,'fixture: product devResetScreens declaration not found');
 const end=source.indexOf("$('#devGrid').innerHTML",start.index);
 assert.ok(end>start.index,'fixture: product DEV block end not found');
 const block=source.slice(start.index,end);
 assert.match(block,/^function devJump\s*\(/m,'fixture: product devJump declaration not found');
 return block;
}
function setup(){
 const e=environment(),c=e.c;c.URLSearchParams=URLSearchParams;c.flags={};c.$=e.node;c.popObjective=()=>{};c.msg=e.node('#msg');
 Object.defineProperty(c.msg,'textContent',{configurable:true,get(){return this._text||this.children.map(n=>n.textContent).join('')},set(v){this._text=v;this.children=[]}});
 c.msg.querySelector=function(s){return this.children.find(n=>s[0]==='.'?n.className===s.slice(1):n.tagName===s.toUpperCase())||null;};
 vm.runInContext(html.slice(html.indexOf('function say(t)'),html.indexOf('function camera()')),c);
 e.load('js/load-coordinator.js');e.load('js/prologue-progress.js');e.load('js/field/moss-forest-story.js');e.load('js/field/rilde-village.js');e.load('js/field/talk-conditions.js');e.load('js/field/field-talk.js');
 c.FieldTalk.loadTable({npc:'other',entries:[{id:'other1',when:{},lines:[['別の会話']]}]});
 const m=e.map('rilde_in_aidan');m.spawns.points.from_bed=m.spawns.points.start;e.worlds.set('rilde_in_aidan',m);
 vm.runInContext(html.split('\n').find(s=>s.startsWith('function enterWorldMap(')),c);
 const devBlock=extractDevBlock(html);vm.runInContext(devBlock,c);
 for(const name of ['devResetScreens','devJump']){assert.equal(typeof c[name],'function','fixture: missing '+name);assert.ok(devBlock.includes(c[name].toString()),'fixture must execute exact product '+name);}
 return e;
}
function loadSave(e){const c=e.c,saved=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/issue54-stage15.json')));c.PartyManager={members:structuredClone(saved.members),active:[],reserve:[],support:{}};c.Inventory={load(){},reconcile(){}};c.EquipmentManager={migrateStarterSword:x=>x,load(){}};c.Quest={load(){}};c.battleItems={};c.gold=0;c.notice=()=>{};c.renderSystemTab=()=>{};c.syncStoryEquipment=()=>{};c.SAVE_KEY='slot';const raw=JSON.stringify(saved);c.localStorage.setItem('slot',raw);e.load('js/prologue-progress.js');e.load('js/training-checkpoint.js');const a=html.indexOf('function saveGrowthData()'),b=html.indexOf("$('#menuOpen').onclick",a);vm.runInContext(html.slice(a,b),c);return {raw,saved};}
async function pendingLoad(){
 const e=setup();await e.complete(e.c.RildeVillage.startOpening());
 const {raw,saved}=loadSave(e);await e.complete(e.c.TrainingCheckpoint.ready);
 const delayed=deferred();e.faults.load.set(saved.prologue.moss.map,delayed);
 const task=e.c.loadGrowthData();await flush();
 assert.equal(e.c.LoadCoordinator.phase,'LOADING');
 return {e,raw,saved,delayed,task};
}
let n=0;async function test(name,fn){if(process.env.STARTUP_TEST_FILTER&&!name.includes(process.env.STARTUP_TEST_FILTER))return;await fn();console.log('PASS',name);n++;}
(async()=>{
 await test('NEW GAME commits initial map, opens narration, close restores normal dialogue state',async()=>{const e=setup();assert.equal(await e.complete(e.c.RildeVillage.startOpening()),true);assert.equal(e.M.mapId,'rilde_in_aidan');assert.equal(e.c.LoadCoordinator.phase,'READY');await e.advance(350);assert.ok(e.c.msg.textContent.includes('朝の風'));e.c.closeDialogue();assert.equal(e.c.document.body.classList.contains('dialogueOpen'),false);assert.equal(e.M.active,true)});
 await test('real FieldTalk begun during narration delay is never overwritten and last-page tap closes it',async()=>{const e=setup();await e.complete(e.c.RildeVillage.startOpening());assert.equal(e.c.FieldTalk.talk('other'),true);await e.advance(350);assert.equal(e.c.FieldTalk.active,true);assert.ok(e.c.msg.textContent.includes('別の会話'));e.c.msg.listeners.click({target:{closest:()=>false},stopImmediatePropagation(){}});assert.equal(e.c.FieldTalk.active,false);assert.equal(e.c.msg.style.display,'none')});
 await test('a newer conversation that already ended also cancels old narration',async()=>{const e=setup();await e.complete(e.c.RildeVillage.startOpening());e.c.FieldTalk.talk('other');e.c.msg.listeners.click({target:{closest:()=>false},stopImmediatePropagation(){}});await e.advance(350);assert.equal(e.c.msg.textContent,'');assert.equal(e.c.FieldTalk.active,false)});
 await test('plain say dialogue has priority over startup narration',async()=>{const e=setup();await e.complete(e.c.RildeVillage.startOpening());e.c.say('調べた内容');await e.advance(350);assert.equal(e.c.msg.textContent,'調べた内容')});
 await test('real devJump invalidates old boot fetch and coordinator owner, latest destination wins',async()=>{const e=setup(),old=deferred();e.faults.load.set('rilde_in_aidan',old);const boot=e.c.RildeVillage.startOpening();await flush();e.c.devJump('map:dev_monster_arena');const done=deferred();e.faults.hook=m=>{if(m.id==='dev_monster_arena')done.resolve()};await e.complete(done.promise);old.resolve(e.worlds.get('rilde_in_aidan'));assert.equal(await e.complete(boot),false);await e.advance(500);assert.equal(e.M.mapId,'dev_monster_arena');assert.equal(e.c.storyStage,15);assert.equal(e.c.LoadCoordinator.phase,'READY');assert.equal(e.c.msg.textContent,'')});
 await test('new boot supersedes older boot without stale map/dialogue/FAILED state',async()=>{const e=setup(),old=deferred();e.faults.load.set('rilde_in_aidan',old);const a=e.c.RildeVillage.startOpening();await flush();e.faults.load.delete('rilde_in_aidan');const b=e.c.RildeVillage.startOpening();assert.equal(await e.complete(b),true);old.resolve(e.worlds.get('rilde_in_aidan'));assert.equal(await e.complete(a),false);await e.advance(350);assert.equal(e.c.LoadCoordinator.phase,'READY');assert.equal(e.M.mapId,'rilde_in_aidan');assert.ok(e.c.msg.textContent.includes('朝の風'))});
 await test('LOAD during boot is rejected without touching original save bytes',async()=>{const e=setup(),d=deferred(),{raw}=loadSave(e);await e.complete(e.c.TrainingCheckpoint.ready);e.faults.load.set('rilde_in_aidan',d);const boot=e.c.RildeVillage.startOpening();assert.equal(await e.c.loadGrowthData(),false);assert.equal(e.c.localStorage.getItem('slot'),raw);d.resolve(e.worlds.get('rilde_in_aidan'));await e.complete(boot)});
 await test('normal LOAD invalidates an already scheduled startup narration and preserves save/flags',async()=>{const e=setup();await e.complete(e.c.RildeVillage.startOpening());const {raw,saved}=loadSave(e);await e.complete(e.c.TrainingCheckpoint.ready);assert.equal(await e.complete(e.c.loadGrowthData()),true);await e.advance(500);assert.equal(e.M.mapId,saved.prologue.moss.map);assert.equal(e.c.storyStage,15);assert.equal(e.c.msg.textContent,'');assert.equal(e.c.localStorage.getItem('slot'),raw)});
 await test('late initial fetch cannot overwrite a DEV destination followed by actual LOAD',async()=>{const e=setup(),d=deferred();e.faults.load.set('rilde_in_aidan',d);const boot=e.c.RildeVillage.startOpening();await flush();e.c.devJump('map:dev_monster_arena');const ready=deferred();e.faults.hook=m=>{if(m.id==='dev_monster_arena')ready.resolve()};await e.complete(ready.promise);const {raw,saved}=loadSave(e);await e.complete(e.c.TrainingCheckpoint.ready);assert.equal(await e.complete(e.c.loadGrowthData()),true);d.resolve(e.worlds.get('rilde_in_aidan'));assert.equal(await e.complete(boot),false);await e.advance(500);assert.equal(e.M.mapId,saved.prologue.moss.map);assert.equal(e.c.localStorage.getItem('slot'),raw);assert.equal(e.c.LoadCoordinator.phase,'READY')});
 await test('pagehide/reload invalidates old realm; fresh realm starts independently',async()=>{const old=setup(),d=deferred();old.faults.load.set('rilde_in_aidan',d);const boot=old.c.RildeVillage.startOpening();await flush();old.c.dispatchEvent({type:'pagehide',persisted:false});const fresh=setup();assert.equal(await fresh.complete(fresh.c.RildeVillage.startOpening()),true);d.resolve(old.worlds.get('rilde_in_aidan'));assert.equal(await old.complete(boot),false);assert.equal(old.M.mapId,null);await fresh.advance(350);assert.equal(fresh.c.LoadCoordinator.phase,'READY');assert.ok(fresh.c.msg.textContent.includes('朝の風'))});
 await test('startup failure stays protected, explicit retry succeeds; stale token cannot start events',async()=>{const e=setup();e.faults.load.set('rilde_in_aidan',Error('offline'));assert.equal(await e.complete(e.c.RildeVillage.startOpening()),false);assert.equal(e.c.LoadCoordinator.canSave,false);e.faults.load.delete('rilde_in_aidan');assert.equal(await e.complete(e.c.LoadCoordinator.retry()),true);const old=e.c.LoadCoordinator.generation;e.c.LoadCoordinator.supersede();await assert.rejects(e.c.RildeVillage.startOpening(old));assert.equal(e.c.LoadCoordinator.phase,'READY')});
 await test('fixture extraction is exact, argument-independent and rejects missing declarations',async()=>{
  const block=extractDevBlock(html);assert.ok(block.includes('function devResetScreens(ownerToken)'));
  assert.ok(extractDevBlock(html.replace('devResetScreens(ownerToken)','devResetScreens(a,b,c)')).includes('devResetScreens(a,b,c)'));
  assert.throws(()=>extractDevBlock(''),/declaration not found/);
  assert.throws(()=>extractDevBlock(html.replace('function devJump(key)','function omitted(key)')),/devJump declaration not found/);
 });
 await test('LOAD internal reset preserves the current token; stale internal reset is rejected before mutations',async()=>{
  const e=setup();await e.complete(e.c.RildeVillage.startOpening());loadSave(e);await e.complete(e.c.TrainingCheckpoint.ready);
  const reset=e.c.devResetScreens,seen=[];
  e.c.devResetScreens=token=>{const before=e.c.LoadCoordinator.generation;reset(token);seen.push({token,before,after:e.c.LoadCoordinator.generation});};
  assert.equal(await e.complete(e.c.loadGrowthData()),true);assert.equal(seen.length,1);assert.equal(seen[0].token,seen[0].before);assert.equal(seen[0].after,seen[0].before);
  const map=e.M.mapId,old=e.c.LoadCoordinator.generation;e.c.LoadCoordinator.supersede();assert.throws(()=>reset(old),/Cancelled load/);assert.equal(e.M.mapId,map);
 });
 await test('NEW GAME during LOAD supersedes the pending LOAD and discards its late map response',async()=>{
  const {e,raw,saved,delayed,task}=await pendingLoad();
  assert.equal(await e.complete(e.c.RildeVillage.startOpening()),true);
  delayed.resolve(e.map(saved.prologue.moss.map));assert.equal(await e.complete(task),false);await e.advance(500);
  assert.equal(e.M.mapId,'rilde_in_aidan');assert.equal(e.c.storyStage,0);assert.equal(e.c.LoadCoordinator.phase,'READY');assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('second LOAD while LOADING is rejected; the latest accepted owner alone commits',async()=>{
  const {e,raw,saved,delayed,task}=await pendingLoad(),owner=e.c.LoadCoordinator.generation;
  assert.equal(await e.c.loadGrowthData(),false);assert.equal(e.c.LoadCoordinator.generation,owner);
  delayed.resolve(e.map(saved.prologue.moss.map));assert.equal(await e.complete(task),true);
  assert.equal(e.M.mapId,saved.prologue.moss.map);assert.equal(e.c.LoadCoordinator.phase,'READY');assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('goto via actual DEV navigation during LOAD wins over an out-of-order LOAD response',async()=>{
  const {e,raw,saved,delayed,task}=await pendingLoad(),arrived=deferred();
  e.faults.hook=m=>{if(m.id==='dev_monster_arena')arrived.resolve()};e.c.devJump('map:dev_monster_arena');await e.complete(arrived.promise);
  delayed.resolve(e.map(saved.prologue.moss.map));assert.equal(await e.complete(task),false);await e.advance(500);
  assert.equal(e.M.mapId,'dev_monster_arena');assert.equal(e.c.LoadCoordinator.phase,'READY');assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('reload during LOAD invalidates old owner; a new realm is unaffected by the late reply',async()=>{
  const {e,raw,saved,delayed,task}=await pendingLoad();e.c.dispatchEvent({type:'pagehide',persisted:false});
  const fresh=setup();assert.equal(await fresh.complete(fresh.c.RildeVillage.startOpening()),true);
  delayed.resolve(e.map(saved.prologue.moss.map));assert.equal(await e.complete(task),false);await fresh.advance(350);
  assert.equal(fresh.M.mapId,'rilde_in_aidan');assert.equal(fresh.c.LoadCoordinator.phase,'READY');assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('failed LOAD preserves source bytes and stable map flags; explicit retry recovers safely',async()=>{
  const e=setup();await e.complete(e.c.RildeVillage.startOpening());const flags=JSON.stringify(e.M.flags),{raw,saved}=loadSave(e);await e.complete(e.c.TrainingCheckpoint.ready);
  e.faults.load.set(saved.prologue.moss.map,Error('offline'));assert.equal(await e.complete(e.c.loadGrowthData()),false);
  assert.equal(e.c.LoadCoordinator.phase,'FAILED');assert.equal(e.c.LoadCoordinator.canSave,false);assert.equal(JSON.stringify(e.M.flags),flags);
  e.c.saveGrowthData();e.c.eraseGrowthData();assert.equal(e.c.localStorage.getItem('slot'),raw);
  e.faults.load.delete(saved.prologue.moss.map);assert.equal(await e.complete(e.c.LoadCoordinator.retry()),true);
  assert.equal(e.M.mapId,saved.prologue.moss.map);assert.equal(e.c.localStorage.getItem('slot'),raw);assert.equal(e.c.LoadCoordinator.phase,'READY');
 });
 await test('actual DOMContentLoaded boot path commits NEW GAME without a test-only ready gate',async()=>{
  const e=setup(),callbacks=[];e.c.document.readyState='loading';e.c.document.addEventListener=(type,fn)=>{if(type==='DOMContentLoaded')callbacks.push(fn)};
  const start=html.indexOf('(function startAtHome(){'),end=html.indexOf("document.addEventListener('contextmenu'",start);assert.ok(start>=0&&end>start);
  vm.runInContext(html.slice(start,end),e.c);assert.equal(callbacks.length,1);callbacks[0]();await e.advance(2000);
  assert.equal(e.c.LoadCoordinator.phase,'READY');assert.equal(e.M.mapId,'rilde_in_aidan');assert.ok(e.c.msg.textContent.includes('朝の風'));
 });
 await test('DEV destination before DOMContentLoaded cancels the scheduled initial boot',async()=>{
  const e=setup(),callbacks=[],arrived=deferred();e.c.document.readyState='loading';e.c.document.addEventListener=(type,fn)=>{if(type==='DOMContentLoaded')callbacks.push(fn)};
  const start=html.indexOf('(function startAtHome(){'),end=html.indexOf("document.addEventListener('contextmenu'",start);vm.runInContext(html.slice(start,end),e.c);
  e.faults.hook=m=>{if(m.id==='dev_monster_arena')arrived.resolve()};e.c.devJump('map:dev_monster_arena');callbacks[0]();await e.complete(arrived.promise);await e.advance(1000);
  assert.equal(e.M.mapId,'dev_monster_arena');assert.equal(e.loads.includes('rilde_in_aidan'),false);assert.equal(e.c.LoadCoordinator.phase,'READY');
 });
 assert.ok(n,'at least one case must run');
 console.log(n+' PASS; real product code, simulated DOM/network/timers; browser NOT_RUN');
})().catch(e=>{console.error('FAIL',e.stack);process.exitCode=1});
