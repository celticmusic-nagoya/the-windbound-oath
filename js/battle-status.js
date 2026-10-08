// Small, turn-scoped modifiers. Same effect refreshes instead of stacking.
(() => {
 const effects=new Map();let revision=0;
 const types=new Set(['atk_up','atk_down','def_up']);
 const key=(battle,target)=>battle+':'+target;
 function list(battle,target){return [...(effects.get(key(battle,target))?.values()||[])].map(x=>({...x}));}
 function apply({battle,target,type,magnitude,remainingTurns=3,source}){
  if(typeof battle!=='string'||typeof target!=='string'||typeof source!=='string'||!types.has(type)||!Number.isFinite(magnitude)||magnitude<0||magnitude>1||!Number.isInteger(remainingTurns)||remainingTurns<1||remainingTurns>99)return false;
  const k=key(battle,target);if(!effects.has(k))effects.set(k,new Map());
  effects.get(k).set(type,{type,magnitude,remainingTurns,source,target,revision:++revision});render(battle);return true;
 }
 function multiplier(battle,target,stat){return list(battle,target).filter(e=>e.type.startsWith(stat+'_')).reduce((n,e)=>n*(e.type.endsWith('down')?1-e.magnitude:1+e.magnitude),1);}
 function damage(battle,source,target,base){return Math.max(1,Math.round(base*multiplier(battle,source,'atk')/multiplier(battle,target,'def')));}
 function snapshot(battle){return [...effects.entries()].filter(([k])=>k.startsWith(battle+':')).flatMap(([k,v])=>[...v].map(([t,e])=>[k,t,e.revision]));}
 function tick(battle,start=snapshot(battle)){for(const[k,t,r]of start){const e=effects.get(k)?.get(t);if(e?.revision===r&&--e.remainingTurns<=0)effects.get(k).delete(t)}render(battle);}
 function clear(battle){for(const k of effects.keys())if(k.startsWith(battle+':'))effects.delete(k);render(battle);}
 function render(battle){for(const id of ['aidan','fiona']){
  const host=document.querySelector(battle==='normal'?(id==='aidan'?'#hudAidan':'#hudFiona'):(id==='aidan'?'.rbNearA':'.rbNearF'))||document.querySelector(battle==='raider'?(id==='aidan'?'#rbAidan':'#rbFiona'):null);
  if(!host)continue;let el=host.querySelector('.battleStatuses');if(!el){el=document.createElement('small');el.className='battleStatuses';host.append(el)}
  const labels={atk_up:'ATK↑',atk_down:'ATK↓',def_up:'DEF↑'};
  const current=list(battle,id),attack=current.filter(e=>e.type.startsWith('atk_'));
  // Display the net ATK effect when UP and DOWN coexist; retain both records.
  const shown=attack.length>1?[{type:multiplier(battle,id,'atk')>=1?'atk_up':'atk_down',remainingTurns:Math.min(...attack.map(e=>e.remainingTurns))},...current.filter(e=>!e.type.startsWith('atk_'))]:current;
  el.textContent=shown.map(e=>labels[e.type]+' '+e.remainingTurns).join(' ');
  el.title=current.map(e=>labels[e.type]+' '+Math.round(e.magnitude*100)+'% / '+e.remainingTurns+'ターン').join('、');
  el.setAttribute('aria-label',el.title);
 }}
 window.BattleStatus=Object.freeze({apply,list,multiplier,damage,snapshot,tick,clear,render});
})();
