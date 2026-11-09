// Run: node tests/moss/m29_height_pieces.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync('js/field/field-height.js', 'utf8');
function makeNode(tag) {
  return { tag, dataset: {}, style: {}, children: [], appendChild(child) { this.children.push(child); }, remove() { this.removed = true; } };
}
const context = { window: {}, document: { createElement: makeNode }, performance: { now: () => 0 }, Map, Set, Math };
vm.runInNewContext(code, context);
const spec = { visuals: [{ id: 'legacy', kind: 'rect', rect: [0,0,10,10], z: 1, color: '#fff' }], pieces: [
  { id: 'rock', asset: 'height_cliff_rock_01', anchor: [100, 200], level: 1, z: 5, fade: 'deck' },
  { id: 'legacy', asset: 'height_cliff_ruin_01', anchor: [50, 50] },
  { id: 'missing', asset: 'unregistered', anchor: [0, 0] }
] };
const height = context.window.FieldHeight.create(spec, { blocked: () => false }, { resolveAsset: id => id === 'height_cliff_rock_01' ? {url:'/registered.png',w:80,h:56} : null });
const world = makeNode('div');
height.mount(world);
assert.equal(world.children.length, 2, 'one legacy placeholder and one registered PNG');
const png = world.children.find(n => n.tag === 'img');
assert.ok(png);
assert.equal(png.src, '/registered.png');
assert.equal(png.style.left, '100px');
assert.equal(png.style.top, '144px', 'lift applied exactly once');
assert.equal(png.style.width, '80px');
assert.equal(png.style.height, '56px');
assert.equal(png.style.transform, 'translate(-50%, -100%)');
assert.equal(png.dataset.fade, 'deck');
height.fade('deck', true);
assert.equal(png.style.opacity, '.42');
height.fade('deck', false);
assert.equal(png.style.opacity, '');
height.destroy();
assert.ok(world.children.every(n => n.removed));
const untouched = context.window.FieldHeight.create({}, { blocked: () => false });
const empty = makeNode('div');
untouched.mount(empty);
assert.equal(empty.children.length, 0);
console.log('m29_height_pieces: PASS');
