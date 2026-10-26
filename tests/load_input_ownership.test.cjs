// Real LoadingInput + LoadCoordinator, actual deferred tasks and cancellation tokens.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),assert=require('node:assert/strict');
const nodes=new Map(),listeners=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{hidden:true,disabled:false,textContent:'',addEventListener(){}});return nodes.get(id)};
const c={console,Promise,document:{getElementById:node,addEventListener(){}},CustomEvent:class{constructor(type){this.type=type}},addEventListener(type,f){listeners.set(type,f)},dispatchEvent(){}};c.window=c;vm.createContext(c);
for(const f of ['js/loading-input.js','js/load-coordinator.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,'..',f),'utf8'),c,{filename:f});
(async()=>{
 assert.equal(await c.LoadCoordinator.boot(async()=>{}),true);assert.equal(c.LoadingInput.busy,false);
 let release;const p=c.LoadCoordinator.run(()=>new Promise(r=>release=r),()=>{});assert.equal(c.LoadCoordinator.phase,'LOADING');assert.equal(c.LoadingInput.busy,true,'LOAD owns input before any map fetch/first await');
 let stopped=false;assert.equal(c.LoadingInput.handle({type:'keydown',code:'Enter',key:'Enter',target:{closest:()=>null},preventDefault(){stopped=true},stopImmediatePropagation(){}}),true);assert.equal(stopped,true);
 c.LoadingInput.lock('map:test');c.LoadingInput.release('map:test');assert.equal(c.LoadingInput.busy,true,'nested map completion cannot release LOAD owner');assert.equal(await c.LoadCoordinator.run(async()=>{}),false);
 release();assert.equal(await p,true);assert.equal(c.LoadingInput.busy,false);console.log('PASS LOAD input ownership, nested completion, duplicate LOAD and release');
 let count=0;const retry=()=>c.LoadCoordinator.run(async()=>{if(++count===1)throw Error('offline')},retry);assert.equal(await retry(),false);assert.equal(c.LoadingInput.busy,true);assert.equal(c.LoadCoordinator.canSave,false);assert.equal(await c.LoadCoordinator.retry(),true);assert.equal(c.LoadingInput.busy,false);console.log('PASS failed LOAD remains protected; explicit retry recovers');
 let oldRelease,newRelease;const old=c.LoadCoordinator.run(()=>new Promise(r=>oldRelease=r));const fresh=c.LoadCoordinator.boot(()=>new Promise(r=>newRelease=r));oldRelease();assert.equal(await old,false);assert.equal(c.LoadingInput.busy,true,'stale completion cannot unlock newer boot');newRelease();assert.equal(await fresh,true);assert.equal(c.LoadingInput.busy,false);console.log('PASS stale LOAD cannot release new boot owner');
})().catch(e=>{console.error('FAIL',e.stack);process.exitCode=1});
