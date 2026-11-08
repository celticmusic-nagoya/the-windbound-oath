const assert=require('node:assert/strict');const fs=require('node:fs');
const scene=fs.readFileSync('js/field/scene-data.js','utf8');
const css=fs.readFileSync('css/style.css','utf8');
const night=scene.indexOf("{cg: {src: 'assets/approved/game/cliff/stargazing_seated.png'");
const nightTalk=scene.indexOf("{talk: 'scene_cliff_night'}");
const standing=scene.indexOf("{cg: {src: 'assets/approved/game/cliff/stargazing_standing_final.png'");
const windBackground=scene.indexOf("{cg: {src: 'assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png'");
const windTalk=scene.indexOf("{talk: 'scene_cliff_wind_stops'}");
assert(night>=0&&night<nightTalk&&nightTalk<standing&&standing<windBackground&&windBackground<windTalk,'seated CG persists, standing unchanged, background on wind stop');
for(const file of ['index.html','dev-fresh-20261108.html']){
 const html=fs.readFileSync(file,'utf8');
 for(const asset of ['road/curve_reveal_APPROVED_user_reference.jpg','raid/attack_with_characters_APPROVED_user_reference.jpg','raid/attack_background_only.png'])assert(html.includes(asset),file+' '+asset);
 assert(html.includes("if(returnIndex===5)$('#returnScene').classList.add('road-reveal-active')"));
 assert(html.includes("if(returnIndex===6){$('#returnScene').classList.remove('road-reveal-active');$('#returnScene').classList.add('raid-composite-active');}"));
 assert(html.includes("if(returnIndex===8){$('#returnScene').classList.remove('raid-composite-active');$('#returnScene').classList.add('raid-background-active');}"));
 assert(!html.includes("if(returnIndex===6){ $('#returnGoblin').style.display='block'"),'no goblin battle sprite insertion');
}
assert(css.includes('raid-composite-active #returnRaidCompositeCg{display:block}'));
assert(css.includes('#returnAidan,#returnFiona,#returnGoblin){display:none!important}'));
console.log('Approved CG sequence static QA PASS');
