const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs');
const out=process.env.MOTION_QA_OUT||__dirname;
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const rows=[];try{
for(const [w,h] of [[1280,720],[1920,1080],[844,390],[390,844]]){
const p=await b.newPage({viewport:{width:w,height:h}}),errors=[],bad=[],requests=[];
p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('response',r=>{if(r.status()>=400)bad.push(r.url())});p.on('request',r=>{if(r.url().includes('/forest_bat/idle/'))requests.push(r.url())});
await p.goto('http://127.0.0.1:8015/dev/battle-motion-preview.html');await p.evaluate(()=>Promise.all([BattleIdleMotion.ready('#bat0 img'),BattleIdleMotion.ready('#bAidan2 img')]));
await p.clock.install();await p.clock.pauseAt(new Date(Date.now()+1000));
await p.clock.runFor(2500);assert.equal(await p.evaluate(()=>BattleMotion.prepareAttack([]).presentation),'legacy');
const initial=await p.evaluate(()=>({nodes:document.querySelectorAll('*').length,rect:document.querySelector('#bat0').getBoundingClientRect().toJSON()}));
await p.evaluate(()=>{window.trace=[];let last=-1;function sample(){const f=Number(document.querySelector('#bat0 canvas').dataset.frame);if(f!==last){trace.push({frame:f,time:performance.now()});last=f;}requestAnimationFrame(sample);}requestAnimationFrame(sample);});
await p.clock.runFor(w===1920?60000:6000);
let stats=await p.evaluate(()=>({trace,now:performance.now(),status:BattleIdleMotion.status,nodes:document.querySelectorAll('*').length,rect:document.querySelector('#bat0').getBoundingClientRect().toJSON()}));assert.equal(stats.nodes,initial.nodes);assert.deepEqual(stats.rect,initial.rect);assert.ok([0,1,2,3].every(f=>stats.trace.some(t=>t.frame===f)));assert.equal(stats.status.cacheCount,2);
const cyc=stats.trace.filter(t=>t.frame===0).map(t=>t.time),intervals=cyc.slice(1).map((t,i)=>t-cyc[i]);assert.ok(intervals.every(t=>t>=780&&t<=1400));
await p.screenshot({path:out+'/bat-'+w+'.png'});
await p.selectOption('#count','3');await p.evaluate(()=>Promise.all([0,1,2].map(i=>BattleIdleMotion.ready('#bat'+i+' img'))));await p.clock.runFor(2500);
const phases=await p.evaluate(()=>BattleIdleMotion.status.actors.filter(r=>r.actor==='forest_bat'));assert.equal(phases.length,3);assert.equal(await p.locator('.battle-idle-canvas').count(),4);assert.equal(new Set(phases.map(r=>r.hoverPeriod)).size,3);assert.equal(new Set(phases.map(r=>r.hoverAmplitude)).size,3);
const before=await p.locator('*').count();if(w===1920){await p.clock.runFor(300000);assert.equal(await p.locator('*').count(),before);}
for(let i=0;i<100;i++){await p.evaluate(()=>{BattleMotion.onState('#bat0 img','forest_bat','attack');BattleMotion.onState('#bat0 img','forest_bat','idle');});}
await p.evaluate(()=>BattleMotion.onState('#bat0 img','forest_bat','ko'));await p.clock.runFor(5000);assert.equal(await p.locator('#bat0 canvas').isVisible(),false);await p.evaluate(()=>BattleMotion.onState('#bat0 img','forest_bat','victory'));await p.clock.runFor(2000);assert.equal(await p.locator('#bat0 canvas').isVisible(),false);
await p.emulateMedia({reducedMotion:'reduce'});await p.clock.runFor(100);assert.equal(await p.evaluate(()=>BattleIdleMotion.status.scheduled),false);assert.ok(await p.evaluate(()=>BattleIdleMotion.status.actors.filter(r=>r.showing).every(r=>r.frame===0)));
await p.emulateMedia({reducedMotion:'no-preference'});await p.selectOption('#count','1');await p.selectOption('#count','3');await p.selectOption('#count','1');await p.clock.runFor(100);assert.equal(await p.locator('.battle-idle-canvas').count(),2);assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);assert.equal(new Set(requests).size,4);
rows.push({viewport:[w,h],intervals,phaseParameters:phases,trace:stats.trace,stress5minutes:w===1920,stress100Transitions:true,domGrowth:0,rootDrift:0,image404:bad.length,exceptions:errors.length});await p.close();console.log(w+'x'+h+' Bat flight, 1/3 actors, interruptions, reduced motion PASS');
}
fs.writeFileSync(out+'/bat-qa.json',JSON.stringify(rows,null,2));}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
