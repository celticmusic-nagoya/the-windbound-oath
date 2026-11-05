// Controlled isolated VM replay of unchanged source functions. No live browser/game state.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const root=process.argv[2];if(!root)throw Error('usage: node clock-counterfactual.cjs <repo>');
const median=a=>{const b=a.slice().sort((x,y)=>x-y),m=b.length>>1;return b.length%2?b[m]:(b[m-1]+b[m])/2};
const results=[];
for(const gap of [1000/60,100])for(const [route,dx,dy]of [['straight',0,-1],['ul',-Math.SQRT1_2,-Math.SQRT1_2],['ur',Math.SQRT1_2,-Math.SQRT1_2]]){
 let cb;const s={WINDBOUND_DEV:true,requestAnimationFrame:f=>{cb=f;return 1}};s.window=s;vm.createContext(s);
 for(const file of ['js/field/field-movement.js','js/field/walk-motion.js','js/field/aidan-field-assets.js'])vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),s,{filename:file});
 const W=s.FieldWalkMotion,M=s.FieldMovement,bank=W.ally('aidan','up');assert.equal(bank.frames.length,5);assert.equal(bank.stride,90);
 cb(0);let x=10000,y=10000,travel=0;const rows=[],tr=[];
 for(let i=1;i<=120;i++){
  const t=i*gap;cb(t);const step=M.settings.pointerStep*M.frameScale;const next=M.advance(x,y,dx*step,dy*step,()=>false,{bounds:{width:20000,height:20000}});travel+=Math.hypot(next.x-x,next.y-y);x=next.x;y=next.y;const phase=W.phaseDistance(travel,bank.frames.length,bank.stride);const row={t,x,y,phase,frameScale:M.frameScale,advance_world:step,total_arc_world:travel};rows.push(row);if(!tr.length||tr[tr.length-1].phase!==phase)tr.push(row);
 }
 const cycles=tr.slice(0,-5).map((a,i)=>({world:Math.hypot(tr[i+5].x-a.x,tr[i+5].y-a.y),seconds:(tr[i+5].t-a.t)/1000}));const order=tr.every((r,i)=>!i||r.phase===(tr[i-1].phase+1)%5);const d=median(cycles.map(r=>r.world)),sec=median(cycles.map(r=>r.seconds));const originalCadence=cycles.length>=4&&Math.abs(d-90)<12&&Math.abs(sec-.3)<.08;
 assert.ok(order);assert.ok(Math.abs(d-90)<1e-7);assert.equal(originalCadence,gap<50);if(gap===100){assert.ok(rows.every(r=>r.frameScale===3));assert.ok(Math.abs(sec-.6)<1e-7)}else assert.ok(Math.abs(sec-.3)<1e-7);
 results.push({route,mock_raf_gap_ms:gap,ordered_five_phases:order,cycle_windows:cycles.length,median_world:d,median_wall_seconds:sec,maximum_frame_scale:Math.max(...rows.map(r=>r.frameScale)),maximum_advance_world:Math.max(...rows.map(r=>r.advance_world)),original_cadence_predicate:originalCadence,rows});
}
console.log(JSON.stringify({kind:'isolated source-function counterfactual; NOT original-failure replay, browser observation or integration QA',source_files:['js/field/field-movement.js','js/field/walk-motion.js','js/field/aidan-field-assets.js'],no_live_game_changes:true,results},null,2));
