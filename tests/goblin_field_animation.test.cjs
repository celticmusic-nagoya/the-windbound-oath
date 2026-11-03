const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function fixture(type = 'goblin') {
  const element = () => ({style: {}, dataset: {}, children: [], appendChild(e) { this.children.push(e); }, remove() { this.removed = true; }});
  const sandbox = {window: {}, document: {createElement: element}, Image: function () {}, performance: {now: () => 10000}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../js/field/walk-motion.js'), 'utf8'), sandbox);
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../js/field/field-monsters.js'), 'utf8'), sandbox);
  const f = sandbox.window.FieldMonsters;
  const ctx = {foot: {ax: 17, ay: 42}, player: () => ({x: 1000, y: 0}),
    blocked: () => false, canEngage: () => false, slain: new Set(),
    advance: (x, y, dx, dy) => ({x: x + dx, y: y + dy})};
  f.mount({monsters: [{id: 'test', type, x: 0, y: 0}]}, element(), ctx);
  f.list[0].wait = 999;
  return {f, m: f.list[0], ctx};
}

test('four idle frames animate without movement or an extra timer', () => {
  const {f, m} = fixture();
  const seen = new Set();
  for (let n = 0; n < 100; n++) { f.update(1 / 60); seen.add(m.el.dataset.src); }
  assert.equal(seen.size, 4);
  assert.ok([...seen].every(p => /goblin_idle_0[1-4]\.png$/.test(p)));
  assert.equal(m.x, 0);
  assert.equal(m.y, 0);
});

for (const [direction, dx, dy] of [['right', 1, 0], ['left', -1, 0], ['up', 0, -1], ['down', 0, 1]]) {
  test(`${direction}: real movement selects four supplied frames without mirroring`, () => {
    const {f, m} = fixture();
    m.sub = 'walk'; m.goal = [dx * 100, dy * 100];
    const seen = new Set();
    for (let n = 0; n < 60; n++) { f.update(1 / 60); seen.add(m.el.dataset.src); }
    assert.equal(seen.size, 4);
    assert.ok([...seen].every(p => p.includes(`walk_${direction}_`)));
    assert.equal(m.facing, direction);
    assert.ok(Math.hypot(m.x, m.y) > 50);
    assert.ok(!m.el.style.transform.includes('scaleX'));
  });
}

test('a blocked goblin idles rather than walking in place', () => {
  const {f, m, ctx} = fixture();
  ctx.advance = (x, y) => ({x, y}); m.sub = 'walk'; m.goal = [100, 0];
  f.update(1 / 60);
  assert.equal(m.travel, 0);
  assert.match(m.el.dataset.src, /goblin_idle_/);
});

test('freeze, resume, return to idle, clear have no animation owner left over', () => {
  const {f, m} = fixture();
  m.sub = 'walk'; m.goal = [100, 0]; f.update(.1);
  const before = [m.x, m.animTime, m.el.dataset.src];
  f.setFrozen(true); f.update(.1);
  assert.deepEqual([m.x, m.animTime, m.el.dataset.src], before);
  f.setFrozen(false); f.update(.1); assert.ok(m.x > before[0]);
  m.sub = 'rest'; m.wait = 999; f.update(.1);
  assert.match(m.el.dataset.src, /goblin_idle_/);
  f.clear(); f.update(.1); assert.equal(f.list.length, 0);
});

for (const [type, count, token] of [['moss_slime', 6, 'moss_slime_walk_'], ['forest_bat', 4, 'forest_bat_idle_'], ['leafy_boar', 11, 'leafy_boar_']]) {
  test(`${type}: legacy preload and animation selection retained`, () => {
    const {f, m} = fixture(type);
    assert.equal(m.frames.length, count);
    assert.ok(m.el.dataset.src.includes(token));
    assert.equal(m.t.art.directions, undefined);
    m.sub = 'walk'; m.goal = [100, 0]; f.update(.1);
    assert.ok(m.el.dataset.src.includes(token));
  });
}
