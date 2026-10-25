// Additive save extension: stable encounter IDs are the source of the forest counter.
(() => {
 const q=s=>document.querySelector(s);
 const ids={forestGob1:'moss_corruption_01',forestGob2:'moss_corruption_02',forestGob3:'moss_corruption_03'};
 let defeated=new Set();
 function count(){return Object.values(ids).filter(id=>defeated.has(id)).length;}
 function cleared(field){return defeated.has(ids[field]||field);}
 function objective(){return '森を侵す異常化ゴブリンを討伐する　'+count()+' / 3';}
 function sync(){
  forestGobWins=count();
  for(const id of ['attackMother','attackChild'])q('#'+id).style.display=defeated.has('attackGob1')?'none':'';
  if(window.MossForestStory&&window.MossForest&&MossForest.map)MossForestStory.syncFlags();
 }
 function defeat(field){
  const id=ids[field]||field;if(defeated.has(id))return false;
  defeated.add(id);sync();
  if(ids[field]){
   setObj(objective());
   forestToast(count()===3?'穢れが消え、古代のルーンに風が戻った……。':'森を覆う異様な気配が、わずかに弱まった……。');
   if(count()===3){q('#forestScene').classList.add('windRestored');setTimeout(()=>q('#forestScene').classList.remove('windRestored'),1800)}
  }
  return true;
 }
 // Explicit false is new/unclaimed; absence is old/unknown, never the same value.
 let legacyUnknown=new Set();
 const legacyKeys=['drawer','pot','balloon','balloonDone','cat','catFound','catDone'];
 function legacyEvents(data){
  if(Object.prototype.hasOwnProperty.call(data,'legacyEvents')){
   const e=data.legacyEvents;
   if(!e||e.v!==1||legacyKeys.some(k=>typeof e[k]!=='boolean'))throw Error('取得イベントの記録が不完全です。');
   if(e.unknown!==undefined&&(!Array.isArray(e.unknown)||e.unknown.some(k=>!['drawer','pot'].includes(k)||e[k]!==true)))throw Error('取得履歴の互換情報が不正です。');
   return Object.fromEntries(legacyKeys.map(k=>[k,e[k]]));
  }
  const result={drawer:true,pot:true}; // history unavailable; compatibility restriction, not proof of collection
  for(const id of ['balloon','cat']){
   const state=data.subQuests?.[id]?.state;
   if(['locked','active','done'].includes(state)){
    result[id]=state!=='locked';result[id+'Done']=state==='done';
    if(id==='cat')result.catFound=state==='done'||(state==='active'&&data.subQuests.cat.objective==='女の子にミルの居場所を知らせよう！');
   }
  }
  return result;
 }
 function eventSnapshot(){return {v:1,...Object.fromEntries(legacyKeys.map(k=>[k,typeof flags==='object'&&flags[k]===true])),unknown:[...legacyUnknown].filter(k=>typeof flags==='object'&&flags[k]===true)};}
 function restoreEventSnapshot(profile,token){LoadCoordinator.assertCurrent(token);const restored=legacyEvents({legacyEvents:profile});if(typeof flags==='object')Object.assign(flags,restored);legacyUnknown=new Set(profile.unknown||[]);}
 function resetLegacyEvents(){legacyUnknown.clear();if(typeof flags==='object')for(const k of legacyKeys)flags[k]=false;}
 // Keep chest/event state, but do not save a hidden field as a free-roam checkpoint.
 function serialize(){
  const moss=window.MossForest?MossForest.snapshot():null;
  if(moss&&storyStage===15&&!MossForest.active)moss.map=null;
  return {version:2,legacyEvents:eventSnapshot(),defeated:[...defeated],corruptionCount:count(),barrierOpen:count()===3,louFound,storyStage,attackStep,northPhase,forestStoneSeen,moss,position:{px,py},currentObjective,subQuests:JSON.parse(JSON.stringify(subQuests))};
 }
 function plan(data,trainingRetry=false){
  if(!data||(data.version!==1&&data.version!==2))throw Error('Unsupported progress');
  legacyEvents(data);
  let stage=Math.max(0,Math.min(15,Number(data.storyStage)||0));
  const wins=Object.values(ids).filter(id=>Array.isArray(data.defeated)&&data.defeated.includes(id)).length;
  if(stage>=11&&wins<3)stage=10;
  if(trainingRetry){if(data.version!==2||stage!==1)throw Error('Invalid training plan');return Object.freeze({kind:'TRAINING_RETRY',stage})}
  if(stage===2)throw Error('Training save requires validated recovery');
  const field=(stage>=9&&stage<=12)||MossForestStory.canRestoreEarlyMap(data,stage)||MossForestStory.canRestoreFreeRoamMap(data,stage);
  return Object.freeze({kind:field?'FIELD_MAP':stage<=8?'LEGACY_SCENE':stage===13?'AFTERMATH':stage===14?'FORT_FINALE':'PROLOGUE_END',stage});
 }
 function restoreModel(data,stage=data.storyStage,token){
  LoadCoordinator.assertCurrent(token);
  const restoredEvents=legacyEvents(data);
  if(typeof flags==='object')Object.assign(flags,restoredEvents);
  legacyUnknown=new Set(data.legacyEvents?.unknown||(Object.prototype.hasOwnProperty.call(data,'legacyEvents')?[]:['drawer','pot']));
  defeated=new Set(Array.isArray(data.defeated)?data.defeated.filter(x=>typeof x==='string'&&([...Object.values(ids),'attackGob1','attackGob2','northGob1','northGob2'].includes(x))):[]);
  louFound=data.louFound===true&&count()===3;storyStage=stage;
  if(storyStage>=11&&count()<3)storyStage=10;
  attackStep=Math.max(0,Math.min(2,Number(data.attackStep)||0));northPhase=Math.max(0,Math.min(3,Number(data.northPhase)||0));forestStoneSeen=!!data.forestStoneSeen;
  for(const id of Object.keys(subQuests))if(['locked','active','done'].includes(data.subQuests?.[id]?.state))Object.assign(subQuests[id],data.subQuests[id]);
 }
 async function load(data,route=plan(data),token){
  if(!data||(data.version!==1&&data.version!==2))return false;
  LoadCoordinator.assertCurrent(token);
  restoreModel(data,route.stage,token);
  PrologueCombat.cancel();devResetScreens(token);document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','raiderFinishing','soloRescue');
  document.body.classList.toggle('villageAttack',storyStage>=5&&storyStage<=8);forestActive=false;
  const handlesField=route.kind==='TRAINING_RETRY'||route.kind==='FIELD_MAP';
  switch(route.kind){
   case 'TRAINING_RETRY':await TrainingCheckpoint.restore(data,token);break;
   case 'FIELD_MAP':forestActive=true;q('#forestScene').style.display='block';await MossForestStory.fromSave(data,{count:count(),louFound,storyStage},token);break;
   case 'LEGACY_SCENE':px=Number(data.position?.px)||420;py=Number(data.position?.py)||1160;camera();if(storyStage===0){room='home';q('#inside').style.display='block';dressRoom();inCamera()}break;
   case 'AFTERMATH':startRaiderAftermath();break;
   case 'FORT_FINALE':startFortFinale();break;
   case 'PROLOGUE_END':showPrologueEnd();break;
   default:throw Error('Unknown restore route');
  }
  LoadCoordinator.assertCurrent(token);
  if(!handlesField&&data.moss&&window.MossForest)MossForest.restoreState(data.moss);
  sync();for(const field of ['attackGob1','attackGob2','northGob1','northGob2']){const el=q('#'+field);if(el){el.hidden=cleared(field);el.style.display=cleared(field)?'none':''}}
  currentObjective=storyStage>=9&&storyStage<=10?objective():String(data.currentObjective||currentObjective);renderJournal();return true;
 }
 function seed(n, preceding=[]){defeated=new Set([...Object.values(ids).slice(0,n),...preceding.filter(id=>['attackGob1','attackGob2','northGob1','northGob2'].includes(id))]);louFound=false;sync();for(const id of ['attackGob1','attackGob2','northGob1','northGob2']){const el=q('#'+id);el.hidden=cleared(id);el.style.display=el.hidden?'none':''}}
 window.PrologueProgress=Object.freeze({cleared,defeat,sync,count,objective,serialize,plan,load,restoreModel,resetLegacyEvents,eventSnapshot,restoreEventSnapshot,seed});
 sync();
})();
