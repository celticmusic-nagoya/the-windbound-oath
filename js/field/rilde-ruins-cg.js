/* Approved ruins CG: opt-in presentation only, never invoked on map enter/save.
 * The narrative event owner must explicitly call show() after its own trigger is approved.
 */
(function(){
 'use strict';
 const ID='rildeRuinsCg';
 const PATH='assets/approved/game/rilde_story/aftermath/ruins_background_only.png';
 let active=false;
 function hide(){
   const el=document.getElementById(ID);
   if(el)el.remove();
   active=false;
 }
 function show(){
   if(active)return false;
   if(!window.RildeCG || window.RildeCG.gameplayPathFor('aftermath_background')!==PATH)return false;
   const el=document.createElement('div');
   el.id=ID;
   el.className='rilde-ruins-cg';
   el.setAttribute('role','dialog');
   el.setAttribute('aria-label','リルド村の廃墟');
   el.tabIndex=0;
   const img=document.createElement('img');
   img.src=PATH;
   img.alt='廃墟となったリルド村';
   img.decoding='async';
   const close=document.createElement('button');
   close.type='button';
   close.textContent='閉じる';
   close.className='rilde-ruins-cg-close';
   close.addEventListener('click',hide);
   el.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();hide();}});
   el.append(img,close);
   document.body.appendChild(el);
   active=true;
   close.focus();
   return true;
 }
 window.RildeRuinsCG=Object.freeze({show,hide,get active(){return active;}});
})();
