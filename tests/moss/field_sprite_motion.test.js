'use strict';
const assert = require('node:assert/strict');
const { test } = require('node:test');
const motion = require('../../js/field/field-sprite-motion.js');
test('all five motion profiles are present', () => assert.deepEqual(Object.keys(motion.profiles), ['player','companion','npc','enemy','fairy']));
test('stationary player, companion and NPC do not bob', () => {
  for (const kind of ['player','companion','npc']) assert.deepEqual(motion.sample({kind,time:0.25,moving:false}), {x:0,y:0,sway:0,scale:1});
});
test('moving PC bounces without changing collision coordinates', () => {
  const s=motion.sample({kind:'player',time:1/(4*2.4),moving:true});
  assert.ok(s.y<0);assert.equal(s.x,0);assert.equal(s.scale,1);
});
test('fairy floats while idle', () => assert.notEqual(motion.sample({kind:'fairy',time:.15,moving:false}).y,0));
test('enemy pulses while stationary', () => assert.notEqual(motion.sample({kind:'enemy',time:.15,moving:false}).scale,1));
test('reduced motion suppresses all effects', () => {
  for (const kind of Object.keys(motion.profiles)) assert.deepEqual(motion.sample({kind,time:.15,moving:true,reducedMotion:true}),{x:0,y:0,sway:0,scale:1});
});
test('same input gives identical output', () => assert.deepEqual(motion.sample({kind:'npc',time:12.34,moving:true,phase:.3}),motion.sample({kind:'npc',time:12.34,moving:true,phase:.3})));
test('invalid inputs never yield NaN', () => {
  for(const opts of [undefined,null,{time:NaN,phase:Infinity,kind:'unknown',moving:true},{time:'1',phase:'2',moving:true}]) {
    const s=motion.sample(opts);for(const v of Object.values(s)) assert.ok(Number.isFinite(v));
  }
});
test('periodic movement has no cumulative drift', () => {
  const first=motion.sample({kind:'npc',time:0,moving:true});
  const last=motion.sample({kind:'npc',time:10/1.8,moving:true});
  assert.ok(Math.abs(first.y-last.y)<1e-9);assert.ok(Math.abs(first.sway-last.sway)<1e-9);
});
