const assert=require('node:assert/strict');
const fs=require('node:fs');
const main=fs.readFileSync('index.html','utf8');
const fresh=fs.readFileSync('dev-fresh-20261108.html','utf8');
for(const s of [main,fresh]){
  assert(s.includes("['cliff_summit','03a　風見の断崖・頂上（CG確認）']"));
  assert(s.includes("enterWorldMap('cliff_moher_01_spiral_ascent','summit')"));
  assert(!s.includes("['sunset','03　夕暮れ']"));
}
assert(fresh.includes('20261108-fresh-entry-02'));
assert(fresh.includes('devHtmlRevision'));
assert(fresh.includes('js/field/cliff-presentation.js'));
assert(fresh.includes('css/style.css'));
console.log('Fresh independent entry retains game scripts, CG and summit jump PASS');
