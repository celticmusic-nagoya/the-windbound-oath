/* GAMEOVER-01: pure progression policy; no battle/DOM/save side effects. */
(function(root){
 'use strict';
 function gameOverEnabled(progress){
  if(!progress||typeof progress!=='object')return false;
  // Existing story stage 5 marks the village attack; do not add a new persisted flag.
  const stage=progress.storyStage;
  return Number.isInteger(stage)&&stage>=5&&stage<=15;
 }
 // Defeat must be a complete active-party wipe, never a single ally reaching 0 HP.
 function decideDefeat({progress,activeHp}={}){
  if(!Array.isArray(activeHp)||!activeHp.length||!activeHp.every(h=>typeof h==='number'&&Number.isFinite(h)&&h>=0))return 'INVALID';
  if(activeHp.some(h=>h>0))return 'CONTINUE';
  if(!gameOverEnabled(progress))return 'RECOVER';
  return 'GAME_OVER';
 }
 const api=Object.freeze({gameOverEnabled,decideDefeat});
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.GameOverPolicy=api;
})(typeof window!=='undefined'?window:null);
