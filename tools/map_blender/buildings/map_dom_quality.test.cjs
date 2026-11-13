const assert=require("node:assert/strict");
const policy=require("./map_graphics_policy.js");
const dom=require("./map_dom_quality.js");
const values=new Map();
const root={dataset:{},style:{setProperty:(k,v)=>values.set(k,v),removeProperty:k=>values.delete(k)}};
for(const preset of Object.keys(policy.PRESETS)){
 assert.equal(dom.apply(root,policy.resolve(preset)),preset);
 assert.equal(root.dataset.twoMapQuality,preset);
 assert.equal(values.get("--two-map-decorative-density"),String(policy.PRESETS[preset].vegetationDensity));
}
assert.equal(values.get("--two-map-shadow-opacity"),"0");
dom.clear(root);
assert.equal(root.dataset.twoMapQuality,undefined);
assert.equal(values.size,0);
assert.throws(()=>dom.apply(root,{preset:"invalid"}));
console.log("MAP-GFX-04 PASS");
