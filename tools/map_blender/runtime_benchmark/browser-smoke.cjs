#!/usr/bin/env node
// Isolated browser smoke test: no production assets or application state changes.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const path = require('node:path');
const { createServer } = require('node:http');
const root = path.resolve(__dirname, '../../..');
const glb = process.env.LIND_GLB || '/tmp/lind-glb-benchmark/technical-scene.glb';
const out = process.env.LIND_QA_OUT || '/tmp/lind-glb-benchmark/browser-smoke.json';
const fullMeasure = process.env.LIND_FULL_MEASURE === '1';
const raceTest = process.env.LIND_RACE_TEST === '1';
const expectedSha = process.env.LIND_EXPECTED_SHA || createHash('sha256').update(fs.readFileSync(glb)).digest('hex');
assert.match(expectedSha,/^[a-f0-9]{64}$/);
assert.equal(createHash('sha256').update(fs.readFileSync(glb)).digest('hex'),expectedSha,'input SHA mismatch');
const repetitions = fullMeasure ? Number(process.env.LIND_REPETITIONS || 1) : 1;
if(!Number.isInteger(repetitions)||repetitions<1||repetitions>10)throw Error('Invalid repetitions');
const types = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.glb':'model/gltf-binary' };
const server = createServer((req,res)=>{
  const p = path.resolve(root, '.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!p.startsWith(root+path.sep)){res.writeHead(403).end();return}
  fs.readFile(p,(e,data)=>{if(e){res.writeHead(404).end('not found');return}res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'}).end(path.extname(p)==='.html'?Buffer.from(data.toString('utf8').replaceAll('https://cdn.jsdelivr.net/npm/three@0.170.0/','/node_modules/three/').replaceAll('https://cdn.jsdelivr.net/npm/babylonjs@7.40.3/','/node_modules/babylonjs/').replaceAll('https://cdn.jsdelivr.net/npm/babylonjs-loaders@7.40.3/','/node_modules/babylonjs-loaders/')):data)});
});
// A test gate pauses the first actual GLTF loader result, not a fake renderer.
async function raceProbe(browser,url,first,second){
 const page=await browser.newPage({viewport:{width:640,height:480},acceptDownloads:false});
 const errors=[],record={first,second,pass:false};
 page.on('pageerror',e=>errors.push(String(e)));
 const fixture=fs.readFileSync(glb),next=Buffer.from(fixture);
 // Only the generated one-triangle smoke fixture is eligible for this mutation.
 assert.ok(fixture.length<4096);
 next.writeFloatLE(.25,next.length-12);
 const nextSha=createHash('sha256').update(next).digest('hex');
 assert.notEqual(nextSha,expectedSha);
 try{
  await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>typeof document.querySelector('#run').onclick==='function');
  await page.evaluate(async first=>{
   let unlock;
   const gate=new Promise(r=>{unlock=r});
   const state=window.__raceGate={entered:false,released:false,release:unlock,oldCanvas:null};
   if(first==='three'){
    const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');
    const original=GLTFLoader.prototype.parse;
    let hold=true;
    GLTFLoader.prototype.parse=function(data,path,onLoad,onError){
     if(!hold)return original.call(this,data,path,onLoad,onError);
     hold=false;
     return original.call(this,data,path,gltf=>{
      state.oldCanvas=document.querySelector('#view');state.entered=true;
      gate.then(()=>{onLoad(gltf);state.released=true});
     },onError);
    };
   }else{
    const B=window.BABYLON,original=B.SceneLoader.ImportMeshAsync;
    let hold=true;
    B.SceneLoader.ImportMeshAsync=async function(...args){
     const first=hold;hold=false;
     const loaded=await original.apply(this,args);
     if(first){state.oldCanvas=document.querySelector('#view');state.entered=true;await gate;state.released=true}
     return loaded;
    };
   }
  },first);
  await page.locator('#file').setInputFiles({name:'old.glb',mimeType:'model/gltf-binary',buffer:fixture});
  await page.locator('#engine').selectOption(first);
  await page.locator('#run').click();
  await page.waitForFunction(()=>window.__raceGate.entered,{},{timeout:30000});
  await page.locator('#stop').click();
  await page.locator('#file').setInputFiles({name:'new.glb',mimeType:'model/gltf-binary',buffer:next});
  await page.locator('#engine').selectOption(second);
  await page.locator('#run').click();
  await page.waitForFunction(()=>JSON.parse(document.querySelector('#report').textContent).status==='RUNNING',{},{timeout:30000});
  await page.evaluate(()=>window.__raceGate.release());
  await page.waitForFunction(()=>window.__raceGate.released,{},{timeout:30000});
  await page.evaluate(()=>new Promise(resolve=>{let n=0;const frame=()=>{if(++n>=8)resolve();else requestAnimationFrame(frame)};requestAnimationFrame(frame)}));
  const observed=await page.evaluate(()=>({report:JSON.parse(document.querySelector('#report').textContent),distinctCanvas:window.__raceGate.oldCanvas!==document.querySelector('#view'),oldCanvasDetached:!window.__raceGate.oldCanvas.isConnected,runDisabled:document.querySelector('#run').disabled}));
  record.observed=observed;
  assert.equal(observed.report.status,'RUNNING','stale load destroyed current rendering');
  assert.equal(observed.report.sha256,nextSha);
  assert.equal(observed.report.engine,second);
  assert.equal(observed.report.filename,'new.glb');
  assert.equal(observed.distinctCanvas,true);
  assert.equal(observed.oldCanvasDetached,true);
  assert.equal(observed.runDisabled,true);
  assert.deepEqual(errors,[]);
  await page.locator('#stop').click();
  assert.equal(JSON.parse(await page.locator('#report').textContent()).status,'STOPPED_EARLY');
  record.pass=true;
 }catch(e){record.error=String(e)}finally{
  record.pageErrors=errors;
  await page.evaluate(()=>window.__raceGate?.release()).catch(()=>{});
  await page.close();
 }
 return record;
}
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl']});
 const results={role:fullMeasure?'TECHNICAL_HEADLESS_30S_BENCHMARK':'TECHNICAL_BROWSER_SMOKE_ONLY',browser:'chromium-headless',android:'NOT_RUN',art:'NOT_RUN',engines:{},repetitions,rounds:[]};
 try{
  const url='http://127.0.0.1:'+server.address().port+'/tools/map_blender/runtime_benchmark/same-glb-compare.html';
  results.expectedSha=expectedSha;
  if(raceTest){
   results.raceCases=[];
   for(const first of ['three','babylon'])for(const second of ['three','babylon'])results.raceCases.push(await raceProbe(browser,url,first,second));
  }
  for(let round=0;round<repetitions;round++){
   const order=round%2?['babylon','three']:['three','babylon'];
   const roundResult={round:round+1,order,engines:{}};
   results.rounds.push(roundResult);
   for(const engine of order){
   const page=await browser.newPage({viewport:{width:960,height:720},acceptDownloads:false});
   const errors=[];page.on('pageerror',e=>errors.push(String(e)));
   await page.goto('http://127.0.0.1:'+server.address().port+'/tools/map_blender/runtime_benchmark/same-glb-compare.html',{waitUntil:'domcontentloaded'});
   await page.locator('#file').setInputFiles(glb);
   await page.locator('#engine').selectOption(engine);
   await page.locator('#run').click();
   try{await page.waitForFunction((measure)=>(measure ? ['COMPLETED','FAIL_LOAD','FAIL_RENDER'] : ['RUNNING','COMPLETED','FAIL_LOAD','FAIL_RENDER']).includes(JSON.parse(document.querySelector('#report').textContent).status),fullMeasure,{timeout:fullMeasure?150000:120000});}
   catch(e){errors.push('Timed out awaiting runtime: '+String(e))}
   const result=await page.locator('#report').textContent().then(JSON.parse);
   roundResult.engines[engine]={status:result.status,sha256:result.sha256,asset:result.asset,loadMs:result.loadMs,frames:result.frames,meanFrameMs:result.meanFrameMs,p95FrameMs:result.p95FrameMs,elapsedMs:result.elapsedMs,renderInfo:result.renderInfo,error:result.error,pageErrors:errors};
   if(result.status==='RUNNING'){await page.locator('#stop').click()}
   await page.close();
   }
  }
  for(const engine of ['three','babylon'])results.engines[engine]=results.rounds.map(r=>r.engines[engine]);
  const entries=results.rounds.flatMap(r=>Object.values(r.engines));
  results.pass=entries.every(e=>fullMeasure?(e.status==='COMPLETED'&&e.frames>0&&Number.isFinite(e.meanFrameMs)&&Number.isFinite(e.p95FrameMs)):(e.status==='RUNNING'||e.status==='COMPLETED'))&&entries.every(e=>e.sha256===expectedSha)&&entries.every(e=>e.asset?.meshes>0&&e.pageErrors.length===0)&&(!raceTest||results.raceCases.length===4&&results.raceCases.every(x=>x.pass));
 }finally{
  await browser.close();server.close();
  fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify(results,null,2));
 }
 if(!results.pass)process.exitCode=1;
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
