// Shared text-only loading view. Owner keys prevent stale map/battle responses closing a newer view.
(() => {
 'use strict';
 let owner=null,panel,text,tip,button,openedAt=0;
 const now=()=>typeof performance!=='undefined'?performance.now():Date.now();
 function open(key,message,retry){
  if(!panel){
   panel=document.createElement('div');panel.id='loadingStatus';panel.setAttribute('role','status');panel.setAttribute('aria-live','polite');
   text=document.createElement('p');tip=document.createElement('p');tip.id='loadingTip';tip.textContent='移動は方向キー・WASD、または目的地のクリック／タップで行えます。';button=document.createElement('button');button.type='button';button.textContent='再試行';button.setAttribute('data-loading-action','retry');
   panel.append(text,tip,button);document.body.append(panel);
  }
  if(owner!==null&&owner!==key)window.LoadingInput?.release(owner);
  owner=key;openedAt=now();window.LoadingInput?.lock(key);panel.hidden=false;text.textContent=message;button.hidden=!retry;button.disabled=!retry;button.onclick=retry||null;if(retry)button.focus?.({preventScroll:true});
 }
 function close(key){if(owner!==key)return;owner=null;window.LoadingInput?.release(key);if(panel)panel.hidden=true;}
 async function settle(key){
  if(owner!==key)return false;
  const started=openedAt;
  const frame=typeof requestAnimationFrame==='function'?requestAnimationFrame:fn=>setTimeout(fn,16);
  await new Promise(resolve=>frame(()=>frame(resolve)));
  const remaining=120-(now()-started);if(remaining>0)await new Promise(resolve=>setTimeout(resolve,remaining));
  return owner===key;
 }
 window.LoadingView=Object.freeze({open,close,settle});
})();
