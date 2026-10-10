// NPC registry consistency: node tests/field/npc_registry.test.js
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.join(__dirname, '..', '..');
const R = require(path.join(root, 'js/field/lind-npc-registry.js'));
const load = f => { const w = {}; vm.runInNewContext(fs.readFileSync(path.join(root, f), 'utf8'), {window: w}); return w; };
const talk = [load('js/field/talk-data.js').TalkData, load('js/field/talk-data-quests.js').TalkDataQuests];
const talkNpcs = new Set(talk.flatMap(d => d.tables.map(t => t.npc)));
const bounds = fs.readFileSync(path.join(root, 'js/field/lind-content-bounds.js'), 'utf8');
const hasBounds = k => new RegExp('^  "' + k + '": \\[', 'm').test(bounds);
const KINDS = ['WORKER', 'LOCAL_WALKER', 'SHOP', 'ELDERLY', 'EMMA'];
let fails = 0; const ok = (c, m) => { console.log((c ? 'ok   ' : 'FAIL ') + m); if (!c) fails++; };
ok(new Set(R.npcs.map(n => n.id)).size === R.npcs.length, 'ids are unique (' + R.npcs.length + ' NPCs)');
for (const n of R.npcs) {
  const idle = path.join(root, R.idlePath(n));
  const problems = [];
  if (!fs.existsSync(idle)) problems.push('idle sprite missing');
  if (!hasBounds(n.id + '_idle')) problems.push('no ' + n.id + '_idle bounds');
  if (n.talk !== null && !talkNpcs.has(n.talk)) problems.push('no talk table for "' + n.talk + '"');
  if (n.routine && !KINDS.includes(n.routine.kind)) problems.push('unknown routine kind ' + n.routine.kind);
  if (n.routine && n.motion) problems.push('routine and motion are exclusive');
  if (!(Number.isFinite(n.x) && Number.isFinite(n.footY) && n.height > 0)) problems.push('bad placement');
  const files = [1, 2, 3, 4, 5, 6].filter(i => fs.existsSync(path.join(root, R.walkPath(n, i))));
  const keys = [1, 2, 3, 4, 5, 6].filter(i => hasBounds(n.id + '_walk_0' + i));
  if (files.join() !== keys.join()) problems.push('walk PNG/bounds mismatch files=' + files + ' bounds=' + keys);
  if (n.walk.frames != null && files.length !== n.walk.frames) problems.push('walk.frames=' + n.walk.frames + ' but ' + files.length + ' installed');
  if (n.walk.frames == null && files.length) problems.push(files.length + ' walk frames installed but registry says waiting: set walk.frames');
  if (n.walk.legacy && !hasBounds(n.walk.legacy) && !files.length) problems.push('legacy walk frame missing');
  ok(!problems.length, n.id.padEnd(14) + (n.walk.frames == null && !n.walk.legacy ? '[walk: waiting for delivery]' : '[walk: ' + (n.walk.frames || 'legacy') + ']') + (problems.length ? '  ' + problems.join('; ') : ''));
}
const waiting = R.npcs.filter(n => n.walk.frames == null && !n.walk.legacy && n.motion !== 'fishing').map(n => n.id);
console.log('walk frames still to deliver (' + waiting.length + '): ' + waiting.join(', '));
process.exit(fails ? 1 : 0);
