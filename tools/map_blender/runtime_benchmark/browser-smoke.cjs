#!/usr/bin/env node
// Isolated browser smoke test: no production assets or application state changes.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { createServer } = require('node:http');
const root = path.resolve(__dirname, '../../..');
const glb = process.env.LIND_GLB || '/tmp/lind-glb-benchmark/technical-scene.glb';
const out = process.env.LIND_QA_OUT || '/tmp/lind-glb-benchmark/browser-smoke.json';
const types = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.glb':'model/gltf-binary' };
const server = createServer((req,res)=>{
  const p = path.resolve(root, '.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!p.startsWith(root+path.sep)){res.writeHead(403).end();return}
  fs.readFile(p,(e,data)=>{if(e){res.writeHead(404).end('not found');return}res.writeHead(200,{'Content-Type':types[path.extname(p)]||'application/octet-stream'}).end(data)});
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl']});
 const results={role:'TECHNICAL_BROWSER_SMOKE_ONLY',browser:'chromium-headless',android:'NOT_RUN',art:'NOT_RUN',engines:{}};
 try{
  for(const engine of ['three','babylon']){
   const page=await browser.newPage({viewport:{width:960,height:720},acceptDownloads:false});
   const errors=[];page.on('pageerror',e=>errors.push(String(e)));
   await page.goto('http://127.0.0.1:'+server.address().port+'/tools/map_blender/runtime_benchmark/same-glb-compare.html',{waitUntil:'domcontentloaded'});
   await page.locator('#file').setInputFiles(glb);
   await page.locator('#engine').selectOption(engine);
   await page.locator('#run').click();
   try{await page.waitForFunction(()=>['RUNNING','COMPLETED','FAIL_LOAD','FAIL_RENDER'].includes(JSON.parse(document.querySelector('#report').textContent).status),null,{timeout:120000});}
   catch(e){errors.push('Timed out awaiting runtime: '+String(e))}
   const result=await page.locator('#report').textContent().then(JSON.parse);
   results.engines[engine]={status:result.status,sha256:result.sha256,asset:result.asset,loadMs:result.loadMs,error:result.error,pageErrors:errors};
   if(result.status==='RUNNING'){await page.locator('#stop').click()}
   await page.close();
  }
  const entries=Object.values(results.engines);
  results.pass=entries.every(e=>e.status==='RUNNING'||e.status==='COMPLETED')&&entries[0].sha256===entries[1].sha256&&entries.every(e=>e.asset?.meshes>0&&e.pageErrors.length===0);
 }finally{
  await browser.close();server.close();
  fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify(results,null,2));
 }
 if(!results.pass)process.exitCode=1;
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
