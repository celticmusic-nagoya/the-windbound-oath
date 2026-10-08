// Presentation owns no HP, actor state or RNG. Motion keyframes remain unchanged.
(() => {
 function show(battle,actor,enemy,hit){
  const token=PrologueCombat.generation,node=document.getElementById(enemy.unit);if(!node)return;
  const r=node.getBoundingClientRect(),pop=document.createElement('div');
  pop.className='battleDamageNumber'+(hit.critical?' isCritical':'');
  const label=document.createElement('span');label.textContent=hit.critical?'CRITICAL!':'';
  const number=document.createElement('strong');number.textContent=hit.damage;pop.append(label,number);
  pop.style.left=Math.max(50,Math.min(innerWidth-50,r.left+r.width/2))+'px';pop.style.top=Math.max(90,Math.min(innerHeight-80,r.top+r.height*.45))+'px';
  document.body.append(pop);setTimeout(()=>pop.remove(),950);
  if(!hit.critical)return;
  const sourceId=battle==='normal'?(actor==='aidan'?'v2AidanUnit':'v2FionaUnit'):(actor==='aidan'?'rbAidan':'rbFiona');
  setTimeout(()=>{
   if(token!==PrologueCombat.generation)return;
   const source=document.getElementById(sourceId);
   const animations=(source?.getAnimations()||[]).filter(a=>a.playState==='running'&&a.effect?.getKeyframes().some(f=>f.translate!==undefined));
   for(const animation of animations)animation.pause();
   setTimeout(()=>{for(const animation of animations){if(token===PrologueCombat.generation&&animation.playState==='paused')animation.play();else if(animation.playState==='paused')animation.cancel()}},100);
  },actor==='aidan'?380:330);
 }
 window.BattleCriticalPresentation=Object.freeze({show});
})();
