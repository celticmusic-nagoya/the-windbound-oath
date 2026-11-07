/* Run: node tests/moss/cliff_presentation.test.js
 * Pure mock test; no browser or image files needed. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('js/field/cliff-presentation.js', 'utf8');
let loadSuccess = true;
const nodes = [];
const document = {
  createElement(tag) {
    const node = {tag, style:{}, classList:{add(){},remove(){},toggle(){}},
      setAttribute(){},removeAttribute(){},appendChild(child){this.child=child;}};
    nodes.push(node); return node;
  },
  body: {appendChild(){}}
};
class MockImage {
  constructor(){this.complete=false;this.naturalWidth=0;}
  set src(value){this._src=value;this.complete=true;this.naturalWidth=loadSuccess?1672:0;
    if(loadSuccess)this.onload?.();else this.onerror?.();}
  get src(){return this._src;}
}
const context={window:{},document,Image:MockImage,Promise};
vm.runInNewContext(source,context);
const api=context.window.CliffPresentation;
assert.equal(api.allowed('assets/approved/game/cliff/stargazing_standing_final.png'),true);
assert.equal(api.allowed('../secrets.png'),false);
assert.equal(api.allowed('assets/approved/game/academy/a.png'),false);
(async()=>{
  assert.equal(await api.show({src:'../bad.png'}),false);
  loadSuccess=false;
  assert.equal(await api.show({src:'assets/approved/game/cliff/missing.png'}),false);
  loadSuccess=true;
  assert.equal(await api.show({src:'assets/approved/game/cliff/stargazing_standing_final.png',alt:'starry sky'}),true);
  assert.equal(nodes[0].style.display,'block');
  api.hide();
  assert.equal(nodes[0].style.display,'none');
  console.log('cliff presentation mock tests: PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
