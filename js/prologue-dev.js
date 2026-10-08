// DEV scene preparation is isolated from normal progression and persistent saves.
(() => {
 window.WINDBOUND_DEV=['localhost','127.0.0.1','[::1]'].includes(location.hostname)||new URLSearchParams(location.search).get('dev')==='1';
 document.body.classList.toggle('developmentMode',WINDBOUND_DEV);
 if(!WINDBOUND_DEV){document.querySelectorAll('.dev-only-command').forEach(b=>b.disabled=true);return;}
 const entries=[['opening','01 エイダンの家'],['training','02 訓練 / フィオナ'],['sunset','03 夕暮れ'],['attack','04 リンド村襲撃'],['mother','05 母娘救出'],['fionaRescue','06 フィオナ救出'],['north','07 北の道'],['escape','08 川への脱出'],['forest','09 苔の森入口'],['moss1','10 森の穢れ 1'],['moss2','11 森の穢れ 2'],['moss3','12 森の穢れ 3'],['barrierBefore','13 結界解除前'],['barrierAfter','14 結界解除後'],['lou','15 ルーとの出会い'],['altar','16 古代祭壇 / 誓いの剣'],['raider','17 ゴブリンレイダー'],['aftermath','18 戦いの後'],['fort','19 アーサー砦'],['prologueEnd','20 プロローグ終了']];
 const old=devJump;let sandbox=false;
 const save=saveGrowthData,load=loadGrowthData;
 saveGrowthData=function(){if(sandbox){notice('DEVジャンプ中は通常セーブを保護しています。ロードか再読み込みで解除できます。');return}return save()};
 loadGrowthData=function(){const value=load();sandbox=false;return value};
 devJump=function(key){
  if(key==='reunion')key='north';
  if(!entries.some(([k])=>k===key))return false;
  sandbox=true;PrologueCombat.cancel();BattleTargetSelector.cancel();
  window.BattleCritical?.resetForce();
  document.querySelector('#battleResult').style.display='none';resultCallback=null;
  devResetScreens();
  document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','raiderFinishing','soloRescue','battleResultMode','villageAttack','northAssault','actionCinematic');
  document.querySelectorAll('.actionFocus,.actionTarget,.actionDim,.actionPose,.raiderKO,.taintedKO').forEach(el=>el.classList.remove('actionFocus','actionTarget','actionDim','actionPose','raiderKO','taintedKO'));
  for(const el of document.querySelectorAll('#attackBattle *,#raiderBattle *'))for(const animation of el.getAnimations())animation.cancel();
  attackBattleBusy=false;rbBusy=false;forestActive=false;room='';target=itarget=ftarget=null;
  setNormalCommandDrawer(false);setRaiderCommandDrawer(false);document.querySelector('#normalItems').classList.remove('isOpen');
  const index=entries.findIndex(([k])=>k===key),pastVillage=index>=6,pastForest=index>=14;
  const n=key==='moss2'?1:key==='moss3'?2:(key==='barrierAfter'||pastForest)?3:0;
  PrologueProgress.seed(n,pastVillage?['attackGob1','attackGob2',...(index>=8?['northGob1','northGob2']:[])]:key==='fionaRescue'?['attackGob1']:[]);
  attackStep=pastVillage?2:key==='fionaRescue'?1:0;northPhase=index>=8?3:key==='north'?1:0;forestStoneSeen=index>=9;louFound=index>=15;
  for(const id of Object.keys(forestChests)){forestChests[id]=false;document.querySelector('#'+id).classList.remove('open')}
  PrologueProgress.sync();
  if(key==='mother'||key==='fionaRescue'){
   old('attack');closeDialogue();startAttackBattle(key==='mother'?'attackGob1':'attackGob2',100);
  }else if(key.startsWith('moss')||key.startsWith('barrier')){
   old('forest');closeDialogue();forestStoneSeen=true;PrologueProgress.sync();
   if(key.startsWith('moss')){const i=Number(key.at(-1)),el=document.querySelector('#forestGob'+i);fpx=parseFloat(el.style.left)-80;fpy=parseFloat(el.style.top);startAttackBattle('forestGob'+i,100)}
   else {storyStage=10;fpx=1430;fpy=610;forestCamera();setObj(PrologueProgress.objective())}
  }else if(key==='lou'){
   old('lou');PrologueProgress.sync();startLouIntro();
  }else old(key);
  if(key==='forest')PrologueProgress.sync();
  // Later destinations need the released forest and Lou, not only a scene index.
  if(index>=15){louFound=true;forestStoneSeen=true;PrologueProgress.sync()}
  renderJournal();return true;
 };
 const grid=document.querySelector('#devGrid');grid.replaceChildren();for(const [key,name]of entries){const b=document.createElement('button');b.dataset.jump=key;b.textContent=name;grid.append(b)}
})();
