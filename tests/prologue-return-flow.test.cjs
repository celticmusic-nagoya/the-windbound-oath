// Isolated Node VM execution of the real aftermath/return handler from index.html.
// Run: node tests/prologue-return-flow.test.cjs
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
function slice(start,end){
 const a=html.indexOf(start),b=html.indexOf(end,a+start.length);
 assert(a>=0&&b>a,'cannot locate scene section');
 return html.slice(a,b);
}
const sceneSource=slice('const rildeReturnLines=[','const fortLines=[');
const elements={};
const get=id=>elements[id]??=( {style:{display:'none'},textContent:'',onclick:null} );
const events=[];
const context={
  $:get,
  window:{TalkPortrait:{
    open:(...x)=>events.push(['open',...x]),
    close:(...x)=>events.push(['close',...x]),
    page:(...x)=>events.push(['page',...x])
  }},
  PartyManager:{support:{joined:false}},
  PrologueCombat:{generation:0},
  aftermathPortraitOwner:'aftermathTalk',
  aftermathLines:['討伐後の会話1','討伐後の会話2'],
  aftermathPortraitPages:[{char:null},{char:null}],
  aftermathIndex:0,
  storyStage:13,
  forestActive:false,
  currentObjective:'',
  renderJournal:()=>{},
  questPop:msg=>events.push(['quest',msg]),
  startFortFinale:()=>events.push(['fort']),
  showAftermathPage:()=>{get('#aftermathText').textContent='aftermath';}
};
vm.createContext(context);
vm.runInContext(sceneSource,context);
const tap=()=>get('#aftermathScene').onclick();
assert.equal(get('#aftermathScene').style.display,'none');
tap(); // aftermath page 2
assert.equal(context.PartyManager.support.joined,false);
tap(); // Lou joins, return page 1
assert.equal(context.PartyManager.support.joined,true);
assert.equal(context.storyStage,14);
assert.equal(get('#aftermathScene').style.display,'block');
assert.match(get('#aftermathText').textContent,/リルド村へ戻った/);
assert.equal(events.filter(x=>x[0]==='fort').length,0);
for(let i=1;i<15;i++){
 tap();
 assert.equal(events.filter(x=>x[0]==='fort').length,0,'premature fort at return page '+i);
}
assert.match(get('#aftermathText').textContent,/ドゥンヴァル砦へ向かった/);
tap(); // after last page: fort exactly once
assert.equal(events.filter(x=>x[0]==='fort').length,1);
assert.equal(get('#aftermathScene').style.display,'none');
assert.equal(events.filter(x=>x[0]==='quest'&&x[1].includes('ルー')).length,1);
console.log('PASS: aftermath → Lou join → 15-page Rilde return → fort once');
