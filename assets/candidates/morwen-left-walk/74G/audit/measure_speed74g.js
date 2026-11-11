// Measure FieldMovement world speed (pointer / keyboard path) and distance-driven frame phase, no browser.
global.window = global; let raf = null; global.requestAnimationFrame = cb => { raf = cb; };
const SRC = process.argv[2] || require('path').resolve(__dirname, '../../../../../js/field'); // repo js/field (field-movement.js, walk-motion.js)
require(require('path').resolve(SRC, 'field-movement.js')); require(require('path').resolve(SRC, 'walk-motion.js'));
const m = window.FieldMovement, W = window.FieldWalkMotion;
function run(hz, seconds) {
  m.clock.set(1); let now = 0, x = 100; const dt = 1000 / hz;
  for (let i = 0; i < hz * seconds; i++) { now += dt; raf(now); x = m.advance(x, 100, m.settings.pointerStep * m.frameScale, 0, () => false, {bounds: {width: 1e6, height: 1e6}}).x; }
  return (x - 100) / seconds;
}
const out = {pointerStep: m.settings.pointerStep, keyboardStep: m.settings.keyboardStep, multiplier: m.settings.multiplier,
  pointer_px_per_s: {'60Hz': run(60, 2), '120Hz': run(120, 2), '144Hz': run(144, 2)}, walkStride: W.STRIDE, walkerFps: W.WALKER_FPS};
// distance-driven phase for a 12-frame bank at several strides, 300 px/s, 60 Hz display
out.phase = {};
for (const stride of [20.8, 90, 120, 180, 252]) {
  const counts = new Map(); let prev = -1, changes = 0;
  for (let i = 0; i < 600; i++) { const d = 300 * i / 60; const k = W.phaseDistance(d, 12, stride); if (k !== prev) { changes++; prev = k; } counts.set(k, (counts.get(k) || 0) + 1); }
  out.phase[stride] = {frames_shown_per_s: changes / 10, cycle_s: stride / 300, distinct_frames_seen: counts.size};
}
console.log(JSON.stringify(out, null, 1));
