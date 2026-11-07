/* Rilde CG registry + renderer policy tests. Run: node tests/moss/rilde_cg_registry.test.js */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const manifest = require('../../docs/art/approved-rilde-story-20261107.json');
const context = {window: {}, document: {}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('js/field/rilde-cg.js', 'utf8'), context);
vm.runInContext(fs.readFileSync('js/field/cliff-presentation.js', 'utf8'), context);
const registry = context.window.RildeCG;
const renderer = context.window.CliffPresentation;
assert.equal(Object.keys(registry.scenes).length, 6);
assert.equal(manifest.files.length, 10);
const approved = new Set(manifest.files.map(x => x.path));
for (const path of Object.values(registry.scenes)) assert.ok(approved.has(path), path);
for (const id of ['cliff_dialogue', 'raid_background', 'aftermath_background']) {
  assert.equal(renderer.allowed(registry.gameplayPathFor(id)), true, id);
}
for (const id of registry.referenceOnly) {
  assert.equal(registry.gameplayPathFor(id), null, id);
  assert.equal(renderer.allowed(registry.pathFor(id)), false, id);
}
assert.equal(renderer.allowed('../assets/approved/game/rilde_story/raid/attack_background_only.png'), false);
assert.equal(renderer.allowed('assets/approved/game/rilde_story/raid/attack_background_only_APPROVED_user_reference.png'), false);
assert.equal(renderer.allowed('assets/approved/game/cliff/sunset_background.png'), true);
assert.equal(renderer.allowed('https://example.com/a.png'), false);
assert.equal(renderer.allowed('assets/approved/game/rilde_story/raid/attack_background_only.jpg'), false);
console.log('Rilde CG registry/renderer policy PASS');
