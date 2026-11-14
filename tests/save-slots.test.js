'use strict';
const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../js/save-slots.js'),'utf8');
function env(){const values=new Map();const localStorage={getItem:k=>values.has(k)?values.get(k):null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};const window={localStorage};vm.runInNewContext(source,{window,Date,JSON,Number,RangeError,Error,Array,String});return {api:window.SaveSlots,values}}
const raw=JSON.stringify({version:30,prologue:{version:2,storyStage:5}});
test('20 independent slots, default empty',()=>{const {api}=env();assert.equal(api.list().length,20);assert.equal(api.list().filter(x=>x.occupied).length,0);assert.equal(api.key(20),'windbound_oath_slot_v1_20')});
test('save/read/overwrite require explicit confirmation',()=>{const {api}=env();api.save(1,raw,{now:'2026-11-14T00:00:00Z'});assert.equal(api.payload(1),raw);assert.throws(()=>api.save(1,raw));api.save(1,raw,{overwrite:true});assert.equal(api.list()[0].storyStage,5)});
test('delete is guarded and legacy is preserved',()=>{const {api,values}=env();values.set('windbound_oath_v028','legacy');api.save(20,raw);assert.throws(()=>api.remove(20));api.remove(20,{confirmed:true});assert.equal(api.payload(20),null);assert.equal(api.legacy(),'legacy')});
test('out-of-range slot cannot be written',()=>{const {api}=env();for(const n of [0,21,1.2])assert.throws(()=>api.save(n,raw))});
test('failed storage write preserves existing slot',()=>{const {api}=env();api.save(1,raw);const before=api.payload(1);const original=window;assert.equal(api.payload(1),before)});
