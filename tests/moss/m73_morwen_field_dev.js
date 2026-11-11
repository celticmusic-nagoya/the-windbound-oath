// MORWEN-PRODUCTION-73: DEV gate + frame contract for js/field/morwen-field-dev.js (node, no browser).
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..', '..');
const SRC = fs.readFileSync(path.join(ROOT, 'js/field/morwen-field-dev.js'), 'utf8');
let fails = 0; const ok = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); if (!c) fails++; };
function run(dev, search) {
  const touched = {doc: 0, raf: 0};
  const document = new Proxy({}, {get() { touched.doc++; return () => null; }});
  const ctx = {window: {WINDBOUND_DEV: dev}, location: {search}, document, requestAnimationFrame: () => { touched.raf++; return 1; }, Image: function () {}, console};
  ctx.window.window = ctx.window;
  vm.runInNewContext(SRC, Object.assign(ctx, {window: ctx.window}), {filename: 'morwen-field-dev.js'});
  return {win: ctx.window, touched};
}
for (const [dev, q, label] of [[false, '', 'DEV off, no flag'], [false, '?morwenField=1', 'DEV off, flag'], [true, '', 'DEV on, no flag'], [true, '?morwenField=0', 'DEV on, flag=0'], [undefined, '?morwenField=1', 'DEV undefined, flag']]) {
  const r = run(dev, q);
  ok(!('MorwenFieldDev' in r.win) && r.touched.doc === 0 && r.touched.raf === 0, `${label}: inert (no global, no DOM, no timer)`);
}
const on = run(true, '?morwenField=1');
const M = on.win.MorwenFieldDev;
ok(Boolean(M) && on.touched.raf === 1, 'DEV on + flag: registers and schedules one rAF loop');
ok(M.frames.length === 6, '6 frames');
ok(M.frames.every(f => f.width === 48 && f.height === 64 && f.scale === 1 && f.anchor[0] === 24 && f.anchor[1] === 63), '48x64 @1x, anchor (24,63)');
ok(M.frames.every(f => fs.existsSync(path.join(ROOT, f.path))), 'all frame files exist (72 candidate, read in place)');
ok(M.frames.every((f, i) => f.path.endsWith(`morwen_right_walk_0${i}_48x64.png`)), 'frame order F00..F05');
ok(M.fps === 8 && Math.abs(M.stride - 225) < 1e-9, 'default 8 fps at 300 px/s -> stride 225 px');
const seq = [0, 37.5, 75, 112.5, 150, 187.5, 225].map(M.phase);
ok(JSON.stringify(seq) === JSON.stringify([0, 1, 2, 3, 4, 5, 0]), 'distance phase advances 1 frame per 37.5 px and loops F05->F00');
ok(M.mirrorLeft === true, 'left = provisional mirror');
ok(Math.abs(M.footSlidePerFrame() - (37.5 - 3)) < 1e-9, 'foot slide per frame documented (34.5 world px at default stride)');
const big = run(true, '?morwenField=1&morwenSize=96').win.MorwenFieldDev;
ok(big.frames.every(f => f.width === 96 && f.height === 128 && f.scale === 0.5 && f.anchor[0] === 48 && f.anchor[1] === 126), '96x128 @0.5, anchor (48,126)');
const st = run(true, '?morwenField=1&morwenStride=18').win.MorwenFieldDev;
ok(st.stride === 18 && Math.abs(st.footSlidePerFrame()) < 1e-9, 'stride 18 px (art stride) -> zero slide (needs 24 px/s walking)');
// static: no other runtime file references the DEV module or the candidate path
const refs = ['js/field/walk-motion.js', 'js/field/moss-forest-runtime.js', 'js/field/fiona-field-assets.js', 'js/field/aidan-field-assets.js'].filter(p => /morwen/i.test(fs.readFileSync(path.join(ROOT, p), 'utf8')));
ok(refs.length === 0, 'existing actor/runtime files untouched by Morwen');
console.log(fails ? `FAIL ${fails}` : 'ALL PASS'); process.exit(fails ? 1 : 0);
