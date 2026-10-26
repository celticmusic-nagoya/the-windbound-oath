// Cold/title restore boundary. Reuses LOAD's application, checkpoint policy and coordinator ownership.
(() => {
 'use strict';
 let phase='TITLE',error='',active=null;
 const clone=x=>JSON.parse(JSON.stringify(x));
 const object=x=>Boolean(x&&typeof x==='object'&&!Array.isArray(x));
 const key=()=>typeof SAVE_KEY==='string'?SAVE_KEY:'windbound_oath_v028';
 const notify=()=>window.TitleScreen?.refresh();
 function checkKeys(x){if(!x||typeof x!=='object')return;for(const [k,v]of Object.entries(x)){if(['__proto__','constructor','prototype'].includes(k))throw Error('未対応の記録です。');checkKeys(v);}}
 function inspect(){
  try{
   const raw=localStorage.getItem(key());if(!raw)return {ok:false,error:'セーブデータがありません。'};
   const saved=JSON.parse(raw);checkKeys(saved);const p=saved?.prologue;
   if(!object(saved)||!object(p)||![1,2].includes(p.version)||!Number.isInteger(p.storyStage)||p.storyStage<0||p.storyStage>15||!(saved.version===30||(saved.version===undefined&&p.version===1)))throw Error('未対応または不完全な記録です。');
   if(!object(saved.inventory)||!object(saved.members)||!object(saved.members.aidan)||!Array.isArray(saved.active))throw Error('復帰に必要な情報が不足しています。');
   for(const [id,m]of Object.entries(saved.members))if(!Object.prototype.hasOwnProperty.call(PartyManager.members,id)||!object(m)||typeof m.joined!=='boolean'||!Number.isInteger(m.level)||m.level<1||m.level>50||!Number.isFinite(m.exp)||m.exp<0)throw Error('仲間の記録が不正です。');
   if(saved.active.length<1||saved.active.length>PartyManager.maxActive||new Set(saved.active).size!==saved.active.length||saved.active.some(id=>typeof id!=='string'||!saved.members[id]?.joined))throw Error('編成の記録が不正です。');
   if(saved.reserve!==undefined&&(!Array.isArray(saved.reserve)||saved.reserve.some(id=>typeof id!=='string'||!saved.members[id]?.joined)))throw Error('控え編成の記録が不正です。');
   for(const values of [saved.inventory.key,saved.inventory.gear,saved.battleItems])if(values!==undefined&&(!object(values)||Object.values(values).some(n=>!Number.isInteger(n)||n<0)))throw Error('所持品の記録が不正です。');
   if(saved.inventory.claimed!==undefined&&(!Array.isArray(saved.inventory.claimed)||saved.inventory.claimed.some(x=>typeof x!=='string')))throw Error('取得履歴の記録が不正です。');
   if(p.moss?.map&&p.version===2){
    if(!['opened','fired'].every(k=>Array.isArray(p.moss[k])&&p.moss[k].every(x=>typeof x==='string')))throw Error('マップイベントの記録が不完全です。');
    if(p.moss.facing!==undefined&&(!object(p.moss.facing)||!['up','down','left','right','dl','ul'].includes(p.moss.facing.dir)||typeof p.moss.facing.flip!=='boolean'))throw Error('向きの記録が不正です。');
   }
   if(saved.gold!==undefined&&(!Number.isFinite(saved.gold)||saved.gold<0))throw Error('所持金の記録が不正です。');
   const checkpoint=TrainingCheckpoint.prepare(saved,raw),data=EquipmentManager.migrateStarterSword(checkpoint.data),progress=data.prologue;
   let fallback=null;
   if(progress.storyStage<=3&&progress.storyStage!==2&&!checkpoint.restoreVillage&&!MossForestStory.canRestoreEarlyMap(progress,progress.storyStage)){
    if(progress.moss?.map)throw Error('この初期マップの記録には復帰できません。');
    fallback=progress.storyStage===0?['rilde_in_aidan','from_bed']:['rilde_village_01_peace',progress.storyStage===1?'from_training':'from_sunset'];
   }
   if(progress.moss?.map&&progress.version===2&&[0,1,3,9,10,11,12,15].includes(progress.storyStage)&&(!Number.isFinite(progress.moss.x)||!Number.isFinite(progress.moss.y)))throw Error('座標の記録が不完全です。');
   if(progress.version===2&&progress.moss?.map){
    const stage=progress.storyStage,supported=stage<=3?MossForestStory.canRestoreEarlyMap(progress,stage):stage>=9&&stage<=12?Object.values(MossForestStory.MAP_IDS).includes(progress.moss.map):stage===15?MossForestStory.canRestoreFreeRoamMap(progress,stage):true;
    if(!supported)throw Error('このマップの記録には復帰できません。');
   }
   const route=PrologueProgress.plan(progress,checkpoint.restoreVillage);
   if(route.stage!==progress.storyStage)throw Error('進行状態の整合性を確認できません。');
   return {ok:true,raw,data,checkpoint,route,fallback};
  }catch(e){return {ok:false,error:e.message||'セーブデータを確認できません。'};}
 }
 function capture(){return {members:clone(PartyManager.members),active:clone(PartyManager.active),reserve:clone(PartyManager.reserve),squads:clone(PartyManager.squads),support:clone(PartyManager.support),gold,battleItems:clone(battleItems),inventory:Inventory.serialize(),equipment:EquipmentManager.serialize(),quests:Quest.serialize(),talk:FieldTalk.serialize(),progress:PrologueProgress.serialize(),flags:clone(flags),room,px,py,oathBound:typeof oathBound==='boolean'?oathBound:false};}
 function replace(target,value){for(const k of Object.keys(target))delete target[k];Object.assign(target,clone(value));}
 function rollback(s,token){
  LoadCoordinator.assertCurrent(token);devResetScreens(token);MossForest.reset();
  replace(PartyManager.members,s.members);PartyManager.active=clone(s.active);PartyManager.reserve=clone(s.reserve);PartyManager.squads=clone(s.squads);PartyManager.support=clone(s.support);
  gold=s.gold;replace(battleItems,s.battleItems);Inventory.load(s.inventory);EquipmentManager.load(s.equipment);Inventory.load(s.inventory);Quest.load(s.quests);FieldTalk.load(s.talk);replace(flags,s.flags);
  PrologueProgress.restoreModel(s.progress,s.progress.storyStage,token);MossForest.restoreState(s.progress.moss);room=s.room;px=s.px;py=s.py;if(typeof oathBound==='boolean')oathBound=s.oathBound;
  for(const id of ['cinema','returnScene','escapeScene','louIntroScene','altarScene','aftermathScene','fortScene','prologueEnd','attackBattle','raiderBattle','inside','forestScene']){const n=document.getElementById(id);if(n)n.style.display='none';}
  document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','villageAttack','northAssault','actionCinematic');
 }
 async function start(){
  if(phase!=='TITLE')return false;
  const prepared=inspect();if(!prepared.ok){error=prepared.error;phase='TITLE';notify();return false;}
  phase='LOADING';error='';notify();let token,unsubscribe=()=>{},restore=null;
  const ok=await LoadCoordinator.boot(async owner=>{
   token=owner;const previous=capture();let applied=false;
   restore=()=>{if(applied)return;applied=true;unsubscribe();rollback(previous,owner);LoadingView.close('continue:'+owner);};
   active={token:owner,rollback:restore};unsubscribe=LoadCoordinator.onInvalidate(restore);
   LoadingView.open('continue:'+owner,'記録を復帰しています。');
   try{
    const {data,checkpoint}=prepared;
    if(prepared.fallback){
     const [map,spawn]=prepared.fallback,m=await ForestLoader.load('data/maps/'+map+'.json');LoadCoordinator.assertCurrent(owner);
     const sp=m.spawns.points[spawn];if(!sp)throw Error('互換復帰地点がありません。');
     data.prologue.version=2;data.prologue.moss={...(data.prologue.moss||{}),map,x:sp.x-17,y:sp.y-42,opened:MossForestStory.openedFromSave(data.prologue),fired:data.prologue.moss?.fired||[]};
    }
    const route=PrologueProgress.plan(data.prologue,checkpoint.restoreVillage);
    await applyGrowthData(data,route,checkpoint,owner);LoadCoordinator.assertCurrent(owner);
    if(route.kind==='FIELD_MAP'||route.kind==='TRAINING_RETRY'){
     const m=data.prologue.moss;
     if(m&&(!MossForest.active||MossForest.mapId!==m.map||Math.abs(MossForest.feet.x-(m.x+17))>1||Math.abs(MossForest.feet.y-(m.y+42))>1))throw Error('保存地点を安全に復帰できませんでした。');
    }else if(data.prologue.storyStage>=4&&data.prologue.storyStage<=8)restoreContinueLegacy(data.prologue);
    await LoadingView.settle('continue:'+owner);LoadCoordinator.assertCurrent(owner);
    unsubscribe();active=null;LoadingView.close('continue:'+owner);
   }catch(e){if(LoadCoordinator.current(owner))restore();throw e;}
  });
  if(!LoadCoordinator.current(token))return false;
  active=null;phase=ok?'READY':'TITLE';if(!ok)error='復帰できませんでした。セーブは保持されています。';notify();return ok;
 }
 async function newGame(launch){phase='NEW_GAME';error='';notify();const ok=await launch();phase=ok===false?'TITLE':'READY';notify();return ok!==false;}
 window.SaveContinue=Object.freeze({inspect,start,newGame,get phase(){return phase},get error(){return error}});
})();
