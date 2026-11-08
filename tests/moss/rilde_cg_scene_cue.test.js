/* Approved sunset → seated stars → standing stars → wind stop cue regression. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ctx={window:{}};
vm.runInNewContext(fs.readFileSync('js/field/scene-data.js','utf8'),ctx);
const scene=ctx.window.FieldSceneData.scenes.cliff_sunset_to_fire;
const steps=scene.steps;
const cg=steps.filter(s=>s.cg&&!s.cg.hide).map(s=>s.cg.src);
assert.deepEqual(cg,[
 'assets/approved/game/cliff/sunset_background.png',
 'assets/approved/game/cliff/sunset_two_characters_back_view.png',
 'assets/approved/game/cliff/stargazing_seated.png',
 'assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png',
 'assets/approved/game/cliff/stargazing_standing_final.png'
]);
const indexOfTalk=id=>steps.findIndex(s=>s.talk===id);
const sunset=indexOfTalk('scene_cliff_sunset');
const night=indexOfTalk('scene_cliff_night');
const wind=indexOfTalk('scene_cliff_wind_stops');
assert(sunset>0&&night>sunset&&wind>night);
assert.equal(steps[wind-2].cg.src,'assets/approved/game/cliff/stargazing_standing_final.png');
assert.equal(steps[wind+1].cg.hide,true);
assert.equal(steps[wind+2].vista.id,'village_fire');
assert.equal(steps.filter(s=>'stage' in s).length,1);
assert.equal(steps.find(s=>'stage' in s).stage,4);
assert.equal(steps.at(-1).call,'cliffRunHome');
assert.equal(scene.requireStage,3);
console.log('Approved 5-CG cliff sequence and wind-stop timing PASS');
