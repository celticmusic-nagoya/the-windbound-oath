// Issue #54: training is not a serializable battle. Old checkpoints retry it.
(() => {
 'use strict';
 const q=s=>document.querySelector(s), MAP='rilde_village_01_peace';
 // Legacy v1 stage 2 is deliberately refused; original bytes are never converted.

 let generation=0, timers=new Set(), fieldLocked=false, map=null, collision=null;
 let preparing=null;
 function ensureMap(){
  if(map)return Promise.resolve();
  if(!preparing)preparing=fetch('data/maps/'+MAP+'.json').then(r=>{if(!r.ok)throw Error('map');return r.json()}).then(m=>{
   collision=ForestLoader.collisionModel(m,{rilde_fiona_waiting:false,rilde_ruined:false});map=m;
  }).finally(()=>{preparing=null});
  return preparing;
 }
 const ready=ensureMap().catch(()=>{});
 async function validate(p){await ensureMap();if(!safeVillagePosition(p.moss))deny();}

 function cancel(){
  generation++;for(const id of timers)clearTimeout(id);timers.clear();
  battleBusy=false;guarding=false;q('#bFiona')?.classList.remove('runeGlow');
  if(fieldLocked&&window.MossForest)MossForest.lock(false);
  fieldLocked=false;
 }
 function later(fn,ms){
  const token=generation,id=setTimeout(()=>{timers.delete(id);if(token===generation)fn()},ms);
  timers.add(id);return id;
 }
 function watchField(){
  MossForest.lock(true);fieldLocked=true;let idle=0;
  const poll=()=>{
   const hidden=q('#battle').style.display==='none';idle=hidden?idle+1:0;
   if(storyStage>=3){later(()=>{MossForest.lock(false);fieldLocked=false},1600);return}
   if(idle>4){MossForest.lock(false);fieldLocked=false;return}
   later(poll,400);
  };
  later(poll,400);
 }
 function deny(){throw Error('この訓練中の記録は安全な復帰条件を確認できません。元のセーブは保持されています。')}
 function consistent(d){
  const p=d.prologue;
  return !d.talk?.flags?.rilde_ruined&&Object.entries(d.members||{}).every(([id,m])=>['aidan','fiona'].includes(id)||m?.joined===false)&&d.members?.aidan?.joined===true&&d.members?.fiona?.joined===true&&d.support?.joined===false&&
   Array.isArray(p.defeated)&&p.defeated.length===0&&p.corruptionCount===0&&p.barrierOpen===false&&
   p.louFound===false&&p.attackStep===0&&p.northPhase===0&&p.forestStoneSeen===false;
 }
 function safeVillagePosition(m){
  if(!map||!collision||m?.map!==MAP||![m.x,m.y].every(Number.isFinite))return false;
  if(m.x<0||m.y<0||m.x+28>=map.world.width||m.y+42>=map.world.height)return false;
  // Training begins by interacting with this dummy, not from another map/room.
  const dummy=(map.eventZones||[]).find(z=>z.hook==='rilde_dummy')?.shape;
  if(!dummy||Math.hypot(m.x+17-dummy.cx,m.y+42-dummy.cy)>180)return false;
  // Refuse blocked/disconnected positions rather than letting enter() move the save.
  const x=dummy.cx-17,y=dummy.cy-42,n=Math.ceil(Math.hypot(x-m.x,y-m.y)/4);
  for(let i=0;i<=Math.max(1,n);i++){
   const t=i/Math.max(1,n);if(collision.blocked(m.x+(x-m.x)*t,m.y+(y-m.y)*t))return false;
  }
  return Array.isArray(m.opened)&&m.opened.every(x=>typeof x==='string')&&
   Array.isArray(m.fired)&&m.fired.every(x=>typeof x==='string');
 }
 function prepare(saved,raw){
  const p=saved?.prologue;
  // A string "2" is not a recognized training checkpoint either.
  if(p?.storyStage!==2){if(p&&Number(p.storyStage)===2)deny();return {data:saved,retry:false}}
  if(p.version===1)throw Error('旧形式v1の訓練中セーブには復帰できません。元のセーブは保持されています。');
  if((window.MossForest?.busy&&!fieldLocked&&LoadCoordinator.phase!=='FAILED')||!consistent(saved))deny();
  if(p.version===2){
   if(saved.version!==30||!window.RildeVillage?.enabled()||p.moss?.map!==MAP||![p.moss.x,p.moss.y].every(Number.isFinite)||p.moss.x<0||p.moss.y<0||!Array.isArray(p.moss.opened)||!Array.isArray(p.moss.fired)||
      !saved.inventory||!saved.equipment||!saved.quests||!saved.talk)deny();
  }else if(p.version===1){
   throw Error('旧形式v1の訓練中セーブには復帰できません。元のセーブは保持されています。');
  }else deny();
  const data=JSON.parse(JSON.stringify(saved));
  data.prologue.storyStage=1;data.prologue.currentObjective='訓練用の木人を調べよう';
  return {data,retry:true,restoreVillage:p.version===2};
 }
 async function restore(p,token){
  forestActive=true;q('#forestScene').style.display='block';
  MossForest.reset();MossForest.restoreState(p.moss);
  await MossForest.enter({map:MAP,x:p.moss.x,y:p.moss.y,flags:MossForestStory.flagsNow(),loadToken:token});
  LoadCoordinator.assertCurrent(token);
  if(MossForest.mapId!==p.moss.map||!MossForest.active||MossForest.feet.x!==p.moss.x+17||MossForest.feet.y!==p.moss.y+42)throw Error('Training position was not restored');
 }

 window.TrainingCheckpoint=Object.freeze({ready,validate,cancel,later,watchField,prepare,restore,get restoring(){return LoadCoordinator.phase==='LOADING'}});
})();
