// Negative-control process only: mutate reads in memory, never production files on disk.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),read=fs.readFileSync,fault=process.env.QA_FIXTURE_FAULT;
const mutations={
 'missing-say':['index.html','function say(t, portrait)','function omittedSay(t, portrait)'],
 'missing-dialogue-end':['index.html','\nfunction camera(){','\nfunction omittedCamera(){'],
 'missing-portrait':['index.html','function storyPortraitPage(','function omittedPortraitPage('],
 'stale-narration':['js/field/rilde-village.js','revision!==LoadCoordinator.dialogueRevision','false'],
 'broken-restore':['js/save-continue.js','await applyGrowthData(data,route,checkpoint,owner);','/* injected missing restore */']
};
assert.ok(mutations[fault],'unknown fixture fault');
const [file,before,after]=mutations[fault];
fs.readFileSync=function(name,...args){
 const source=read.call(this,name,...args);
 if(typeof name==='string'&&path.resolve(name)===path.join(root,file)){
  assert.equal(typeof source,'string');assert.ok(source.includes(before),'fault injection target missing');
  return source.replace(before,after);
 }
 return source;
};
