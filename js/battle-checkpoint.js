/* BATTLE-CHECKPOINT-01: isolated pre-battle snapshot store. Restoration is gated separately. */
(function(root){
 'use strict';
 const KEY='two_battle_checkpoint_v1';
 const VALID_KINDS=new Set(['normal','raider']);
 function store(){if(!root?.sessionStorage)throw Error('Session storage unavailable');return root.sessionStorage}
 function capture(kind,encounterId,raw){
  if(!VALID_KINDS.has(kind)||typeof encounterId!=='string'||!encounterId||typeof raw!=='string')return false;
  let data;try{data=JSON.parse(raw)}catch{return false}
  if(!data||data.version!==30||!data.prologue||!Number.isInteger(data.prologue.storyStage)||data.prologue.storyStage<0||data.prologue.storyStage>15)return false;
  const snapshot={schema:1,kind,encounterId,storyStage:data.prologue.storyStage,payload:raw};
  try{store().setItem(KEY,JSON.stringify(snapshot));return true}catch{return false}
 }
 function inspect(){
  try{const raw=store().getItem(KEY);if(!raw)return {ok:false,reason:'missing'};
   const snapshot=JSON.parse(raw);if(!snapshot||snapshot.schema!==1||!VALID_KINDS.has(snapshot.kind)||typeof snapshot.encounterId!=='string'||!snapshot.encounterId||typeof snapshot.payload!=='string')return {ok:false,reason:'invalid'};
   const data=JSON.parse(snapshot.payload);
   if(!data||data.version!==30||!data.prologue||!Number.isInteger(data.prologue.storyStage)||data.prologue.storyStage<0||data.prologue.storyStage>15||data.prologue.storyStage!==snapshot.storyStage)return {ok:false,reason:'invalid'};
   return {ok:true,snapshot};
  }catch{return {ok:false,reason:'unavailable'}}
 }
 function clear(){try{store().removeItem(KEY);return true}catch{return false}}
 const api=Object.freeze({capture,inspect,clear,KEY});
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.BattleCheckpoint=api;
})(typeof window!=='undefined'?window:null);
