// UI-03 presentation coordinates only. No actor IDs, slots, HP or motion state are assigned.
(() => {
 'use strict';
 const q=s=>document.querySelector(s),set=(el,k,v)=>{if(el&&el.style.getPropertyValue(k)!==v)el.style.setProperty(k,v,'important');};
 const pos=(el,x,y,w,h)=>{set(el,'left',x+'px');set(el,'bottom',y+'px');set(el,'right','auto');set(el,'top','auto');if(w)set(el,'width',w+'px');if(h)set(el,'height',h+'px');};
 function layout(b){
  const region=BattleUIRegions.get(b),field=region.field,w=field.clientWidth,h=field.clientHeight;if(!w||!h)return;
  const portrait=innerHeight>innerWidth,short=h<440,normal=b==='normal',ground=normal&&region.root.dataset.bg==='BG-01';
  const allyH=Math.min(normal?176:190,h*(portrait?.30:short?.40:.48)),allyW=allyH*.76;
  ['aidan','fiona'].forEach((id,i)=>{
   const unit=q(normal?(i?'#v2FionaUnit':'#v2AidanUnit'):(i?'#rbFiona':'#rbAidan')),visual=q(normal?(i?'#bFiona2':'#bAidan2'):(i?'#rbFiona':'#rbAidan'));
   const x=portrait?w*(i?.36:.06):w*(i?(short?.27:.23):.05),floor=Math.max(70,h*(portrait?.08:.14));
   pos(unit,x,floor,allyW,allyH);set(visual,'width',allyW+'px');set(visual,'height',allyH+'px');
   if(!normal){const hud=q(i?'.rbNearF':'.rbNearA');pos(hud,x-5,8,110);}
  });
  if(normal){
   const eh=Math.min(portrait?150:short?128:150,h*(portrait?.34:.43)),ew=eh*.80;pos(q('#v2GobUnit'),Math.min(w-ew-8,w*(portrait?.70:.72)),Math.max(70,h*(portrait?(ground?.30:.51):.15)),ew,eh);set(q('#bGob'),'width',ew+'px');set(q('#bGob'),'height',eh+'px');
  }else{
   const bossH=Math.min(504,h*(portrait?.44:.77)),bossW=Math.min(w*.90,bossH*(537.6/504));pos(q('#raiderSprite'),w-bossW-8,h*(portrait?.49:.10),bossW,bossH);
   // Lou's native float/flight controller and transforms remain untouched.
   const louRange=window.BattleLouFlight?.tune.rangeX||0;
   const louX=!portrait&&!short?Math.max(8,Math.min(w*.43,w-bossW-8-52-12-louRange)):w*.43;
   pos(q('#rbLou'),louX,h*.53,52,66);
  }
  [...region.extras.querySelectorAll('.prologueEnemy')].forEach((el,i)=>{
   const desktop=normal&&!portrait&&!short,eh=Math.min(normal?(desktop?150:portrait?100:110):126,h*(normal?.30:.28)),ew=desktop?140:100;
   pos(el,Math.min(w-ew-8,normal?w*(portrait?(i%2?.38:.08):(i?.84:.56)):portrait?w-ew-8:w*(.62+i*.17)),normal?h*(portrait?(ground?.30:.52):(ground?.20:.45)):portrait?h*.06+i*(eh+12):h*.06,ew,eh);
   const sprite=el.querySelector('.prologueSprite'),spriteW=desktop?119:80;set(sprite,'width',spriteW+'px');set(sprite,'height',Math.min(desktop?150:100,eh)+'px');set(sprite,'left',((ew-spriteW)/2)+'px');
  });
  BattleTargetSelector.refresh();
 }
 let frame=0;function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;const b=document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null;if(b)layout(b);});}
 addEventListener('resize',schedule);
 new MutationObserver(schedule).observe(document.body,{attributes:true,attributeFilter:['class']});
 for(const b of ['normal','raider']){const field=BattleUIRegions.get(b).field;new MutationObserver(schedule).observe(field,{childList:true,subtree:true});new ResizeObserver(schedule).observe(field);}
 document.addEventListener('focusin',e=>{const controls=e.target.closest?.('.battleUIOperations');if(controls)e.target.scrollIntoView({block:'nearest',inline:'nearest'});});
 new MutationObserver(schedule).observe(BattleUIRegions.get('normal').root,{attributes:true,attributeFilter:['data-bg']});
 // The target view is a list inside controls: keep its selected actor identifiable on the field.
 function highlight(){
  const b=document.body.classList.contains('raiderBattleMode')?'raider':'normal',id=BattleTargetSelector.active?BattleTargetSelector.selected:null;
  const candidate=id&&[...BattleActionTargets.enemies(b),...BattleActionTargets.allies(b)].find(x=>x.id===id);
  const node=candidate&&q(candidate.node);
  document.querySelectorAll('.ui3TargetSelected').forEach(el=>{if(el!==node){el.classList.remove('ui3TargetSelected');delete el.dataset.ui3TargetId;}});
  if(node){node.classList.add('ui3TargetSelected');node.dataset.ui3TargetId=id;}
 }
 new MutationObserver(highlight).observe(BattleUIRegions.targets,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','class']});
 window.BattleUIResponsive=Object.freeze({layout});schedule();
})();
