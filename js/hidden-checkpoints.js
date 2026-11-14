/* HIDDEN-CHECKPOINTS-02: isolated persistent storage; not wired to live restore. */
(function(root){
 'use strict';
 const PREFIX='two_hidden_checkpoint_v1_',KINDS=Object.freeze({safe:21,retry:22});
 function storage(){if(!root?.localStorage)throw Error('Storage unavailable');return root.localStorage}
 function key(kind){if(!Object.prototype.hasOwnProperty.call(KINDS,kind))throw RangeError('Invalid checkpoint kind');return PREFIX+KINDS[kind]}
 function validate(kind,raw,context){
  if(typeof raw!=='string'||!raw||!context||typeof context!=='object')return null;
  let data;try{data=JSON.parse(raw)}catch{return null}
  if(!data||data.version!==30||!data.prologue||!Number.isInteger(data.prologue.storyStage)||data.prologue.storyStage<0||data.prologue.storyStage>15)return null;
  if(!Number.isInteger(context.storyStage)||context.storyStage!==data.prologue.storyStage)return null;
  if(typeof context.mapId!=='string'||!context.mapId||!Number.isFinite(context.x)||!Number.isFinite(context.y))return null;
  if(kind==='safe'){
   if(context.inBattle!==false||context.transitioning!==false||context.forcedEncounter!==false||context.canEscape!==true||context.canRecover!==true)return null;
  }else if(kind==='retry'){
   if(context.inBattle!==false||context.transitioning!==false||typeof context.encounterId!=='string'||!context.encounterId||context.canAvoidEncounter!==true)return null;
  }else return null;
  return {schema:1,slot:KINDS[kind],kind,storyStage:data.prologue.storyStage,context:{...context},payload:raw};
 }
 function read(kind){
  try{const item=storage().getItem(key(kind));if(!item)return {ok:false,reason:'missing'};
   const record=JSON.parse(item);
   if(!record||record.schema!==1||record.slot!==KINDS[kind]||record.kind!==kind)return {ok:false,reason:'invalid'};
   const valid=validate(kind,record.payload,record.context);
   if(!valid||JSON.stringify(valid.context)!==JSON.stringify(record.context)||valid.storyStage!==record.storyStage)return {ok:false,reason:'invalid'};
   return {ok:true,record};
  }catch{return {ok:false,reason:'unavailable'}}
 }
 function write(kind,raw,context){
  const record=validate(kind,raw,context);if(!record)return false;
  try{storage().setItem(key(kind),JSON.stringify(record));return true}catch{return false}
 }
 const api=Object.freeze({KINDS,key,read,write});
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.HiddenCheckpoints=api;
})(typeof window!=='undefined'?window:null);
