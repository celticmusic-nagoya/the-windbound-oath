/* Approved road/raid composite transition regression. */
const assert=require('node:assert/strict'),fs=require('node:fs');
const css=fs.readFileSync('css/style.css','utf8');
for(const path of ['index.html','dev-fresh-20261108.html']){
 const html=fs.readFileSync(path,'utf8');
 const start=html.indexOf('function startReturnScene(){');const end=html.indexOf('function showBurningVillageVisuals(){',start);
 assert(start>=0&&end>start);const scene=html.slice(start,end);
 for(const [id,file] of [['returnRoadRevealCg','road/curve_reveal_APPROVED_user_reference.jpg'],['returnRaidCompositeCg','raid/attack_with_characters_APPROVED_user_reference.jpg'],['returnRaidCg','raid/attack_background_only.png']]){
  assert(html.includes('id="'+id+'" src="assets/approved/game/rilde_story/'+file+'"'));
 }
 assert(scene.includes('returnIndex===5')&&scene.includes("classList.add('road-reveal-active')"));
 assert(scene.includes('returnIndex===6')&&scene.includes("classList.add('raid-composite-active')"));
 assert(scene.includes('returnIndex===8')&&scene.includes("classList.add('raid-background-active')"));
 assert(scene.includes("classList.remove('raid-cg-active','road-reveal-active','raid-composite-active','raid-background-active')"));
 assert(scene.includes('enterBurningVillage()'));
}
for(const selector of ['#returnScene.road-reveal-active #returnRoadRevealCg{display:block}', '#returnScene.raid-composite-active #returnRaidCompositeCg{display:block}', '#returnScene.raid-background-active #returnRaidCg{display:block}'])assert(css.includes(selector));
assert(css.includes('#returnAidan,#returnFiona,#returnGoblin){display:none!important}'));
const cliff=fs.readFileSync('js/field/cliff-presentation.js','utf8');
assert(cliff.includes('z-index:172'));assert(cliff.includes("classList?.add('cliff-cg-active')"));assert(cliff.includes("classList?.remove('cliff-cg-active')"));
assert(css.includes('body.cliff-cg-active #msg{z-index:200!important}'));
assert(css.includes('body.cliff-cg-active #talkPortrait{z-index:201!important}'));
console.log('Approved raid composition and clean portrait transition PASS');
