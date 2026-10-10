/* Manual PNG ground-contact fixtures + browser input, live navigation and depth QA.
 * No production code is replaced. Browser clock bounds deterministic route tests. */
const {chromium}=require('playwright');
const assert=require('assert/strict'),fs=require('fs'),path=require('path');
const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,'front-fixtures.json')));
const out=process.env.FRONT_QA_OUT||'/tmp/lind-front-qa';fs.mkdirSync(out,{recursive:true});
const views=JSON.parse(process.env.FRONT_QA_VIEWS||'[[1280,720],[1920,1080],[844,390],[390,844]]');
const ids=process.env.FRONT_QA_ONLY?.split(',');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox'],...(process.env.LIND_QA_PUBLIC?{proxy:{server:process.env.HTTPS_PROXY}}:{})});
 const results=[];
 try{for(const [width,height]of views){
  const page=await browser.newPage({viewport:{width,height},hasTouch:width<1000});
  const errors=[],bad=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  page.on('response',r=>{if(r.status()>=400)bad.push(r.url());});
  await page.goto(process.env.LIND_QA_URL||'http://127.0.0.1:8015');
  await page.evaluate(()=>AidanFieldActor.ready());
  await page.clock.install();await page.clock.pauseAt(new Date(Date.now()+1000));
  const saved=await page.evaluate(()=>({px,py,stage:storyStage,room,flags:JSON.stringify(flags),storage:JSON.stringify({...localStorage})}));
  await page.evaluate(()=>LindFieldReview.open());
  await page.locator('#lindReviewLayer img').evaluateAll(async images=>{
   images.forEach(i=>i.loading='eager');await Promise.all(images.map(i=>i.decode()));
  });
  assert.equal(await page.getByLabel('フィールドカメラ倍率').inputValue(),'1');
  assert.deepEqual(await page.evaluate(()=>FieldCollision.footprint),{x:6,y:32,width:22,height:10,anchorX:17,anchorY:42});
  const subjects=fixtures.filter(f=>!ids||ids.includes(f.id));
  const scaleRows=[];
  async function position(x,y){await page.evaluate(({x,y})=>{
   target=null;FieldNavigation.cancel();px=x;py=y;document.activeElement?.blur();camera();
  },{x,y});await page.clock.runFor(20);}
  async function clickAt(x,y){
   const q=await page.evaluate(({x,y})=>{const r=world.getBoundingClientRect(),s=FieldCamera.scale;
    return{x:r.left+(x+17)*s,y:r.top+(y+42)*s};},{x,y});
   const toolbar=await page.locator('#lindReviewControls').boundingBox();
   assert.ok(q.x>0&&q.x<width&&q.y>toolbar.y+toolbar.height&&q.y<height,'visible pointer target '+JSON.stringify(q));
   if(width<1000)await page.touchscreen.tap(q.x,q.y);else await page.mouse.click(q.x,q.y);
  }
  async function arrive(label){
   await page.evaluate(()=>LindFieldReview.collisionDebug.setEnabled(false));
   for(let n=0;n<14&&await page.evaluate(()=>Boolean(target));n++)await page.clock.runFor(250);
   assert.equal(await page.evaluate(()=>target),null,label+' target settles');
   const outcome=await page.evaluate(()=>FieldNavigation.status.outcome);
   if(outcome!=='arrived'){const diagnostic=await page.evaluate(()=>({px,py,target,nav:FieldNavigation.status,staticBlocked:LindFieldReview.collisionModel.blocked(px,py),animalBlocked:LindFieldAnimals.blocked(px,py),npcBlocked:LindFieldNPCs.blocked(px,py),animals:LindFieldAnimals.actors.map(a=>({id:a.id,x:a.x,foot:a.foot,state:a.state}))}));fs.writeFileSync(path.join(out,'route-failure.json'),JSON.stringify({label,outcome,diagnostic},null,2));}
   assert.equal(outcome,'arrived',label);
   assert.equal(await page.evaluate(()=>blockedWorld(px,py)),false,label+' final ground clear');
   await page.evaluate(()=>LindFieldReview.collisionDebug.setEnabled(true));
   await page.clock.runFor(130);
  }
  for(const scale of JSON.parse(process.env.FRONT_QA_SCALES||'[1,1.5,1.8,2.1]')){
   const beforeScale=await page.evaluate(()=>({px,py}));
   await page.getByLabel('フィールドカメラ倍率').selectOption(String(scale));
   assert.deepEqual(await page.evaluate(()=>({px,py})),beforeScale);
   await page.evaluate(()=>LindFieldReview.collisionDebug.setEnabled(true));
   const records=[];
   for(const fixture of subjects){
    const object=await page.evaluate(id=>LindFieldAssets.objects.find(o=>o.id===id),fixture.id);
    const shapes=await page.evaluate(id=>LindFieldReview.collisionModel.shapes.filter(s=>s.objectId===id),fixture.id);
    assert.ok(shapes.some(s=>s.role==='building'));assert.ok(shapes.some(s=>s.role==='front-prop'));
    const box={left:Math.min(...shapes.map(s=>s.x)),right:Math.max(...shapes.map(s=>s.x+s.width)),
     top:Math.min(...shapes.map(s=>s.y)),bottom:Math.max(...shapes.map(s=>s.y+s.height))};
    const door={x:object.x+fixture.door[0]*object.width-17,y:object.y+fixture.door[1]*object.height-42};
    const contacts=await page.evaluate(({o,f})=>f.contacts.map(([nx,ny])=>blockedWorld(o.x+nx*o.width-17,o.y+ny*o.height-42)),{o:object,f:fixture});
    assert.ok(contacts.every(Boolean),'manual front ground contacts '+fixture.id);
    assert.equal(await page.evaluate(q=>blockedWorld(q.x,q.y),door),false,'manual door sample '+fixture.id);
    // Ten requested approaches; Arrow/WASD share the actual keyboard event handler.
    const approaches=await page.evaluate(({o,box,door})=>{
     function key(k,type='keydown'){document.body.dispatchEvent(new KeyboardEvent(type,{key:k,bubbles:true}));}
     function free(anchor,dx,dy){for(const extra of[0,8,16,24,40,64,96])for(const side of[0,-12,12,-24,24,-40,40]){
      const x=anchor.x-dx*extra+(dy?side:0)-17,y=anchor.y-dy*extra+(dx?side:0)-42;
      if(x>=0&&x<=2160&&y>=0&&y<=1500&&!blockedWorld(x,y))return{x,y};
     }throw Error('No free approach '+o.id);}
     const directions=[['LEFT',{x:box.left-24,y:(box.top+box.bottom)/2},1,0],
      ['RIGHT',{x:box.right+24,y:(box.top+box.bottom)/2},-1,0],
      ['FRONT LEFT',{x:o.x+o.width*.25,y:box.bottom+24},0,-1],
      ['FRONT CENTER',{x:o.x+o.width*.5,y:box.bottom+24},0,-1],
      ['FRONT RIGHT',{x:o.x+o.width*.84,y:box.bottom+24},0,-1],
      ['DOOR',{x:door.x+17,y:box.bottom+24},0,-1],
      ['DOOR LEFT',{x:door.x-20,y:box.bottom+24},1,-1],
      ['DOOR RIGHT',{x:door.x+54,y:box.bottom+24},-1,-1],
      ['CORNER LEFT',{x:box.left-24,y:box.bottom+24},1,-1],
      ['CORNER RIGHT',{x:box.right+24,y:box.bottom+24},-1,-1]];
     document.activeElement?.blur();const result=[];
     for(const mode of['arrow','wasd'])for(const[name,anchor,dx,dy]of directions){
      const start=free(anchor,dx,dy);px=start.x;py=start.y;target={x:px+10,y:py+10};
      const keys=[];if(dx)keys.push(mode==='arrow'?(dx>0?'ArrowRight':'ArrowLeft'):(dx>0?'d':'a'));
      if(dy)keys.push(mode==='arrow'?(dy>0?'ArrowDown':'ArrowUp'):(dy>0?'s':'w'));
      for(let n=0;n<8;n++)for(const k of keys){const x=px,y=py;key(k);
       if(LindFieldReview.collisionModel.blocked(px,py)||LindFieldRiver.blocked(px,py))throw Error(o.id+' penetration '+name);
       if(Math.hypot(px-x,py-y)>26)throw Error(o.id+' teleport '+name);
       if(target!==null)throw Error('Manual target cancellation failed');
      }
      keys.forEach(k=>key(k,'keyup'));const stuck={px,py};
      for(const k of keys){const opposite={ArrowLeft:'ArrowRight',ArrowRight:'ArrowLeft',ArrowUp:'ArrowDown',ArrowDown:'ArrowUp',a:'d',d:'a',w:'s',s:'w'}[k];key(opposite);key(opposite,'keyup');}
      if(Math.hypot(px-stuck.px,py-stuck.py)===0)throw Error(o.id+' stuck '+name);
      result.push({name,mode,penetration:false,escape:true});
     }
     return result;
    },{o:object,box,door});assert.equal(approaches.length,20);
    // Stop under the first independently measured prop's ground-contact line.
    const [nx,base]=fixture.contacts[0];
    const frontStart=await page.evaluate(({o,nx,box})=>{
     for(const offset of[24,32,48,64]){const x=o.x+nx*o.width-17,y=box.bottom+offset-42;if(!blockedWorld(x,y))return{x,y};}
     throw Error('No front stop start '+o.id);
    },{o:object,nx,box});await position(frontStart.x,frontStart.y);
    for(let n=0;n<12;n++)await page.keyboard.down('ArrowUp');await page.keyboard.up('ArrowUp');await page.clock.runFor(150);
    const stop=await page.evaluate(()=>({x:px,y:py,feetTop:py+32,anchor:py+42,z:Number(pl.style.zIndex)}));
    const actualGround=object.y+base*object.height;
    assert.ok(stop.feetTop>=actualGround-2,'front stop before PNG ground line '+fixture.id+' '+JSON.stringify({stop,actualGround}));
    assert.ok(stop.feetTop<=actualGround+8,'front stop not excessively far '+fixture.id+' '+JSON.stringify({stop,actualGround}));
    assert.ok(stop.z>=Math.round(object.depthY),'front actor paints above facade '+fixture.id);
    if(scale===2.1)await page.screenshot({path:path.join(out,fixture.id+'-front-contact.png')});
    // Real click/tap from straight and both sides into the central steps/approach.
    for(const offset of[0,-40,40]){
     const start=await page.evaluate(({door,offset})=>{for(const dy of[35,40,45,50,55]){const q={x:door.x+offset,y:door.y+dy};if(!blockedWorld(q.x,q.y))return q;}throw Error('No door route start');},{door,offset});
     await position(start.x,start.y);await clickAt(door.x,door.y);assert.ok(await page.evaluate(()=>target),'door route '+fixture.id);
     await arrive(fixture.id+' door '+offset);
     assert.ok(await page.evaluate(({door,depth})=>Math.hypot(px-door.x,py-door.y)<4&&Number(pl.style.zIndex)>Math.round(depth),{door,depth:object.depthY}),'door ground/depth '+fixture.id);
    }
    if(scale===2.1){await page.screenshot({path:path.join(out,fixture.id+'-door-on.png')});await page.evaluate(()=>LindFieldReview.collisionDebug.setEnabled(false));await page.screenshot({path:path.join(out,fixture.id+'-door-off.png')});await page.evaluate(()=>LindFieldReview.collisionDebug.setEnabled(true));}
    // A real blocked front-prop pointer destination must not consume a route or push inside.
    const solid=await page.evaluate(({o,f})=>{
     // Aim inside a prop, not an NPC button's edge. Chrome touch adjustment
     // legitimately activates nearby interactive targets; do not change NPC UX.
     const worldRect=world.getBoundingClientRect(),scale=FieldCamera.scale;
     const hits=[...document.querySelectorAll('.lind-npc-interaction,.lind-training-interaction,.lind-stone-interaction')]
      .map(el=>{const r=el.getBoundingClientRect();return{x:(r.left-worldRect.left)/scale,y:(r.top-worldRect.top)/scale,
       width:r.width/scale,height:r.height/scale};});
     for(let i=0;i<f.contacts.length;i++){
      const [nx,ny]=f.contacts[i],anchor={x:o.x+nx*o.width,y:o.y+ny*o.height-8};
      if(hits.some(r=>Math.hypot(Math.max(r.x-anchor.x,0,anchor.x-r.x-r.width),
        Math.max(r.y-anchor.y,0,anchor.y-r.y-r.height))<24))continue;
      if(blockedWorld(anchor.x-17,anchor.y-42))return{x:anchor.x-17,y:anchor.y-42,contactIndex:i};
     }throw Error('No unobstructed solid pointer sample '+o.id);
    },{o:object,f:fixture});
    const solidStart=await page.evaluate(solid=>{for(const dy of[30,35,40,45]){
     const q={x:solid.x,y:solid.y+dy};if(!blockedWorld(q.x,q.y))return q;
    }throw Error('No clear solid approach');},solid);
    await position(solidStart.x,solidStart.y);
    await clickAt(solid.x,solid.y);assert.equal(await page.evaluate(()=>target),null);assert.equal(await page.evaluate(()=>FieldNavigation.status.outcome),'blocked-destination');
    assert.deepEqual(await page.evaluate(()=>({x:px,y:py})),solidStart);
    // Real visible destination behind the building's left/back corner.
    const rear=await page.evaluate(({box})=>{
     const options=[];for(const startY of[box.top+28,box.top-10,box.bottom+20,box.bottom+48])for(const side of[-1,1])for(const extra of[0,8,16,24,32,48]){
      const edge=side<0?box.left:box.right;
      const start={x:edge+side*(18+extra)-17,y:startY-42};
      const goal={x:edge-side*28-17,y:box.top-14-42-extra};
      if(!blockedWorld(start.x,start.y)&&!blockedWorld(goal.x,goal.y))options.push({start,goal});
     }if(!options.length)throw Error('No rear route');return options[0];
    },{box});await position(rear.start.x,rear.start.y);await clickAt(rear.goal.x,rear.goal.y);await arrive(fixture.id+' behind');
    const trace={frames:0,violations:[]};
    // Shared geometry remains aligned in rendered screen space; compare every current subject part.
    await page.clock.runFor(20);const alignment=await page.evaluate(id=>{const r=world.getBoundingClientRect(),scale=FieldCamera.scale;return LindFieldReview.collisionModel.shapes.filter(s=>s.objectId===id).map(s=>{const el=[...document.querySelectorAll('[data-collision-id]')].find(e=>e.dataset.collisionId===s.id),q=el.getBoundingClientRect();return Math.max(Math.abs(q.left-r.left-s.x*scale),Math.abs(q.top-r.top-s.y*scale),Math.abs(q.width-s.width*scale),Math.abs(q.height-s.height*scale));});},fixture.id);
    assert.ok(alignment.every(v=>v<.04));
    records.push({id:fixture.id,groundContacts:contacts.length,approaches:approaches.length,frontStop:stop,groundLine:actualGround,doorPointerDirections:3,doorDepth:true,blockedPointer:true,blockedPointerPoint:solid,behindPointer:true,perimeterLaps:0,traceFrames:trace.frames,penetrations:0,overlayMaxError:Math.max(...alignment)});
    fs.writeFileSync(path.join(out,'front-progress.json'),JSON.stringify({viewport:[width,height],completedScales:scaleRows,currentScale:scale,buildings:records},null,2));
    console.log(width+'x'+height+' '+scale+' '+fixture.id+' front/door/corners/contact/input PASS');
   }
   await page.evaluate(()=>LindFieldReview.collisionDebug.setEnabled(false));const frames=await page.evaluate(()=>LindFieldReview.collisionDebug.status.renders);await page.clock.runFor(500);assert.equal(await page.evaluate(()=>LindFieldReview.collisionDebug.status.renders),frames);
   scaleRows.push({scale,buildings:records,debugOffRenders:0});
  }
  for(let n=0;n<20;n++)await page.locator('.field-collision-toggle').click();assert.equal(await page.locator('.field-collision-debug').count(),1);
  await page.evaluate(()=>LindFieldReview.close());assert.deepEqual(await page.evaluate(()=>({px,py,stage:storyStage,room,flags:JSON.stringify(flags),storage:JSON.stringify({...localStorage})})),saved);
  assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);results.push({viewport:[width,height],browserZoom:1,scales:scaleRows,image404:0,jsExceptions:0,consoleErrors:0,stateAndSavePreserved:true});await page.close();
 }
 fs.writeFileSync(path.join(out,'front-qa.json'),JSON.stringify(results,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
