const{chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs');
const out=process.env.LIND_QA_OUT||'/tmp/aidan-field-a1-qa';fs.mkdirSync(out,{recursive:true});
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const rows=[];try{for(const[w,h]of[[1280,720],[844,390],[390,844]]){
 const p=await b.newPage({viewport:{width:w,height:h},hasTouch:w<1000}),errors=[],bad=[],fieldRequests=[];
 p.on('request',r=>{if(r.url().includes('/img/field/characters/aidan/'))fieldRequests.push(r.url())});
 p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('response',r=>{if(r.status()>=400)bad.push(r.url())});
 await p.goto(process.env.LIND_QA_URL||'http://127.0.0.1:8015');await p.waitForFunction(()=>window.AidanFieldActor);assert.equal(fieldRequests.length,0,'no Aidan texture load outside DEV review');await p.evaluate(()=>AidanFieldActor.ready());await p.clock.install();await p.clock.pauseAt(new Date(Date.now()+1000));
 const saved=await p.evaluate(()=>({px,py,stage:storyStage,storage:JSON.stringify({...localStorage})}));await p.evaluate(()=>LindFieldReview.open());
 assert.equal(await p.evaluate(()=>AidanFieldActor.status.frame),'aidan_idle_down');
 const loaded=await p.locator('#player .aidan-field-frame').evaluateAll(es=>es.map(e=>({frame:e.dataset.frame,loaded:e.complete&&e.naturalWidth>0})));assert.equal(loaded.length,20);assert.ok(loaded.every(e=>e.loaded));
 await p.screenshot({path:`${out}/aidan-plaza-${w}.png`});
 const animation=[];
 for(const[d,dx,dy]of[['down',0,160],['left',-160,0],['right',160,0],['up',0,-160]]){
  await p.evaluate(({dx,dy})=>{target=null;FieldNavigation.cancel();px=800;py=1250;camera();target=FieldNavigation.destination(px+dx,py+dy,blockedWorld)},{dx,dy});
  const seen=new Set();for(let i=0;i<8;i++){await p.clock.runFor(70);const status=await p.evaluate(()=>AidanFieldActor.status);if(status.state==='WALK'){assert.equal(status.direction,d);seen.add(status.frame);}
   const anchor=await p.evaluate(()=>{const s=AidanFieldActor.status,a=AidanFieldAssets.frames[s.frame],e=document.querySelector('#player .aidan-field-frame:not([hidden])'),r=e.getBoundingClientRect(),worldRect=world.getBoundingClientRect();return{dx:r.left+a.anchor[0]*a.scale-(worldRect.left+px+17),dy:r.top+a.anchor[1]*a.scale-(worldRect.top+py+42),height:a.bounds[3]*a.scale};});assert.ok(Math.abs(anchor.dx)<.04&&Math.abs(anchor.dy)<.04,'visual feet registered to nav ground anchor');assert.ok(Math.abs(anchor.height-44)<.001);
  }
  assert.equal(seen.size,4,'all four walk frames play in real field RAF');await p.clock.runFor(400);assert.equal(await p.evaluate(()=>AidanFieldActor.status.state),'IDLE');assert.equal(await p.evaluate(()=>AidanFieldActor.status.frame),'aidan_idle_'+d);
  await p.screenshot({path:`${out}/aidan-idle-${d}-${w}.png`});animation.push({direction:d,frames:[...seen],idle:true});
 }
 // Real directional input changes sprite facing without changing the 22.5/input speed.
 for(const[key,d]of[['ArrowDown','down'],['a','left'],['ArrowRight','right'],['w','up']]){await p.evaluate(()=>{target=null;px=800;py=1250;camera()});await p.clock.runFor(120);await p.keyboard.press(key);await p.clock.runFor(20);assert.equal(await p.evaluate(()=>AidanFieldActor.status.direction),d);await p.clock.runFor(150);assert.equal(await p.evaluate(()=>AidanFieldActor.status.state),'IDLE');}
 // Compare without changing position/route, using actual mouse/touch toggle.
 const before=await p.evaluate(()=>({px,py}));const toggle=p.locator('#aidanFieldToggle');if(w<1000)await toggle.tap();else await toggle.click();assert.equal(await p.evaluate(()=>AidanFieldActor.enabled),false);assert.equal(await p.locator('#player').evaluate(e=>e.classList.contains('aidan-field-active')),false);if(w<1000)await toggle.tap();else await toggle.click();assert.equal(await p.evaluate(()=>AidanFieldActor.enabled),true);assert.deepEqual(await p.evaluate(()=>({px,py})),before);
 for(const[id,name]of[['emma','emma'],['cow','cow'],['lind_bridge','bridge'],['train_dummy','training'],['lind_aidan_house','door']]){await p.evaluate(id=>LindFieldReview.focus(id),id);await p.clock.runFor(160);await p.screenshot({path:`${out}/aidan-scale-${name}-${w}.png`});}
 await p.evaluate(()=>LindFieldReview.close());assert.equal(await p.locator('#player').evaluate(e=>e.classList.contains('aidan-field-active')),false);assert.equal(await p.evaluate(()=>AidanFieldActor.active),false);assert.deepEqual(await p.evaluate(()=>({px,py,stage:storyStage,storage:JSON.stringify({...localStorage})})),saved);
 await p.evaluate(()=>LindFieldReview.open());await p.clock.runFor(140);assert.equal(await p.evaluate(()=>AidanFieldActor.status.frame),'aidan_idle_down');await p.evaluate(()=>LindFieldReview.close());
 assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);rows.push({viewport:[w,h],loadedFrames:loaded.length,lazyReviewOnlyLoading:true,animation,visualNavigationAnchor:true,bodyHeight:44,keyboard:true,toggle:w<1000?'touch':'mouse',saveAndExitRestored:true,image404:0,jsExceptions:0,consoleErrors:0});await p.close();console.log(`${w}x${h} Aidan animation/anchor/input/lifecycle PASS`);
}fs.writeFileSync(out+'/aidan-qa.json',JSON.stringify(rows,null,2));}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
