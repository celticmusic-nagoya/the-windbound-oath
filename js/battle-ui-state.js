// Presentation state only. The existing engine owns targets, resources, queues and timing.
(() => {
 'use strict';
 const q=s=>document.querySelector(s),states=new Map();let scheduled=false;
 const mode=()=>document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null;
 const token=b=>[PrologueCombat.generation,b==='normal'?PrologueCombat.roundNumber:rbRound,b==='normal'?normalActor:rbActor].join(':');
 const blocked=b=>!!(b==='normal'?attackBattleBusy:rbBusy)||!!window.BattlePresentation?.busy||document.body.classList.contains('actionCinematic')||document.body.classList.contains('battlePresentationBusy')||document.body.classList.contains('battleResultMode')||!(PrologueCombat.targets(b)||[]).some(e=>e.hp()>0);
 function current(b,t){return mode()===b&&token(b)===t;}
 function record(b){let s=states.get(b);if(!s){s={battle:b,key:null,status:'inactive',resume:'collapsed',itemReturn:null,targetReturn:null};states.set(b,s);}return s;}
 function style(el,name,value){if(el.style.getPropertyValue(name)!==value)el.style.setProperty(name,value,'important');}
 function focus(b,preferred){
  if((!InputManager.keyboard&&!preferred)||mode()!==b)return;
  const s=record(b);if(s.status==='busy'||s.status==='inactive')return;
  const root=s.status==='collapsed'?q(b==='normal'?'#normalCommandToggle':'#rbCommandToggle'):s.status==='items'?q('#normalItems'):s.status==='targets'?BattleUIRegions.targets:q(b==='normal'?'#normalBattleCmd':'#rbCmd');
  const el=preferred?.isConnected&&root?.contains(preferred)?preferred:s.status==='collapsed'?root:root?.querySelector('button:not([disabled]):not(.drawerClose)');
  if(el&&getComputedStyle(el).display!=='none'&&getComputedStyle(el).visibility!=='hidden')el.focus({preventScroll:true});
 }
 function render(b){
  const s=record(b),normal=b==='normal',panel=q(normal?'#normalBattleCmd':'#rbCmd'),toggle=q(normal?'#normalCommandToggle':'#rbCommandToggle');
  const commands=s.status==='commands',collapsed=s.status==='collapsed';
  panel.hidden=!commands;panel.classList.toggle('expanded',commands);toggle.hidden=!collapsed;
  style(panel,'display',commands?'grid':'none');style(panel,'visibility',commands?'visible':'hidden');style(panel,'pointer-events',commands?'auto':'none');style(toggle,'display',collapsed?'flex':'none');
  toggle.setAttribute('aria-expanded',String(commands));toggle.setAttribute('aria-controls',panel.id);
  const root=BattleUIRegions.get(b).root;if(root.dataset.uiState!==s.status)root.dataset.uiState=s.status;
  if(mode()!==b)return;
  const items=q('#normalItems'),showItems=s.status==='items';style(items,'display',showItems?'grid':'none');style(items,'visibility',showItems?'visible':'hidden');style(items,'pointer-events',showItems?'auto':'none');
  const showTargets=s.status==='targets'&&BattleTargetSelector.active;
  for(const el of [q('#battleTargetPanel'),...document.querySelectorAll('.battleTargetHit')]){style(el,'visibility',showTargets?'visible':'hidden');style(el,'pointer-events',showTargets?'auto':'none');}
 }
 function change(s,next,preferred){const changed=s.status!==next;s.status=next;render(s.battle);if(changed)focus(s.battle,preferred);}
 function clearItems(){q('#normalItems').classList.remove('isOpen');}
 function sync(b=mode()){
  if(!b){if(BattleTargetSelector.active)BattleTargetSelector.cancel();style(q('#normalItems'),'display','none');style(q('#normalItems'),'visibility','hidden');style(q('#normalItems'),'pointer-events','none');style(q('#battleTargetPanel'),'visibility','hidden');for(const s of states.values()){s.key=null;s.targetReturn=s.itemReturn=null;change(s,'inactive');}clearItems();return;}
  const s=record(b),key=token(b);
  if(mode()!==b){s.key=null;s.targetReturn=s.itemReturn=null;change(s,'inactive');return;}
  if(s.key!==key){
   s.key=key;s.targetReturn=s.itemReturn=null;s.resume='collapsed';clearItems();
   if(BattleTargetSelector.active)BattleTargetSelector.cancel();
   change(s,blocked(b)?'busy':'collapsed');return;
  }
  if(blocked(b)){if(s.status!=='busy')s.resume=s.status==='inactive'?'collapsed':s.status;change(s,'busy');return;}
  if(s.status==='busy'||s.status==='inactive')change(s,s.resume||'collapsed');
  if(BattleTargetSelector.active&&s.status!=='targets'){s.targetReturn={key,status:s.status,focus:document.activeElement};change(s,'targets');}
  else if(!BattleTargetSelector.active&&s.status==='targets'){const back=s.targetReturn;s.targetReturn=null;change(s,back?.status||'collapsed',back?.focus);}
  else render(b);
 }
 function commands(b,open){sync(b);const s=record(b);if(!current(b,s.key)||blocked(b)||s.status==='targets'||s.status==='items')return;change(s,open?'commands':'collapsed');}
 function items(b){sync(b);const s=record(b);if(!current(b,s.key)||blocked(b))return;s.itemReturn={key:s.key,status:s.status,focus:document.activeElement};q('#normalItems').classList.add('isOpen');change(s,'items');}
 function backItems(b){sync(b);const s=record(b);if(s.status!=='items'||!current(b,s.key))return;clearItems();const back=s.itemReturn;s.itemReturn=null;change(s,back?.status||'commands',back?.focus);}
 function beginTargets(b){sync(b);const s=record(b);if(!current(b,s.key)||blocked(b))return null;const tx={key:s.key,status:s.status,focus:document.activeElement};s.targetReturn=tx;change(s,'targets');return tx;}
 function cancelTargets(b,tx){const s=record(b);if(!current(b,tx.key)||s.targetReturn!==tx)return;s.targetReturn=null;if(blocked(b)){s.resume=tx.status;change(s,'busy');return;}change(s,tx.status,tx.focus);}
 function confirmTargets(b,tx,submit,value){const s=record(b);if(!current(b,tx.key)||s.targetReturn!==tx||blocked(b))return;s.targetReturn=null;change(s,'collapsed');submit(value);sync(b);if(current(b,tx.key)&&!blocked(b))change(s,tx.status,tx.focus);}
 function schedule(){if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;sync();});}
 new MutationObserver(schedule).observe(document.body,{attributes:true,attributeFilter:['class']});
 for(const b of ['normal','raider'])new MutationObserver(schedule).observe(BattleUIRegions.get(b).root,{subtree:true,childList:true,characterData:true});
 new MutationObserver(schedule).observe(q('#battleTargetPanel'),{attributes:true,attributeFilter:['hidden']});
 addEventListener('resize',schedule);
 window.BattleUIState=Object.freeze({sync,commands,items,backItems,beginTargets,cancelTargets,confirmTargets,current,token,snapshot:b=>({...record(b),itemReturn:record(b).itemReturn?.status,targetReturn:record(b).targetReturn?.status})});
 sync();
})();
