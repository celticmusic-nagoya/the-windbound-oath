/* Real screen input + existing navigation sweeps at every QA scale.
 * Route sweeps are stepped deterministically; a separate Aidan suite exercises RAF animation. */
const {chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs');
const out=process.env.LIND_CAMERA_QA_OUT||'/tmp/lind-camera-qa';fs.mkdirSync(out,{recursive:true});
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const rows=[];
try{for(const[w,h]of[[1280,720],[844,390],[390,844],[1920,1080]]){
 const p=await b.newPage({viewport:{width:w,height:h},hasTouch:w<1000}),errors=[],bad=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('response',r=>{if(r.status()>=400)bad.push(r.url())});
 await p.goto(process.env.LIND_QA_URL||'http://127.0.0.1:8015');await p.evaluate(()=>AidanFieldActor.ready());await p.clock.install();await p.clock.pauseAt(new Date(Date.now()+1000));
 const saved=await p.evaluate(()=>({px,py,storage:JSON.stringify({...localStorage}),stage:storyStage}));await p.evaluate(()=>LindFieldReview.open());const selector=p.getByLabel('フィールドカメラ倍率');assert.equal(await selector.inputValue(),'1');
 assert.equal(await p.evaluate(()=>FieldCamera.scale),1);assert.equal(await p.evaluate(()=>visualViewport.scale),1);
 async function position(x,y){await p.evaluate(({x,y})=>{target=null;FieldNavigation.cancel();px=x;py=y;camera()},{x,y});}
 async function clickGoal(x,y){
  // Independent DOM measurement, not the conversion implementation under test.
  const point=await p.evaluate(({x,y})=>{const r=world.getBoundingClientRect(),s=r.width/2200;return{x:Math.round(r.left+(x+17)*s),y:Math.round(r.top+(y+42)*s),left:r.left,top:r.top,scale:s}},{x,y});
  assert.ok(point.x>0&&point.x<w&&point.y>0&&point.y<h,JSON.stringify({w,h,x,y,point}));
  if(w<1000)await p.touchscreen.tap(point.x,point.y);else await p.mouse.click(point.x,point.y);
  const goal=await p.evaluate(()=>target);assert.ok(goal,'screen click sets a destination');
  const expected={x:(point.x-point.left)/point.scale-17,y:(point.y-point.top)/point.scale-42};
  assert.ok(Math.abs(goal.x-expected.x)<.0001&&Math.abs(goal.y-expected.y)<.0001,'inverse screen conversion has zero systematic error');
  const arrived=await p.evaluate(()=>{let steps=0,maxStep=0;while(target&&steps<2000){const before={x:px,y:py},m=FieldNavigation.follow(px,py,target,blockedWorld);if(blockedWorld(m.x,m.y))throw Error('route entered collision');maxStep=Math.max(maxStep,Math.hypot(m.x-before.x,m.y-before.y));px=m.x;py=m.y;target=m.target;camera();steps++;}return{x:px,y:py,target,steps,maxStep,outcome:FieldNavigation.status.outcome};});
  assert.equal(arrived.target,null);assert.equal(arrived.outcome,'arrived');assert.ok(arrived.maxStep<=5.001,'world pointer speed unchanged');assert.ok(Math.hypot(arrived.x-expected.x,arrived.y-expected.y)<=3.01);return{expected,steps:arrived.steps,maxStep:arrived.maxStep};
 }
 const scaleRows=[];
 for(const scale of [1,1.15,1.2,1.25,1.28,1.3,1.35]){
  await position(1100,900);const before=await p.evaluate(()=>({px,py}));await selector.selectOption(String(scale));await p.clock.runFor(20);assert.deepEqual(await p.evaluate(()=>({px,py})),before);
  assert.equal(await p.evaluate(()=>FieldCamera.scale),scale);assert.equal(await p.evaluate(()=>FieldMovement.settings.pointerStep),5);assert.equal(await p.evaluate(()=>FieldMovement.settings.keyboardStep),22.5);
  const center=await p.evaluate(()=>{const r=pl.getBoundingClientRect(),s=FieldCamera.scale,c=document.getElementById('lindReviewControls').getBoundingClientRect(),v=document.getElementById('game').getBoundingClientRect(),vh=Math.min(innerHeight,v.bottom)-v.top;return{x:r.left+17*s,y:r.top+22*s,expectedY:v.top+(vh+Math.min(vh/2,Math.max(0,c.bottom-v.top)))/2,world:world.getBoundingClientRect().toJSON(),sourceHeight:parseFloat(pl.style.height)||44};});
  assert.ok(Math.abs(center.x-w/2)<.01&&Math.abs(center.y-center.expectedY)<.01,'actor centered in unobstructed review viewport');
  const edges=[];for(const[x,y]of[[0,0],[2160,0],[0,1500],[2160,1500],[1100,0],[1100,1500],[0,750],[2160,750]]){await position(x,y);const r=await p.locator('#world').boundingBox(),v=await p.locator('#game').boundingBox();assert.ok(r.x<=v.x+.01&&r.y<=v.y+.01&&r.x+r.width>=Math.min(w,v.x+v.width)-.01&&r.y+r.height>=Math.min(h,v.y+v.height)-.01,'world covers viewport at every map edge/corner');edges.push([x,y]);}
  await position(800,1250);await clickGoal(835,1250);await clickGoal(900,1200);
  // A destination near the visible edge; diagonal and longer route.
  const far=await p.evaluate(()=>{const r=world.getBoundingClientRect(),s=r.width/2200;for(const sx of [innerWidth-25,25])for(const sy of [innerHeight-30,innerHeight*.7,innerHeight*.6]){const x=(sx-r.left)/s-17,y=(sy-r.top)/s-42;if(x>0&&x<2160&&y>0&&y<1500&&!blockedWorld(x,y)&&!document.elementFromPoint(sx,sy)?.closest('button,.npc,.fisher,.door'))return{x,y};}return null;});assert.ok(far);await clickGoal(far.x,far.y);
  const crossings=[];await position(1390,560);for(let n=0;n<5;n++){for(const x of [1480,1560,1660])await clickGoal(x,560);assert.ok(await p.evaluate(()=>px>1630));for(const x of [1560,1480,1390])await clickGoal(x,560);assert.ok(await p.evaluate(()=>px<1420));crossings.push({roundTrip:n+1,pass:true});}
  // Actual arrows/WASD, wall sliding and narrow passage assist use unchanged world steps.
  for(const key of ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','a','d','w','s']){await position(1100,900);await p.keyboard.press(key);const q=await p.evaluate(()=>({px,py}));assert.ok(Math.abs(Math.hypot(q.px-1100,q.py-900)-22.5)<.001);}
  await position(1418,720);await p.keyboard.down('ArrowRight');await p.keyboard.down('ArrowDown');await p.keyboard.up('ArrowRight');await p.keyboard.up('ArrowDown');assert.ok(await p.evaluate(()=>px<=1420.001&&py>735));
  await position(1380,545);for(let n=0;n<17;n++)await p.keyboard.down('ArrowRight');await p.keyboard.up('ArrowRight');assert.ok(await p.evaluate(()=>px>1630&&py>=548&&py<=568));
  await position(1380,800);const blocked=await p.evaluate(()=>{const r=world.getBoundingClientRect(),s=r.width/2200;return{x:r.left+1517*s,y:r.top+852*s};});if(w<1000)await p.touchscreen.tap(blocked.x,blocked.y);else await p.mouse.click(blocked.x,blocked.y);assert.equal(await p.evaluate(()=>target),null);assert.equal(await p.evaluate(()=>FieldNavigation.status.outcome),'blocked-destination');
  for(const id of ['emma','merchant','fisherman']){await p.getByLabel('素材確認場所').selectOption(id);const hit=p.locator(`[data-interaction-id="${id}"]`);if(w<1000)await hit.tap();else await hit.click();assert.equal(await p.evaluate(()=>LindFieldNPCs.lastInteraction?.id),id);await p.evaluate(()=>LindFieldNPCs.clear());await p.keyboard.press('Enter');assert.equal(await p.evaluate(()=>LindFieldNPCs.lastInteraction?.id),id);await p.evaluate(()=>LindFieldNPCs.clear());}
  await p.getByLabel('素材確認場所').selectOption('lind_wind_stone');for(const state of ['NORMAL','GLOW','OFF']){await p.getByLabel('風の石の状態').selectOption(state);assert.equal(await p.evaluate(()=>LindFieldWindStone.state),state);}
  assert.equal(await p.evaluate(()=>LindFieldBirds.status.ground.every(g=>!g.visible)&&LindFieldBirds.status.visibleFlock===0),true);assert.ok(await p.locator('.lind-wind-driven').evaluateAll(es=>es.every(e=>getComputedStyle(e).animationPlayState==='paused')));
  const water=p.locator('.lind-water-flow'),waterBefore=await water.evaluate(e=>getComputedStyle(e).backgroundPosition);await p.clock.runFor(100);assert.notEqual(await water.evaluate(e=>getComputedStyle(e).backgroundPosition),waterBefore);await p.getByLabel('風の石の状態').selectOption('NORMAL');assert.equal(await p.evaluate(()=>LindFieldBirds.status.active&&LindFieldEnvironment.wind),true);
  const stone=p.locator('[data-interaction-id="lind_wind_stone"]');if(w<1000)await stone.tap();else await stone.click();assert.equal(await p.evaluate(()=>LindFieldWindStone.lastInteraction?.id),'lind_wind_stone');await p.clock.runFor(20);const toolbar=await p.locator('#lindReviewControls').boundingBox(),monument=await p.locator('.lind-wind-stone').boundingBox();assert.ok(toolbar.y+toolbar.height<monument.y,'landmark is below toolbar');await p.evaluate(()=>LindFieldWindStone.clear());
  if([1,1.25,1.28,1.3,1.35].includes(scale)){await p.getByLabel('素材確認場所').selectOption('emma');await p.clock.runFor(130);await p.screenshot({path:`${out}/camera-${w}-${scale.toFixed(2)}.png`});}
  scaleRows.push({scale,center:true,edges,cameraRoundTrips:5,worldSpeed:true,pointerConversion:true,keyboard:true,wallSliding:true,cornerAssist:true,blockedDestination:true,npcInput:true,windStone:true,waterContinues:true,crossings});console.log(w+'x'+h+' camera '+scale+' PASS');
 }
 await position(1100,900);await p.evaluate(()=>{target=FieldNavigation.destination(1200,900,blockedWorld)});const held=await p.evaluate(()=>({px,py,target:{...target}}));for(const scale of [1,1.3,1])await selector.selectOption(String(scale));assert.deepEqual(await p.evaluate(()=>({px,py,target:{...target}})),held);
 await selector.selectOption('1.35');await p.evaluate(()=>{target=null;LindFieldReview.close()});assert.equal(await p.evaluate(()=>FieldCamera.scale),1);assert.deepEqual(await p.evaluate(()=>({px,py,storage:JSON.stringify({...localStorage}),stage:storyStage})),saved);
 assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);rows.push({viewport:[w,h],browserZoom:1,scales:scaleRows,positionAndDestinationPreserved:true,reviewExitRestored:true,image404:0,jsExceptions:0,consoleErrors:0});await p.close();
 }fs.writeFileSync(out+'/camera-qa.json',JSON.stringify(rows,null,2));}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
