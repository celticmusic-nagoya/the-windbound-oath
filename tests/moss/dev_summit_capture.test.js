const assert=require('node:assert/strict');const fs=require('node:fs');
for(const path of ['index.html','dev-fresh-20261108.html']){
 const s=fs.readFileSync(path,'utf8');
 assert(s.includes("devGridEl.addEventListener('click',e=>{"),path+' capture listener');
 assert(s.includes("e.preventDefault();e.stopImmediatePropagation();"),path+' suppress stale bubbling');
 assert(s.includes("e.target.closest('[data-jump=\"cliff_summit\"]')"),path+' summit target');
 assert(s.includes("enterWorldMap('cliff_moher_01_spiral_ascent','summit')"),path+' summit map');
 assert(s.includes("Promise.resolve(task).then("),path+' await navigation');
 assert(s.includes("message.id='devSummitError'"),path+' user visible error');
 assert(s.indexOf("devGridEl.addEventListener('click',e=>{")<s.indexOf("$('#devGrid').onclick=e=>"),path+' handler order');
}
console.log('Summit capture and error feedback static QA PASS');
