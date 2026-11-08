'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'../..');
const html=fs.readFileSync(path.join(root,'dev/field-motion-preview/index.html'),'utf8');
const script=fs.readFileSync(path.join(root,'dev/field-motion-preview/preview.js'),'utf8');
test('preview references only existing images',()=>{
  const refs=[...html.matchAll(/src="(\.\.\/\.\.\/img\/[^"]+\.png)"/g)].map(x=>x[1]);
  assert.equal(refs.length,3);
  for(const ref of refs) assert.ok(fs.existsSync(path.resolve(root,'dev/field-motion-preview',ref)),ref);
});
test('preview loads shared sampler without touching game index',()=>{
  assert.match(html,/src="\.\.\/\.\.\/js\/field\/field-sprite-motion\.js"/);
  assert.match(script,/FieldSpriteMotion\.sample/);
  const game=fs.readFileSync(path.join(root,'index.html'),'utf8');
  assert.doesNotMatch(game,/dev\/field-motion-preview|field-sprite-motion\.js/);
});
test('reduced motion and visibility are handled',()=>{
  assert.match(script,/prefers-reduced-motion: reduce/);
  assert.match(script,/document\.hidden/);
  assert.match(script,/pagehide/);
});
