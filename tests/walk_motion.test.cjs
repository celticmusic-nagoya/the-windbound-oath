const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.join(__dirname, '..');
function fixture() {
  const s = {WINDBOUND_DEV: true, Image: function () {}, performance: {now: () => 0},
    FieldMovement: {settings: {pointerStep: 5}}, document: {createElement() { throw Error('unexpected DOM creation'); }}};
  s.ForestLoader = {art:{manifest:JSON.parse(fs.readFileSync(path.join(root,'img/field/moss/manifest.json'),'utf8'))}};
  s.requestAnimationFrame = () => 1; s.cancelAnimationFrame = () => {};
  s.window = s; vm.createContext(s);
  for (const f of ['js/field/walk-motion.js', 'js/field/aidan-field-assets.js', 'js/field/fiona-field-assets.js', 'js/field/field-monsters.js', 'js/field/field-walkers.js'])
    vm.runInContext(fs.readFileSync(path.join(root, f), 'utf8'), s);
  return {s, W: s.FieldWalkMotion};
}
test('catalog exposes only real walking allies and implemented field enemies', () => {
  const {W} = fixture();
  assert.deepEqual(Array.from(W.catalog('ally'), x => x.id), ['aidan', 'fiona']);
  assert.equal(W.catalog('enemy').length, 4);
  assert.equal(W.resolve('ally', 'emma', 'down'), null);
});
test('every direction uses exact production metadata and declared direction banks', () => {
  const {s, W} = fixture();
  for (const actor of ['aidan', 'fiona']) for (const dir of ['up', 'down', 'left', 'right']) {
    const def = W.resolve('ally', actor, dir), registry = actor === 'aidan' ? s.AidanFieldAssets : s.FionaFieldAssets;
    assert.ok(def.frames.length >= 4);
    for (const f of def.frames) {
      const source = registry.frames[f.key];
      assert.equal(f.url, source.path); assert.equal(f.scale, source.scale);
      assert.deepEqual(Array.from(f.anchor), Array.from(source.anchor));
      assert.ok(Object.isFrozen(def.frames));
    }
  }
});
test('phase selectors preserve production arithmetic across cycles and frame counts', () => {
  const {W} = fixture();
  for (const count of [4, 6, 11]) for (let i = 0; i < 4000; i++) {
    const d = i * .173;
    for (const stride of [50,72,90,180]) {
      assert.equal(W.phaseDistance(d,count,stride),Math.floor(d/(stride/count))%count);
      assert.equal(W.bob(d,stride).toFixed(2),(-Math.abs(Math.sin(d/(stride/2)*Math.PI))*1.5).toFixed(2));
    }
    assert.equal(W.phaseDistance(d, 4, 48), Math.floor(d / 48 * 4) % 4);
    assert.equal(W.phaseTime(d, count, 7), Math.floor(d * 7) % count);
    assert.equal(W.bob(d).toFixed(2), (-Math.abs(Math.sin(d / 45 * Math.PI)) * 1.5).toFixed(2));
  }
});
test('future ally frame count follows the registry without a DEV frame table', () => {
  const {s, W} = fixture();
  const frames = {...s.AidanFieldAssets.frames};
  frames.aidan_walk_up_07 = frames.aidan_walk_up_06;
  s.AidanFieldAssets = {...s.AidanFieldAssets,frames};
  assert.equal(W.resolve('ally', 'aidan', 'up').frames.length, 7);
});
test('goblin directions, boar walk-only bank and shared flyer bank match game config', () => {
  const {s, W} = fixture();
  for (const dir of ['up', 'down', 'left', 'right']) {
    const d = W.resolve('enemy', 'goblin', dir); assert.equal(d.frames.length, 4);
    assert.ok(d.frames.every(f => f.url.includes(`goblin_walk_${dir}_`))); assert.equal(d.flip, false);
  }
  assert.equal(W.resolve('enemy', 'leafy_boar', 'down'), null);
  assert.equal(W.resolve('enemy', 'leafy_boar', 'left').frames.length, 4);
  assert.equal(W.resolve('enemy', 'forest_bat', 'left'), null);
  const bat = W.resolve('enemy', 'forest_bat', 'left','idle');
  assert.equal(bat.frames.length, s.FieldMonsters.MONSTER_TYPES.forest_bat.art.frames);
  assert.equal(bat.fps, s.FieldMonsters.MONSTER_TYPES.forest_bat.art.fps);
  assert.equal(bat.flip, false);
  assert.equal(W.air(bat.art, .3), bat.art.air + Math.sin(.9) * 4);
});
test('manual frames and speed multipliers use the shared selector', () => {
  const {W} = fixture();
  for (const group of ['ally', 'enemy', 'npc']) for (const actor of W.catalog(group)) for (const dir of ['up', 'down', 'left', 'right']) for (const state of ['walk','idle']) {
    const def = W.resolve(group, actor.id, dir,state); if (!def) continue;
    for (let index = 0; index < def.frames.length; index++) {
      const t = W.frameTime(def, index) + 1e-8;
      assert.equal(W.frameAt(def, t).index, index);
    }
    for (const rate of [.5, 1, 2]) {
      const t = .137 * rate;
      const expected = def.kind === 'distance' ? W.phaseDistance(t * def.speed(), def.frames.length, def.stride) : W.phaseTime(t, def.frames.length, def.fps);
      assert.equal(W.frameAt(def, t).index, expected);
    }
  }
});
test('DEV-disabled UI never installs DOM, input handlers or a timer', () => {
  const s = {window: {WINDBOUND_DEV: false}};
  vm.runInNewContext(fs.readFileSync(path.join(root, 'js/dev/walk-test.js'), 'utf8'), s);
  assert.equal(s.window.DevWalkTest, undefined);
});

test('NPC metadata and missing directions reflect production, including future six-frame soldier', () => {
 const {s,W}=fixture(); assert.ok(W.catalog('npc').length>10);
 const d=W.resolve('npc','soldier','left');assert.ok(d.frames.length>0);assert.equal(d.fps,s.FieldWalkers.describe('soldier').fps);assert.equal(d.flip,true);
 assert.equal(W.resolve('npc','soldier','up'),null);assert.equal(W.resolve('npc','soldier','down'),null);
 assert.equal(W.resolve('npc','soldier','left','idle').frames.length,1);
 const node=s.ForestLoader.art.manifest.node.find(r=>r.match==='^npc_slot_soldier$');node.walk.frames=6;assert.equal(W.resolve('npc','soldier','right').frames.length,6);
 s.MossForest={walkStride:(id,dir)=>id==='aidan'&&dir==='left'?72:90};assert.equal(W.resolve('ally','aidan','left').stride,72);assert.equal(W.resolve('ally','fiona','left').stride,90);
});

test('adopted down bank uses source01/05/02/repaired06 and quarter bob only', () => {
 const {s,W}=fixture(),d=W.ally('aidan','down');
 assert.deepEqual(Array.from(d.frames,f=>f.key),[1,5,2,6].map(n=>'aidan_walk_down_'+String(n).padStart(2,'0')));
 assert.equal(d.stride,90);assert.equal(d.bobScale,.25);assert.equal(d.speed(),300);
 assert.match(d.frames[3].url,/down4\/aidan_walk_down_06_ground.png/);
 for(let i=0;i<100;i++){const t=i*.013;assert.equal(W.frameAt(d,t).lift,-W.bob(t*300,90)*.25);}
 for(const actor of ['aidan','fiona'])for(const dir of ['up','down','left','right']){
  const b=W.ally(actor,dir);if(actor==='aidan'&&dir==='down')continue;assert.equal(b.bobScale,1);
 }
 assert.deepEqual(Array.from(d.frames[3].anchor),[1024,1230]);assert.equal(d.frames[3].scale,.0625);
});

test('director-adopted ARM02 PNG bytes and live slot references are pinned', () => {
 const crypto=require('node:crypto'),{W}=fixture(),d=W.ally('aidan','down');
 for(const [n,h] of [[5,'6c857b4cbf1459df48ecd305b41ffa7f1b7b98a1458b6d2243a8c50c94e17bad'],[2,'614bdeffb8c09b3dbb7e0b688cea21efdfc7b68ccdeea0ddf53694f0bc13824f']]){
  const f=d.frames.find(f=>f.key==='aidan_walk_down_'+String(n).padStart(2,'0'));
  assert.match(f.url,/down4\/arm02\//);assert.ok(!f.url.includes('candidate'));
  assert.equal(crypto.createHash('sha256').update(fs.readFileSync(path.join(root,f.url.split('?')[0]))).digest('hex'),h);
 }
 assert.match(d.frames[0].url,/aidan\/aidan_walk_down_01.png/);assert.match(d.frames[3].url,/down4\/aidan_walk_down_06_ground.png/);
});

test('ARM02 adoption retains the original production adoption history', () => {
 const m=JSON.parse(fs.readFileSync(path.join(root,'img/field/characters/aidan/down4/adopted-walk.json'),'utf8'));
 const old=m.adoption_history[0].files;assert.equal(old.find(f=>f.frame===5).sha256,'6efcfe75cce44aea3a11ae3712c1277d0f324cb384870ed93efe2f6af01404ec');
 assert.equal(old.find(f=>f.frame===2).sha256,'7b5b916807987cf9219488939c1f538aeca9d9f8a21b843d1e70bd27aa31b16d');
 assert.ok(m.files.filter(f=>[5,2].includes(f.frame)).every(f=>f.source_pr===144&&f.path.includes('/arm02/')));
});
