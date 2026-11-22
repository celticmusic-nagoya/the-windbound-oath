import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdir,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {join} from 'node:path';
const root=process.env.STUDIO_ROOT || join(process.env.RUNNER_TEMP,'studio-site');
const manifest=JSON.parse(await readFile(join(root,'gallery-manifest.json')));
assert.equal(manifest.entries.length,5);
for(const e of manifest.entries){const data=await readFile(join(root,e.path));assert.equal(data.length,e.bytes);assert.equal(createHash('sha256').update(data).digest('hex'),e.sha256);}
await mkdir('gallery-qa',{recursive:true});
const server=spawn('python3',['-m','http.server','8766','--bind','127.0.0.1','--directory',root],{stdio:'ignore'});
let browser;
try{
 for(let i=0;i<40;i++){try{if((await fetch('http://127.0.0.1:8766')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
 browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://api.github.com/**',r=>r.fulfill({json:r.request().url().includes('/pulls/')?{state:'open',draft:true,head:{sha:'a'.repeat(40)}}:{workflow_runs:[]}}));
 await page.goto('http://127.0.0.1:8766/');
 await page.waitForFunction(()=>document.querySelector('#published-status').textContent.startsWith('5 件'));
 const images=page.locator('#published-gallery img');
 assert.equal(await images.count(),5);
 for(const img of await images.all()){await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());assert.ok(await img.evaluate(e=>e.naturalWidth>0&&e.naturalHeight>0));}
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/actual-gallery.png'});
 assert.deepEqual(errors,[]);
 console.log('PASS: five production images decoded; SHA-256 verified; mobile width.');
}finally{await browser?.close();server.kill();}
