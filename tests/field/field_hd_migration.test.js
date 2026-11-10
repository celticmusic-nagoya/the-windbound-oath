const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const spec = JSON.parse(fs.readFileSync('data/field-hd-migration-v1.json', 'utf8'));
const reg = JSON.parse(fs.readFileSync('data/morwen-hd-canonical-v2.json', 'utf8'));
const rig = JSON.parse(fs.readFileSync('data/sprite-rig/morwen_hd_left_walk6_v2_recheck.json', 'utf8'));

test('new HD policy targets 7.5 heads but preserves legacy', () => {
  assert.equal(spec.proportion.target_heads, 7.5);
  assert.equal(spec.proportion.legacy_status, 'COMPATIBILITY_ONLY');
  assert.equal(spec.pilot.production_connected, false);
});
test('pilot is bound to new canonical left, never superseded 3V', () => {
  assert.equal(spec.pilot.canonical_left_sha256, reg.assets['pixel.left'].sha256);
  assert.equal(spec.pilot.canonical_left_sha256, rig.canonical_source.sha256);
  assert.ok(!reg.superseded.some(a => a.sha256 === spec.pilot.canonical_left_sha256));
});
test('walk output anchor is consistent with recheck', () => {
  assert.deepEqual(spec.pilot.walk.canvas, rig.recommended_frame_space.canvas);
  assert.deepEqual(spec.pilot.walk.ground_anchor, rig.recommended_frame_space.ground_anchor);
  assert.equal(spec.pilot.walk.frames, 6);
  assert.equal(spec.pilot.walk.fps, 10);
  assert.deepEqual(spec.pilot.walk.alpha_allowed, [0,255]);
  assert.equal(spec.pilot.walk.status, 'NOT_DRAWN');
});
