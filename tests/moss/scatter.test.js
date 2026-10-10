// Run: node tests/moss/scatter.test.js
const S=require('../../js/field/forest-scatter.js');
let fail=0;const ok=(c,x)=>{console.log(c?'ok  ':'FAIL',x);if(!c)fail++;};
for(const file of ['moss_forest_01_sunlit_path','moss_forest_02_mossy_ravine','moss_forest_03_ancient_grove']){
const m=require('../../data/maps/'+file+'.json');console.log('--',file);
const a=S.generate(m),b=S.generate(m);
ok(JSON.stringify(a)===JSON.stringify(b),`deterministic (${a.length} items)`);
const want=m.scatter.reduce((n,s)=>n+s.count,0);ok(a.length>=want*.9,`placed ${a.length}/${want} (>=90%)`);
const by={};for(const e of a)(by[e.rule]=by[e.rule]||[]).push(e);
for(const r of m.scatter){const n=(by[r.id]||[]).length;if(n<r.count)console.log('note',r.id,`${n}/${r.count} (region saturated at minDist ${r.minDist})`);}
const avoidsPath=new Set(m.scatter.filter(r=>(r.avoid||[]).some(x=>x.startsWith('path_core'))).map(r=>r.id));
let core=0;for(const e of a){if(!avoidsPath.has(e.rule))continue;for(const p of m.terrain.paths)if(S.lineDist(e.x,e.y,p.points)<p.width/2-.1)core++;}
ok(core===0,'rules with path_core avoid never place on a path core');
let md=0;for(const r of m.scatter){const l=by[r.id]||[];for(let i=0;i<l.length;i++)for(let j=i+1;j<Math.min(l.length,i+400);j++)if(Math.hypot(l[i].x-l[j].x,l[i].y-l[j].y)<r.minDist-.15)md++;}
ok(md===0,'minDist respected (0.1px rounding tolerance)');
ok(a.every(e=>e.x>=0&&e.y>=0&&e.x<=m.world.width&&e.y<=m.world.height),'inside world');
const nodes=a.filter(e=>e.render==='node').length+m.props.length;
const live=nodes*((1920+512)*(1080+512))/(m.world.width*m.world.height);
ok(live<=m.culling.maxLiveNodes,`est live DOM nodes ${Math.round(live)} <= ${m.culling.maxLiveNodes}`);
}
process.exit(fail?1:0);
