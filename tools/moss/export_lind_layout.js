// Dumps the Lind village layout (js/field/lind-*.js) as JSON for tools/moss/build_rilde_village.py.  usage: node tools/moss/export_lind_layout.js > out.json
const fs=require('fs'),path=require('path'),vm=require('vm');
const root=path.join(__dirname,'..','..');
const win={};const ctx=vm.createContext({window:win,console});
for(const f of ['lind-content-bounds.js','lind-assets.js','lind-terrain-layout.js','lind-river.js','lind-npc-registry.js'])
  try{vm.runInContext(fs.readFileSync(path.join(root,'js/field',f),'utf8'),ctx,{filename:f});}catch(e){if(f!=='lind-river.js')throw e;}
const out={objects:win.LindFieldAssets.objects.map(o=>({id:o.id,label:o.label,path:o.path,x:o.x,y:o.y,width:o.width,height:o.height,draw:o.draw||null,layer:o.layer||null,motion:o.motion||null,category:o.category||null,collision:o.collision||null,collisions:o.collisions||null})),
  terrain:win.LindFieldAssets.terrain,layout:win.LindTerrainLayout};
const wb=win.LindFieldContentBounds.lind_wind_stone,ws=95/wb[4];   // landmark actor of js/field/lind-wind-stone.js (DEV-gated there, so rebuilt here)
out.windStone={id:'lind_wind_stone',x:695,y:490,width:95,height:Math.round(wb[5]*ws),collision:[14,100,70,23]};
out.npcs=win.LindNpcRegistry.npcs;
console.log(JSON.stringify(out));
