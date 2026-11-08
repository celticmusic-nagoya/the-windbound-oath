// Execute actual saveGrowthData() with a stubbed storage and scene state.
// Run: node tests/prologue-return-save-guard.test.cjs
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const a=html.indexOf('function saveGrowthData(){');
const b=html.indexOf('function restoreContinueLegacy(',a);
assert(a>=0&&b>a,'saveGrowthData not found');
const source=html.slice(a,b);
const writes=[];
const notices=[];
const context={
 window:{BattleLoading:{canSave:true},FieldTalk:{serialize:()=>({})}},
 LoadCoordinator:{canSave:true},
 MossForest:{canSave:true,active:false,busy:false},
 forestActive:false,
 storyStage:14,
 rildeReturnActive:true,
 document:{body:{classList:{contains:()=>false}}},
 notice:msg=>notices.push(msg),
 localStorage:{setItem:(key,value)=>writes.push([key,value])},
 SAVE_KEY:'test',
 Inventory:{serialize:()=>({})},
 EquipmentManager:{serialize:()=>({})},
 Quest:{serialize:()=>({})},
 PrologueProgress:{serialize:()=>({})},
 PartyManager:{members:{},active:[],reserve:[],squads:{},support:{}},
 gold:0,battleItems:{},
 $:()=>null,
 renderSystemTab:()=>{}
};
vm.createContext(context);
vm.runInContext(source,context);
vm.runInContext('saveGrowthData()',context);
assert.equal(writes.length,0,'return-scene SAVE must be blocked');
assert.equal(notices.length,1,'user should be informed');
context.rildeReturnActive=false;
vm.runInContext('saveGrowthData()',context);
assert.equal(writes.length,1,'SAVE should resume outside return scene');
assert.equal(JSON.parse(writes[0][1]).version,30,'SAVE schema unchanged');
console.log('PASS return scene blocks SAVE and displays notice');
console.log('PASS outside return scene SAVE succeeds with version 30');
