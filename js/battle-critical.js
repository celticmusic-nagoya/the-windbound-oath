// Resolve once per executed action, after defence and status modifiers.
(() => {
 const MULTIPLIER=1.5,results=new WeakMap();let forceNext=false;
 function chance(actor,enemy=false){if(enemy)return 0;const value=CHARACTER_DB[actor]?.cri;return Math.max(0,Math.min(100,Number.isFinite(value)?value:5));}
 function calculate(base,{canCrit=false,cri=0,random=Math.random,forced=false}={}){
  const eligible=canCrit===true,critical=eligible&&(forced||random()<Math.max(0,Math.min(100,cri))/100);
  return Object.freeze({base,damage:critical?Math.round(base*MULTIPLIER):base,critical,multiplier:critical?MULTIPLIER:1});
 }
 function resolve(action,base){
  if(results.has(action))return results.get(action);
  const canCrit=action.kind==='atk',forced=canCrit&&forceNext&&window.WINDBOUND_DEV===true;
  const result=calculate(base,{canCrit,cri:chance(action.who),forced});
  if(forced){forceNext=false;const button=document.querySelector('#devForceCritical');if(button)button.textContent='DEV｜次の通常攻撃を会心に';}
  results.set(action,result);return result;
 }
 window.BattleCritical=Object.freeze({MULTIPLIER,chance,calculate,resolve,force(){if(!window.WINDBOUND_DEV)return false;forceNext=true;return true},resetForce(){forceNext=false},get forced(){return forceNext}});
})();
