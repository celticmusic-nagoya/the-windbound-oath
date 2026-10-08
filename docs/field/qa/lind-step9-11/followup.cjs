const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs');
const dir='/workspace/onboarding/lind-step9-11',step=Number(process.env.LIND_STEP||4);
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const results=[];
try { for(const [w,h] of [[1280,720],[844,390],[390,844]]) {
 const page=await browser.newPage({viewport:{width:w,height:h},hasTouch:w<1000}),errors=[],bad=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)bad.push({url:r.url(),status:r.status()})});
 page.on('console',m=>{if(m.type()==='error')errors.push('console: '+m.text())});
 await page.goto('http://127.0.0.1:8015');await page.waitForFunction(()=>window.LindFieldReview);await page.clock.install();
 const saved=await page.evaluate(()=>({px,py,target,room,stage:storyStage,flags:JSON.stringify(flags),storage:JSON.stringify({...localStorage}),z:pl.style.zIndex,display:inside.style.display}));
 await page.evaluate(()=>LindFieldReview.open());await page.clock.runFor(100);
 assert.ok(await page.locator('#lindReviewControls').isVisible());
 const loads=await page.evaluate(async()=>{const paths=[...Object.values(LindFieldAssets.terrain),...LindFieldAssets.objects.map(o=>o.path),...LindFieldAnimals.actors.flatMap(a=>Object.values(a.paths))];return Promise.all(paths.map(path=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve({path,ok:true});i.onerror=()=>resolve({path,ok:false});i.src=path})));});
 assert.ok(loads.every(i=>i.ok),'all production paths must load');
 await page.locator('#lindReviewLayer img').evaluateAll(async els=>{els.forEach(i=>i.loading='eager');await Promise.all(els.map(i=>i.decode()))});
 await page.evaluate(()=>saveGrowthData());assert.equal(await page.evaluate(()=>JSON.stringify({...localStorage})),saved.storage);
 const animals=await page.evaluate(()=>LindFieldAnimals.actors.map(a=>({id:a.id,x:a.x,y:a.y,state:a.state,width:a.width,height:a.height,pen:a.pen})));
 assert.ok(animals.every(a=>a.state==='IDLE'));await page.clock.runFor(7000);
 const walking=await page.evaluate(()=>LindFieldAnimals.actors.map(a=>({id:a.id,x:a.x,state:a.state})));
 assert.ok(walking.every((a,i)=>a.x!==animals[i].x&&a.state==='WALK'),'actual RAF must start moving each animal');
 await page.evaluate(()=>{for(let i=0;i<1200;i++)LindFieldAnimals.actors.forEach(a=>a.update(.1));});
 assert.equal(await page.evaluate(()=>LindFieldAnimals.actors.every(a=>a.x>=a.pen.x&&a.x+a.width<=a.pen.x+a.pen.width+.001&&a.y>=a.pen.y&&a.y+a.height<=a.pen.y+a.pen.height)),true);
 assert.equal(await page.evaluate(()=>LindFieldAnimals.actors.every(a=>{const f=a.foot;return blockedWorld(f.x+f.width/2-17,f.y+f.height/2-37)})),true,'animal foot collision');
 for(const id of ['cow','pig','chicken']) {await page.evaluate(id=>LindFieldReview.focus(id),id);await page.screenshot({path:`${dir}/step${step}-${id}-${w}.png`});}
 assert.equal(await page.evaluate(()=>blockedWorld(1500,800)),true);assert.equal(await page.evaluate(()=>blockedWorld(1500,560)),false);
 await page.evaluate(()=>{target=null;px=620;py=740;camera()});await page.keyboard.press('ArrowRight');assert.equal(await page.evaluate(()=>px),642.5);
 if(w<1000)await page.touchscreen.tap(w/2+55,h/2+50);else await page.mouse.click(w/2+55,h/2+50);await page.clock.runFor(180);assert.ok(await page.evaluate(()=>target!==null||px!==642.5));
 const collision=await page.evaluate(()=>LindFieldAssets.objects.flatMap(o=>(o.collisions||(o.collision?[o.collision]:[])).map(c=>({id:o.id,blocked:blockedWorld(o.x+c[0]+c[2]/2-17,o.y+c[1]+c[3]/2-37)}))));assert.ok(collision.every(c=>c.blocked),'declared collider feet must block');
 if(step>=5) {
  assert.equal(await page.evaluate(()=>{LindFieldEnvironment.setWind(false);return LindFieldEnvironment.wind}),false);
  assert.equal(await page.locator('#lindWindToggle').textContent(),'風OFF');
  const wind=await page.locator('.lind-wind-driven').evaluateAll(els=>els.map(e=>getComputedStyle(e).animationPlayState));assert.ok(wind.length>0&&wind.every(s=>s==='paused'));
  await page.evaluate(()=>LindFieldReview.focus('lind_tree_01'));await page.screenshot({path:`${dir}/step${step}-nature-${w}.png`});
  await page.evaluate(()=>LindFieldEnvironment.setWind(true));
 }
 if(step>=6) {
  await page.evaluate(()=>{target=null;px=1380;py=560;camera()});for(let i=0;i<18;i++)await page.keyboard.press('ArrowRight');assert.ok(await page.evaluate(()=>px>1630),'player crosses bridge to eastern bank');
  await page.evaluate(()=>{target=null;px=1500;py=1340;camera()});await page.keyboard.press('ArrowDown');assert.ok(await page.evaluate(()=>py<1358&&!blockedWorld(px,py)),'player cannot step off deck into water');
  assert.equal(await page.evaluate(()=>blockedWorld(1500,1340)),false,'fishing deck must be walkable');assert.equal(await page.evaluate(()=>blockedWorld(1500,1280)),true,'water outside deck must block');
  await page.evaluate(()=>LindFieldEnvironment.setWind(false));const water=page.locator('.lind-water-flow');const before=await water.evaluate(e=>getComputedStyle(e).backgroundPosition);await page.clock.runFor(1000);const after=await water.evaluate(e=>getComputedStyle(e).backgroundPosition);assert.notEqual(after,before,'water keeps flowing with wind stopped');assert.equal(await water.evaluate(e=>getComputedStyle(e).animationPlayState),'running');
  const spaces=await page.evaluate(()=>LindFieldRiver.standingAreas.map(s=>({id:s.id,walkable:!blockedWorld(s.x,s.y),groundWalkable:!LindFieldRiver.blocked(s.x,s.y)})));assert.ok(spaces.every(s=>s.groundWalkable));assert.equal(spaces.find(s=>s.id==='player').walkable,true);assert.equal(spaces.find(s=>s.id==='fisherman_future').walkable,false,'reserved fisherman area now occupied by the NPC');
  await page.evaluate(()=>LindFieldReview.focus('lind_fishing_pier'));await page.screenshot({path:`${dir}/step${step}-fishing-${w}.png`});await page.evaluate(()=>LindFieldEnvironment.setWind(true));
 }
 if(step>=7) {
  const gate=await page.evaluate(()=>LindFieldAssets.objects.find(o=>o.id==='train_gate'));
  await page.evaluate(o=>{target=null;px=o.x+o.width/2-17;py=o.y+o.height-70;camera()},gate);
  for(let i=0;i<7;i++)await page.keyboard.press('ArrowDown');assert.ok(await page.evaluate(o=>py>o.y+o.height,gate),'open gate passage');
  assert.equal(await page.evaluate(()=>blockedWorld(1860,730)),false,'open yard walkable');
  assert.equal(await page.evaluate(()=>LindFieldAssets.objects.filter(o=>o.category==='training').every(o=>o.x>=1630)),true,'training east of river');
  await page.evaluate(()=>LindFieldReview.focus('train_dummy'));await page.clock.runFor(50);
  const dummy=page.locator('[data-interaction-id="train_dummy"]');if(w<1000)await dummy.tap();else await dummy.click();
  assert.equal(await page.evaluate(()=>LindFieldTraining.lastInteraction?.id),'train_dummy');assert.ok(await page.locator('#lindInteractionNotice').isVisible());assert.equal(await page.evaluate(()=>storyStage),saved.stage);
  assert.equal(await page.evaluate(()=>{LindFieldTraining.clear();return LindFieldTraining.lastInteraction}),null);await page.keyboard.press('Enter');assert.equal(await page.evaluate(()=>LindFieldTraining.lastInteraction?.id),'train_dummy');
  await page.screenshot({path:`${dir}/step${step}-training-${w}.png`});
 }
 await page.evaluate(()=>LindFieldReview.close());assert.equal(await page.evaluate(()=>LindFieldAnimals.active),false);
 if(step>=6)assert.equal(await page.evaluate(()=>blockedWorld(1500,1340)),true,'review deck cannot change live river collision');
 const pos=await page.evaluate(()=>LindFieldAnimals.actors.map(a=>a.x));await page.clock.runFor(1000);assert.deepEqual(await page.evaluate(()=>LindFieldAnimals.actors.map(a=>a.x)),pos,'actors stop outside DEV placement');
 const restored=await page.evaluate(()=>({px,py,target,room,stage:storyStage,flags:JSON.stringify(flags),storage:JSON.stringify({...localStorage}),z:pl.style.zIndex,display:inside.style.display}));assert.deepEqual(restored,saved);
 assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);
 results.push({viewport:[w,h],step,loads,animals,walking,collision,reviewRestore:true,boundedBehavior:true,wind:step>=5,river:step>=6,training:step>=7,image404:bad.length,jsExceptions:errors.length});
 await page.close();console.log(`STEP ${step} ${w}x${h} PASS`);
 } fs.writeFileSync(`${dir}/step${step}-qa.json`,JSON.stringify(results,null,2));
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
