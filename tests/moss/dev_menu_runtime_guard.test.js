const assert=require('node:assert/strict');
const fs=require('node:fs');
for(const path of ['index.html','dev-fresh-20261108.html']){
 const s=fs.readFileSync(path,'utf8');
 assert(s.includes("['cliff_summit','03a　風見の断崖・頂上（CG確認）']"),path+' summit entry');
 assert(s.includes("['sunset','03　風見の断崖（入口）']"),path+' current sunset label');
 assert(!s.includes("['sunset','03　夕暮れ']"),path+' no obsolete sunset');
 assert(s.includes('new MutationObserver(()=>renderDevEvents())'),path+' DOM mutation guard');
 assert(s.includes("devMenuObserver.observe(devGridEl,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['data-jump']})"),path+' observer config');
 assert(s.includes("$('#devBtn').addEventListener('click',renderDevEvents,true)"),path+' opening guard');
 assert(s.includes("if(devGridEl.innerHTML!==expected)devGridEl.innerHTML=expected"),path+' no-op on unchanged DOM');
}
console.log('DEV menu runtime guard static regression PASS');
