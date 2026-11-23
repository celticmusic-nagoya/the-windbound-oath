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
const photo=e=>/\.(png|jpe?g)$/.test(e.path);
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
 assert.equal(await page.locator('#published-gallery img').count(),new Set(manifest.entries.filter(photo).map(e=>isCliff(e)?'cliff':e.category||'other')).size);
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/category-home.png'});
 await page.getByRole('button',{name:/風待ちの崖/}).click();
 const images=page.locator('#published-gallery img');
 assert.equal(await images.count(),manifest.entries.filter(e=>isCliff(e)&&photo(e)).length);
 for(const img of await images.all()){await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());assert.ok(await img.evaluate(e=>e.naturalWidth>0&&e.naturalHeight>0));}
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/actual-gallery.png'});
 await page.locator('.gallery-image-button').first().click();
 await page.locator('dialog img').evaluate(e=>e.decode());
 await page.getByRole('button',{name:'閉じる',exact:true}).click();
 await page.getByRole('button',{name:'← カテゴリ一覧'}).click();
 await page.getByRole('button',{name:/モルウェン/}).click();
 await page.getByRole('button',{name:/モルウェン \/ 全件/}).click();
 if(morwen.length){const imgs=page.locator('#published-gallery img');assert.equal(await imgs.count(),morwen.filter(photo).length);for(const img of await imgs.all()){await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());}await page.locator('#published-gallery').screenshot({path:'gallery-qa/morwen.png'});}else assert.ok(await page.getByText('成果物はまだ同期されていません。').isVisible());
 if(morwen.filter(photo).length>=2){
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
 await dialog.waitFor({state:'detached',timeout:5000});
 }
 // Verify pinned HairHarpy v3/v4 history in Morwen / Hair assets.
 const hair=manifest.entries.filter(e=>photo(e)&&/HairHarpy v[34]/.test(e.stage||''));
 if(hair.some(e=>e.stage.includes('v3'))&&hair.some(e=>e.stage.includes('v4'))){
 await page.getByRole('button',{name:'← カテゴリ一覧'}).click();
 await page.getByRole('button',{name:/ヘアアセット/}).click();
 await page.getByRole('button',{name:'画像比較',exact:true}).click();
 const dialog=page.locator('dialog');
 const options=await dialog.getByRole('combobox',{name:'比較A'}).locator('option').allTextContents();
 const v3=options.findIndex(s=>s.includes('HairHarpy v3'));
 const v4=options.findIndex(s=>s.includes('HairHarpy v4'));
 assert.ok(v3>=0&&v4>=0,'v3/v4 compare options absent');
 await dialog.getByRole('combobox',{name:'比較A'}).selectOption(String(v3));
 await dialog.getByRole('combobox',{name:'比較B'}).selectOption(String(v4));
 for(const img of await dialog.locator('img').all())await img.evaluate(e=>e.decode());
 assert.notEqual(await dialog.locator('img').nth(0).getAttribute('src'),await dialog.locator('img').nth(1).getAttribute('src'));
 assert.ok(await dialog.evaluate(e=>e.scrollWidth<=e.clientWidth+1),'hair compare overflow');
 await dialog.screenshot({path:'gallery-qa/hairharpy-v3-v4-compare-mobile.png'});
 await dialog.getByRole('button',{name:'閉じる',exact:true}).click();
 await dialog.waitFor({state:'detached',timeout:5000});
 }
 for(const [category,label] of [['cliff','風待ちの崖'],['morwen','モルウェン'],['village','リルド村'],['other','その他']]){
 const models=manifest.entries.filter(e=>(isCliff(e)?'cliff':e.category||'other')===category&&!photo(e));
 if(!models.length)continue;
 await page.getByRole('button',{name:'← カテゴリ一覧'}).click();
 await page.getByRole('button',{name:new RegExp(label)}).click();
 const buttons=page.locator('#published-gallery').getByRole('button',{name:'3D表示'});
 assert.equal(await buttons.count(),models.length);
 await buttons.first().click();
 await page.waitForFunction(()=>document.querySelector('#render-status').textContent.includes('基本glTF描画'));
 await page.screenshot({path:'gallery-qa/model-'+category+'.png'});
 }
 assert.deepEqual(errors,[]);
 console.log('PASS: production images decoded; SHA-256 verified; mobile width.');
}finally{await browser?.close();server.kill();}
