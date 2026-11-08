// PROLOGUE-ESCAPE-RETURN-INTEGRATION-01
// Run: node tests/prologue-escape-return-static.test.cjs
// Static integration contract; does not replace browser, Android or SAVE replay QA.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const html = fs.readFileSync('index.html','utf8');
const attack = fs.readFileSync('js/field/talk-data-attack.js','utf8');
const scenes = fs.readFileSync('js/field/talk-data-scenes.js','utf8');
const progress = fs.readFileSync('js/prologue-progress.js','utf8');
const between = (text, start, end) => {
  const i = text.indexOf(start); assert(i>=0, 'missing '+start);
  const j = text.indexOf(end, i+start.length); assert(j>i,'missing '+end);
  return text.slice(i+start.length,j);
};
const cases = [
 ['12 escape pages', () => assert.equal((between(attack,'const ATTACK_ESCAPE_LINES = Object.freeze([',']);').match(/^\s*'/gm)||[]).length,12)],
 ['12 escape portraits', () => assert.equal(JSON.parse(between(attack,'const ATTACK_ESCAPE_PORTRAITS = Object.freeze(',');')).length,12)],
 ['approved river jump', () => ['……川だ！','飛ぶぞ！ 手を離すな！','……うん！'].forEach(x=>assert(attack.includes(x)))],
 ['jump visual cue', () => assert(html.includes('if(escapeIndex===9)'))],
 ['Moss Forest riverbank', () => assert(scenes.includes('モスの森の岸辺'))],
 ['no old cliff arrival', () => assert(!scenes.includes('崖の上へは戻れそうにない'))],
 ['15 return pages', () => assert.equal((between(html,'const rildeReturnLines=[','];').match(/^\s*'/gm)||[]).length,15)],
 ['15 return portraits', () => assert.equal((between(html,'const rildeReturnPortraitPages=[','];').match(/\{char:/g)||[]).length,15)],
 ['Emma reunion', () => ['フィオナ「エマぁっ！！」','エマ「……おかえり、フィオナ。」','フィオナ「……ただいま……エマ……！」'].forEach(x=>assert(html.includes(x)))],
 ['return click routing', () => assert(html.includes('if(rildeReturnActive){advanceRildeReturnScene();return;}'))],
 ['return save guard', () => assert(html.includes('if(rildeReturnActive||window.BattleLoading?.canSave'))],
 ['fort after return', () => assert(html.includes("startFortFinale();\n $('#aftermathScene').style.display='none';"))],
 ['legacy stage14 fort restore', () => assert(progress.includes("stage===14?'FORT_FINALE'"))],
 ['legacy stage13 aftermath restore', () => assert(progress.includes("stage===13?'AFTERMATH'"))],
 ['equipment grant unchanged', () => assert(html.includes('if(fortIndex===6)grantStarterGear(true)'))],
];
let passed=0;
for(const [name,run] of cases){try{run();console.log('PASS',name);passed++;}catch(e){console.error('FAIL',name,e.message);process.exitCode=1;}}
console.log(passed+'/'+cases.length+' static integration checks passed');
