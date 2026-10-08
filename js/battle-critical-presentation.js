// Presentation owns no HP, actor state or RNG. Motion keyframes remain unchanged.
(() => {
 function show(battle,actor,enemy,hit){
  const token=PrologueCombat.generation,node=document.getElementById(enemy.unit);if(!node)return;
  const r=node.getBoundingClientRect(),pop=document.createElement('div');
  pop.className='battleDamageNumber'+(hit.critical?' isCritical':'');
  const label=document.createElement('span');label.textContent=hit.critical?'CRITICAL!':'';
  const number=document.createElement('strong');number.textContent=hit.damage;pop.append(label,number);
  document.body.append(pop);
  const width=pop.offsetWidth,height=pop.offsetHeight,center=r.left+r.width/2,y=r.top+r.height*.45;
  const huds=[...document.querySelectorAll('.v2NearHud,.prologueEnemyHud,.rbNearHud,.rbEnemyHud,#battleBanner,#rbMsg')].filter(el=>el.offsetWidth&&el.offsetHeight&&getComputedStyle(el).visibility!=='hidden').map(el=>el.getBoundingClientRect());
  const candidates=[[center,y],[r.left-45,y],[r.left-90,y],[r.right+45,y],[center,r.top-55],[center,r.bottom+55],[center,r.bottom+100]].map(([x,y])=>[Math.max(width/2+8,Math.min(innerWidth-width/2-8,x)),Math.max(90,Math.min(innerHeight-80,y))]);
  const position=candidates.find(([x,y])=>!huds.some(h=>x+width/2+8>h.left&&x-width/2-8<h.right&&y+height/2+16>h.top&&y-height/2-16<h.bottom))||candidates[0];
  pop.style.left=position[0]+'px';pop.style.top=position[1]+'px';setTimeout(()=>pop.remove(),hit.critical?1150:950);
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
