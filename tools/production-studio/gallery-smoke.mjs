import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import {mkdir,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {join} from 'node:path';
const root=process.env.STUDIO_ROOT || join(process.env.RUNNER_TEMP,'studio-site');
const manifest=JSON.parse(await readFile(join(root,'gallery-manifest.json')));
assert.ok(manifest.entries.length>=5);
const isCliff=e=>e.category==='cliff'||e.run_id===44708204132;
const morwen=manifest.entries.filter(e=>e.category==='morwen');
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
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);
 assert.equal(await page.locator('.category-card').count(),4);
 assert.equal(await page.locator('#published-gallery img').count(),new Set(manifest.entries.map(e=>isCliff(e)?'cliff':e.category||'other')).size);
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/category-home.png'});
 await page.getByRole('button',{name:/風待ちの崖/}).click();
 const images=page.locator('#published-gallery img');
 assert.equal(await images.count(),manifest.entries.filter(isCliff).length);
 for(const img of await images.all()){await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());assert.ok(await img.evaluate(e=>e.naturalWidth>0&&e.naturalHeight>0));}
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/actual-gallery.png'});
 await page.locator('.gallery-image-button').first().click();
 await page.locator('dialog img').evaluate(e=>e.decode());
 await page.getByRole('button',{name:'閉じる',exact:true}).click();
 await page.getByRole('button',{name:'← カテゴリ一覧'}).click();
 await page.getByRole('button',{name:/モルウェン/}).click();
 if(morwen.length){const imgs=page.locator('#published-gallery img');assert.equal(await imgs.count(),morwen.length);for(const img of await imgs.all()){await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());}await page.locator('#published-gallery').screenshot({path:'gallery-qa/morwen.png'});}else assert.ok(await page.getByText('公開用成果物はまだ同期されていません。').isVisible());
 if(morwen.length>=2){
 await page.getByRole('button',{name:'画像比較',exact:true}).click();
 const dialog=page.locator('dialog');
 await dialog.getByRole('combobox',{name:'比較A'}).selectOption('0');
 await dialog.getByRole('combobox',{name:'比較B'}).selectOption('1');
 const imgs=dialog.locator('img');
 assert.equal(await imgs.count(),2);
 for(const img of await imgs.all())await img.evaluate(e=>e.decode());
 assert.notEqual(await imgs.nth(0).getAttribute('src'),await imgs.nth(1).getAttribute('src'));
 const a=await imgs.nth(0).boundingBox(),b=await imgs.nth(1).boundingBox();
 assert.ok(a.x+a.width<=b.x+1);
 assert.ok(await dialog.evaluate(e=>e.scrollWidth<=e.clientWidth+1));
 await dialog.screenshot({path:'gallery-qa/compare-mobile.png'});
 await dialog.getByRole('button',{name:'閉じる',exact:true}).click();
 assert.equal(await page.locator('dialog').count(),0);
 }
 assert.deepEqual(errors,[]);
 console.log('PASS: production images decoded; SHA-256 verified; mobile width.');
}finally{await browser?.close();server.kill();}
