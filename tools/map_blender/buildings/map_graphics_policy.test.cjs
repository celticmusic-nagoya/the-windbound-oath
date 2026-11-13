const assert=require('node:assert/strict');
const p=require('./map_graphics_policy.js');
assert.equal(Object.keys(p.PRESETS).length,4);
for(const name of Object.keys(p.PRESETS)){
 const c=p.resolve(name);
 assert.ok(c.renderScale>=.5&&c.renderScale<=1);
 assert.ok(c.vegetationDensity>0&&c.vegetationDensity<=1);
 const d=p.canvasSize(390,844,2,c);
 assert.ok(d.width>0&&d.height>0);
}
assert.equal(p.resolve('low',{renderScale:2}).renderScale,1);
assert.throws(()=>p.resolve('invalid'));
assert.throws(()=>p.resolve('high',{renderScale:NaN}));
assert.deepEqual(p.canvasSize(100,200,1,p.resolve('low')),{width:50,height:100});
assert.equal(p.visibleDecoration('flower-1',12,1),true);
assert.equal(p.visibleDecoration('flower-1',12,0),false);
assert.equal(p.visibleDecoration('flower-1',12,.5),p.visibleDecoration('flower-1',12,.5));
console.log('MAP-GFX-01 PASS');
