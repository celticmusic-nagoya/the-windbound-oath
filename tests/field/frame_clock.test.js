// Exercise the actual rAF clock, not clock.set(), over equal simulated wall time.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
for(const hz of [30,60,120,144,240,1000]){
  let tick;
  const w={requestAnimationFrame:cb=>{tick=cb;}};w.window=w;
  vm.runInNewContext(fs.readFileSync('js/field/field-movement.js','utf8'),w);
  tick(0);
  let x=100;
  for(let i=1;i<=hz*2;i++){
    tick(i*1000/hz);
    const m=w.FieldMovement;
    x=m.advance(x,100,m.settings.pointerStep*m.frameScale,0,()=>false,{bounds:{width:5000,height:1000}}).x;
  }
  assert(Math.abs(x-700)<.001,`${hz} Hz: ${x-100} px instead of 600`);
  console.log(`ok ${hz} Hz actual clock: ${(x-100).toFixed(3)} px / 2 s`);
}

// First RAF may predate mount's performance.now() after a delayed rendering task.
// The real renderer must never send an undefined image URL or rewind its animation clock.
{
 const sources=[];let nextFrame,rafId=0;
 const makeElement=()=>({style:{},dataset:{},appendChild(){},remove(){},set src(value){sources.push(String(value));}});
 const fixture={performance:{now:()=>1000},requestAnimationFrame:fn=>(nextFrame=fn,++rafId),cancelAnimationFrame(){},document:{createElement:makeElement},Image:function(){return makeElement()},ForestLoader:{art:{manifest:{base:'img/',node:[{match:'npc_slot_test',file:'idle.png',w:32,h:48,walk:{file:'walk_{n}.png',frames:6}}]}}},MossForest:{snapshot:()=>({x:0,y:0})}};fixture.window=fixture;
 vm.runInNewContext(fs.readFileSync('js/field/field-walkers.js','utf8'),fixture);
 fixture.FieldWalkers.mount({walkers:[{id:'test',look:'test',x:1000,y:1000,anim:true}]},makeElement());
 nextFrame(750);
 assert(fixture.FieldWalkers.list[0].clock>=0,'first RAF must not rewind the NPC clock');
 assert(sources.every(path=>path.startsWith('img/')),'negative first-frame delta must not request undefined image');
 for(let time=1000;time<=2000;time+=1000/60)nextFrame(time);
 assert(sources.every(path=>path.startsWith('img/')),'subsequent normal frames retain valid images');
 assert(sources.includes('img/walk_02.png')&&sources.includes('img/walk_06.png'),'normal walk frames continue to advance');
 fixture.FieldWalkers.clear();assert(fixture.FieldWalkers.list.length===0,'scene cleanup releases NPC records');
 console.log('ok walker real renderer: delayed first RAF, valid image URLs, normal frames and cleanup');
}
