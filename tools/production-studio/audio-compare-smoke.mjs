import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const host='http://127.0.0.1:8767';
const server=spawn('python3',['-m','http.server','8767','--bind','127.0.0.1'],{stdio:'ignore'});
let browser;
function fixture(amplitude){
 const frames=48000, data=Buffer.alloc(44+frames*2);
 data.write('RIFF');data.writeUInt32LE(data.length-8,4);data.write('WAVEfmt ',8);
 data.writeUInt32LE(16,16);data.writeUInt16LE(1,20);data.writeUInt16LE(1,22);
 data.writeUInt32LE(48000,24);data.writeUInt32LE(96000,28);data.writeUInt16LE(2,32);data.writeUInt16LE(16,34);
 data.write('data',36);data.writeUInt32LE(frames*2,40);
 let energy=0,peak=0;for(let i=0;i<frames;i++){const x=Math.round(amplitude*Math.sin(2*Math.PI*220*i/48000));data.writeInt16LE(x,44+i*2);energy+=x*x;peak=Math.max(peak,Math.abs(x));}
 const db=x=>20*Math.log10(x/32768);
 return {data,sha:createHash('sha256').update(data).digest('hex'),m:{channels:1,sample_rate:48000,frames,sample_peak_dbfs:db(peak),rms_dbfs:db(Math.sqrt(energy/frames)),full_scale_samples:0}};
}
try{
 for(let i=0;i<40;i++){try{if((await fetch(host)).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
 browser=await chromium.launch({args:['--autoplay-policy=no-user-gesture-required']});
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
 const errors=[],writes=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',req=>{if(!['GET','HEAD'].includes(req.method()))writes.push(req.url());});
 await page.route('https://**/*',route=>route.fulfill({status:503,body:'fixture offline'}));
 await page.goto(host+'/index.html');
 const a=fixture(16000),b=fixture(8000);
 const receipt={schema:'two.audio.candidate.v1',candidate_only:true,preset:'warm',backend:'synthetic fixture',source_sha256:a.sha,output_sha256:b.sha,before:a.m,after:b.m};
 const put=(id,name,buffer,mimeType)=>page.locator('#'+id).setInputFiles({name,mimeType,buffer});
 const rec=r=>put('audio-receipt','receipt.json',Buffer.from(JSON.stringify(r)),'application/json');
 await put('audio-source','source.wav',a.data,'audio/wav');await put('audio-candidate','candidate.wav',b.data,'audio/wav');await rec(receipt);
 await page.locator('#audio-check').click();await page.waitForFunction(()=>document.querySelector('#audio-status').textContent.includes('照合 PASS'));
 await page.waitForFunction(()=>['audio-a','audio-b'].every(id=>document.getElementById(id).readyState>=1));
 assert.match(await page.locator('#audio-b-metrics').innerText(),/1\.000 秒/);
 await page.locator('#audio-a').evaluate(p=>{p.currentTime=.2;return p.play()});
 await page.locator('#audio-switch').click();await page.waitForFunction(()=>document.getElementById('audio-a').paused&&!document.getElementById('audio-b').paused);
 assert.ok(await page.locator('#audio-b').evaluate(p=>p.currentTime>=.15));
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await mkdir('qa-output',{recursive:true});await page.locator('#audio-review').screenshot({path:'qa-output/audio-comparison-mobile.png'});
 await rec({...receipt,output_sha256:'0'.repeat(64)});await page.locator('#audio-check').click();await page.waitForFunction(()=>document.querySelector('#audio-status').textContent.includes('SHA-256不一致'));assert.equal(await page.locator('#audio-results').isVisible(),false);
 await rec({...receipt,after:{...b.m,rms_dbfs:0}});await page.locator('#audio-check').click();await page.waitForFunction(()=>document.querySelector('#audio-status').textContent.includes('測定記録不一致'));assert.equal(await page.locator('#audio-results').isVisible(),false);
 await rec(receipt);await page.locator('#audio-check').click();await page.waitForFunction(()=>document.querySelector('#audio-status').textContent.includes('照合 PASS'));await page.locator('#audio-clear').click();
 assert.equal(await page.locator('#audio-results').isVisible(),false);assert.equal(await page.locator('#audio-source').evaluate(x=>x.files.length),0);assert.equal(await page.locator('#audio-a').getAttribute('src'),null);
 assert.deepEqual(writes,[]);assert.deepEqual(errors,[]);
 console.log('PASS: PCM and exact hashes, native playback, same-position A/B, mismatch rejection, clear, mobile, no network writes');
}finally{await browser?.close();server.kill();}
