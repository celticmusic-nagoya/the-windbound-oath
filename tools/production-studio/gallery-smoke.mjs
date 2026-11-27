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
const morwen=manifest.entries.filter(e=>e.category==='morwen'||/hairharpy|ヘアアセット/i.test([e.name,e.stage,e.asset_id].join(' ')));
for(const e of manifest.entries){const data=await readFile(join(root,e.path));assert.equal(data.length,e.bytes);assert.equal(createHash('sha256').update(data).digest('hex'),e.sha256);}
await mkdir('gallery-qa',{recursive:true});
const server=spawn('python3',['-m','http.server','8766','--bind','127.0.0.1','--directory',root],{stdio:'ignore'});
let browser;
try{
 for(let i=0;i<40;i++){try{if((await fetch('http://127.0.0.1:8766')).ok)break;}catch{}await new Promise(r=>setTimeout(r,250));}
 browser=await chromium.launch({args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:360,height:780},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('https://api.github.com/**',r=>r.fulfill({json:r.request().url().includes('/pulls/')?{state:'open',draft:true,head:{sha:'a'.repeat(40)}}:{workflow_runs:[]}}));
 await page.goto('http://127.0.0.1:8766/');
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);

 // Automatic gallery refresh must preserve an active search and survive a failed fetch.
 await page.getByRole('button',{name:'全成果物・新着順',exact:true}).click();
 const liveSearch=page.getByRole('searchbox',{name:'成果物検索'});
 await liveSearch.fill('qa-live-fixture');
 await page.route('**/gallery-manifest.json',route=>route.fulfill({json:{...manifest,entries:manifest.entries.slice(0,-1)}}));
 await page.evaluate(()=>loadPublishedGallery(true));
 assert.equal(await liveSearch.inputValue(),'qa-live-fixture');
 assert.match(await page.locator('#published-live-status').innerText(),/新しい一覧あり/);
 await page.unroute('**/gallery-manifest.json');
 await page.route('**/gallery-manifest.json',route=>route.fulfill({status:503}));
 await page.evaluate(()=>loadPublishedGallery(true));
 assert.equal(await liveSearch.inputValue(),'qa-live-fixture');
 assert.match(await page.locator('#published-live-status').innerText(),/前回取得分を保持/);
 await page.unroute('**/gallery-manifest.json');
 await page.getByRole('button',{name:'← カテゴリ一覧',exact:true}).click();
 await page.route('**/gallery-manifest.json',route=>route.fulfill({json:{...manifest,entries:manifest.entries.slice(0,-1)}}));
 await page.evaluate(()=>loadPublishedGallery(true));
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length-1);
 await page.unroute('**/gallery-manifest.json');
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);

 // Race regression: the first refresh is delayed and carries a stale, shorter manifest.
 // The second refresh must win, even if the older response arrives last.
 let refreshCount=0;
 await page.route('**/gallery-manifest.json',async route=>{
  const request=++refreshCount;
  if(request===1){
   await new Promise(resolve=>setTimeout(resolve,500));
   await route.fulfill({json:{...manifest,entries:manifest.entries.slice(0,-1)}});
  }else{
   await route.fulfill({json:manifest});
  }
 });
 const firstRefresh=page.waitForRequest(req=>req.url().includes('/gallery-manifest.json'));
 await page.locator('#refresh-published').click();
 await firstRefresh;
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);
 await page.waitForTimeout(600);
 assert.ok((await page.locator('#published-status').innerText()).startsWith(manifest.entries.length+' 件'),'stale gallery response overwrote refresh');
 assert.equal(refreshCount,2,'expected two refresh requests');
 await page.unroute('**/gallery-manifest.json');
 // Model download ordering: fixture GLBs are generated locally, not published assets.
 const triangleGlb=tag=>{
  const bin=Buffer.alloc(36);[0,0,0,1,0,0,0,1,0].forEach((x,i)=>bin.writeFloatLE(x,i*4));
  const j=Buffer.from(JSON.stringify({asset:{version:'2.0',generator:tag},scene:0,scenes:[{nodes:[0]}],nodes:[{mesh:0}],meshes:[{primitives:[{attributes:{POSITION:0}}]}],buffers:[{byteLength:36}],bufferViews:[{buffer:0,byteLength:36,target:34962}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[0,0,0],max:[1,1,0]}]}));
  const pad=Buffer.alloc((4-j.length%4)%4,32),body=Buffer.concat([j,pad]),h=Buffer.alloc(12),jh=Buffer.alloc(8),bh=Buffer.alloc(8);
  h.writeUInt32LE(0x46546c67,0);h.writeUInt32LE(2,4);h.writeUInt32LE(12+8+body.length+8+bin.length,8);
  jh.writeUInt32LE(body.length,0);jh.writeUInt32LE(0x4e4f534a,4);bh.writeUInt32LE(bin.length,0);bh.writeUInt32LE(0x004e4942,4);
  return Buffer.concat([h,jh,body,bh,bin]);
 };
 const modelFixtures=['slow','fast'].map(tag=>{
  const bytes=triangleGlb(tag),sha256=createHash('sha256').update(bytes).digest('hex');
  return {bytes,entry:{name:'QA model '+tag,path:'published/'+sha256+'.glb',sha256,bytes:bytes.length,qa:'NOT_RUN',adoption:'UNADOPTED',category:'other'}};
 });
 const [slowModel,fastModel]=modelFixtures;
 const modelPath=f=>'**/'+f.entry.path;
 await page.route('**/gallery-manifest.json',r=>r.fulfill({json:{...manifest,entries:[...manifest.entries,...modelFixtures.map(f=>f.entry)]}}));
 await page.route(modelPath(fastModel),r=>r.fulfill({body:fastModel.bytes,contentType:'model/gltf-binary'}));
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length+2);
 await page.getByRole('button',{name:'全成果物・新着順',exact:true}).click();
 const modelTile=f=>page.locator('#published-gallery article.tile').filter({has:page.getByRole('heading',{name:f.entry.name,exact:true})});
 const modelButton=f=>modelTile(f).getByRole('button',{name:'3D表示',exact:true});
 const selectedModel=()=>page.locator('#model-file').evaluate(el=>el.files[0]?.name||'');
 async function delayedModelSelection(choose,expected){
  let release,complete;
  const gate=new Promise(r=>{release=r;}),finished=new Promise(r=>{complete=r;});
  await page.route(modelPath(slowModel),async route=>{try{await gate;await route.fulfill({body:slowModel.bytes,contentType:'model/gltf-binary'});}catch{}finally{complete();}});
  try{
   const started=page.waitForRequest(req=>req.url().endsWith(slowModel.entry.path));
   await modelButton(slowModel).click();await started;
   await choose();
   await page.waitForFunction(n=>document.getElementById('model-file').files[0]?.name===n,expected);
   release();await finished;
   await page.waitForFunction(()=>Array.from(document.querySelectorAll('#published-gallery article.tile')).some(t=>t.querySelector('h3')?.textContent==='QA model slow'&&t.querySelector('[role=status]')?.textContent==='取得を中止しました'));
   assert.equal(await selectedModel(),expected,'stale model overwrote latest selection');
   assert.match(await page.locator('#published-status').innerText(),/^\d+ 件/,'download error replaced gallery count');
  }finally{release();await page.unroute(modelPath(slowModel));}
 }
 await delayedModelSelection(()=>modelButton(fastModel).click(),fastModel.entry.path.split('/').pop());
 await delayedModelSelection(()=>page.locator('#model-file').setInputFiles({name:'manual.glb',mimeType:'model/gltf-binary',buffer:fastModel.bytes}),'manual.glb');
 await page.locator('#model-file').setInputFiles([]);
 await page.unroute(modelPath(fastModel));
 await page.unroute('**/gallery-manifest.json');
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);

 // Malformed manifest entries are ignored without losing valid gallery entries.
 await page.route('**/gallery-manifest.json',route=>route.fulfill({json:{...manifest,entries:[null,{...manifest.entries[0],name:{unexpected:"object"}},{...manifest.entries[0],stage:[]},...manifest.entries]}}));
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);
 assert.equal(await page.locator('.category-card').count(),7,'malformed metadata crashed gallery');
 await page.unroute('**/gallery-manifest.json');
 assert.equal(await page.locator('.category-card').count(),7);
 // Category cards may legitimately have no cover when the manifest only contains 3D files.
 assert.ok(await page.locator('#published-gallery img').count()<=7);
 // Every category containing a published image must render its thumbnail.
 const categoryOrder=['cliff','morwen','village','world','blueprint','map','other'];
 const categoryCards=page.locator('.category-card');
 const categoryOf=e=>{
  const raw=[e.name,e.stage,e.asset_id,e.source_path].filter(Boolean).join(' ').toLowerCase();
  const top=['cliff','morwen','village','world','blueprint','map','other'].includes(e.category)?e.category:isCliff(e)?'cliff':'other';
  if(top!=='other')return top;
  if(/blueprint|design[-_ ]?sheet|設計図|四面図|寸法図|断面図/.test(raw))return 'blueprint';
  if(/(^|[^a-z])map([^a-z]|$)|site[-_ ]?plan|layout[-_ ]?plan|地図|配置図|平面図|俯瞰図/.test(raw))return 'map';
  if(/hairharpy|hair[-_ ]asset|ヘアアセット/i.test(raw))return 'morwen';
  if(/aidan|エイダン|(?:^|[^a-z])inn(?:$|[^a-z])|宿屋/.test(raw))return 'village';
  return 'other';
 };
 for(let i=0;i<categoryOrder.length;i++){
  const id=categoryOrder[i];
  // The published gallery can infer a category from legacy asset metadata.
 const hasImage=manifest.entries.some(e=>photo(e)&&categoryOf(e)===id);
  if(hasImage)assert.equal(await categoryCards.nth(i).locator('img').count(),1,'missing category cover: '+id);
 }

 // World categories are separate even before any additional publication is approved.
 await page.locator('#published-gallery').getByRole('button',{name:/世界・自然／遺構/}).click();
 for(const label of ['植物・草花','樹木','森林','河川・水辺','地形','聖域','遺跡'])assert.equal(await page.locator('#published-gallery .category-card').filter({hasText:label}).count(),1);
 await page.locator('#published-gallery').getByRole('button',{name:'← カテゴリ一覧',exact:true}).click();
 const worldFixtures=['plant','tree','forest','river','terrain','sanctuary','ruin'].map((subcategory,i)=>({...manifest.entries[0],name:'world-fixture-'+subcategory,category:'world',subcategory,created_at:'2026-11-26T00:00:0'+i+'Z'}));
 await page.route('**/gallery-manifest.json',route=>route.fulfill({json:{...manifest,entries:worldFixtures}}));
 await page.locator('#refresh-published').click();
 await page.waitForFunction(()=>document.querySelector('#published-status').textContent.startsWith('7 件'));
 await page.locator('#published-gallery').getByRole('button',{name:/世界・自然／遺構/}).click();
 for(const [subcategory,label] of [['plant','植物・草花'],['tree','樹木'],['forest','森林'],['river','河川・水辺'],['terrain','地形'],['sanctuary','聖域'],['ruin','遺跡']]){
  await page.locator('#published-gallery .category-card').filter({hasText:label}).click();
  assert.deepEqual(await page.locator('#published-gallery article h3').allTextContents(),['world-fixture-'+subcategory]);
  assert.ok(await page.locator('.gallery-design-links a').count()>0);
  if(subcategory==='river'){assert.match(await page.locator('.gallery-design-links').innerText(),/下流メッシュV28/);assert.match(await page.locator('.gallery-design-links').innerText(),/水深・材質V34/);assert.ok(await page.locator('.gallery-design-links a').first().getAttribute('href').then(s=>s.includes('3440af1b22a9c87c55237bab25921aa20aa80d34')));}
  await page.locator('#published-gallery').getByRole('button',{name:'← カテゴリ一覧',exact:true}).click();
 }
 await page.unroute('**/gallery-manifest.json');
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);
 // UX regression: bundled stylesheet, breadcrumbs, 390px layout and QA metadata.
 const uxCss=await page.request.get('http://127.0.0.1:8766/studio-ux.css');
 assert.equal(uxCss.status(),200,'UX stylesheet missing from published bundle');
 assert.equal(await page.locator('.gallery-breadcrumb').count(),1,'root breadcrumb missing');
 await page.setViewportSize({width:390,height:844});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'390px gallery overflow');
 await page.setViewportSize({width:360,height:780});
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/category-home.png'});
 // Exact full HEAD history: distinguish equal prefixes, missing HEAD and mixed domain metadata.
 const h1='a'.repeat(39)+'1',h2='a'.repeat(39)+'2';
 const fixtures=[
  {...manifest.entries[0],name:'history map',category:'cliff',head:h1,created_at:'2026-11-24T00:00:00Z',qa:'NOT_RUN'},
  {...manifest.entries[0],name:'history character',category:'morwen',head:h1,created_at:'2026-11-25T00:00:00Z',qa:'FAIL'},
  {...manifest.entries[0],name:'history village',category:'village',head:h2,created_at:'2026-11-23T00:00:00Z'},
  {...manifest.entries[0],name:'history unknown',head:'invalid',created_at:'2026-11-26T00:00:00Z'}
 ];
 await page.route('**/gallery-manifest.json',route=>route.fulfill({json:{...manifest,entries:fixtures}}));
 await page.locator('#refresh-published').click();
 await page.waitForFunction(()=>document.querySelector('#published-status').textContent.startsWith('4 件'));
 await page.getByRole('button',{name:'制作改訂履歴（HEAD別）',exact:true}).click();
 const historyCards=page.locator('#published-gallery [data-revision-head]');
 assert.equal(await historyCards.count(),3);
 assert.deepEqual(await historyCards.evaluateAll(es=>es.map(e=>e.dataset.revisionHead)),[h1,h2,'unknown']);
 const first=historyCards.first();
 assert.ok((await first.innerText()).includes('NOT_RUN: 1'));
 assert.ok((await first.innerText()).includes('FAIL: 1'));
 assert.ok((await first.innerText()).includes('モルウェン'));
 assert.ok((await first.innerText()).includes(h1));
 assert.equal(await historyCards.last().locator('a').count(),0);
 await first.getByRole('button',{name:'この一覧の成果物を見る',exact:true}).click();
 assert.deepEqual(await page.locator('#published-gallery article h3').allTextContents(),['history character','history map']);
 await page.getByRole('button',{name:'← カテゴリ一覧',exact:true}).click();
 assert.equal(await historyCards.count(),3);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'history mobile overflow');
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/revision-history-fixture.png'});
 await page.unroute('**/gallery-manifest.json');
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);
 // Provenance fixtures: known expiry is not live availability; malformed links must not escape the repository.
 const sourceFixture=manifest.entries.find(photo);
 const provenanceBase='https://github.com/celticmusic-nagoya/the-windbound-oath';
 const variants=[
  {...sourceFixture,name:'expiry past',source_type:'artifact',run_id:123,artifact_id:456,expires_at:'2000-01-01T00:00:00Z',review_ref:provenanceBase+'/pull/599#issuecomment-123'},
  {...sourceFixture,name:'expiry unknown',source_type:'artifact',run_id:123,artifact_id:456,expires_at:null,review_ref:'https://example.org/fake'},
  {...sourceFixture,name:'invalid identity',source_type:'artifact',run_id:null,artifact_id:456,review_ref:'javascript:alert(1)'},
  {...sourceFixture,name:'git source',source_type:'git',head:'a'.repeat(40),source_path:'assets/candidates/LIND-HOME-01/test.png'},
  {...sourceFixture,name:'git unsafe',source_type:'git',head:'a'.repeat(40),source_path:'assets/candidates/LIND-HOME-01/../test.png'},
 ];
 await page.route('**/gallery-manifest.json',route=>route.fulfill({json:{...manifest,entries:variants}}));
 await page.locator('#refresh-published').click();
 await page.waitForFunction(()=>document.querySelector('#published-status').textContent.startsWith('5 件'));
 await page.getByRole('button',{name:'全成果物・新着順',exact:true}).click();
 const sourceCard=name=>page.locator('#published-gallery article').filter({has:page.getByRole('heading',{name,exact:true})});
 assert.equal(await sourceCard('expiry past').locator('.gallery-source-link').getAttribute('href'),provenanceBase+'/actions/runs/123');
 assert.match(await sourceCard('expiry past').locator('.gallery-source-expiry').innerText(),/経過済み/);
 assert.equal(await sourceCard('expiry past').locator('.gallery-review-link').getAttribute('href'),provenanceBase+'/pull/599#issuecomment-123');
 assert.match(await sourceCard('expiry unknown').locator('.gallery-source-expiry').innerText(),/期限未記録/);
 assert.equal(await sourceCard('expiry unknown').locator('.gallery-review-link').count(),0);
 assert.equal(await sourceCard('invalid identity').locator('.gallery-source-link').count(),0);
 assert.equal(await sourceCard('invalid identity').locator('.gallery-review-link').count(),0);
 assert.equal(await sourceCard('git source').locator('.gallery-source-link').getAttribute('href'),provenanceBase+'/blob/'+'a'.repeat(40)+'/assets/candidates/LIND-HOME-01/test.png');
 assert.equal(await sourceCard('git unsafe').locator('.gallery-source-link').count(),0);
 await sourceCard('expiry past').locator('.gallery-image-button').click();
 const sourceDialog=page.getByRole('dialog',{name:'成果物画像レビュー'});
 await sourceDialog.locator('summary').click();
 assert.equal(await sourceDialog.locator('.gallery-review-link').getAttribute('href'),provenanceBase+'/pull/599#issuecomment-123');
 await sourceDialog.getByRole('button',{name:'閉じる',exact:true}).click();
 await page.unroute('**/gallery-manifest.json');
 await page.locator('#refresh-published').click();
 await page.waitForFunction(n=>document.querySelector('#published-status').textContent.startsWith(n+' 件'),manifest.entries.length);
 // Global recent view and exact independent QA/adoption filters.
 await page.getByRole('button',{name:'全成果物・新着順',exact:true}).click();
 const allTiles=page.locator('#published-gallery article');
 const visibleTiles=page.locator('#published-gallery article:visible');
 const recent=[...manifest.entries].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
 assert.equal(await allTiles.count(),recent.length);
 assert.deepEqual(await allTiles.locator('h3').allTextContents(),recent.map(e=>e.name));
 const sample=recent[0];
 const qaFilter=page.getByRole('combobox',{name:'QA状態',exact:true}),adoptionFilter=page.getByRole('combobox',{name:'採用状態',exact:true});
 await qaFilter.selectOption({label:sample.qa||'未記録'});
 assert.equal(await visibleTiles.count(),recent.filter(e=>e.qa===sample.qa).length);
 await adoptionFilter.selectOption({label:sample.adoption||'未記録'});
 const matching=recent.filter(e=>e.qa===sample.qa&&e.adoption===sample.adoption);
 assert.equal(await visibleTiles.count(),matching.length);
 if(matching.some(photo)){
  await visibleTiles.locator('.gallery-image-button').first().click();
  const filteredReview=page.getByRole('dialog',{name:'成果物画像レビュー'});
  assert.equal(await filteredReview.getByRole('status').innerText(),'1 / '+matching.filter(photo).length);
  await filteredReview.getByRole('button',{name:'閉じる',exact:true}).click();
 }
 await page.getByRole('searchbox',{name:'成果物検索'}).fill('NO_MATCH_9c32e9e8');
 assert.equal(await visibleTiles.count(),0);
 assert.ok(await page.getByText('条件に一致する成果物はありません。').isVisible());
 await page.getByRole('button',{name:'絞り込み解除',exact:true}).click();
 assert.equal(await visibleTiles.count(),recent.length);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'all-results mobile overflow');
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/recent-filters-mobile.png'});
 await page.getByRole('button',{name:'← カテゴリ一覧',exact:true}).click();
 await page.getByRole('button',{name:/風待ちの崖/}).click();
 const images=page.locator('#published-gallery img');
 assert.equal(await images.count(),manifest.entries.filter(e=>isCliff(e)&&photo(e)).length);
 // Public gallery presence does not prove preservation of the source ZIP.
 const cliffEntries=manifest.entries.filter(e=>isCliff(e));
 assert.equal(await page.locator('#published-gallery article .gallery-meta').count(),cliffEntries.length,'QA/adoption chips missing');
 assert.ok(await page.locator('.gallery-breadcrumb').innerText().then(t=>t.includes('制作領域')&&t.includes('風待ちの崖')),'detail breadcrumb missing');
 const preservationLabels=page.locator('#published-gallery article .gallery-preservation');
 assert.equal(await preservationLabels.count(),cliffEntries.length);
 // The gallery includes non-entry controls; only article tiles are counted.
 for(let i=0;i<cliffEntries.length;i++){
  const e=[...cliffEntries].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')))[i];
  const expected=e.preservation_status==='PRESERVED_AND_READBACK_VERIFIED'?'manifest申告：再取得SHA検証済み（独立未検証）':e.preservation_status==='PRESERVATION_BLOCKED'?'権利確認待ち・未保全':'未検証';
  assert.ok((await preservationLabels.nth(i).innerText()).includes(expected));
 }
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'360px gallery overflow');
 for(const img of await images.all()){await img.scrollIntoViewIfNeeded();await img.evaluate(e=>e.decode());assert.ok(await img.evaluate(e=>e.naturalWidth>0&&e.naturalHeight>0));}
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.locator('#published-gallery').screenshot({path:'gallery-qa/actual-gallery.png'});
 await page.locator('.gallery-image-button').first().click();
 await page.locator('dialog img').evaluate(e=>e.decode());
 const review=page.getByRole('dialog',{name:'成果物画像レビュー'});
 const cliffPhotos=cliffEntries.filter(photo).sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
 assert.equal(await review.getByRole('status').innerText(),'1 / '+cliffPhotos.length);
 assert.ok(await review.getByRole('button',{name:'← 前へ'}).isDisabled());
 const zoomRegion=review.getByRole('region',{name:'画像拡大表示'});
 await review.getByRole('button',{name:'拡大',exact:true}).click();
 assert.equal(await review.locator('[aria-label="拡大率"]').innerText(),'150%');
 assert.ok(await zoomRegion.evaluate(e=>e.scrollWidth>e.clientWidth),'zoom must permit horizontal inspection');
 await review.getByRole('button',{name:'全体表示',exact:true}).click();
 assert.equal(await review.locator('[aria-label="拡大率"]').innerText(),'100%');
 assert.ok(await zoomRegion.evaluate(e=>e.scrollWidth<=e.clientWidth+1),'reset must fit image');

 await review.getByText('制作情報・QA・来歴',{exact:true}).click();
 assert.ok((await review.locator('.gallery-review-metadata').innerText()).includes(cliffPhotos[0].sha256));
 if(cliffPhotos.length>1){
  await review.getByRole('button',{name:'次へ →'}).click();
  assert.equal(await review.getByRole('status').innerText(),'2 / '+cliffPhotos.length);
  assert.ok((await review.locator('.gallery-review-metadata').innerText()).includes(cliffPhotos[1].sha256));
  await review.getByRole('button',{name:'← 前へ'}).click();
  assert.equal(await review.getByRole('status').innerText(),'1 / '+cliffPhotos.length);
 }
 assert.ok(await review.evaluate(e=>e.scrollWidth<=e.clientWidth+1),'review overflow');
 await review.screenshot({path:'gallery-qa/image-review-mobile.png'});
 await page.getByRole('button',{name:'閉じる',exact:true}).click();
 assert.ok(await page.locator('.gallery-image-button').first().evaluate(e=>document.activeElement===e),'review focus not restored');
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
 // Comparison provenance must remain visible for each selected published image.
 const selected=morwen.filter(photo).sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
 const info=dialog.locator('p').filter({hasText:'SHA-256:'});
 assert.equal(await info.count(),2);
 for(let i=0;i<2;i++){
  const text=await info.nth(i).innerText();
  assert.ok(text.includes(selected[i].sha256),'comparison SHA missing');
  assert.ok(text.includes('HEAD: '+(selected[i].head||'未記録')),'comparison HEAD missing');
  assert.ok(text.includes('run: '+(selected[i].run_id??'未記録')),'comparison run missing');
  assert.ok(text.includes('Artifact: '+(selected[i].artifact_id??'未記録')),'comparison artifact missing');
  assert.ok(text.includes('採用: '+selected[i].adoption),'comparison adoption missing');
 }
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
 for(const [category,label] of [['cliff','風待ちの崖'],['morwen','モルウェン'],['village','リルド村'],['blueprint','設計図'],['map','地図・配置図'],['other','その他']]){
 const models=manifest.entries.filter(e=>(isCliff(e)?'cliff':e.category||'other')===category&&!photo(e));
 if(!models.length)continue;
 await page.getByRole('button',{name:'← カテゴリ一覧'}).click();
 await page.getByRole('button',{name:new RegExp(label)}).click();
 if(category==='morwen'||category==='village')await page.getByRole('button',{name:/全件/}).click();
 const buttons=page.locator('#published-gallery').getByRole('button',{name:'3D表示'});
 assert.equal(await buttons.count(),models.length);
 await buttons.first().click();
 await page.waitForFunction(()=>document.querySelector('#render-status').textContent.includes('基本glTF描画'));
 await page.screenshot({path:'gallery-qa/model-'+category+'.png'});
 }
 assert.deepEqual(errors,[]);
 console.log('PASS: production images decoded; SHA-256 verified; 360px mobile width and preservation-status semantics.');
}finally{await browser?.close();server.kill();}
