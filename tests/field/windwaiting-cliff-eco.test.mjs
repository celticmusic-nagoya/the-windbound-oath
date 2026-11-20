import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { test } from 'node:test';

const root = new URL('../../assets/candidates/lind/windwaiting-cliff-playable/', import.meta.url);
const bytes = (path) => readFileSync(new URL(path, root));
const document = (path) => JSON.parse(bytes(path));
const sha = (path) => createHash('sha256').update(bytes(path)).digest('hex');
const source = document('eco-v2/source.json');
const plan = document('eco-v2/placement.json');

test('ECO v2 keeps the original cliff GLB, Blender source and navigation binary-identical', () => {
  assert.equal(sha('cliff.glb'), source.base_glb_sha256);
  assert.equal(sha('cliff_UNAPPROVED.blend'), source.base_blend_sha256);
  assert.equal(sha('navigation.json'), source.navigation_sha256);
  assert.ok(Object.keys(plan.protected_geometry_sha256).length >= 100);
});

test('packed ECO sources are pinned, wind weighted and exclude grass LOD2', () => {
  const assets = readdirSync(new URL('eco-v2/glb/', root));
  assert.equal(assets.length, Object.keys(plan.assets).length);
  for (const asset of assets) {
    assert.match(asset, /_LOD1\.glb$/);
    const key = `glb/${asset}`;
    assert.equal(sha(`eco-v2/${key}`), source.members[key]);
    const glb = bytes(`eco-v2/${key}`);
    const descriptor = JSON.parse(glb.subarray(20, 20 + glb.readUInt32LE(12)));
    assert.ok(descriptor.nodes.some((node) => node.extras?.eco_wind?.channel === 'lind_wind_strength'));
    for (const mesh of descriptor.meshes) {
      for (const primitive of mesh.primitives) {
        assert.ok('_WIND_WEIGHT' in primitive.attributes);
      }
    }
  }
  for (const [path, expected] of Object.entries(source.members)) assert.equal(sha(`eco-v2/${path}`), expected);
});

test('turf is bounded to foreground and landmark roles, and flowers form groups', () => {
  const turf = plan.instances.filter((instance) => instance.asset.includes('_turf_'));
  assert.ok(turf.length > 0);
  assert.ok(turf.every(({ role }) => role === 'foreground' || role === 'landmark'));
  assert.ok(plan.roles.foreground.range < plan.roles.middle.range);
  const flowers = plan.instances.filter((instance) => instance.asset.includes('_flower_'));
  const groups = new Map();
  for (const { cluster } of flowers) groups.set(cluster, (groups.get(cluster) ?? 0) + 1);
  assert.equal(groups.size, 4);
  assert.ok([...groups].every(([id, count]) => Number.isInteger(id) && count >= 2));
});
