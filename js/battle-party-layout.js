// Visual dimensions and slot placement only. WAAPI translation/scale remains motion-owned.
(() => {
 const q=s=>document.querySelector(s);
 const current={normal:[{id:'aidan',unit:'#v2AidanUnit',visual:'#bAidan2',hud:'#v2AidanHud'},{id:'fiona',unit:'#v2FionaUnit',visual:'#bFiona2',hud:'#v2FionaHud'}],raider:[{id:'aidan',unit:'#rbAidan',visual:'#rbAidan',hud:'.rbNearA'},{id:'fiona',unit:'#rbFiona',visual:'#rbFiona',hud:'.rbNearF'}]};
 function arrange(battle,actors){
  const portrait=innerHeight>innerWidth,short=!portrait&&innerHeight<=520,count=Math.max(1,Math.min(4,actors.length)),density=count<=2?1:count===3?1.2/1.3:1.1/1.3;
  const columns=2,rows=Math.ceil(count/columns),layout=[];
  actors.slice(0,4).forEach((actor,i)=>{
   const unit=q(actor.unit),visual=q(actor.visual);if(!unit||!visual)return;
   const fiona=actor.id==='fiona',base=actor.baseSize|| (battle==='normal'?{width:portrait?(fiona?112:116):(fiona?96:100),height:portrait?150:126}:{width:fiona?108:112,height:140});
   const relative=(portrait?(fiona?1.15:1.17):short?(fiona?1.20:1.24):(fiona?1.30:1.32))*density;
   const width=base.width*relative,height=base.height*relative;
   visual.style.setProperty('width',width+'px','important');visual.style.setProperty('height',height+'px','important');
   const centers=portrait?[.22,.58]:battle==='normal'?(short?[.32,.49]:[.345,.478]):[.17,short?.35:.325];
   const column=i%columns,row=Math.floor(i/columns),parentLeft=unit.offsetParent?.getBoundingClientRect().left||0;
   const unitWidth=battle==='normal'?unit.offsetWidth:width;
   let center=Math.max(innerWidth*centers[column],parentLeft+unitWidth/2+4);
   const previous=layout.find(x=>x.row===row&&x.column===0);if(column&&previous)center=Math.max(center,previous.center+(previous.width+width)/2+16);
   unit.style.setProperty('left',(center-parentLeft-unitWidth/2)+'px','important');
   // Existing two-character floor anchors stay unchanged. Future rows use a shared grid.
   if(rows>1){const floor=portrait?innerHeight*.20:innerHeight*.10;const spacing=short?Math.min(170,innerHeight*.43):height+95;unit.style.setProperty('bottom',(floor+row*spacing)+'px','important')}
   else unit.style.removeProperty('bottom');
   const hud=actor.hud&&q(actor.hud);
   if(hud&&battle==='raider'){hud.style.setProperty('left',(center-hud.offsetWidth/2)+'px','important');hud.style.setProperty('bottom',((parseFloat(getComputedStyle(unit).bottom)||0)+height+10)+'px','important')}
   layout.push({id:actor.id,width,height,relative,center,row,column});
  });
  q(battle==='normal'?'#attackBattle':'#raiderBattle').dataset.activeParty=String(count);BattleTargetSelector.refresh();return layout;
 }
 function refresh(battle){return arrange(battle,current[battle].filter(actor=>PrologueCombat.activeAlly(battle,actor.id)))}
 addEventListener('resize',()=>{if(document.body.classList.contains('normalBattleMode'))refresh('normal');else if(document.body.classList.contains('raiderBattleMode'))refresh('raider')});
 window.BattlePartyLayout=Object.freeze({arrange,refresh});
})();
