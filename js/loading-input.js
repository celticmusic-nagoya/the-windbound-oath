// One input policy for map/battle Loading and their explicit recovery controls.
// Installed in <head> before game handlers; InputManager also calls the same policy itself.
(() => {
 'use strict';
 let owner=null,suppressClick=false;
 const down=new Set(),quarantined=new Set(),pointers=new Set(),blockedPointers=new Set(),handled=new WeakSet();
 const stop=e=>{e.preventDefault();e.stopImmediatePropagation();handled.add(e);return true;};
 function control(target){
  const button=target?.closest?.('button[data-loading-action]');
  const root=button?.closest?.('#loadingStatus,#fieldEntryError,#loadStatus');
  return root&&!root.hidden&&!button.hidden&&!button.disabled?button:null;
 }
 function handle(e){
  if(handled.has(e))return true;
  const action=control(e.target),key=e.code||e.key;
  if(e.type==='keydown'){
   const repeated=e.repeat||down.has(key);down.add(key);
   if(quarantined.has(key))return stop(e);
   if(owner!==null||action){
    quarantined.add(key);
    // Consume native key activation too: Enter/Space can only click once, never again on keyup.
    if(action&&!repeated&&(e.key==='Enter'||e.key===' ')){stop(e);action.click();return true;}
    if(action&&!repeated&&e.key==='Tab'){action.focus?.({preventScroll:true});return stop(e);}
    return stop(e);
   }
   return false;
  }
  if(e.type==='keyup'){
   down.delete(key);const blocked=quarantined.delete(key);
   return owner!==null||blocked?stop(e):false;
  }
  if(e.type==='pointerdown'){
   pointers.add(e.pointerId);
   if(owner!==null&&!action){blockedPointers.add(e.pointerId);suppressClick=true;return stop(e);}
   if(owner===null||action){blockedPointers.delete(e.pointerId);suppressClick=false;}
  }
  if(e.type==='pointerup'||e.type==='pointercancel')pointers.delete(e.pointerId);
  if(blockedPointers.has(e.pointerId)&&e.type!=='pointerdown'&&!action)return stop(e);
  if(e.type==='click'&&suppressClick&&!action){suppressClick=false;return stop(e);}
  if(owner!==null&&!action)return stop(e);
  return false;
 }
 function lock(key){
  owner=key;down.forEach(k=>quarantined.add(k));pointers.forEach(id=>blockedPointers.add(id));
  if(pointers.size)suppressClick=true;
  dispatchEvent(new CustomEvent('loading-input-lock'));
 }
 function release(key){if(owner===key)owner=null;}
 for(const type of ['keydown','keyup','pointerdown','pointermove','pointerup','pointercancel','click','dblclick','contextmenu'])addEventListener(type,handle,true);
 addEventListener('blur',()=>{down.forEach(k=>quarantined.add(k));down.clear();pointers.clear();});
 window.LoadingInput=Object.freeze({lock,release,handle,allowedTarget:target=>Boolean(control(target)),get busy(){return owner!==null}});
})();
