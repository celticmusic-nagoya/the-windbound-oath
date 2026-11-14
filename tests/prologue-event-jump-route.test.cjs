// TWO-NIGHTLY-PROLOGUE-QA: Event Jump 1-14 (AGENTS.md §16) x prologue canonical route (§15)
// Run: node tests/prologue-event-jump-route.test.cjs
// Static contract over index.html DEV_EVENTS/devJump and js/prologue-dev.js entries/devJump wrapper.
// Does not replace browser/Android QA of the destinations themselves.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const dev = fs.readFileSync(path.join(root, 'js/prologue-dev.js'), 'utf8');

function literal(source, re, what) {
  const m = re.exec(source);
  assert.ok(m, 'fixture: ' + what + ' not found');
  return JSON.parse(m[1].replace(/'/g, '"'));
}
const DEV_EVENTS = literal(html, /^const DEV_EVENTS=(\[[\s\S]*?\n\]);/m, 'DEV_EVENTS');
const entries = literal(dev, /const entries=(\[.*?\]\]);/, 'prologue-dev entries');
const jumpStart = html.search(/^function devJump\s*\(/m);
assert.ok(jumpStart >= 0, 'fixture: devJump declaration not found');
const jumpEnd = html.indexOf('\n}\n', jumpStart);
assert.ok(jumpEnd > jumpStart, 'fixture: devJump end not found');
const devJump = html.slice(jumpStart, jumpEnd + 2);

// §16 canonical destinations 1..14, in order, mapped to the current DEV_EVENTS keys.
const CANON = [
  [1, 'opening'], [2, 'training'], [3, 'sunset'], [4, 'attack'], [5, 'reunion'],
  [6, 'north'], [7, 'escape'], [8, 'forest'], [9, 'lou'], [10, 'altar'],
  [11, 'raider'], [12, 'aftermath'], [13, 'fort'], [14, 'prologueEnd'],
];
const ALIAS = { reunion: 'north' }; // js/prologue-dev.js: if(key==='reunion')key='north'
const normalize = k => ALIAS[k] || k;

function legacyStage(key) {
  const re = new RegExp("(?:if|else if)\\(key==='" + key + "'\\)\\{\\s*storyStage=(\\d+)");
  const m = re.exec(devJump);
  assert.ok(m, 'devJump branch with storyStage missing for ' + key);
  return Number(m[1]);
}

let n = 0;
function test(name, fn) { fn(); console.log('PASS', name); n++; }

test('DEV_EVENTS numbers 01..14 are exactly the §16 canonical destinations in order', () => {
  const numbered = DEV_EVENTS
    .map(([k, label]) => [Number((/^(\d{2})　/.exec(label) || [])[1]), k])
    .filter(([num]) => num >= 1 && num <= 14);
  assert.deepEqual(numbered, CANON);
});

test('post-prologue jumps are numbered after 14 PROLOGUE END', () => {
  for (const key of ['rilde_ruin', 'fort_free']) {
    const e = DEV_EVENTS.find(([k]) => k === key);
    assert.ok(e, 'missing ' + key);
    assert.ok(Number(e[1].slice(0, 2)) > 14, key + ' must come after PROLOGUE END');
  }
  assert.match(DEV_EVENTS.find(([k]) => k === 'prologueEnd')[1], /PROLOGUE END/);
  assert.match(DEV_EVENTS.find(([k]) => k === 'fort')[1], /ドゥンヴァル砦/);
});

test('storyStage set by each canonical jump never decreases along the §15 route', () => {
  const stages = CANON.map(([, k]) => [k, legacyStage(k)]);
  for (let i = 1; i < stages.length; i++) {
    assert.ok(stages[i][1] >= stages[i - 1][1],
      'storyStage regresses: ' + stages[i - 1].join('=') + ' -> ' + stages[i].join('='));
  }
  assert.equal(stages[0][1], 0, 'Aidan house starts the prologue at stage 0');
  assert.equal(stages.at(-2)[1], 14, 'Dunvar Fortress is the last stage before PROLOGUE END');
  assert.equal(stages.at(-1)[1], 15, 'PROLOGUE END stage');
});

test('RildeVillage fast-path branches agree with the legacy stage for the same key', () => {
  const re = /if\(key==='(\w+)'&&window\.RildeVillage&&RildeVillage\.enabled\(\)\)\{storyStage=(\d+);/g;
  let m, seen = 0;
  while ((m = re.exec(devJump))) { seen++; assert.equal(Number(m[2]), legacyStage(m[1]), m[1]); }
  assert.ok(seen >= 2, 'fixture: expected training/sunset RildeVillage branches');
});

test('map: jumps never lower storyStage below PROLOGUE END', () => {
  assert.match(devJump, /if\(key\.startsWith\('map:'\)\)\{if\(storyStage<15\)\{storyStage=15;/);
});

test('runtime wrapper keeps the reunion alias and the summit capture handler', () => {
  assert.match(dev, /if\(key==='reunion'\)key='north';/);
  assert.match(dev, /if\(!entries\.some\(\(\[k\]\)=>k===key\)\)return false;/);
  assert.match(html, /closest\('\[data-jump="cliff_summit"\]'\)[\s\S]{0,200}stopImmediatePropagation\(\)/);
});

test('every visible DEV_EVENTS button is accepted by the prologue-dev devJump wrapper', () => {
  // renderDevEvents() reconciles #devGrid back to DEV_EVENTS, but clicks go through the
  // wrapper, which silently returns false for keys missing from its entries list.
  const accepted = new Set(entries.map(([k]) => k));
  const rejected = DEV_EVENTS.map(([k]) => k)
    .filter(k => k !== 'cliff_summit') // handled by the capture listener before devJump
    .filter(k => !accepted.has(normalize(k)));
  assert.deepEqual(rejected, []);
});

test('wrapper entries keep canonical keys in route order (index thresholds depend on it)', () => {
  const idx = CANON.map(([, k]) => [k, entries.findIndex(([e]) => e === normalize(k))]);
  for (const [k, i] of idx) assert.ok(i >= 0, 'wrapper missing ' + k);
  for (let i = 1; i < idx.length; i++) assert.ok(idx[i][1] >= idx[i - 1][1], idx[i - 1][0] + ' -> ' + idx[i][0]);
});

console.log(n + ' passed');
