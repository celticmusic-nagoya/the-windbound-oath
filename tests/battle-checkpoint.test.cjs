'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const checkpoint=require('../js/battle-checkpoint.js');
const records=new Map();
global.window=undefined;
const storage={getItem:k=>records.has(k)?records.get(k):null,setItem:(k,v)=>records.set(k,v),removeItem:k=>records.delete(k)};
const api=require('../js/battle-checkpoint.js');
test('fail closed without browser sessionStorage',()=>{assert.equal(api.capture('normal','fieldGob1','{}'),false);assert.equal(api.inspect().ok,false)});
test('snapshot does not write numbered save slots',()=>{const original=global.sessionStorage;global.sessionStorage=storage;try{const raw=JSON.stringify({version:30,prologue:{storyStage:9}});assert.equal(api.capture('normal','fieldGob1',raw),false)}finally{global.sessionStorage=original}});
