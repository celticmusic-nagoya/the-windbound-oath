// Owns the boot/load boundary. Failed loads never become saveable implicitly.
(() => {
 'use strict';
 let phase='BOOTING',generation=0,retryAction=null,initialized=false,dialogueRevision=0;
 const invalidators=new Set();let inputOwner=null;
 function releaseInput(key){window.LoadingView?.close(key+':view');window.LoadingInput?.release(key);if(inputOwner===key)inputOwner=null;}
 function releaseCurrentInput(){if(inputOwner!==null)releaseInput(inputOwner);}
 function invalidate(){for(const fn of [...invalidators])fn();}
 const node=id=>document.getElementById(id);
 function message(text,failed=false){
  const panel=node('loadStatus');if(!panel)return;
  panel.hidden=false;node('loadStatusText').textContent=text;
  node('retryLoad').hidden=!failed;node('retryLoad').disabled=!failed;
 }
 function hide(){const panel=node('loadStatus');if(panel)panel.hidden=true;}
 const current=token=>token===generation;
 function assertCurrent(token){if(token!==undefined&&!current(token))throw new Error('Cancelled load');}
 async function execute(task,isBoot,retry){
  invalidate();releaseCurrentInput();
  const token=++generation;phase=isBoot?'BOOTING':'LOADING';retryAction=retry;
  if(isBoot)window.MossForest?.cancelPendingEnter();
  const owner='coordinator:'+token;inputOwner=owner;window.LoadingInput?.lock(owner);
  window.LoadingView?.open(owner+':view',isBoot?'起動処理中です。':'記録を復帰しています。');
  message(isBoot?'起動処理中です。':'記録を復帰しています。');
  try{
   await task(token);assertCurrent(token);await window.LoadingView?.settle(owner+':view');assertCurrent(token);
   if(isBoot)initialized=true;phase='READY';retryAction=null;hide();releaseInput(owner);return true;
  }catch(error){
   if(current(token)){
    phase='FAILED';window.LoadingView?.close(owner+':view');message('復帰できませんでした。セーブデータは保持されています。再試行してください。',true);
   }else releaseInput(owner);
   return false;
  }
 }
 function boot(task){return execute(task,true,()=>boot(task));}
 function mayLoad(){return initialized&&(phase==='READY'||phase==='FAILED');}
 function run(task,retry){
  if(!mayLoad()){message(phase==='BOOTING'?'起動処理中のためロードできません。開始後にもう一度操作してください。':'記録を復帰中のためロードできません。');return Promise.resolve(false)}
  return execute(task,false,retry);
 }
 function retry(){if(phase==='FAILED'&&retryAction)return retryAction();return Promise.resolve(false);}
 function explainGuard(){message(!initialized?'起動が完了していないためロードできません。開始後にもう一度操作してください。':'記録を復帰中のためロードできません。',phase==='FAILED');}
 // A deliberate DEV destination takes ownership from boot/load; its map transaction keeps its own S2 save guard.
 function supersede(){invalidate();releaseCurrentInput();generation++;retryAction=null;initialized=true;phase='READY';hide();}
 if(typeof addEventListener==='function')addEventListener('pagehide',e=>{
  if(e.persisted)return; // bfcache resumes the same page; a real reload/goto discards this owner.
  invalidate();releaseCurrentInput();generation++;retryAction=null;initialized=false;phase='BOOTING';
  window.MossForest?.cancelPendingEnter();window.BattleLoading?.cancel();
 });
 node('retryLoad')?.addEventListener('click',retry);
 for(const type of ['pointerdown','keydown'])document.addEventListener(type,e=>{if((phase==='LOADING'||phase==='FAILED')&&!window.LoadingInput?.allowedTarget(e.target)&&!e.target.closest?.('#loadStatus,#systemMenu,#menuOpen')){e.preventDefault();e.stopImmediatePropagation();}},true);
 window.LoadCoordinator=Object.freeze({boot,run,retry,mayLoad,explainGuard,current,assertCurrent,supersede,onInvalidate(fn){invalidators.add(fn);return ()=>invalidators.delete(fn);},noteDialogue(){dialogueRevision++;},get dialogueRevision(){return dialogueRevision},get phase(){return phase},get generation(){return generation},get canSave(){return phase==='READY'}});
})();
