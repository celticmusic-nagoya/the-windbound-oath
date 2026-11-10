// MORWEN-WALK-4DIR: DEV gate, 12-frame banks, distance / event clock, turn / stop / resume continuity (node, no browser).
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..', '..');
const SRC = fs.readFileSync(path.join(ROOT, 'js/field/morwen-walk4-dev.js'), 'utf8');
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
function run(dev, search) {
  const touched = {doc: 0, raf: 0, storage: 0};
  const document = new Proxy({}, {get() { touched.doc++; return () => null; }});
  const localStorage = new Proxy({}, {get() { touched.storage++; return () => null; }});
  const win = {WINDBOUND_DEV: dev, localStorage};
  win.window = win;
  const ctx = {window: win, location: {search}, document, localStorage, requestAnimationFrame: () => { touched.raf++; return 1; }, Image: function () {}, console};
  vm.runInNewContext(SRC, ctx, {filename: 'morwen-walk4-dev.js'});
  return {win, touched};
}
for (const [dev, q, label] of [[false, '', 'DEV off'], [false, '?morwenWalk4=1', 'DEV off + flag'], [true, '', 'DEV on, no flag'],
  [true, '?morwenWalk4=0', 'flag=0'], [undefined, '?morwenWalk4=1', 'DEV undefined + flag'], [true, '?morwenField=1', 'other DEV flag only']]) {
  const r = run(dev, q);
  ok(!('MorwenWalk4Dev' in r.win) && r.touched.doc === 0 && r.touched.raf === 0 && r.touched.storage === 0, `${label}: inert`);
}
const on = run(true, '?morwenWalk4=1'); const M = on.win.MorwenWalk4Dev;
ok(Boolean(M) && on.touched.raf === 1 && on.touched.storage === 0, 'DEV + flag: one rAF loop, no storage access (SAVE untouched)');
ok(M.frameCount === 12 && M.cycleMs === 840 && M.stride === 180, '12 frames, 840 ms event cycle, field stride 180');
ok(['left', 'right', 'up', 'down'].every(k => M.frames[k].length === 12), 'left/right/up/down banks, 12 frames each');
ok(Object.values(M.frames).flat().every(f => fs.existsSync(path.join(ROOT, f.path))), 'all 48 frame files exist (read in place)');
ok(Object.values(M.frames).flat().every(f => f.width === 48 && f.height === 64 && f.anchor[0] === 24 && f.anchor[1] === 62), '48x64, anchor (24,62)');
ok(M.frames.left.every((f, i) => f.path.endsWith(`74G_12f_${String(i).padStart(2, '0')}_48x64.png`)) && M.frames.right[11].path.endsWith('75_12f_11_48x64.png') && M.frames.up[0].path.includes('morwen-up-walk/76/') && M.frames.down[5].path.endsWith('morwen-down-walk/77/morwen_down_walk_77_12f_05_48x64.png'), 'frame order F00..F11 per facing');
const big = run(true, '?morwenWalk4=1&morwenSize=96').win.MorwenWalk4Dev;
ok(Object.values(big.frames).flat().every(f => f.width === 96 && f.scale === 0.5 && f.anchor[1] === 124), '96x128 @0.5, anchor (48,124)');

// distance clock at 300 px/s for 60 / 120 / 144 Hz (FieldMovement is frame-rate normalised: 300 px/s at every rate)
for (const hz of [60, 120, 144]) {
  const s = M.createState(); let prev = 0, maxStep = 0, changes = 0, wraps = 0;
  for (let i = 0; i < hz * 2; i++) {
    const r = s.step({dx: 300 / hz, dy: 0, dt: 1000 / hz});
    const st = (r.frame - prev + 12) % 12; maxStep = Math.max(maxStep, st); if (st) changes++; if (r.frame < prev) wraps++; prev = r.frame;
  }
  ok(maxStep === 1 && Math.abs(changes / 2 - 20) <= 1 && wraps >= 3, `${hz} Hz field: 20 frames/s at 300 px/s, never skips a frame (max step ${maxStep})`);
  const e = M.createState({mode: 'event'}); let n = 0, p = 0, ms = 0;
  for (let i = 0; i < hz * 2; i++) { const r = e.step({dx: 0.4, dy: 0, dt: 1000 / hz}); const st = (r.frame - p + 12) % 12; ms = Math.max(ms, st); if (st) n++; p = r.frame; }
  ok(Math.abs(n / 2 - 1000 / 70) <= 1 && ms === 1, `${hz} Hz event: 840 ms cycle (${(n / 2).toFixed(1)} frames/s), no skip`);
}
// turning keeps the phase
{
  const s = M.createState(); let r;
  for (let i = 0; i < 7; i++) r = s.step({dx: 5, dy: 0});
  const before = r.frame; r = s.step({dx: 0, dy: -5});
  ok(r.face === 'up' && (r.frame - before + 12) % 12 <= 1, `turn right->up keeps the leg phase (F${before} -> F${r.frame})`);
  r = s.step({dx: -5, dy: 0}); ok(r.face === 'left', 'turn up->left');
  r = s.step({dx: 0, dy: 5}); ok(r.face === 'down', 'turn left->down (77)');
  const fd = r.frame; r = s.step({dx: 5, dy: 0}); ok(r.face === 'right' && (r.frame - fd + 12) % 12 <= 1, 'turn down->right keeps the leg phase');
  r = s.step({dx: -5, dy: 0});
  r = s.step({dx: 4, dy: 4}); ok(r.face === 'left', 'diagonal dead zone does not flicker the facing');
}
// stop settles forward on a contact frame, resume continues from it
{
  const s = M.createState(); let r;
  for (let i = 0; i < 9; i++) r = s.step({dx: 5, dy: 0});
  const moving = r.frame; const seen = [r.frame]; let maxStep = 0;
  for (let i = 0; i < 120; i++) { r = s.step({dx: 0, dy: 0, dt: 1000 / 60}); const st = (r.frame - seen[seen.length - 1] + 12) % 12; maxStep = Math.max(maxStep, st); seen.push(r.frame); }
  ok(r.frame % 6 === 0 && maxStep <= 1 && !r.settling, `stop: F${moving} runs on to contact F${String(r.frame).padStart(2, '0')} one frame at a time, then holds`);
  const held = r.frame; r = s.step({dx: 5, dy: 0});
  ok((r.frame - held + 12) % 12 <= 1, `resume continues from F${held} (F${r.frame})`);
}
// static: existing runtime / actor files and FieldMovement are untouched by this module
const refs = ['js/field/walk-motion.js', 'js/field/field-movement.js', 'js/field/moss-forest-runtime.js', 'js/field/fiona-field-assets.js', 'js/field/aidan-field-assets.js'].filter(p => fs.existsSync(path.join(ROOT, p)) && /morwen/i.test(fs.readFileSync(path.join(ROOT, p), 'utf8')));
ok(refs.length === 0, 'walk-motion / field-movement / actor files do not reference Morwen (speed and other actors unchanged)');
ok(!/localStorage|sessionStorage|PartyManager|saveGame/.test(SRC), 'module has no save / party references');
console.log(fails ? `FAIL ${fails}` : 'ALL PASS'); process.exit(fails ? 1 : 0);
