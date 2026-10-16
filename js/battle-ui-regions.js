// UI-01: DOM ownership only; all legacy IDs, callbacks, positioning and view state survive.
(() => {
 'use strict';
 if(window.BattleUIRegions)return;
 const q=s=>document.querySelector(s), battles=new Map();
 function region(name,battle){
  const el=document.createElement('section');el.className='battleUIRegion';
  el.id='battleUI-'+battle+'-'+name;el.dataset.uiRegion=name;el.dataset.battle=battle;
  el.setAttribute('aria-label',({field:'戦場','field-extras':'追加敵',log:'バトルログ',command:'COMMAND',actions:'行動コマンド',items:'アイテム選択',targets:'対象選択'})[name]);
  return el;
 }
 for(const b of ['normal','raider']){
  const normal=b==='normal',root=q(normal?'#attackBattle':'#raiderBattle');
  const field=normal?q('#attackBattle > .v2BattleStage'):region('field',b),extras=normal?region('field-extras',b):field,operations=document.createElement('section');
  operations.className='battleUIOperations';operations.dataset.battle=b;
  const toggle=q(normal?'#normalCommandToggle':'#rbCommandToggle'),command=region('command',b),actions=region('actions',b),log=region('log',b);
  if(normal){
   field.dataset.uiRegion='field';field.dataset.battle=b;field.setAttribute('aria-label','戦場');
   field.append(extras);field.setAttribute('aria-owns',extras.id);
  }
  else{
   root.insertBefore(field,q('#rbAidan'));
   ['#rbAidan','#rbFiona','#rbLou','#raiderSprite','#rbEnemyHud'].forEach(sel=>field.append(q(sel)));
   root.querySelectorAll('.rbNearHud').forEach(el=>field.append(el));
  }
  root.insertBefore(operations,toggle);operations.append(command,actions);command.append(toggle);
  actions.append(q(normal?'#normalActor':'#rbTurn'),q(normal?'#normalBattleCmd':'#rbCmd'));
  // These were body portals to avoid legacy clipping. Retain that rendering contract in UI-01.
  operations.prepend(log);log.append(q(normal?'#battleMsg2':'#rbMsg'));
  root.dataset.uiStructure=b;
  battles.set(b,{root,field,extras,operations,command,actions,log});
 }
 const items=region('items','shared'),targets=region('targets','shared');
 document.body.append(items,targets);items.append(q('#normalItems'));targets.append(q('#battleTargetPanel'));
 function placeOverlay(id,el){
  const container=id==='normalItems'?items:id==='battleMsg2'?battles.get('normal').log:id==='rbMsg'?battles.get('raider').log:null;
  if(container&&el.parentElement!==container)container.append(el);
 }
 function adoptEnemies(){
  for(const {root,extras}of battles.values())root.querySelectorAll(':scope > .prologueEnemy').forEach(el=>extras.append(el));
 }
 function owner(){
  const b=document.body.classList.contains('raiderBattleMode')?'raider':'normal';
  items.dataset.battle=targets.dataset.battle=b;
  const controls=battles.get(b).operations;
  if(items.parentElement!==controls)controls.append(items);
  if(targets.parentElement!==controls)controls.append(targets);
  for(const [id,{root,log}]of battles)root.setAttribute('aria-owns',id===b?[log.id,items.id,targets.id].join(' '):log.id);
 }
 for(const {root}of battles.values())new MutationObserver(adoptEnemies).observe(root,{childList:true});
 new MutationObserver(owner).observe(document.body,{attributes:true,attributeFilter:['class']});
 // Target hitboxes remain viewport positioned; moving them under a neutral portal preserves coordinates.
 new MutationObserver(records=>{for(const record of records)for(const el of record.addedNodes)if(el.nodeType===1&&el.classList.contains('battleTargetHit'))targets.append(el);}).observe(document.body,{childList:true});
 adoptEnemies();owner();
 window.BattleUIRegions=Object.freeze({get:b=>battles.get(b),items,targets,placeOverlay});
})();
