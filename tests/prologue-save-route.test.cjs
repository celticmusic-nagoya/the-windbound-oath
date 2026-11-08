// Executes actual PrologueProgress.plan() with isolated dependencies.
// Run: node tests/prologue-save-route.test.cjs
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('js/prologue-progress.js','utf8');
const dom=new Map();
const context={
 document:{querySelector:(selector)=>{if(!dom.has(selector))dom.set(selector,{style:{display:''},classList:{add(){},remove(){}},hidden:false});return dom.get(selector);}},
 window:{MossForest:null,MossForestStory:null},
 MossForestStory:{canRestoreEarlyMap:()=>false,canRestoreFreeRoamMap:()=>false},
 MossForest:{map:null},
 flags:{},
 forestGobWins:0,
};
vm.createContext(context);
vm.runInContext(source,context);
const defeated=['moss_corruption_01','moss_corruption_02','moss_corruption_03'];
const progress=(stage,version=2)=>({version,storyStage:stage,defeated,subQuests:{}});
for(const [stage,expected] of [[13,'AFTERMATH'],[14,'FORT_FINALE'],[15,'PROLOGUE_END']]){
 for(const version of [1,2]){
  const actual=context.window.PrologueProgress.plan(progress(stage,version));
  assert.equal(actual.kind,expected,'old SAVE stage '+stage+' v'+version);
  assert.equal(actual.stage,stage);
  console.log('PASS SAVE v'+version+' stage '+stage+' → '+expected);
 }
}
const damaged=context.window.PrologueProgress.plan({...progress(14),defeated:[]});
assert.equal(damaged.stage,10,'inconsistent forest victories must not bypass progression');
console.log('PASS invalid stage14 with missing victories falls back to stage10');
console.log('7/7 SAVE routing cases passed');
