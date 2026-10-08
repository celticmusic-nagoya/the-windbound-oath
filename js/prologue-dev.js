// Uses the existing DEV gate. No additional controls outside the development panel.
(() => {
 const entries=[['mother','15 母娘救出'],['fionaRescue','16 フィオナ救出'],['moss1','17 森の穢れ 1'],['moss2','18 森の穢れ 2'],['moss3','19 森の穢れ 3'],['barrierBefore','20 結界解除前'],['barrierAfter','21 結界解除後']];
 const old=devJump;
 devJump=function(key){
  PrologueCombat.cancel();BattleTargetSelector.cancel();
  document.body.classList.remove('battleMode','normalBattleMode','raiderBattleMode','raiderFinishing','soloRescue');attackBattleBusy=false;rbBusy=false;
  if(entries.some(([k])=>k===key)){
   if(key==='mother'||key==='fionaRescue'){
    old('attack');PrologueProgress.seed(0);attackStep=key==='mother'?0:1;closeDialogue();startAttackBattle(key==='mother'?'attackGob1':'attackGob2',100);
   }else{
    const n=key==='moss2'?1:key==='moss3'?2:key==='barrierAfter'?3:0;PrologueProgress.seed(n);old('forest');closeDialogue();PrologueProgress.sync();
    if(key.startsWith('moss')){const i=Number(key.at(-1));const el=document.querySelector('#forestGob'+i);fpx=parseFloat(el.style.left)-80;fpy=parseFloat(el.style.top);startAttackBattle('forestGob'+i,100)}
    else {fpx=1370;fpy=520;forestCamera();setObj(PrologueProgress.objective())}
   }
   return;
  }
  old(key);if(key==='forest')PrologueProgress.sync();if(key==='lou'){PrologueProgress.seed(3);PrologueProgress.sync()}
 };
 const grid=document.querySelector('#devGrid');for(const [key,name]of entries){const b=document.createElement('button');b.dataset.jump=key;b.textContent=name;grid.append(b)}
})();
