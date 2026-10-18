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
 function serialize(){return {version:2,defeated:[...defeated],corruptionCount:count(),barrierOpen:count()===3,louFound,storyStage,attackStep,northPhase,forestStoneSeen,moss:window.MossForest?MossForest.snapshot():null,position:{px,py},currentObjective,subQuests:JSON.parse(JSON.stringify(subQuests))};}
 function load(data,restoration){
  if(!data||(data.version!==1&&data.version!==2))return false;
  defeated=new Set(Array.isArray(data.defeated)?data.defeated.filter(x=>typeof x==='string'&&([...Object.values(ids),'attackGob1','attackGob2','northGob1','northGob2'].includes(x))):[]);
  louFound=data.louFound===true&&count()===3;storyStage=Math.max(0,Math.min(15,Number(data.storyStage)||0));
  if(storyStage>=11&&count()<3)storyStage=10;
  attackStep=Math.max(0,Math.min(2,Number(data.attackStep)||0));northPhase=Math.max(0,Math.min(3,Number(data.northPhase)||0));forestStoneSeen=!!data.forestStoneSeen;
  for(const id of Object.keys(subQuests))if(['locked','active','done'].includes(data.subQuests?.[id]?.state))Object.assign(subQuests[id],data.subQuests[id]);
  PrologueCombat.cancel();devResetScreens();document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','raiderFinishing','soloRescue');
  document.body.classList.toggle('villageAttack',storyStage>=5&&storyStage<=8);forestActive=false;
  if(storyStage>=9&&storyStage<=12){forestActive=true;q('#forestScene').style.display='block';const pending=MossForestStory.fromSave(data,{count:count(),louFound,storyStage},restoration&&restoration.token);if(restoration){restoration.kind='forest';restoration.pending=pending;restoration.verify=()=>forestActive&&storyStage>=9&&storyStage<=12&&q('#forestScene').style.display==='block'&&!document.body.classList.contains('battleMode');}}
  else if(storyStage<=8){px=Number(data.position?.px)||420;py=Number(data.position?.py)||1160;camera();if(storyStage===0){room='home';q('#inside').style.display='block';dressRoom();inCamera()}}
  else if(storyStage===13)startRaiderAftermath();else if(storyStage===14)startFortFinale();else showPrologueEnd();
  if(!(storyStage>=9&&storyStage<=12)&&data.moss&&window.MossForest)MossForest.restoreState(data.moss);   // herbs/chests opened on 風見の断崖 etc.
  if(restoration&&!restoration.pending){
   restoration.kind='legacy';
   const expected={stage:storyStage,x:px,y:py,ix:ipx,iy:ipy};
   const cssPx=n=>{const style=document.createElement('i').style;style.left=n+'px';return style.left;};
   restoration.verify=()=>{
    if(forestActive||storyStage!==expected.stage||document.body.classList.contains('battleMode')||q('#forestScene').style.display!=='none')return false;
    if(storyStage<=8){
     if(!Number.isFinite(px)||!Number.isFinite(py)||px!==expected.x||py!==expected.y||px<0||py<0||px>=world.offsetWidth||py>=world.offsetHeight||pl.style.left!==cssPx(px)||pl.style.top!==cssPx(py))return false;
     return storyStage===0?room==='home'&&q('#inside').style.display==='block'&&Number.isFinite(ipx)&&Number.isFinite(ipy)&&ipx===expected.ix&&ipy===expected.iy&&ipx>=0&&ipx<1000&&ipy>=0&&ipy<720&&q('#inPlayer').style.left===cssPx(ipx)&&q('#inPlayer').style.top===cssPx(ipy):q('#inside').style.display==='none';
    }
    const scene={13:'#aftermathScene',14:'#fortScene',15:'#prologueEnd'}[storyStage];
    return !!scene&&q(scene).style.display==='block';
   };
  }
  sync();for(const field of ['attackGob1','attackGob2','northGob1','northGob2']){const el=q('#'+field);if(el){el.hidden=cleared(field);el.style.display=cleared(field)?'none':''}}
  currentObjective=storyStage>=9&&storyStage<=10?objective():String(data.currentObjective||currentObjective);renderJournal();return true;
 }
 function seed(n, preceding=[]){defeated=new Set([...Object.values(ids).slice(0,n),...preceding.filter(id=>['attackGob1','attackGob2','northGob1','northGob2'].includes(id))]);louFound=false;sync();for(const id of ['attackGob1','attackGob2','northGob1','northGob2']){const el=q('#'+id);el.hidden=cleared(id);el.style.display=el.hidden?'none':''}}
 window.PrologueProgress=Object.freeze({cleared,defeat,sync,count,objective,serialize,load,seed});
 sync();
})();
