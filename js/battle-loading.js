// One battle-entry transaction for normal and Raider. Existing combat owns everything after commit.
(() => {
 'use strict';
 let generation=0,pending=null,phase='IDLE';
 const originals={normal:startAttackBattle,raider:startRaiderBattle};
 function view(failed=false){
  LoadingView.open('battle',failed?'戦闘の準備ができませんでした。記録は保持されています。':'戦闘を準備しています。',failed?retry:null);
  document.body.classList.add('battleLoadingBusy');window.syncBattleCommandLocks?.();
 }
 function hide(){LoadingView.close('battle');document.body.classList.remove('battleLoadingBusy');window.syncBattleCommandLocks?.();}
 function actors(kind,id){
  if(kind==='raider')return ['aidan','fiona','lou','goblin_raider'];
  const enemies=/^mossSlime/.test(id)?['moss_slime']:/^forestBat/.test(id)?['forest_bat']:/^leafyBoar/.test(id)?['leafy_boar']:/^fieldGob/.test(id)||id==='attackGob1'?['goblin']:['goblin','tainted_goblin'];
  return ['aidan',...(id==='attackGob1'?[]:['fiona']),...enemies];
 }
 async function prepare(kind,id){
  const cast=actors(kind,id),urls=new Set();
  for(const actor of cast){
   if(!BATTLE_ASSETS[actor]?.idle)throw Error('Missing required actor '+actor);
   urls.add(BATTLE_ASSETS[actor].idle);
   for(const frame of window.BATTLE_IDLE_ASSETS?.[actor]?.frames||[])urls.add(frame.path);
  }
  // Wait for the existing optional manifest request; a missing manifest has the established still-only fallback.
  await BattleMotion.manifestReady;
  for(const [actor,state] of window.BattleOpening?.states||[]){
   if(!cast.includes(actor))continue;
   const motion=BattleMotion.frames(actor,state);
   if(motion){for(const url of motion.urls)urls.add(url);if(BATTLE_ASSETS[actor]?.[state])urls.add(BATTLE_ASSETS[actor][state]);}
  }
  for(const actor of cast)for(const url of BattleMotion.frames(actor,'idle')?.urls||[])urls.add(url);
  const bg=kind==='normal'&&window.BattleBackground?.BG[BattleBackground.forEnemy(id)];
  if(bg?.src)urls.add(bg.src); // Unregistered regions retain the established CSS gradient.
  const results=await Promise.all([...urls].map(url=>LoadingAssets.image(url)));
  const missing=results.filter(r=>r.status!=='ready');
  if(missing.length)throw Error('Required battle art unavailable');
  return results;
 }
 async function execute(request){
  const token=++generation;phase='LOADING';pending=request;view();
  const combatGeneration=window.PrologueCombat?.generation;
  try{
   await prepare(request.kind,request.args[0]);
   if(token!==generation||pending!==request)return false;
   if(combatGeneration!==window.PrologueCombat?.generation){cancel();return false;}
   // Keep the overlay/input lock through synchronous combat initialization.
   originals[request.kind](...request.args);
   await LoadingView.settle('battle');
   if(token!==generation||pending!==request)return false;
   pending=null;phase='IDLE';hide();return true;
  }catch(error){
   if(token===generation&&pending===request){phase='FAILED';view(true);}
   return false;
  }
 }
 function start(kind,args){
  if(phase!=='IDLE'||document.body.classList.contains('battleMode')||window.MossForest?.entering||window.LoadCoordinator?.canSave===false)return Promise.resolve(false);
  if(kind==='normal'&&(attackBattleBusy||PrologueProgress.cleared(args[0])))return Promise.resolve(false);
  return execute({kind,args});
 }
 function retry(){return phase==='FAILED'&&pending?execute(pending):Promise.resolve(false);}
 function cancel(){generation++;pending=null;phase='IDLE';hide();}
 startAttackBattle=(...args)=>start('normal',args);
 startRaiderBattle=(...args)=>start('raider',args);
 window.BattleLoading=Object.freeze({prepare,retry,cancel,get phase(){return phase},get busy(){return phase!=='IDLE'},get canSave(){return phase==='IDLE'}});
})();
