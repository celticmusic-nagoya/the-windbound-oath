// Fixture-only source extraction. Missing declarations/boundaries must never run a stub.
const assert=require('node:assert/strict');
function productBlock(source,start,end,label,names){
 const match=start.exec(source);
 assert.ok(match,`fixture: ${label} declaration not found`);
 const stop=source.indexOf(end,match.index+match[0].length);
 assert.ok(stop>match.index,`fixture: ${label} end not found`);
 const block=source.slice(match.index,stop);
 assert.ok(block.trim(),`fixture: ${label} empty block`);
 for(const name of names)assert.match(block,new RegExp('^function '+name+'\\s*\\(','m'),`fixture: ${label} missing ${name}`);
 return block;
}
const dialogueBlock=source=>productBlock(source,/^function say\s*\(/m,'\nfunction camera(','dialogue',['say','closeDialogue']);
const portraitBlock=source=>productBlock(source,/^function storyPortraitPage\s*\(/m,'\nconst hillLines=','story portrait',['storyPortraitPage']);
module.exports={dialogueBlock,portraitBlock};
