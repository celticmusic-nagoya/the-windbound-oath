// MORWEN-HD-CANONICAL-V2: registry module unit test (node --test).
const test = require('node:test');
const assert = require('node:assert');
const fs = require('fs');
const M = require('../../js/field/morwen-hd-canonical.js');
const reg = JSON.parse(fs.readFileSync('data/morwen-hd-canonical-v2.json', 'utf8'));

test('four directions resolve to registered display derivatives', () => {
  const r = M.create(reg);
  for (const d of r.directions) {
    const p = r.placeDisplay(d, { height: 1600, footX: 600, footY: 1540 });
    assert.strictEqual(p.left, 0);
    assert.strictEqual(p.top, 0);
    assert.strictEqual(p.width, 1200);
    assert.match(p.src, /hd-v2\/display\/pixel\//);
  }
});

test('anchor correction moves boot centre onto the anchor', () => {
  const r = M.create(reg);
  for (const d of r.directions) {
    const a = r.asset('display.pixel.' + d);
    const p = r.placeDisplay(d, { height: 1600, footX: 600, footY: 1540, anchorCorrection: true });
    assert.ok(Math.abs(p.left + a.measured.foot_center_x - 600) < 1e-9, d);
  }
});

test('scaled placement keeps the foot on the given point', () => {
  const r = M.create(reg);
  const p = r.placeDisplay('left', { height: 80, footX: 17, footY: 42 });
  assert.ok(Math.abs(p.left + 600 * p.scale - 17) < 1e-9);
  assert.ok(Math.abs(p.top + 1540 * p.scale - 42) < 1e-9);
});

test('canonical left is the new pixel left; superseded left is rejected', () => {
  const r = M.create(reg);
  assert.strictEqual(r.canonicalLeft, 'pixel.left');
  assert.strictEqual(r.original('pixel', 'left').sha256, '5d0608bf2d60708325b0cdbb0a75a160e7153365cb402d5b33183c608c7eccf8');
  assert.ok(r.isSuperseded('d858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591'));
  const bad = JSON.parse(JSON.stringify(reg));
  bad.assets['real.left'].sha256 = 'd858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591';
  assert.throws(() => M.create(bad).original('real', 'left'), /superseded/);
});

test('bad schema and direction are rejected', () => {
  assert.throws(() => M.create({ schema: 'x' }), /schema/);
  assert.throws(() => M.create(reg).placeDisplay('up'), /direction/);
});
