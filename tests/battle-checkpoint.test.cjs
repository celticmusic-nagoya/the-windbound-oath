'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync('js/battle-checkpoint.js','utf8');
function setup(fail=false){const records=new Map();const storage={getItem:k=>records.has(k)?records.get(k):null,setItem:(k,v)=>{if(fail)throw Error('quota');records.set(k,v)},removeItem:k=>records.delete(k)};const window={sessionStorage:storage};vm.runInNewContext(source,{window});return {api:window.BattleCheckpoint,records}}
const raw=JSON.stringify({version:30,prologue:{storyStage:9},battleItems:{potion:3}});
test('captures valid battle snapshot without touching numbered slots',()=>{const {api,records}=setup();assert.equal(api.capture('normal','fieldGob1',raw),true);assert.equal(api.inspect().ok,true);assert.equal(api.inspect().snapshot.encounterId,'fieldGob1');assert.deepEqual([...records.keys()],[api.KEY]);assert.equal(api.clear(),true);assert.equal(api.inspect().ok,false)});
test('rejects invalid snapshot and unsupported kind',()=>{const {api}=setup();assert.equal(api.capture('normal','fieldGob1','{}'),false);assert.equal(api.capture('unknown','fieldGob1',raw),false);assert.equal(api.inspect().ok,false)});
test('quota failure fails closed',()=>{const {api}=setup(true);assert.equal(api.capture('raider','raider',raw),false);assert.equal(api.inspect().ok,false)});
test('detects corrupted payload',()=>{const {api,records}=setup();records.set(api.KEY,'not json');assert.equal(api.inspect().ok,false)});

test('rejects tampered stage and retains no numbered slot writes',()=>{const {api,records}=setup();assert.equal(api.capture('raider','raider',raw),true);const tampered=JSON.parse(records.get(api.KEY));tampered.storyStage=16;records.set(api.KEY,JSON.stringify(tampered));assert.equal(api.inspect().ok,false);assert.equal([...records.keys()].some(k=>k.startsWith('windbound_oath_slot_v1_')),false)});
