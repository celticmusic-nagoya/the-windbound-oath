'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('js/hidden-checkpoints.js','utf8');
function setup(){const data=new Map([['windbound_oath_slot_v1_01','manual']]);const window={localStorage:{getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v)}};vm.runInNewContext(source,{window});return {api:window.HiddenCheckpoints,data}}
const payload=JSON.stringify({version:30,prologue:{storyStage:9},battleItems:{potion:1}});
const safe={storyStage:9,mapId:'forest',x:4,y:5,inBattle:false,transitioning:false,forcedEncounter:false,canEscape:true,canRecover:true};
const retry={storyStage:9,mapId:'forest',x:4,y:5,inBattle:false,transitioning:false,encounterId:'fieldGob1',canAvoidEncounter:true};
test('safe slot 21 and retry slot 22 are separate from manual slots',()=>{const {api,data}=setup();assert.equal(api.write('safe',payload,safe),true);assert.equal(api.write('retry',payload,retry),true);assert.equal(api.read('safe').ok,true);assert.equal(api.read('retry').ok,true);assert.equal(data.get('windbound_oath_slot_v1_01'),'manual');assert.equal(data.size,3)});
test('unsafe map entry cannot replace last safe checkpoint',()=>{const {api,data}=setup();assert.equal(api.write('safe',payload,safe),true);const before=data.get(api.key('safe'));assert.equal(api.write('safe',payload,{...safe,forcedEncounter:true}),false);assert.equal(api.write('safe',payload,{...safe,canRecover:false}),false);assert.equal(data.get(api.key('safe')),before)});
test('retry requires avoidable encounter and prebattle state',()=>{const {api}=setup();assert.equal(api.write('retry',payload,{...retry,canAvoidEncounter:false}),false);assert.equal(api.write('retry',payload,{...retry,inBattle:true}),false);assert.equal(api.read('retry').ok,false)});
test('rejects corrupt and inconsistent checkpoint',()=>{const {api,data}=setup();assert.equal(api.write('safe',payload,safe),true);const record=JSON.parse(data.get(api.key('safe')));record.storyStage=10;data.set(api.key('safe'),JSON.stringify(record));assert.equal(api.read('safe').ok,false)});

test('browser loads hidden storage module but never exposes unverified restore',()=>{const html=fs.readFileSync('index.html','utf8'),combat=fs.readFileSync('js/prologue-combat.js','utf8');assert.match(html,/src="js\/hidden-checkpoints\.js/);assert.match(html,/src="js\/battle-checkpoint\.js/);assert.doesNotMatch(combat,/onRetry:\(\)=>|onContinue:\(\)=>/)});

test('manual save and hidden checkpoints share one v30 serializer without automatic writes',()=>{const html=fs.readFileSync('index.html','utf8');assert.match(html,/function serializeCheckpointGrowthData\(\)/);assert.match(html,/const raw=serializeCheckpointGrowthData\(\)/);assert.match(html,/SaveSlots\.save\(slot,raw,\{overwrite:!!old\}\)/);assert.doesNotMatch(html,/HiddenCheckpoints\.write\(/)});
