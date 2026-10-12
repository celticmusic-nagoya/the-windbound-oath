const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = {window:{}};
vm.createContext(context);
vm.runInContext(fs.readFileSync('js/field/field-collision.js','utf8'),context);
const map = JSON.parse(fs.readFileSync('data/maps/rilde_in_house_02.json','utf8'));
const solid = context.window.FieldCollision.compileMap([...map.collision.edgeBlockers,...map.collision.blockers]);
const blockedFeet=(x,y)=>solid.blocked(x-17,y-42);
assert(blockedFeet(430,452),'old spawn must reproduce the intact stool collision');
for(const [id,spawn] of Object.entries(map.spawns.points)) {
  assert(!blockedFeet(spawn.x,spawn.y),`${id}: declared spawn overlaps the 22x10 foot box`);
  const exit=map.transitions.find(t=>t.id==='tr_exit').rect;
  assert(!(spawn.x>=exit.x&&spawn.x<=exit.x+exit.w&&spawn.y>=exit.y&&spawn.y<=exit.y+exit.h),`${id}: spawn must not immediately retrigger the exit`);
  const endY=exit.y+20;
  for(let y=spawn.y;y<=endY;y+=2) assert(!blockedFeet(spawn.x,y),`${id}: route toward exit blocked at y=${y}`);
}
console.log('PASS house02 exact feet collision, preserved stool, safe entry and exit route');
