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
