// Real inventory/progress/LOAD modules; the legacy house proximity adapter is DOM-only.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {env,save,put}=require('./continue_restore.test.cjs'),{deferred,flush}=require('./s2_transition_recovery.test.cjs');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
let n=0;async function test(name,fn){await fn();n++;console.log('PASS',name)}
async function ready(){const e=env();await e.complete(e.c.RildeVillage.startOpening());e.c.closeDialogue();return e;}
function legacy(e,id){const line=html.split('\n').find(s=>s.startsWith("$('#"+id+"').onclick="));assert.ok(line,'fixture: house handler missing');e.c.needNear=(_el,fn)=>fn();e.c.room='home';vm.runInContext(line,e.c);e.node('#'+id).onclick();}
(async()=>{
 for(const [id,item,amount] of [['drawer','potion',1],['pot','gold',3]])for(const oldFirst of [false,true])await test(id+' old/new entry share one flag, legacy first='+oldFirst,async()=>{
  const e=await ready(),c=e.c,count=()=>item==='gold'?c.gold:c.Inventory.count(item),before=count();
  const hook=()=>c.RildeVillage.hook({hook:'rilde_'+id},e.M.map);
  if(oldFirst)legacy(e,id);else hook();assert.equal(count()-before,amount);assert.equal(c.flags[id],true);
  legacy(e,id);hook();legacy(e,id);assert.equal(count()-before,amount);
 });
 for(const value of [undefined,0,2])await test('cold CONTINUE restores optional antidote exactly: '+value,async()=>{
  const e=env(),d=save();d.prologue.legacyEvents={v:1,drawer:true,pot:true,balloon:true,balloonDone:true,cat:true,catFound:true,catDone:true};
  if(value!==undefined)d.battleItems.antidote=value;
  const raw=put(e,d);e.c.battleItems.antidote=9;
  assert.equal(await e.complete(e.c.SaveContinue.start()),true);assert.equal(e.c.Inventory.count('antidote'),value||0);assert.equal(e.c.flags.catDone,true);assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('successful in-game old LOAD removes only absent new stock and never compensates',async()=>{
  const e=await ready(),d=save(),raw=put(e,d);e.c.battleItems.antidote=9;
  assert.equal(await e.complete(e.c.loadGrowthData()),true);assert.equal(e.c.Inventory.count('antidote'),0);assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('failed old LOAD keeps current antidote and source SAVE',async()=>{
  const e=await ready(),d=save(),raw=put(e,d);e.c.battleItems.antidote=2;e.faults.prepare=()=>{throw Error('offline')};
  assert.equal(await e.complete(e.c.loadGrowthData()),false);assert.equal(e.c.Inventory.count('antidote'),2);assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('superseded old LOAD cannot clear antidote when its late response arrives',async()=>{
  const e=await ready(),gate=deferred(),raw=put(e,save());e.c.battleItems.antidote=2;let prepared=false;e.faults.prepare=()=>{prepared=true;return gate.promise};const task=e.c.loadGrowthData();await flush();assert.equal(prepared,true,'fixture must hold actual map preparation');assert.equal(e.c.LoadCoordinator.phase,'LOADING');e.c.LoadCoordinator.supersede();gate.resolve();assert.equal(await e.complete(task),false);assert.equal(e.c.Inventory.count('antidote'),2);assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 await test('NEW GAME starts new optional stock at zero without touching existing SAVE',async()=>{
  const e=await ready(),raw=put(e,save());e.c.battleItems.antidote=2;await e.complete(e.c.RildeVillage.startOpening());assert.equal(e.c.Inventory.count('antidote'),0);assert.equal(e.c.flags.catDone,false);assert.equal(e.c.localStorage.getItem('slot'),raw);
 });
 for(const battle of ['normal','raider'])await test(battle+': held antidote cannot consume, act or apply an effect; potion/ether unchanged',async()=>{
  const e=await ready(),c=e.c;c.battleItems.antidote=2;c.PrologueCombat.activeAlly=()=>true;
  Object.assign(c,{aahp:40,normalFHP:30,normalFMP:5,normalActor:'aidan',normalActs:[],rbHP:40,rbFHP:30,rbFMP:5,rbActor:'aidan',rbActs:[]});
  c.BattleTargetSelector={active:false,open(){throw Error('held item must not select a target')}};
  c.advanceNormalActor=c.resolvePartyRound=()=>{throw Error('held item must not advance a turn')};
  e.load('js/battle-action-targets.js');
  const state=()=>JSON.stringify([c.battleItems,c.aahp,c.normalFHP,c.normalFMP,c.normalActor,c.normalActs,c.rbHP,c.rbFHP,c.rbFMP,c.rbActor,c.rbActs]);
  const before=state(),action={who:'aidan',kind:'item',item:'antidote',target:'fiona'};
  assert.equal(c.BattleActionTargets.item(battle,'antidote'),false);assert.equal(c.BattleActionTargets.applyItem(battle,action),false);assert.equal(action.used,undefined);assert.equal(state(),before);
  assert.equal(c.BattleActionTargets.applyItem(battle,{item:'potion',target:'aidan'}),true);assert.equal(battle==='normal'?c.aahp:c.rbHP,85);
  assert.equal(c.BattleActionTargets.applyItem(battle,{item:'ether',target:'fiona'}),true);assert.equal(battle==='normal'?c.normalFMP:c.rbFMP,17);assert.equal(c.Inventory.count('antidote'),2);
 });
 console.log(n+' PASS; real reward and SAVE logic; browser NOT_RUN');
})().catch(e=>{console.error('FAIL',e.stack);process.exitCode=1});
