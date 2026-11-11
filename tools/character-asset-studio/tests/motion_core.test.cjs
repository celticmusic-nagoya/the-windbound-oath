// node --test tools/character-asset-studio/tests/motion_core.test.cjs
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const M = require('../motion-core.js');

test('frame <-> time: mid-frame seek round-trips at 24/25/30 fps', () => {
  for (const fps of [24, 25, 30]) for (const f of [0, 1, 23, 24, 617]) assert.strictEqual(M.timeToFrame(M.frameToTime(f, fps), fps), f);
  assert.strictEqual(M.frameCountFor(24.72, 25), 618);
  assert.strictEqual(M.stepFrame(0, -1, 618), 0);
  assert.strictEqual(M.stepFrame(617, 1, 618), 617);
  assert.strictEqual(M.stepFrame(10, 1, 618), 11);
  assert.strictEqual(M.timecode(50, 25), '00:02+00f');
});

test('phases: register, replace on same frame, sort, reject unknown', () => {
  const r = M.createRef({ video: { fps: 25 } });
  M.setPhase(r, 140, 'contact', 'B'); M.setPhase(r, 85, 'contact', 'A'); M.setPhase(r, 111, 'passing', 'A');
  M.setPhase(r, 111, 'down', 'A');
  assert.deepStrictEqual(r.phases.map(p => [p.frame, p.phase]), [[85, 'contact'], [111, 'down'], [140, 'contact']]);
  assert.throws(() => M.setPhase(r, 1, 'jump'));
  assert.throws(() => M.setPhase(r, 1, 'contact', 'X'));
  M.removePhase(r, 111); assert.strictEqual(r.phases.length, 2);
});

test('cycles: same-side contacts; alternation assumed (flagged) when side unknown', () => {
  const r = M.createRef({ video: { fps: 25 } });
  [[85, 'A'], [140, 'B'], [194, 'A'], [243, 'B']].forEach(([f, s]) => M.setPhase(r, f, 'contact', s));
  assert.deepStrictEqual(M.cycles(r).map(c => [c.start, c.end, c.sideAssumed]), [[85, 194, false], [140, 243, false]]);
  const u = M.createRef({ video: { fps: 25 } });
  [85, 140, 194].forEach(f => M.setPhase(u, f, 'contact'));
  assert.deepStrictEqual(M.cycles(u), [{ start: 85, end: 194, length: 109, side: 'unknown', sideAssumed: true }]);
  const s = M.stats(r);
  assert.deepStrictEqual(s.stepFrames, [55, 54, 49]);
  assert.strictEqual(s.status, 'UNAPPROVED_REFERENCE');
});

test('6/8/12 sampling covers [start,end) evenly and maps to a 12-frame sprite', () => {
  assert.deepStrictEqual(M.sampleCycle(0, 12, 6), [0, 2, 4, 6, 8, 10]);
  assert.deepStrictEqual(M.sampleCycle(85, 194, 8), [85, 99, 112, 126, 140, 153, 167, 180]);
  for (const n of M.SAMPLE_COUNTS) {
    const s = M.sampleCycle(85, 194, n);
    assert.strictEqual(s.length, n); assert.ok(s.every((f, i) => i === 0 || f > s[i - 1])); assert.ok(s[n - 1] < 194);
    assert.deepStrictEqual(Array.from({ length: n }, (_, i) => M.spriteFrameFor(i, n, 12)).length, n);
  }
  assert.deepStrictEqual([0, 1, 2, 3, 4, 5].map(i => M.spriteFrameFor(i, 6, 12)), [0, 2, 4, 6, 8, 10]);
  assert.throws(() => M.sampleCycle(10, 10, 6));
});

test('anchors: per-frame record, clamp, trajectory order, interpolation', () => {
  const r = M.createRef({ video: { fps: 25 } });
  M.setAnchor(r, 20, 'hip', [0.6, 0.5]); M.setAnchor(r, 10, 'hip', [0.4, 0.5]); M.setAnchor(r, 10, 'ankle_L', [1.4, -0.2]);
  assert.deepStrictEqual(M.trajectory(r, 'hip'), [[10, 0.4, 0.5], [20, 0.6, 0.5]]);
  assert.deepStrictEqual(r.anchors['10'].ankle_L.n, [1, 0]);
  assert.deepStrictEqual(M.anchorAt(r, 'hip', 15), [0.5, 0.5]);
  assert.strictEqual(M.anchorAt(r, 'hip', 25), null);
  assert.throws(() => M.setAnchor(r, 1, 'tail', [0, 0]));
  M.removeAnchor(r, 10, 'ankle_L'); M.removeAnchor(r, 10, 'hip'); assert.deepStrictEqual(Object.keys(r.anchors), ['20']);
});

test('JSON: deterministic, round-trips, status cannot be upgraded on import, no pixel payload', () => {
  const r = M.createRef({ video: { name: 'v.mp4', sha256: 'ab'.repeat(32), width: 640, height: 360, fps: 25, frameCount: 618 }, region: 'left_half' });
  M.setPhase(r, 85, 'contact', 'A'); M.setPhase(r, 194, 'contact', 'A'); M.setAnchor(r, 85, 'hip', [0.5, 0.45]);
  const a = M.serialize(r), b = M.serialize(M.parse(a));
  assert.strictEqual(a, b);
  const j = JSON.parse(a);
  assert.strictEqual(j.status, 'UNAPPROVED_REFERENCE'); assert.strictEqual(j.autoApply, false);
  assert.deepStrictEqual(j.region, [0, 0, 0.5, 1]);
  const forged = JSON.parse(a); forged.status = 'APPROVED'; forged.autoApply = true;
  const p = JSON.parse(M.serialize(M.parse(forged)));
  assert.strictEqual(p.status, 'UNAPPROVED_REFERENCE'); assert.strictEqual(p.autoApply, false);
  assert.ok(!/data:image|base64/.test(a));
  assert.throws(() => M.parse('{"schema":"other"}'));
});

test('committed Grid Overlay reference JSON is valid, unapproved and self-consistent', () => {
  const f = path.join(__dirname, '..', 'motion', 'grid_overlay_walk.reference.json');
  const text = fs.readFileSync(f, 'utf8');
  const ref = M.parse(text);
  assert.strictEqual(M.serialize(ref), text, 'file is in canonical serialized form');
  const j = JSON.parse(text);
  assert.strictEqual(j.status, 'UNAPPROVED_REFERENCE');
  assert.ok(j.video.sha256 && /^[0-9a-f]{64}$/.test(j.video.sha256));
  assert.ok(M.cycles(ref).length >= 3);
});

test('box mapping helpers', () => {
  const box = M.fitBox(320, 360, 0, 0, 640, 360);
  assert.deepStrictEqual([box.w, box.h], [320, 360]);
  assert.deepStrictEqual(M.boxToRegion(M.regionToBox([0.25, 0.75], box), box), [0.25, 0.75]);
});
