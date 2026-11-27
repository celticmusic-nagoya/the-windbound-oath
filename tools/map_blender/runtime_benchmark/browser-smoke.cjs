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
const transmissionProbe = process.env.LIND_TRANSMISSION_PROBE === '1';
const expectedSha = process.env.LIND_EXPECTED_SHA || createHash('sha256').update(fs.readFileSync(glb)).digest('hex');
assert.match(expectedSha,/^[a-f0-9]{64}$/);
assert.equal(createHash('sha256').update(fs.readFileSync(glb)).digest('hex'),expectedSha,'input SHA mismatch');
const expectedTriangles=process.env.LIND_EXPECTED_TRIANGLES===undefined?null:Number(process.env.LIND_EXPECTED_TRIANGLES);
const expectedMeshes=process.env.LIND_EXPECTED_MESHES===undefined?null:Number(process.env.LIND_EXPECTED_MESHES);
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
  assert.equal(observed.report.asset.triangles,1,'non-indexed triangle count');
  assert.equal(observed.report.asset.meshes,1);
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
// Exact, one-byte material diagnostic. Never modify the original file or export the variant.
async function probeTransmission(browser,url,results){
 const source=fs.readFileSync(glb);
 assert.equal(expectedSha,'b32fbe55777dcdc43cde9e8ad337aac15cc447de568aac8fdd7f9f5fc473f57d');
 assert.equal(source.length,50732020);
 assert.equal(source.readUInt32LE(0),0x46546c67);assert.equal(source.readUInt32LE(4),2);
 assert.equal(source.readUInt32LE(8),source.length);assert.equal(source.readUInt32LE(16),0x4e4f534a);
 const jsonEnd=20+source.readUInt32LE(12),doc=JSON.parse(source.subarray(20,jsonEnd).toString('utf8'));
 const key='KHR_materials_transmission',material=doc.materials[5];
 assert.equal(material.name,'MAT_GLASS_CROWN_A');
 assert.equal(material.extensions[key].transmissionFactor,1);
 assert.deepEqual(doc.materials.flatMap((m,i)=>m.extensions?.[key]?[i]:[]),[5]);
 const needle=Buffer.from('"transmissionFactor":1'),offset=source.indexOf(needle,20);
 assert.ok(offset>=20&&offset+needle.length<=jsonEnd);
 assert.ok(source.indexOf(needle,offset+needle.length)===-1||source.indexOf(needle,offset+needle.length)>=jsonEnd);
 const changed=Buffer.from(source),byteOffset=offset+needle.length-1;
 changed[byteOffset]=48;
 const changedDoc=JSON.parse(changed.subarray(20,jsonEnd).toString('utf8'));
 const expectedDoc=structuredClone(doc);expectedDoc.materials[5].extensions[key].transmissionFactor=0;
 assert.deepEqual(changedDoc,expectedDoc);
 assert.ok(source.subarray(0,byteOffset).equals(changed.subarray(0,byteOffset)));
 assert.ok(source.subarray(byteOffset+1).equals(changed.subarray(byteOffset+1)));
 const changedSha=createHash('sha256').update(changed).digest('hex');
 results.role='TRANSMISSION_SINGLE_BYTE_DRAW_CALL_DIAGNOSTIC';
 results.sourceSha=expectedSha;results.variantSha=changedSha;results.changedByteOffset=byteOffset;
 results.material={index:5,name:material.name,from:1,to:0};results.probes=[];
 for(const variant of ['original','disabled','disabled','original']){
  const page=await browser.newPage({viewport:{width:960,height:720},acceptDownloads:false});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  const row={variant,pass:false};results.probes.push(row);
  try{
   await page.goto(url,{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>typeof document.querySelector('#run').onclick==='function');
   await page.locator('#file').setInputFiles({name:variant+'.glb',mimeType:'model/gltf-binary',buffer:variant==='original'?source:changed});
   await page.locator('#engine').selectOption('three');
   await page.locator('#run').click();
   await page.waitForFunction(()=>['RUNNING','FAIL_LOAD','FAIL_RENDER'].includes(JSON.parse(document.querySelector('#report').textContent).status),{},{timeout:90000});
   row.report=JSON.parse(await page.locator('#report').textContent());
   assert.equal(row.report.status,'RUNNING');
   assert.equal(row.report.sha256,variant==='original'?expectedSha:changedSha);
   assert.equal(row.report.asset.meshes,389);
   assert.equal(row.report.asset.triangles,803031);
   assert.equal(row.report.asset.materials,83);
   assert.ok(Number.isInteger(row.report.renderInfo?.drawCalls)&&row.report.renderInfo.drawCalls>0);
   assert.ok(Number.isInteger(row.report.renderInfo?.triangles)&&row.report.renderInfo.triangles>0);
   assert.deepEqual(errors,[]);
   await page.locator('#stop').click();
   row.pass=true;
  }catch(e){row.error=String(e)}finally{row.pageErrors=errors;await page.close()}
 }
 const rows=results.probes,first=rows[0].report;
 results.sameConditions=rows.every(x=>x.pass&&JSON.stringify(x.report.camera)===JSON.stringify(first.camera)&&JSON.stringify(x.report.environment)===JSON.stringify(first.environment)&&JSON.stringify(x.report.asset)===JSON.stringify(first.asset)&&x.report.engineVersion===first.engineVersion);
 results.repeatable=rows.every(x=>x.pass)&&JSON.stringify(rows[0].report.renderInfo)===JSON.stringify(rows[3].report.renderInfo)&&JSON.stringify(rows[1].report.renderInfo)===JSON.stringify(rows[2].report.renderInfo);
 results.pass=results.sameConditions&&results.repeatable;
 if(results.pass){
  results.drawCalls={original:rows[0].report.renderInfo.drawCalls,disabled:rows[1].report.renderInfo.drawCalls};
  results.submittedTriangles={original:rows[0].report.renderInfo.triangles,disabled:rows[1].report.renderInfo.triangles};
  results.interpretation='Causal diagnostic only: glass appearance intentionally changed; no asset adoption, FPS or Android claim.';
 }
 assert.equal(createHash('sha256').update(fs.readFileSync(glb)).digest('hex'),expectedSha,'source file must remain unchanged');
}
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl']});
 const results={role:fullMeasure?'TECHNICAL_HEADLESS_30S_BENCHMARK':'TECHNICAL_BROWSER_SMOKE_ONLY',browser:'chromium-headless',android:'NOT_RUN',art:'NOT_RUN',engines:{},repetitions,rounds:[]};
 try{
  const url='http://127.0.0.1:'+server.address().port+'/tools/map_blender/runtime_benchmark/same-glb-compare.html';
  results.expectedSha=expectedSha;
  if(transmissionProbe){await probeTransmission(browser,url,results);}
  else{
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
   await page.waitForFunction(()=>typeof document.querySelector('#run').onclick==='function');
   await page.locator('#file').setInputFiles(glb);
   await page.locator('#engine').selectOption(engine);
   await page.locator('#run').click();
   try{await page.waitForFunction((measure)=>(measure ? ['COMPLETED','FAIL_LOAD','FAIL_RENDER'] : ['RUNNING','COMPLETED','FAIL_LOAD','FAIL_RENDER']).includes(JSON.parse(document.querySelector('#report').textContent).status),fullMeasure,{timeout:fullMeasure?150000:120000});}
   catch(e){errors.push('Timed out awaiting runtime: '+String(e))}
   const result=await page.locator('#report').textContent().then(JSON.parse);
   roundResult.engines[engine]={...result,pageErrors:errors};
   if(result.status==='RUNNING'){await page.locator('#stop').click()}
   await page.close();
   }
  }
  for(const engine of ['three','babylon'])results.engines[engine]=results.rounds.map(r=>r.engines[engine]);
  const entries=results.rounds.flatMap(r=>Object.values(r.engines));
  const near=(a,b)=>Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=1e-5*Math.max(1,Math.abs(a),Math.abs(b));
  const vectorNear=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===3&&b.length===3&&a.every((x,i)=>near(x,b[i]));
  const matchingCamera=(a,b)=>!!a&&!!b&&a.rightHanded&&b.rightHanded&&['min','max','eye','target'].every(k=>vectorNear(a[k],b[k]))&&['near','far','verticalFovDegrees'].every(k=>near(a[k],b[k]));
  const validTiming=e=>Array.isArray(e.frameIntervalsMs)&&e.frames===e.frameIntervalsMs.length&&e.frames>0&&e.frameIntervalsMs.every(x=>Number.isFinite(x)&&x>0)&&near(e.elapsedMs,e.frameIntervalsMs.reduce((a,b)=>a+b,0))&&e.elapsedMs>=30000&&near(e.meanFrameMs,e.elapsedMs/e.frames)&&Number.isFinite(e.p95FrameMs);
  results.conditions=results.rounds.map(r=>{const a=r.engines.three,b=r.engines.babylon;return {round:r.round,cameraMatch:matchingCamera(a.camera,b.camera),drawingBufferMatch:!!a.environment&&!!b.environment&&a.environment.width===b.environment.width&&a.environment.height===b.environment.height&&a.environment.width===a.dimensions.width&&a.environment.height===a.dimensions.height&&b.environment.width===b.dimensions.width&&b.environment.height===b.dimensions.height,rendererMatch:!!a.environment&&!!b.environment&&a.environment.renderer===b.environment.renderer,trianglesMatch:a.asset?.triangles===b.asset?.triangles,meshCountMatch:a.asset?.meshes===b.asset?.meshes};});
  results.pass=entries.every(e=>fullMeasure?(e.status==='COMPLETED'&&validTiming(e)):(e.status==='RUNNING'||e.status==='COMPLETED'))&&entries.every(e=>e.sha256===expectedSha)&&entries.every(e=>e.asset?.meshes>0&&e.asset.triangles>0&&e.pageErrors.length===0&&(expectedTriangles===null||e.asset.triangles===expectedTriangles)&&(expectedMeshes===null||e.asset.meshes===expectedMeshes))&&results.conditions.every(c=>c.cameraMatch&&c.drawingBufferMatch&&c.rendererMatch&&c.trianglesMatch&&c.meshCountMatch)&&(!raceTest||results.raceCases.length===4&&results.raceCases.every(x=>x.pass));
  }
 }finally{
  await browser.close();server.close();
  fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify(results,null,2));
 }
 if(!results.pass)process.exitCode=1;
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
