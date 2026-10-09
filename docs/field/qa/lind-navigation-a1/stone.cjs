const{chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs');
const out='/workspace/onboarding/lind-navigation';
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const rows=[];
try{for(const[w,h]of[[1280,720],[844,390],[390,844]]){
const p=await browser.newPage({viewport:{width:w,height:h},hasTouch:w<1000}),errors=[],bad=[];p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('response',r=>{if(r.status()>=400)bad.push(r.url())});
await p.goto('http://127.0.0.1:8015');await p.waitForFunction(()=>window.LindFieldWindStone);await p.clock.install();await p.clock.pauseAt(new Date(Date.now()+1000));
const saved=await p.evaluate(()=>({stage:storyStage,flags:JSON.stringify(flags),storage:JSON.stringify({...localStorage}),px,py}));
await p.evaluate(()=>{LindFieldReview.open();LindFieldReview.focus('lind_wind_stone')});await p.clock.runFor(100);
const loads=await p.evaluate(async()=>Promise.all(Object.values(LindFieldWindStone.paths).map(path=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve({path,ok:true});i.onerror=()=>resolve({path,ok:false});i.src=path}))));assert.ok(loads.every(i=>i.ok));
const object=await p.evaluate(()=>LindFieldWindStone.object);assert.ok(object.x>=570&&object.x+object.width<=920&&object.y>=430&&object.y+object.height<=730);assert.ok(object.height>44&&object.width<150);
const geometry=[];
for(const state of ['NORMAL','GLOW','OFF']){
 await p.locator('#lindWindStoneState').selectOption(state);assert.equal(await p.evaluate(()=>LindFieldWindStone.state),state);
 assert.equal(await p.locator('.lind-wind-stone img:visible').getAttribute('data-stone-state'),state);
 geometry.push(await p.locator('.lind-wind-stone').boundingBox());
 await p.screenshot({path:`${out}/stone-${state.toLowerCase()}-${w}.png`});
}
assert.deepEqual(geometry[0],geometry[1]);assert.deepEqual(geometry[1],geometry[2]);
assert.equal(await p.evaluate(()=>LindFieldEnvironment.wind),false);
assert.equal(await p.locator('.lind-stone-leaf').first().evaluate(e=>getComputedStyle(e).display),'none');
assert.ok(await p.locator('.lind-wind-driven').evaluateAll(els=>els.every(e=>getComputedStyle(e).animationPlayState==='paused')));
const water=p.locator('.lind-water-flow'),before=await water.evaluate(e=>getComputedStyle(e).backgroundPosition);await p.clock.runFor(1000);assert.notEqual(await water.evaluate(e=>getComputedStyle(e).backgroundPosition),before);assert.equal(await water.evaluate(e=>getComputedStyle(e).animationPlayState),'running');
await p.locator('#lindWindToggle').click();assert.equal(await p.evaluate(()=>LindFieldWindStone.state),'GLOW');
await p.locator('#lindWindStoneState').selectOption('NORMAL');await p.locator('#lindWindToggle').click();assert.equal(await p.evaluate(()=>LindFieldWindStone.state),'OFF');await p.locator('#lindWindToggle').click();assert.equal(await p.evaluate(()=>LindFieldWindStone.state),'NORMAL');
await p.evaluate(()=>LindFieldReview.focus('lind_wind_stone'));
const hit=p.locator('[data-interaction-id="lind_wind_stone"]');if(w<1000)await hit.tap();else await hit.click();assert.equal(await p.evaluate(()=>LindFieldWindStone.lastInteraction?.reviewOnly),true);assert.ok(await p.locator('#lindStoneNotice').isVisible());await p.evaluate(()=>LindFieldWindStone.clear());await p.keyboard.press('Enter');assert.equal(await p.evaluate(()=>LindFieldWindStone.lastInteraction?.id),'lind_wind_stone');
assert.equal(await p.evaluate(()=>storyStage),saved.stage);assert.equal(await p.evaluate(()=>JSON.stringify(flags)),saved.flags);assert.equal(await p.evaluate(()=>JSON.stringify({...localStorage})),saved.storage);
const physical=await p.evaluate(()=>{const o=LindFieldWindStone.object,c=o.collision;return {blocked:blockedWorld(o.x+c[0]+c[2]/2-17,o.y+c[1]+c[3]/2-37),around:[[-35,120],[100,120],[30,140],[30,50]].map(([dx,dy])=>!blockedWorld(o.x+dx,o.y+dy)),approach:FieldMovement.advance(o.x+30,o.y+145,0,-70,blockedWorld)}});assert.equal(physical.blocked,true);assert.ok(physical.around.every(Boolean));assert.ok(physical.approach.stopped&&physical.approach.y>object.y+80);
assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
const controls=await p.locator('#lindReviewControls').boundingBox();assert.ok(controls.x>=0&&controls.x+controls.width<=w&&controls.y+controls.height<h/2);assert.ok((await p.locator('.lind-wind-stone').boundingBox()).y>controls.y+controls.height,'notice does not cover monument');
 await p.evaluate(()=>LindFieldWindStone.clear());const cleanControls=await p.locator('#lindReviewControls').boundingBox(), stone=await p.locator('.lind-wind-stone').boundingBox();assert.ok(stone.y>cleanControls.y+cleanControls.height,'full monument below controls');assert.ok(stone.x>=0&&stone.x+stone.width<=w&&stone.y+stone.height<=h,'whole stone visible');
await p.emulateMedia({reducedMotion:'reduce'});assert.equal(await p.locator('.lind-stone-leaf').first().evaluate(e=>getComputedStyle(e).animationName),'none');
await p.evaluate(()=>LindFieldReview.close());assert.deepEqual(await p.evaluate(()=>({stage:storyStage,flags:JSON.stringify(flags),storage:JSON.stringify({...localStorage}),px,py})),saved);
assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);rows.push({viewport:[w,h],loads,object,geometry,physical,controls,allStates:true,windSync:true,waterContinues:true,interaction:w<1000?'tap + Enter':'click + Enter',saveUnchanged:true,noHorizontalOverflow:true,reducedMotion:true,image404:0,jsExceptions:0,consoleErrors:0});await p.close();console.log(`${w}x${h} stone state/collision/interaction/wind/water PASS`);
}fs.writeFileSync(`${out}/stone-runtime-qa.json`,JSON.stringify(rows,null,2));}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
