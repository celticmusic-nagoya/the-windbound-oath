/* GAMEOVER-01: opt-in overlay. No gameplay side effects until wired to defeat paths. */
(function(root){
 'use strict';
 let active=false,overlay=null,previousFocus=null;
 function show(actions){
  if(active)return false;
  if(!actions||typeof actions.onContinue!=='function'||typeof actions.onTitle!=='function')return false;
  active=true;previousFocus=document.activeElement;
  overlay=document.createElement('section');overlay.id='twoGameOver';overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-labelledby','twoGameOverHeading');
  overlay.innerHTML='<div class="twoGameOverPanel"><p class="twoGameOverEyebrow">THE WINDBOUND OATH</p><h2 id="twoGameOverHeading">GAME OVER</h2><p>風の誓いは、まだ果たされていない。</p><div class="twoGameOverActions"><button type="button" data-action="continue">タイトルでセーブを選んで再開</button><button type="button" data-action="title">タイトルへ戻る</button></div><p role="status" class="twoGameOverStatus"></p></div>';
  const status=overlay.querySelector('[role=status]');
  async function invoke(callback){
   overlay.querySelectorAll('button').forEach(b=>b.disabled=true);
   try{const ok=await callback();if(ok===false)throw Error('Action unavailable');hide();}
   catch(_){status.textContent='処理を完了できませんでした。もう一度お試しください。';overlay.querySelectorAll('button').forEach(b=>b.disabled=false);}
  }
  overlay.addEventListener('click',e=>{const action=e.target.closest('button')?.dataset.action;if(action==='continue')void invoke(actions.onContinue);if(action==='title')void invoke(actions.onTitle)});
  overlay.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();return}if(e.key!=='Tab')return;const buttons=[...overlay.querySelectorAll('button:not(:disabled)')];if(!buttons.length)return;const first=buttons[0],last=buttons[buttons.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}});
  document.body.append(overlay);overlay.querySelector('button').focus();return true;
 }
 function hide(){if(!active)return false;active=false;overlay?.remove();overlay=null;if(previousFocus?.isConnected)previousFocus.focus();previousFocus=null;return true}
 root.GameOverScreen=Object.freeze({show,hide,get active(){return active}});
})(typeof window!=='undefined'?window:{});
