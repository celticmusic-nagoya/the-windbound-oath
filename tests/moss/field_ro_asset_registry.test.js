'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../..');
const manifest=JSON.parse(fs.readFileSync(path.join(root,'data/field-ro-asset-registry.json'),'utf8'));
test('registry is planning-only, never falsely approved',()=>{
  assert.equal(manifest.status,'planning_only');
  assert.equal(manifest.visualStyle.humanHeadToBodyRatio,2.8);
  assert.deepEqual(manifest.projection.downwardAngleDegrees,[25,30]);
  assert.deepEqual(manifest.requiredDirections,['down','left','right','up']);
  assert.deepEqual(manifest.assets.map(x=>x.id),['aidan','emma','goblin']);
  for(const asset of manifest.assets)assert.equal(asset.status,'awaiting_new_art');
});
test('every original reference path exists and is unique',()=>{
  const seen=new Set();
  for(const asset of manifest.assets){
    assert.ok(asset.referencePaths.length);
    for(const p of asset.referencePaths){
      assert.ok(!p.startsWith('/')&&!p.includes('..'));
      assert.ok(!seen.has(p),p);seen.add(p);
      assert.ok(fs.existsSync(path.join(root,p)),p);
    }
  }
});
test('legacy walk PRs remain held',()=>assert.deepEqual(manifest.legacyWalkPRs,{status:'hold',numbers:[139,140,144,145,153,154]}));
test('no newly approved pixel sprite is claimed',()=>{
  for(const a of manifest.assets){assert.match(a.targetDirectory,/^assets\/candidates\/field-ro\//);assert.equal(a.sourceStatus,'existing_field_art_not_new_pixel_art');}
});
