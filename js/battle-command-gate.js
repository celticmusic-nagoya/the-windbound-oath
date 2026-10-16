// Player-command admission only. Combat execution, costs and turn order stay in the existing engine.
(() => {
 'use strict';
 if(window.BattleCommandGate)return; // Mount once; reloading must not create another owner.
 let provider=null,epoch=0,scheduled=false;const contexts=new Map();
 const receipts=new WeakMap();
 const mode=()=>document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null;
 function read(b=mode()){
  const generation=window.PrologueCombat?.generation;
  const actor=b==='normal'?normalActor:b==='raider'?rbActor:null;
  const round=b==='normal'?window.PrologueCombat?.roundNumber:b==='raider'?rbRound:null;
  let requestId='ui-only',phase='input',opening='legacy',reason=null;
  if(!['normal','raider'].includes(b)||mode()!==b||!document.body.classList.contains('battleMode')||!Number.isInteger(generation))reason='inactive';
  // Known frozen API is read defensively. No assumed future BattlePresentation API is called.
  if(window.BattleLoading?.frozen)reason='loading';
  if(provider){
   try{
    const s=provider();
    if(!s||typeof s.requestId!=='string'||!s.requestId||s.battle!==b||s.generation!==generation)reason='admission-context';
    requestId=s?.requestId;phase=s?.phase;opening=s?.opening;
    if(phase!=='input'||!(opening==='completed'||opening==='skipped'&&s.skipAllowed===true&&typeof s.skipReason==='string'&&s.skipReason))reason='start-not-complete';
   }catch(e){reason='admission-error';requestId='provider-error';phase='failed';}
  }else if(window.BattleLoading){reason='bridge-required';phase='unbound';}
  if(window.BattlePresentation?.busy||document.body.classList.contains('battlePresentationBusy')||document.body.classList.contains('actionCinematic'))reason='presentation';
  if(b==='normal'?attackBattleBusy:b==='raider'?rbBusy:false)reason='engine';
  if(document.body.classList.contains('battleResultMode'))reason='result';
  if(['normal','raider'].includes(b)&&window.PrologueCombat&&!(PrologueCombat.targets(b)||[]).some(e=>e.hp()>0))reason='no-live-targets';
  const signature=JSON.stringify([mode(),b,generation,round,actor,requestId,phase,opening,reason]);
  let context=contexts.get(b);
  if(context?.signature!==signature){context={signature,epoch:++epoch};contexts.set(b,context);notify();}
  return Object.freeze({battle:b,generation,round,actor,requestId,phase,opening,reason,allowed:!reason,key:signature+'@'+context.epoch});
 }
 function notify(){if(scheduled)return;scheduled=true;queueMicrotask(()=>{scheduled=false;dispatchEvent(new CustomEvent('battle-command-admission'));});}
 function issue(b){const s=read(b);if(!s.allowed)return null;const receipt=Object.freeze({});receipts.set(receipt,{...s,used:false});return receipt;}
 function valid(receipt,b){const r=receipts.get(receipt);return !!r&&!r.used&&r.battle===b&&read(b).allowed&&r.key===read(b).key;}
 function legal(b,a){
  const f=a.who==='fiona',normal=b==='normal';
  if(a.kind==='item')return ['potion','ether'].includes(a.item)&&battleItems[a.item]>0;
  if(!f&&a.kind==='skill'&&(normal?aatp:rbTP)<30)return false;
  if(!normal&&!f&&a.kind==='wind'&&rbRune<100)return false;
  if(f&&['heal','windbloom'].includes(a.kind)&&(normal?normalFMP:rbFMP)<8)return false;
  if(f&&a.kind===(normal?'prayer':'rune')&&(normal?normalFMP:rbFMP)<6)return false;
  if(f&&a.kind==='winddance'&&(!window.WindDance?.commandVisible()||(normal?normalFMP:rbFMP)<WindDance.mp()))return false;
  return true;
 }
 function commit(receipt,action){
  const r=receipts.get(receipt);if(!r||!action||!valid(receipt,r.battle)||action.who!==r.actor||!legal(r.battle,action))return false;
  // One owner consumes the receipt BEFORE any callback, pose or turn transition can re-enter.
  r.used=true;
  const b=r.battle;
  if(action.kind==='item'){document.querySelector('#normalItems').classList.remove('isOpen');document.querySelector('#normalItems').style.display='none';}
  if(action.kind==='guard')BattleActorState.set(r.actor,'guard',{battle:b});
  if(b==='normal'){normalActs.push(action);advanceNormalActor();}
  else{
   rbActs.push(action);
   if(r.actor==='aidan'){
    rbActor='fiona';
    if(action.kind!=='item')showRaiderBattleLog('フィオナの行動を選択。');
    updateRaider();
   }else{rbBusy=true;resolvePartyRound();}
  }
  read(b);return true;
 }
 window.BattleCommandGate=Object.freeze({snapshot:read,canInteract:b=>read(b).allowed,issue,valid,commit,
  revoke(receipt){const r=receipts.get(receipt);if(r)r.used=true;},
  // Explicit Codex-owned adapter point. Claude's eventual public contract must be mapped here after review.
  installAdmissionProvider(fn){if(typeof fn!=='function')throw new TypeError('Admission provider must be a function');provider=fn;contexts.clear();read();},
  refresh(){return read();}
 });
})();
