import assert from 'node:assert/strict';
import {selectOak,mixOak} from './select_oak_v88.mjs';
let n=0;const ok=x=>{assert.ok(x);n++};const near=(a,b)=>Math.abs(a-b)<1e-7;
const at=(az,el,spanPx=9,previous='mesh')=>{const a=az*Math.PI/180,e=el*Math.PI/180;return selectOak({direction:[Math.cos(a)*Math.cos(e),Math.sin(e),-Math.sin(a)*Math.cos(e)],spanPx,previous})};
for(let az=0;az<360;az+=45)for(let el of [-35,0,35]){
  const r=at(az,el);ok(r.mode==='impostor');ok(r.weights.length===1&&r.weights[0].col===az/45&&r.weights[0].row===(el+35)/35);
}
const r=at(22.5,17.5);ok(r.weights.length===4&&r.weights.every(w=>near(w.weight,.25)));ok(near(r.weights.reduce((s,w)=>s+w.weight,0),1));
ok(at(0,0,10).mode==='impostor');ok(at(0,0,11).mode==='mesh');ok(at(0,0,12,'impostor').mode==='impostor');ok(at(0,0,12.01,'impostor').mode==='mesh');ok(at(0,36).mode==='mesh');
const a=at(0,0);ok(near(a.right[2],-1));ok(near(a.up[1],1));ok(a.corners[0][2]>a.corners[1][2]);ok(a.corners[0][1]<a.corners[3][1]);
for(let i=0;i<3;i++)ok(near(a.corners.reduce((s,v)=>s+v[i],0)/4,[.033129096031188965,2.4933953285217285,-.17469823360443115][i]));
const wrap=at(337.5,0);ok(wrap.weights.length===2&&wrap.weights.some(w=>w.col===7)&&wrap.weights.some(w=>w.col===0));ok(wrap.weights.every(w=>near(w.weight,.5)));
ok(mixOak([[1,0,0,0],[0,1,0,1]],[.5,.5]).every((v,i)=>near(v,[0,1,0,.5][i])));ok(mixOak([[1,0,0,0],[0,1,0,0]],[.5,.5]).every(v=>v===0));
assert.throws(()=>selectOak({direction:[0,0,0],spanPx:1}));n++;
assert.throws(()=>selectOak({direction:[NaN,0,0],spanPx:1}));n++;
console.log(`${n}/${n} PASS (pure numeric contract, no renderer)`);
