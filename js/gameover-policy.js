/* GAMEOVER-01: pure progression policy; no battle/DOM/save side effects. */
(function(root){
 'use strict';
 function gameOverEnabled(progress){
  if(!progress||typeof progress!=='object')return false;
  // Existing story stage 5 marks the village attack; do not add a new persisted flag.
  const stage=progress.storyStage;
  return Number.isInteger(stage)&&stage>=5&&stage<=15;
 }
 const api=Object.freeze({gameOverEnabled});
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.GameOverPolicy=api;
})(typeof window!=='undefined'?window:null);
