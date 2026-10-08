const{chromium}=require('playwright'),assert=require('assert/strict'),fs=require('fs');
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});const rows=[];try{for(const[w,h]of[[1280,720],[844,390],[390,844]]){
 const p=await b.newPage({viewport:{width:w,height:h},hasTouch:w<1000}),errors=[],bad=[];
 p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('response',r=>{if(r.status()>=400)bad.push(r.url())});
 await p.goto('http://127.0.0.1:8015');await p.waitForFunction(()=>window.LindFieldReview);
 const assets=await p.evaluate(async()=>{const paths=[...new Set([...Object.values(BATTLE_ASSETS).flatMap(a=>Object.values(a)),...Object.values(BATTLE_CUTINS)])].filter(p=>typeof p==='string');return Promise.all(paths.map(path=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve({path,ok:true});i.onerror=()=>resolve({path,ok:false});i.src=path})));});assert.ok(assets.every(a=>a.ok),'every registered battle image exists');
 await p.evaluate(()=>{LindFieldReview.open();LindFieldEnvironment.setWind(false)});
 assert.equal(await p.evaluate(()=>LindFieldAssets.objects.filter(o=>o.motion==='wind').every(o=>document.querySelector('[data-asset-id="'+o.id+'"]').classList.contains('lind-wind-driven'))),true);
 await p.evaluate(()=>{LindFieldReview.close();devJump('training');closeDialogue();px=1710;py=845;camera()});
 const dummy=p.locator('#dummy1');if(w<1000)await dummy.tap();else await dummy.click();
 assert.equal(await p.evaluate(()=>storyStage),2);assert.ok(await p.locator('#battle').isVisible());
 await p.evaluate(()=>devJump('raider'));await p.waitForTimeout(1000);
 const geometry=await p.evaluate(()=>{const s=document.querySelector('#raiderSprite'),hud=document.querySelector('#rbEnemyHud');return {sprite:{width:s.offsetWidth,height:s.offsetHeight,left:s.offsetLeft,top:s.offsetTop},hud:{width:hud.offsetWidth,height:hud.offsetHeight,left:hud.offsetLeft,top:hud.offsetTop},hudIndependent:!s.contains(hud),bossHP:rbBoss}});
 assert.equal(geometry.bossHP,1250);assert.equal(geometry.hudIndependent,true);
 const toggle=p.locator('#rbCommandToggle');if(w<1000)await toggle.tap();else await toggle.click();assert.ok(await p.locator('#rbCmd').isVisible());
 const close=p.locator('#rbCommandClose');if(w<1000)await close.tap();else await close.click();assert.equal(await p.locator('#rbCmd').isVisible(),false);
 assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);rows.push({viewport:[w,h],registeredBattleImages:assets.length,legacyTraining:true,mobileTap:w<1000,command:true,geometry,image404:0,jsExceptions:0,consoleErrors:0});await p.close();console.log(`${w}x${h} final live field/tutorial/battle assets/HUD/input PASS`);
 }fs.writeFileSync('/workspace/onboarding/lind-step8/final-live-qa.json',JSON.stringify(rows,null,2));}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
