import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeNavigation, groundStep } from '../../dev/windwaiting-cliff/navigation.mjs';

const data = JSON.parse(readFileSync(new URL(
  '../../assets/candidates/lind/windwaiting-cliff-playable/navigation.json', import.meta.url)));
const nav = makeNavigation(data);

test('spawn reaches overlook through walkable neighboring cells', () => {
  const [x, y, z] = data.spawn;
  const route = nav.path(x, z, data.overlook[0], data.overlook[2]);
  assert.ok(route.length > 40);
  const ids = route.map(([a, b]) => nav.cell(a, b));
  let position = { x, y, z };
  for (const next of ids.slice(1)) {
    const [tx, tz] = nav.point(next);
    position = groundStep(position, tx, tz, nav, () => nav.levels[next], data.maxStep);
    assert.ok(position);
  }
  assert.ok(Math.hypot(position.x - data.overlook[0], position.z - data.overlook[2]) < 0.001);
});

test('every exposed cell boundary rejects unsupported movement before ray casting', () => {
  let tested = 0;
  for (let id = 0; id < nav.levels.length; id++) {
    if (!nav.open(id)) continue;
    const [x, z] = nav.point(id);
    for (const [dx, dz] of [[data.stride, 0], [-data.stride, 0], [0, data.stride], [0, -data.stride]]) {
      if (nav.open(nav.cell(x + dx, z + dz))) continue;
      assert.equal(groundStep({ x, y: nav.levels[id], z }, x + dx, z + dz, nav,
        () => assert.fail('unsupported destination raycast'), data.maxStep), null);
      tested++;
    }
  }
  assert.ok(tested > 200, tested);
  console.log('Blocked boundary probes:', tested);
});

test('trunks and moss-covered rock colliders close the corresponding grid cells', () => {
  for (const [x, z, radius] of data.obstacles) {
    const id = nav.cell(x, z);
    assert.ok(!nav.open(id));
    assert.ok(radius > data.stride);
  }
});

test('an absent hit or excessive level difference blocks passage', () => {
  const [x, y, z] = data.spawn;
  const position = { x, y, z };
  assert.equal(groundStep(position, x + .01, z, nav, () => null, data.maxStep), null);
  assert.equal(groundStep(position, x + .01, z, nav, () => y + .8, data.maxStep), null);
  assert.equal(groundStep(position, x + .01, z, nav, () => y - .8, data.maxStep), null);
});
