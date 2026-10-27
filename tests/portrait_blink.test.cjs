// PortraitBlink (timing) and PortraitRegistry (data) — pure logic, fake clock. Run: node --test tests/portrait_blink.test.cjs
const test = require('node:test'), assert = require('node:assert/strict'), vm = require('node:vm'), fs = require('node:fs'), path = require('node:path');
const root = path.join(__dirname, '..');
const PB = require(path.join(root, 'js/field/portrait-blink.js'));
function clock() {
  let t = 0, id = 0; const q = new Map();
  return {
    now: () => t, setTimeout: (f, ms) => { q.set(++id, {at: t + ms, f}); return id; }, clearTimeout: i => q.delete(i), pending: () => q.size,
    advance(ms) { const end = t + ms; for (;;) { let n = null; for (const [k, v] of q) if (v.at <= end && (!n || v.at < n[1].at)) n = [k, v]; if (!n) break; q.delete(n[0]); t = n[1].at; n[1].f(); } t = end; }
  };
}
const V3 = {seq: [[1, 30], [2, 30], [3, 35], [4, 70], [3, 35], [2, 30], [1, 30]], gap: [3000, 6000]};
function make(c, extra = {}) { const log = []; const b = PB.create({...V3, onState: s => log.push([c.now(), s]), setTimeout: c.setTimeout, clearTimeout: c.clearTimeout, now: c.now, ...extra}); return {b, log}; }

test('one blink follows the v3 sequence exactly (260 ms) after a 3-6 s gap', () => {
  const c = clock(), {b, log} = make(c, {random: () => 0.5}); b.start();
  assert.equal(b.status.timers, 1); c.advance(4499); assert.deepEqual(log, []);
  c.advance(1 + 260); const t0 = 4500;
  assert.deepEqual(log, [[t0, 1], [t0 + 30, 2], [t0 + 60, 3], [t0 + 95, 4], [t0 + 165, 3], [t0 + 200, 2], [t0 + 230, 1], [t0 + 260, 0]]);
  assert.equal(b.status.timers, 1, 'next blink scheduled, still one timer');
});
test('gaps stay within 3-6 s and blinks never overlap over a long run', () => {
  const c = clock(); let r = 0; const {b, log} = make(c, {random: () => (r = (r * 9301 + 49297) % 233280) / 233280}); b.start(); c.advance(600000);
  const starts = log.filter(([, s], i) => s === 1 && (i === 0 || log[i - 1][1] === 0)).map(([t]) => t);
  assert.ok(starts.length > 90);
  for (let i = 1; i < starts.length; i++) { const g = starts[i] - starts[i - 1] - 260; assert.ok(g >= 3000 && g <= 6000, 'gap ' + g); }
  assert.ok(c.pending() <= 1);
});
test('stop() mid-blink reopens the eyes once and leaves no timer; start() again does not duplicate', () => {
  const c = clock(), {b, log} = make(c, {random: () => 0}); b.start(); c.advance(3000 + 70); assert.equal(b.status.state, 3);
  b.stop(); assert.equal(b.status.state, 0); assert.equal(log.at(-1)[1], 0); assert.equal(c.pending(), 0); assert.equal(b.status.timers, 0);
  const n = log.length; c.advance(20000); assert.equal(log.length, n, 'no state changes after stop');
  b.start(); b.start(); b.start(); assert.equal(c.pending(), 1, 'repeated start keeps a single timer');
});
test('stop() when idle reports nothing; blinkNow runs one blink immediately', () => {
  const c = clock(), {b, log} = make(c); b.stop(); assert.deepEqual(log, []);
  b.blinkNow(); c.advance(260); assert.deepEqual(log.map(x => x[1]), [1, 2, 3, 4, 3, 2, 1, 0]); assert.equal(c.pending(), 1);
});

function loadRegistry() {
  const ctx = {window: {}, console}; vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(root, 'js/field/portrait-registry.js'), 'utf8'), ctx); return ctx.window.PortraitRegistry;
}
test('registry: Aidan paths, faces, side and blink come from one place', () => {
  const R = loadRegistry(), sha = require('node:crypto');
  const J = x => JSON.stringify(x);   // values come from another vm realm
  assert.equal(J(R.get('aidan').faces), J(['normal', 'smile', 'angry', 'worried', 'sad', 'surprised']));
  assert.equal(R.imageUrl('aidan', 'worried'), 'assets/images/characters/portraits/aidan/aidan_worried.png');
  assert.equal(R.faceOf('determined', 'aidan'), 'normal'); assert.equal(R.faceOf('06', 'aidan'), 'worried'); assert.equal(R.faceOf('nope', 'aidan'), 'normal');
  assert.equal(R.sideOf('aidan'), 'left'); assert.equal(R.sideOf('aidan', 'right'), 'right'); assert.equal(R.sideOf('nobody'), 'right'); assert.equal(R.sideOf('aidan', 'up'), 'left');
  for (const f of R.get('aidan').faces) {
    assert.ok(fs.existsSync(path.join(root, R.imageUrl('aidan', f))), f);
    const b = R.blinkOf('aidan', f); assert.equal(J(Object.keys(b.eyes)), J(['L', 'R']));
    for (const e of Object.values(b.eyes)) { assert.equal(e.urls.length, 4); for (const u of e.urls) assert.ok(fs.existsSync(path.join(root, u)), u); }
  }
  assert.equal(J(R.blinkOf('aidan', 'smile').seq), J(V3.seq)); assert.equal(J(R.blinkOf('aidan', 'smile').gap), J(V3.gap));
  assert.equal(R.blinkOf('nobody', 'normal'), null);
  // a character without blink is a still portrait
  R.define('still_test', {src: {w: 10, h: 10}, base: 'x/', file: f => f + '.png', crop: {x: 0, y: 0, w: 10, h: 10}, faces: ['normal']});
  assert.equal(R.blinkOf('still_test', 'normal'), null); assert.equal(R.sideOf('still_test'), 'right');
});
test('adopted Aidan files are byte-identical to the approved originals', () => {
  const h = f => require('node:crypto').createHash('sha256').update(fs.readFileSync(path.join(root, 'assets/images/characters/portraits/aidan', f))).digest('hex');
  const want = {normal: 'c2036b46c91a3a47ffeec43b5b5ebb0035e8b347f82ee6338ab23d6062dfce53', smile: '8cb95b14db8e2508d5b0b5ae95d0657f19fccacdca7019ce21fcabe6bc4e69cf',
    angry: '6152d05b31a357aea6a091107c4e011f1bb55c914e4ede6eac8bdc281138af35', worried: '0d3d63643ff90dbb28b1a1e5beeacc0a205ed1aa462c14231158c72c29e939d4',
    sad: 'c53e564c73e8b97d5a4268a642b5fda0c2c8c5b60db236c49ea4ca3e33d2873d', surprised: '50f7b7f2628d2aa3bed57d697bf823c702feb1199d9a8db8977c4d1b30f94182'};
  for (const [f, s] of Object.entries(want)) assert.equal(h('aidan_' + f + '.png'), s, f);
  assert.equal(fs.readdirSync(path.join(root, 'assets/images/characters/portraits/aidan/blink')).filter(f => f.endsWith('.png')).length, 48);
});
