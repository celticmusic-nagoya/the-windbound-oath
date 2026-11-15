'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('js/hidden-checkpoints.js','utf8');
function setup(){const data=new Map([['windbound_oath_slot_v1_01','manual']]);const window={localStorage:{getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v)}};vm.runInNewContext(source,{window});return {api:window.HiddenCheckpoints,data}}
const payload=JSON.stringify({version:30,prologue:{version:2,storyStage:9,moss:{map:'forest',x:4,y:5}},inventory:{},members:{aidan:{joined:true}},active:['aidan'],battleItems:{potion:1}});
const safe={storyStage:9,mapId:'forest',x:4,y:5,inBattle:false,transitioning:false,forcedEncounter:false,canEscape:true,canRecover:true};
const retry={storyStage:9,mapId:'forest',x:4,y:5,inBattle:false,transitioning:false,encounterId:'fieldGob1',canAvoidEncounter:true};
test('safe slot 21 and retry slot 22 are separate from manual slots',()=>{const {api,data}=setup();assert.equal(api.write('safe',payload,safe),true);assert.equal(api.write('retry',payload,retry),true);assert.equal(api.read('safe').ok,true);assert.equal(api.read('retry').ok,true);assert.equal(data.get('windbound_oath_slot_v1_01'),'manual');assert.equal(data.size,3)});
test('unsafe map entry cannot replace last safe checkpoint',()=>{const {api,data}=setup();assert.equal(api.write('safe',payload,safe),true);const before=data.get(api.key('safe'));assert.equal(api.write('safe',payload,{...safe,forcedEncounter:true}),false);assert.equal(api.write('safe',payload,{...safe,canRecover:false}),false);assert.equal(data.get(api.key('safe')),before)});
test('retry requires avoidable encounter and prebattle state',()=>{const {api}=setup();assert.equal(api.write('retry',payload,{...retry,canAvoidEncounter:false}),false);assert.equal(api.write('retry',payload,{...retry,inBattle:true}),false);assert.equal(api.read('retry').ok,false)});
test('rejects corrupt and inconsistent checkpoint',()=>{const {api,data}=setup();assert.equal(api.write('safe',payload,safe),true);const record=JSON.parse(data.get(api.key('safe')));record.storyStage=10;data.set(api.key('safe'),JSON.stringify(record));assert.equal(api.read('safe').ok,false)});

test('browser loads hidden storage module but never exposes unverified restore',()=>{const html=fs.readFileSync('index.html','utf8'),combat=fs.readFileSync('js/prologue-combat.js','utf8');assert.match(html,/src="js\/hidden-checkpoints\.js/);assert.match(html,/src="js\/battle-checkpoint\.js/);assert.doesNotMatch(combat,/onRetry:\(\)=>|onContinue:\(\)=>/)});

test('manual save and hidden checkpoints share one v30 serializer without automatic writes',()=>{const html=fs.readFileSync('index.html','utf8');assert.match(html,/function serializeCheckpointGrowthData\(\)/);assert.match(html,/const raw=serializeCheckpointGrowthData\(\)/);assert.match(html,/SaveSlots\.save\(slot,raw,\{overwrite:!!old\}\)/);assert.doesNotMatch(html,/HiddenCheckpoints\.write\(/)});

test('rejects mismatched map coordinates and incomplete party data',()=>{const {api}=setup();assert.equal(api.write('safe',payload,{...safe,x:100}),false);assert.equal(api.write('safe',JSON.stringify({version:30,prologue:{version:2,storyStage:9,moss:{map:'forest',x:4,y:5}}}),safe),false)});

test('read-only field readiness probe checks map consistency and does not write checkpoints',()=>{const html=fs.readFileSync('index.html','utf8');const a=html.indexOf('function inspectHiddenCheckpointField()'),b=html.indexOf('function serializeCheckpointGrowthData()',a);assert.ok(a>=0&&b>a);const source=html.slice(a,b);const context={window:{MossForest:{active:true,busy:false,entering:false,recoveryRequired:false,canSave:true,mapId:'forest',checkpointHazards:()=>({clear:true}),checkpointRecovery:()=>({canEscape:true,canRecover:true}),snapshot:()=>({map:'forest',x:4,y:5})},BattleLoading:{canSave:true}},forestActive:true,LoadCoordinator:{canSave:true},document:{body:{classList:{contains:()=>false}}},rildeReturnActive:false,PrologueProgress:{serialize:()=>({version:2,storyStage:9,moss:{map:'forest',x:4,y:5}})},storyStage:9};vm.createContext(context);vm.runInContext(source,context);assert.equal(context.inspectHiddenCheckpointField().ok,true);context.window.MossForest.snapshot=()=>({map:'forest',x:4,y:99});assert.equal(context.inspectHiddenCheckpointField().ok,false);context.window.MossForest.busy=true;assert.equal(context.inspectHiddenCheckpointField().ok,false);assert.doesNotMatch(source,/HiddenCheckpoints\\.write/)});

test('hazard probe blocks unknown and dangerous field states',()=>{const html=fs.readFileSync('index.html','utf8');const a=html.indexOf('function inspectHiddenCheckpointField()'),b=html.indexOf('function serializeCheckpointGrowthData()',a);const context={window:{MossForest:{active:true,busy:false,entering:false,recoveryRequired:false,canSave:true,mapId:'forest',snapshot:()=>({map:'forest',x:4,y:5})},BattleLoading:{canSave:true}},forestActive:true,LoadCoordinator:{canSave:true},document:{body:{classList:{contains:()=>false}}},rildeReturnActive:false,PrologueProgress:{serialize:()=>({version:2,storyStage:9,moss:{map:'forest',x:4,y:5}})},storyStage:9};vm.createContext(context);vm.runInContext(html.slice(a,b),context);assert.equal(context.inspectHiddenCheckpointField().ok,false);context.window.MossForest.checkpointHazards=()=>({clear:false,reason:'enemy-nearby'});assert.equal(context.inspectHiddenCheckpointField().ok,false);context.window.MossForest.checkpointHazards=()=>({clear:true});assert.equal(context.inspectHiddenCheckpointField().ok,false);context.window.MossForest.checkpointRecovery=()=>({canEscape:true,canRecover:false});assert.equal(context.inspectHiddenCheckpointField().ok,false);context.window.MossForest.checkpointRecovery=()=>({canEscape:true,canRecover:true});assert.equal(context.inspectHiddenCheckpointField().ok,true)});

test('runtime hazard probe rejects unverified roaming monsters and active random encounters',()=>{const source=fs.readFileSync('js/field/moss-forest-runtime.js','utf8');assert.match(source,/dynamic-enemies-unverified/);assert.match(source,/random-encounter-zone/);assert.match(source,/!enc\.off/);assert.match(source,/FieldMonsters\?\.checkpointClearance\?\./)});

test('roaming monster clearance uses current positions and alert states',()=>{const source=fs.readFileSync('js/field/field-monsters.js','utf8');assert.match(source,/function checkpointClearance\(x,y,radius=280\)/);assert.match(source,/Math\.hypot\(x-m\.x,y-m\.y\)<=safeRadius/);assert.match(source,/\['engage','engaged','alert','chase','windup','rush'\]/);assert.match(source,/monster-context-unavailable/)});

test('roaming checkpoint clearance accounts for goblin detection and boar charge',()=>{const source=fs.readFileSync('js/field/field-monsters.js','utf8');assert.match(source,/Math\.max\(radius,Number\.isFinite\(m\.t\?\.detect\)\?m\.t\.detect\+64:Infinity\)/);assert.match(source,/\['engage','engaged','alert','chase','windup','rush'\]/)});

test('live roaming clearance rejects nearby, charging, and unknown monsters',()=>{
 const src=fs.readFileSync('js/field/field-monsters.js','utf8');
 const a=src.indexOf('function checkpointClearance('),b=src.indexOf('window.FieldMonsters = Object.freeze(',a);
 assert.ok(a>=0&&b>a);
 const monsters=[{state:'wander',x:450,y:0,lv:0,t:{detect:420}}];
 const context={ctx:{level:()=>0},list:monsters};
 vm.createContext(context);vm.runInContext(src.slice(a,b),context);
 assert.equal(context.checkpointClearance(0,0).clear,false);
 monsters[0].x=600;assert.equal(context.checkpointClearance(0,0).clear,true);
 monsters[0].state='rush';assert.equal(context.checkpointClearance(0,0).clear,false);
 monsters[0].state='wander';monsters[0].t.detect=undefined;assert.equal(context.checkpointClearance(0,0).clear,false);
 context.ctx=null;assert.equal(context.checkpointClearance(0,0).clear,false);
});

test('checkpoint probe rejects queued movement, encounter latches and auto-firing interact events',()=>{const source=fs.readFileSync('js/field/moss-forest-runtime.js','utf8');const a=source.indexOf('function checkpointHazards()');const b=source.indexOf('window.MossForest=Object.freeze(',a);assert.ok(a>=0&&b>a);const body=source.slice(a,b);assert.match(body,/S\.battleLatch\|\|S\.transitionLatch\|\|S\.target\|\|S\.pending\|\|S\.hold\|\|S\.keys\.size/);assert.match(body,/z\.type===\x27interact\x27&&z\.eventId/)});

test('checkpoint event hazard resolves ref-based event geometry like gameplay',()=>{const source=fs.readFileSync('js/field/moss-forest-runtime.js','utf8');const a=source.indexOf('function checkpointHazards()');const b=source.indexOf('window.MossForest=Object.freeze(',a);assert.ok(a>=0&&b>a);assert.match(source.slice(a,b),/inShape\(zoneShape\(z\),fx,fy\)/);assert.match(source,/function zoneShape\(z\)/)});

test('recovery proof explicitly fails closed without verified healing and exit route',()=>{const source=fs.readFileSync('js/field/moss-forest-runtime.js','utf8');const a=source.indexOf('function checkpointRecovery()'),b=source.indexOf('window.MossForest=Object.freeze(',a);assert.ok(a>=0&&b>a);const part=source.slice(a,b);assert.match(part,/reason:'no-rest-zone'/);assert.match(part,/reason:'recovery-action-and-exit-unverified'/);assert.match(source.slice(b,b+1800),/checkpointHazards,checkpointRecovery/);assert.doesNotMatch(part,/canEscape:true|canRecover:true/)});

test('recovery proof executes and rejects rest metadata without a healing action',()=>{
 const source=fs.readFileSync('js/field/moss-forest-runtime.js','utf8');
 const a=source.indexOf('function checkpointRecovery()'),b=source.indexOf('window.MossForest=Object.freeze(',a);
 assert.ok(a>=0&&b>a);
 const S={active:true,busy:false,map:{eventZones:[{type:'rest',id:'camp'}]},forest:{}};
 const sandbox={S,entry:null,recoveryRequired:false,reqOk:()=>true,lvOk:()=>true};
 vm.createContext(sandbox);vm.runInContext(source.slice(a,b),sandbox);
 assert.equal(sandbox.checkpointRecovery().reason,'route-probe-unavailable');
 assert.equal(sandbox.checkpointRecovery().canRecover,false);
 S.map.eventZones=[];assert.equal(sandbox.checkpointRecovery().reason,'no-rest-zone');
 S.active=false;assert.equal(sandbox.checkpointRecovery().reason,'not-ready');
});

test('read-only route probe detects clear, blocked and invalid paths without mutating navigation',()=>{
 const source=fs.readFileSync('js/field/field-navigation.js','utf8');
 const context={window:{},performance:{now:()=>0}};
 vm.createContext(context);vm.runInContext(source,context);
 const nav=context.window.FieldNavigation;
 nav.configure({width:96,height:96,grid:16,maxNodes:1000});
 const before=JSON.stringify(nav.status);
 assert.equal(nav.probeRoute({x:4,y:4},{x:90,y:90},()=>false).reachable,true);
 assert.equal(nav.probeRoute({x:4,y:4},{x:90,y:90},()=>true).reachable,false);
 assert.equal(nav.probeRoute({x:4,y:4},{x:120,y:90},()=>false).reason,'out-of-bounds');
 assert.equal(nav.probeRoute({x:NaN,y:4},{x:90,y:90},()=>false).reason,'invalid-input');
 assert.equal(JSON.stringify(nav.status),before);
});

test('recovery probe checks rest path but never treats it as proof of healing',()=>{
 const src=fs.readFileSync('js/field/moss-forest-runtime.js','utf8');
 const a=src.indexOf('function checkpointRecovery()'),b=src.indexOf('window.MossForest=Object.freeze(',a);
 const S={active:true,busy:false,x:20,y:20,map:{eventZones:[{type:'rest',shape:{x:80,y:80,w:20,h:20}}]},forest:{blocked:()=>false}};
 const calls=[];
 const context={S,entry:null,recoveryRequired:false,FOOT:{ax:17,ay:42},reqOk:()=>true,lvOk:()=>true,zoneShape:z=>z.shape,centerOf:z=>({x:z.x+z.w/2,y:z.y+z.h/2}),window:{FieldNavigation:{probeRoute:(from,to,blocked)=>{calls.push([from,to]);return {reachable:true}}}}};
 vm.createContext(context);vm.runInContext(src.slice(a,b),context);
 assert.equal(context.checkpointRecovery().reason,'recovery-action-and-exit-unverified');
 assert.equal(context.checkpointRecovery().canRecover,false);
 assert.equal(calls.length,1);
 context.window.FieldNavigation.probeRoute=()=>({reachable:false});
 assert.equal(context.checkpointRecovery().reason,'rest-route-unverified');
 S.forest.height={level:0};
 assert.equal(context.checkpointRecovery().reason,'height-route-unverified');
});

test('BATTLE-DEFEAT-01 boundary: defeat callbacks never cold-load from the active battle',()=>{
 const combat=fs.readFileSync('js/prologue-combat.js','utf8');
 const screen=fs.readFileSync('js/gameover-screen.js','utf8');
 const loader=fs.readFileSync('js/save-continue.js','utf8');
 assert.match(combat,/GameOverScreen\?\.show/);
 assert.doesNotMatch(combat,/SaveContinue\.start\(/);
 assert.match(combat,/onLoad:\(\)=>window\.TitleScreen\?\.returnToTitle\(\{openLoad:true\}\)/);
 assert.match(screen,/typeof actions\.onRetry!=='function'/);
 assert.match(screen,/typeof actions\.onContinue!=='function'/);
 assert.match(loader,/if\(phase!=='TITLE'\)return false/);
 assert.match(loader,/rollback\(previous,owner\)/);
});
