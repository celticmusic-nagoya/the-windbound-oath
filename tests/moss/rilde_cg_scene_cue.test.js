/* Approved CG order and story invariants, including director's 2026-11-08 update. */
const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const ctx={window:{}};vm.runInNewContext(fs.readFileSync('js/field/scene-data.js','utf8'),ctx);
const scene=ctx.window.FieldSceneData.scenes.cliff_sunset_to_fire,steps=scene.steps;
const idx=id=>steps.findIndex(s=>s.talk===id);
const sunset=idx('scene_cliff_sunset'),night=idx('scene_cliff_night'),standing=idx('scene_cliff_standing'),wind=idx('scene_cliff_wind_stops');
assert(sunset>=0&&night>sunset&&standing>night&&wind>standing);
const cg=steps.filter(s=>s.cg&&!s.cg.hide).map(s=>s.cg.src);
assert.deepEqual(Array.from(cg),[
 'assets/approved/game/cliff/sunset_background.png',
 'assets/approved/game/cliff/sunset_two_characters_back_view.png',
 'assets/approved/game/cliff/stargazing_seated.png',
 'assets/approved/game/cliff/stargazing_standing_final.png',
 'assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png'
]);
assert.equal(steps[night-2].cg.src,'assets/approved/game/cliff/stargazing_seated.png');
assert.equal(steps[standing-2].cg.src,'assets/approved/game/cliff/stargazing_standing_final.png');
assert.equal(steps[wind-2].cg.src,'assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png');
assert.equal(steps[wind-1].wait,1200);
assert.equal(steps[wind+1].cg.hide,true);
assert(!steps.some(s=>s.vista?.id==='village_fire'));
assert(!steps.some(s=>s.talk==='scene_cliff_fire'));
assert.equal(steps.filter(s=>'stage' in s).length,1);
assert.equal(steps.find(s=>'stage' in s).stage,4);
assert.equal(steps.at(-1).call,'cliffRunHome');assert.equal(scene.requireStage,3);
console.log('Approved seated/standing/wind-stop CG sequence PASS');
