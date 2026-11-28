import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(new URL('../production-studio/package.json',import.meta.url));
const {chromium}=require('playwright');
const root=fileURLToPath(new URL('../production-studio/',import.meta.url));
const packet=resolve(process.argv[2]),out=resolve(process.argv[3]);
const host='http://127.0.0.1:8768';
const server=spawn('python3',['-m','http.server','8768','--bind','127.0.0.1'],{cwd:root,stdio:'ignore'});
let browser;
try{
 for(let i=0;i<40;i++){try{if((await fetch(host)).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
 browser=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
 const errors=[],writes=[],checks={};
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!['GET','HEAD'].includes(r.method()))writes.push(r.url());});
 await page.route('https://**/*',r=>r.fulfill({status:503,body:'fixture offline'}));
 await page.goto(host+'/index.html');
 await mkdir(out,{recursive:true});
 for(const [name,source] of [['clean','synthetic-stereo.wav'],['warm','synthetic-stereo.wav'],['warm-repeat','synthetic-stereo.wav'],['mono','synthetic-mono.wav']]){
   await page.locator('#audio-source').setInputFiles(join(packet,source));
   await page.locator('#audio-candidate').setInputFiles(join(packet,name,'candidate.wav'));
   await page.locator('#audio-receipt').setInputFiles(join(packet,name,'receipt.json'));
   await page.locator('#audio-loudness').setInputFiles(join(out,'loudness.json'));
   await page.locator('#audio-check').click();
   await page.waitForFunction(()=>document.querySelector('#audio-status').textContent.includes('照合 PASS'));
   await page.waitForFunction(()=>document.querySelector('#audio-loudness-status').textContent.includes('紐付け一致'));
   const inspection=JSON.parse(await readFile(join(out,'loudness.json'),'utf8')).pairs[name];
   assert.ok((await page.locator('#audio-loudness-b').innerText()).includes(inspection.after.integrated_lufs.toFixed(2)));
   await page.locator('#audio-match-level').check();
   await page.waitForFunction(()=>document.querySelector('#audio-gain-status').textContent.includes('試聴補正'));
   await page.waitForFunction(()=>['audio-a','audio-b'].every(id=>document.getElementById(id).readyState>=1));
   assert.match(await page.locator('#audio-b-metrics').innerText(),/2\.000 秒/);
   await page.locator('#audio-a').evaluate(a=>{a.currentTime=.25;return a.play()});
   await page.locator('#audio-switch').click();
   await page.waitForFunction(()=>document.getElementById('audio-a').paused&&!document.getElementById('audio-b').paused);
   assert.ok(await page.locator('#audio-b').evaluate(a=>a.currentTime>=.2));
   const receipt=JSON.parse(await readFile(join(packet,name,'receipt.json'),'utf8'));
   assert.ok((await page.locator('#audio-b-metrics').innerText()).includes(receipt.after.rms_dbfs.toFixed(2)));
   assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   checks[name]={sha_pcm:'PASS',loudness_binding:'PASS',level_match:'PASS',playback:'PASS',switch:'PASS',source_sha256:receipt.source_sha256,output_sha256:receipt.output_sha256};
   if(name==='warm')await page.locator('#audio-review').screenshot({path:join(out,'actual-warm-mobile.png')});
   await page.locator('#audio-clear').click();
   assert.equal(await page.locator('#audio-results').isVisible(),false);
 }
 assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);
 await writeFile(join(out,'browser-packet-qa.json'),JSON.stringify({checks,network_writes:0,errors,scope:'synthetic actual FFmpeg outputs; Chromium, not Android or listening QA'},null,2)+'\n',{flag:'wx'});
 console.log('PASS: actual FFmpeg packet 4/4 browser SHA/PCM/playback/A-B, no writes');
}finally{await browser?.close();server.kill();}
