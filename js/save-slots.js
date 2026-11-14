/* SAVE-SLOTS-20: storage layer only; game integration is a separate gated change. */
(function(root){
 'use strict';
 const COUNT=20,LEGACY='windbound_oath_v028',PREFIX='windbound_oath_slot_v1_';
 function validSlot(n){if(!Number.isInteger(n)||n<1||n>COUNT)throw new RangeError('Invalid save slot');return n}
 function key(n){return PREFIX+String(validSlot(n)).padStart(2,'0')}
 function storage(){if(!root||!root.localStorage)throw Error('Storage unavailable');return root.localStorage}
 function read(n){const raw=storage().getItem(key(n));if(raw===null)return null;const envelope=JSON.parse(raw);if(!envelope||envelope.schema!==1||envelope.slot!==n||typeof envelope.payload!=='string'||!envelope.payload)throw Error('Invalid slot data');const data=JSON.parse(envelope.payload);if(!data||!(data.version===30||(data.version===undefined&&data.prologue?.version===1))||!data.prologue||!Number.isInteger(data.prologue.storyStage)||data.prologue.storyStage<0||data.prologue.storyStage>15||envelope.storyStage!==data.prologue.storyStage||typeof envelope.savedAt!=='string'||!Number.isFinite(Date.parse(envelope.savedAt)))throw Error('Invalid slot payload');return envelope}
 function list(){return Array.from({length:COUNT},(_,i)=>{const slot=i+1;try{const item=read(slot);return {slot,occupied:!!item,savedAt:item?.savedAt||null,storyStage:item?.storyStage??null,corrupt:false}}catch(_){return {slot,occupied:true,savedAt:null,storyStage:null,corrupt:true}}})}
 function save(n,raw,{overwrite=false,now=new Date().toISOString()}={}){
  validSlot(n);if(typeof raw!=='string'||!raw)throw Error('Invalid payload');
  const data=JSON.parse(raw);if(!data||typeof data!=='object'||Array.isArray(data)||!data.prologue||!Number.isInteger(data.prologue.storyStage))throw Error('Invalid save format');
  const store=storage(),k=key(n);if(store.getItem(k)!==null&&!overwrite)throw Error('Overwrite confirmation required');
  // setItem is atomic for a single key; storage quota failure leaves existing value intact.
  const record={schema:1,slot:n,savedAt:now,storyStage:data.prologue.storyStage,payload:raw};store.setItem(k,JSON.stringify(record));return {slot:n,savedAt:now};
 }
 function remove(n,{confirmed=false}={}){validSlot(n);if(!confirmed)throw Error('Delete confirmation required');storage().removeItem(key(n));return true}
 function legacy(){return storage().getItem(LEGACY)}
 function payload(n){const record=read(n);return record?record.payload:null}
 const api=Object.freeze({COUNT,key,list,read,payload,save,remove,legacy});
 if(typeof module==='object'&&module.exports)module.exports=api;
 if(root)root.SaveSlots=api;
})(typeof window!=='undefined'?window:null);
