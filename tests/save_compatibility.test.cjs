const path=require('node:path'),assert=require('node:assert/strict');
const {env,save,put}=require(path.resolve(process.argv[2]||path.join(__dirname,'..'),'tests/continue_restore.test.cjs'));
let passed=0;async function test(name,f){await f();console.log('PASS',name);passed++;}
async function ready(){const e=env();await e.complete(e.c.LoadCoordinator.boot(async()=>{}));return e;}
function resave(e){const q=e.c.$;e.c.$=s=>s==='#doSave'?null:q(s);e.c.saveGrowthData();e.c.$=q;return JSON.parse(e.c.localStorage.getItem('slot'));}
(async()=>{
 for(const version of [1,2])for(const stage of [0,1,3,4,5,6,7,8])await test(`legacy v${version} stage${stage} LOAD/SAVE/LOAD normalizes hidden map and keeps history`,async()=>{
  const e=await ready(),c=e.c;await e.complete(e.M.enter({map:'moss_forest_01_sunlit_path',x:300,y:400}));
  const d=save(stage,null);d.prologue.version=version;if(version===1)delete d.prologue.moss;
  d.prologue.legacyEvents={v:1,drawer:false,pot:true,balloon:false,balloonDone:false,cat:false,catFound:false,catDone:false};
  const raw=put(e,d);assert.equal(await e.complete(c.loadGrowthData()),true);assert.equal(c.localStorage.getItem('slot'),raw);
  const prior=JSON.parse(JSON.stringify(e.M.snapshot()));const record=resave(e);
  assert.equal(record.prologue.storyStage,stage);assert.equal(record.prologue.moss.map,null);assert.equal(record.prologue.moss.x,0);assert.equal(record.prologue.moss.y,0);assert.equal(Object.hasOwn(record.prologue.moss,'level'),false);
  assert.deepEqual(record.prologue.moss.opened,prior.opened);assert.deepEqual(record.prologue.moss.fired,prior.fired);
  assert.equal(record.prologue.legacyEvents.drawer,false);assert.equal(record.prologue.legacyEvents.pot,true);
  assert.equal(await e.complete(c.loadGrowthData()),true);assert.equal(c.storyStage,stage);assert.equal(e.M.active,false);
  if(stage===0)assert.equal(e.node('#inside').style.display,'block');
 });
 for(const stage of [0,1,3,9,10,11,12,15])await test(`active field stage${stage} exact map/coordinates/events roundtrip`,async()=>{
  const e=await ready(),d=save(stage,stage===15?'fort_dunvall_03_keep':stage<4?'rilde_in_aidan':'moss_forest_01_sunlit_path');
  put(e,d);assert.equal(await e.complete(e.c.loadGrowthData()),true);assert.equal(e.M.active,true);
  const before=JSON.parse(JSON.stringify(e.M.snapshot())),r=resave(e);
  assert.deepEqual(r.prologue.moss,before);assert.equal(await e.complete(e.c.loadGrowthData()),true);
  assert.equal(e.M.mapId,before.map);assert.equal(e.c.storyStage,stage);assert.deepEqual(JSON.parse(JSON.stringify(e.M.snapshot())),before);
 });
 await test('inactive snapshot drops only destination/position/height, never mutates runtime history',async()=>{
  const e=await ready();await e.complete(e.M.enter({map:'moss_forest_01_sunlit_path',x:300,y:400}));e.M.restoreState({opened:['chest'],fired:['event']});e.M.hide();
  const before=JSON.stringify(e.M.snapshot()),s=e.c.PrologueProgress.serialize();
  assert.equal(s.moss.map,null);assert.equal(s.moss.x,0);assert.equal(s.moss.y,0);assert.equal(JSON.stringify(e.M.snapshot()),before);assert.deepEqual(Array.from(s.moss.opened),['chest']);assert.deepEqual(Array.from(s.moss.fired),['event']);
 });
 for(const version of [1,2])for(const stage of [9,10,11,12])await test(`forest fallback v${version} stage${stage} null/legacy coordinates restores safe map and chest history`,async()=>{
  const e=await ready(),d=save(stage,null);d.prologue.version=version;
  // Migration selects named spawns absent from the generic network fixture. Use the shipped map definitions.
  for(const id of ['moss_forest_01_sunlit_path','moss_forest_03_ancient_grove'])e.worlds.set(id,JSON.parse(require('node:fs').readFileSync(path.join(__dirname,'../data/maps',id+'.json'),'utf8')));
  if(version===1){delete d.prologue.moss;d.prologue.forestChests={fChest1:true};}
  const raw=put(e,d);assert.equal(await e.complete(e.c.loadGrowthData()),true);
  assert.equal(e.c.localStorage.getItem('slot'),raw);assert.equal(e.M.active,true);assert.equal(e.c.storyStage,stage);
  assert.equal(e.M.mapId,stage>=11?'moss_forest_03_ancient_grove':'moss_forest_01_sunlit_path');
  assert.ok(e.M.snapshot().opened.includes('tr_a1_hollow'));
  const record=resave(e);assert.equal(record.prologue.moss.map,e.M.mapId);
  assert.equal(await e.complete(e.c.loadGrowthData()),true);assert.equal(e.c.storyStage,stage);
 });
 console.log(`${passed} PASS; actual SAVE/LOAD; simulated DOM/network`);
})().catch(e=>{console.error('FAIL',e.stack);process.exitCode=1});
