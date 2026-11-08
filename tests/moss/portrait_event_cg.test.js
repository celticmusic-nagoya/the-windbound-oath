const assert=require('node:assert/strict'),fs=require('node:fs');
const css=fs.readFileSync('css/style.css','utf8');
const cliff=fs.readFileSync('js/field/cliff-presentation.js','utf8');
assert(cliff.includes("ambient.src = opts.src;"));
assert(cliff.includes('object-fit:contain;object-position:center'));
assert(cliff.includes("ambient?.removeAttribute('src')"));
assert(css.includes('object-fit:contain;object-position:center center'));
assert(css.includes('height:calc(100% - clamp(132px,19vh,210px))'));
for(const p of ['index.html','dev-fresh-20261108.html']){
 const s=fs.readFileSync(p,'utf8');
 assert(s.includes("if(returnIndex===5){window.TalkPortrait?.close('story:returnScene');"));
 assert(s.includes("if(returnIndex===6){window.TalkPortrait?.close('story:returnScene');"));
 assert(s.includes("if(returnIndex===8){$('#returnScene').classList.remove('raid-composite-active');"));
 assert(s.includes("id=\"returnRaidCompositeCg\""));
}
console.log('Portrait CG full-frame and reveal portrait suppression PASS');
