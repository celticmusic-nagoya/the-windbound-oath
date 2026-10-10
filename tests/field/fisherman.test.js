// Run: node tests/field/fisherman.test.js
const fs=require('fs'),vm=require('vm'),path=require('path');
const w={WINDBOUND_DEV:true,LindFishermanAssets:{},console};w.window=w;const ctx=vm.createContext(w);
vm.runInContext(fs.readFileSync(path.join(__dirname,'../../js/field/lind-fisherman.js'),'utf8'),ctx);
const F=w.LindFisherman;let fail=0;const ok=(c,m)=>{console.log(c?'ok  ':'FAIL',m);if(!c)fail++;};
function sim(seed,minutes,dt=1/60){
  const a={fishing:{state:'FISH_IDLE',elapsed:0,time:0,wait:12,seed,catches:0,lastCatch:0,nextCatch:45+((Math.imul(seed,1664525)+1013904223)>>>0)/4294967296*30}};
  const times=[];let prev=a.fishing.catches;
  for(let t=0;t<minutes*60;t+=dt){F.advance(a,dt);if(a.fishing.catches!==prev){times.push(a.fishing.time);prev=a.fishing.catches;}}
  return times.map((t,i)=>i?t-times[i-1]:null).slice(1);
}
const all=[];for(const seed of [8721,1,42,99999]){const iv=sim(seed,30);all.push(...iv);
  ok(iv.length>=24&&iv.every(x=>x>=44.5&&x<=76),`seed ${seed}: ${iv.length+1} catches / 30 min, intervals ${Math.min(...iv).toFixed(1)}-${Math.max(...iv).toFixed(1)}s`);}
const mean=all.reduce((x,y)=>x+y,0)/all.length;ok(mean>=55&&mean<=65,`mean catch interval ${mean.toFixed(1)}s (target 60s)`);
process.exit(fail?1:0);
