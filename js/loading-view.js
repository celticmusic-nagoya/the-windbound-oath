// Shared text-only loading view. Owner keys prevent stale map/battle responses closing a newer view.
(() => {
 'use strict';
 let owner=null,panel,text,button;
 function open(key,message,retry){
  if(!panel){
   panel=document.createElement('div');panel.id='loadingStatus';panel.setAttribute('role','status');panel.setAttribute('aria-live','polite');
   text=document.createElement('p');button=document.createElement('button');button.type='button';button.textContent='再試行';button.setAttribute('data-loading-action','retry');
   panel.append(text,button);document.body.append(panel);
  }
  owner=key;window.LoadingInput?.lock(key);panel.hidden=false;text.textContent=message;button.hidden=!retry;button.disabled=!retry;button.onclick=retry||null;if(retry)button.focus?.({preventScroll:true});
 }
 function close(key){if(owner!==key)return;owner=null;window.LoadingInput?.release(key);if(panel)panel.hidden=true;}
 window.LoadingView=Object.freeze({open,close});
})();
