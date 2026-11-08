const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={window:{}};vm.runInNewContext(fs.readFileSync('js/field/portrait-registry.js','utf8'),ctx);
const r=ctx.window.PortraitRegistry;
for(const id of ['aidan','fiona','lou','emma']){
 assert(r.has(id),id+' registered');
 const normal=r.imageUrl(id,'normal');assert(fs.existsSync(normal),id+' normal portrait exists');
 for(const face of r.get(id).blink.faces){
  const b=r.blinkOf(id,face);assert(b&&b.eyes,id+' '+face+' blink configured');
  for(const eye of Object.values(b.eyes))for(const url of eye.urls)assert(fs.existsSync(url),id+' missing '+url);
 }
 console.log(id+' normal + '+r.get(id).blink.faces.length+' blinking faces: all overlay PNGs exist');
}
const css=fs.readFileSync('css/style.css','utf8');assert(css.includes('#talkPortrait canvas{\n -webkit-mask-image:'));assert(css.includes('#talkPortrait[data-side="left"] canvas{'));
const talk=fs.readFileSync('js/field/talk-data.js','utf8');assert(!talk.includes('"char":"emma","face":"smile"'));assert(!talk.includes('"char":"emma","face":"relieved"'));
console.log('Portrait edges + Emma open-eye expression fallback PASS');
