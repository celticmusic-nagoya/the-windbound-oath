'use strict';
const assert=require('node:assert/strict');
const {test}=require('node:test');
const r=require('../../js/field/field-headgear-renderer.js');
const directions=['down','left','right','up'];
const mk=(name)=>Object.fromEntries(directions.map(d=>[d,name+'/'+d+'.png']));
test('all four directions select matching base and overlay',()=>{
 for(const d of directions){const plan=r.plan(mk('base'),[{slot:'middle',directions:mk('glasses')}],d);assert.equal(plan[0].src,'base/'+d+'.png');assert.equal(plan[1].src,'glasses/'+d+'.png');}
});
test('deterministic upper middle lower z-order',()=>{const p=r.plan(mk('base'),[{slot:'lower',directions:mk('scarf')},{slot:'upper',directions:mk('ribbon')},{slot:'middle',directions:mk('glasses')}],'up');assert.deepEqual(p.map(x=>x.slot),['base','upper','middle','lower']);});
test('reject missing sprites and duplicate slots',()=>{assert.throws(()=>r.plan(mk('base'),[{slot:'upper',directions:{}}],'down'));assert.throws(()=>r.plan(mk('base'),[{slot:'upper',directions:mk('a')},{slot:'upper',directions:mk('b')}],'down'));assert.throws(()=>r.plan(mk('base'),[],'diagonal'));});
test('DOM render layers share one parent for motion',()=>{const children=[];const documentRef={createDocumentFragment:()=>({appendChild(x){this.child=x}}),createElement:tag=>({tag,style:{},dataset:{},appendChild(x){(this.children||(this.children=[])).push(x)}})};const container={replaceChildren(x){children.push(x)}};const w=r.render(documentRef,container,[{slot:'base',src:'a.png'},{slot:'middle',src:'b.png'}],{width:80,height:120});assert.equal(w.children.length,2);assert.equal(w.children[0].style.transform,undefined);assert.equal(w.style.height,'120px');assert.equal(children.length,1);});
