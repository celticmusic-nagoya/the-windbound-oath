// node --test tools/character-asset-studio/tests/studio_core.test.cjs
const test = require('node:test');
const assert = require('node:assert');
const C = require('../studio-core.js');

test('normalised <-> pixel round trip on 1200x1600 and other presets', () => {
  for (const cv of [{ width: 1200, height: 1600 }, { width: 1024, height: 1280 }, { width: 96, height: 128 }]) {
    const n = C.toNorm([cv.width / 2, cv.height * 0.9625], cv);
    assert.deepStrictEqual(C.toPixel(n, cv), [Math.round(cv.width / 2), Math.round(cv.height * 0.9625)]);
  }
});
test('template ground is (600,1540) on the Morwen 1200x1600 profile', () => {
  const lm = C.templateLandmarks();
  assert.deepStrictEqual(C.toPixel(lm.front.ground.n, { width: 1200, height: 1600 }), [600, 1540]);
  assert.strictEqual(lm.back.neck.confidence, 'provisional');
});
test('placement: exact for same size, uniform bottom-centred otherwise', () => {
  const cv = { width: 1200, height: 1600 };
  assert.deepStrictEqual(C.placement(1200, 1600, cv), { scale: 1, x: 0, y: 0, w: 1200, h: 1600, exact: true });
  const p = C.placement(1152, 1536, cv);
  assert.ok(!p.exact); assert.ok(Math.abs(p.w / p.h - 1152 / 1536) < 1e-6); assert.strictEqual(p.y + p.h, 1600);
  const q = C.placement(2000, 1000, cv); assert.ok(Math.abs(q.w - 1200) < 1e-6); assert.ok(Math.abs(q.y + q.h - 1600) < 1e-6);
});
test('spec export is deterministic and round-trips through parseSpec', () => {
  const preset = { id: 'MORWEN_REAL_1200x1600', canvas: [1200, 1600], ground: [0.5, 0.9625], frames: 12, pixelsPerUnit: null };
  const lm = C.templateLandmarks(); lm.left.kneeLeft = { n: [0.41, 0.7], confidence: 'medium', source: 'manual_edit' };
  const assets = [{ name: 'b.png', view: 'back', layer: 'reference', frame: 0, sha256: 'a'.repeat(64), dimensions: [1200, 1600] }, { name: 'a.png', view: 'front', layer: 'reference', frame: 0, sha256: 'b'.repeat(64), dimensions: [1200, 1600] }];
  const s1 = C.stableStringify(C.buildSpec({ characterId: 'x', preset, landmarks: lm, assets }));
  const s2 = C.stableStringify(C.buildSpec({ characterId: 'x', preset, landmarks: lm, assets: assets.slice().reverse() }));
  assert.strictEqual(s1, s2);
  const back = C.parseSpec(JSON.parse(s1), preset);
  assert.deepStrictEqual(back.landmarks.left.kneeLeft, lm.left.kneeLeft);
  assert.strictEqual(JSON.parse(s1).status, 'candidate_not_canonical');
});
test('parseSpec accepts v1.0 pixel specs and rejects bad input', () => {
  const v1 = { schemaVersion: '1.0', canvas: { width: 1200, height: 1600 }, landmarks: {} };
  const px = { headTop: [600, 120], neck: [600, 310], shoulderLeft: [480, 350], shoulderRight: [720, 350], pelvis: [600, 820], kneeLeft: [535, 1160], kneeRight: [665, 1160], footLeft: [520, 1540], footRight: [680, 1540], ground: [600, 1540] };
  for (const v of C.VIEWS) v1.landmarks[v] = px;
  const r = C.parseSpec(v1, null);
  assert.deepStrictEqual(C.toPixel(r.landmarks.front.ground.n, { width: 1200, height: 1600 }), [600, 1540]);
  assert.ok(r.warnings.length === 1);
  const bad = JSON.parse(JSON.stringify(v1)); bad.landmarks.front.neck = [600, 9999];
  assert.throws(() => C.parseSpec(bad, null));
  assert.throws(() => C.parseSpec({ schemaVersion: '9.9', landmarks: {} }, null));
});
test('alphaStats counts border, transparency and bbox', () => {
  const w = 4, h = 4, d = new Uint8ClampedArray(w * h * 4);
  d[(1 * w + 1) * 4 + 3] = 255; d[(2 * w + 2) * 4 + 3] = 100;
  const s = C.alphaStats(d, w, h);
  assert.deepStrictEqual([s.opaque, s.semi, s.border, s.hasTransparency], [1, 1, 0, true]);
  assert.deepStrictEqual(s.bbox, [1, 1, 1, 1]);
});
