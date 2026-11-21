import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdir} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
await mkdir('qa-output',{recursive:true});
const server=spawn('python3',['-m','http.server','8765','--bind','127.0.0.1'],{stdio:'ignore'});
let browser;
try {
 for(let i=0;i<40;i++){try{if((await fetch('http://127.0.0.1:8765')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
 browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://api.github.com/**',route=>route.fulfill({json:route.request().url().includes('/pulls/')?{state:'open',draft:true,head:{sha:'a'.repeat(40)},updated_at:'2026-11-22'}:{workflow_runs:[]}}));
 await page.goto('http://127.0.0.1:8765/index.html');
 await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('取得完了'));
 assert.equal(await page.locator('#projects article').count(),3);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 const fixture=Buffer.from('diagnostic only');
 await page.locator('#artifact-zip').setInputFiles({name:'diagnostic.zip',mimeType:'application/zip',buffer:fixture});
 await page.locator('#artifact-digest').fill(createHash('sha256').update(fixture).digest('hex'));
 await page.locator('#verify-artifact').click();
 await page.waitForFunction(()=>document.querySelector('#verify-result').textContent.startsWith('PASS:'));
 await page.locator('#artifact-digest').fill('0'.repeat(64));
 await page.locator('#verify-artifact').click();
 await page.waitForFunction(()=>document.querySelector('#verify-result').textContent.startsWith('FAIL:'));
 const vertices=Buffer.alloc(36);[0,0,0,1,0,0,0,1,0].forEach((v,i)=>vertices.writeFloatLE(v,i*4));
 const doc={asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0}],meshes:[{primitives:[{attributes:{POSITION:0}}]}],buffers:[{byteLength:36}],bufferViews:[{buffer:0,byteLength:36,target:34962}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[0,0,0],max:[1,1,0]}]};
 const raw=Buffer.from(JSON.stringify(doc)),n=Math.ceil(raw.length/4)*4,b=Buffer.alloc(28+n+36);b.writeUInt32LE(0x46546c67,0);b.writeUInt32LE(2,4);b.writeUInt32LE(b.length,8);b.writeUInt32LE(n,12);b.writeUInt32LE(0x4e4f534a,16);b.fill(32,20,20+n);raw.copy(b,20);b.writeUInt32LE(36,20+n);b.writeUInt32LE(0x004e4942,24+n);vertices.copy(b,28+n);
 await page.locator('#model-file').setInputFiles({name:'diagnostic.glb',mimeType:'model/gltf-binary',buffer:b});
 await page.waitForFunction(()=>document.querySelector('#render-status').textContent.includes('基本glTF描画'));
 assert.equal(await page.locator('#model-view canvas').count(),1);
 await page.screenshot({path:'qa-output/mobile-diagnostic.png',fullPage:true});
 assert.deepEqual(errors,[]);
 console.log('PASS: mocked API, mobile width, SHA-256 match/mismatch, diagnostic GLB loader. Not actual asset QA.');
}finally{await browser?.close();server.kill();}
