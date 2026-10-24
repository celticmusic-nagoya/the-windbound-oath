// Run: node tests/issue54_coordinator.test.cjs (no server or dependencies).
const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict'),path=require('node:path');
const elements=new Map();const element=id=>{if(!elements.has(id))elements.set(id,{hidden:true,disabled:false,textContent:'',addEventListener(){}});return elements.get(id)};
const ctx={document:{getElementById:element,addEventListener(){}},console,Promise,Error,Object};ctx.window=ctx;
vm.createContext(ctx);vm.runInContext(fs.readFileSync(path.join(__dirname,'../js/load-coordinator.js'),'utf8'),ctx);
const c=ctx.LoadCoordinator;
(async()=>{
 assert.equal(c.phase,'BOOTING');assert.equal(c.mayLoad(),false);assert.equal(c.canSave,false);
 assert.equal(await c.run(async()=>{}),false);
 assert.equal(await c.boot(async()=>{}),true);assert.equal(c.phase,'READY');assert.equal(c.canSave,true);
 let finish;const p=c.run(()=>new Promise(r=>finish=r),()=>{});assert.equal(c.phase,'LOADING');assert.equal(c.canSave,false);assert.equal(await c.run(async()=>{}),false);finish();assert.equal(await p,true);
 let tries=0;const retry=()=>c.run(async()=>{if(++tries===1)throw Error('injected failure')},retry);
 assert.equal(await retry(),false);assert.equal(c.phase,'FAILED');assert.equal(c.canSave,false);assert.equal(elements.get('retryLoad').hidden,false);
 assert.equal(await c.retry(),true);assert.equal(tries,2);assert.equal(c.phase,'READY');
 let oldDone;const old=c.run(()=>new Promise(r=>oldDone=r),()=>{});await c.boot(async()=>{});oldDone();assert.equal(await old,false);assert.equal(c.phase,'READY');
 console.log('PASS: boot guard, load exclusion, failure latch, explicit retry, stale generation');
})().catch(e=>{console.error(e);process.exitCode=1});
