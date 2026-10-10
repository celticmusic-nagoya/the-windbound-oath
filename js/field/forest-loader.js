/* Moss Forest map runtime (M1). Builds collision, chunk layer and culled entity nodes from a
 * runtime JSON produced by tools/moss/export_runtime.py. Depends on FieldCollision, FieldCulling,
 * ForestScatter, ForestLayer. Knows nothing about Lind, story saves or battle. */
(function () {
  'use strict';
  const FOOT={ax:17,ay:42};   // actor top-left = feet - (17,42)
  const SIZE=[[/^tree_.*_L/,[96,140]],[/^tree_.*_M/,[70,104]],[/^tree_/,[60,90]],[/^rock_L/,[60,40]],[/^rock_M/,[44,28]],[/^rock_/,[30,20]],
    [/^veg_shrub/,[40,30]],[/^prop_/,[40,36]],[/^anc_/,[44,56]]];
  const COLOR=[[/^tree_/,'#2f6b34'],[/^rock_/,'#8b8b84'],[/^veg_shrub/,'#3f8a3a'],[/^prop_/,'#8a5a2b'],[/^anc_/,'#9aa3a8']];
  const pick=(table,a,d)=>{for(const [re,v] of table)if(re.test(a))return v;return d;};
  function entities(map,scatter){
    const list=map.props.map(p=>({...p,rule:'prop'}));
    for(const e of scatter)if(e.render==='node')list.push(e);
    return list;
  }
  function collision(map,ents,flags){
    const blockers=[];
    map.collision.edgeBlockers.forEach((b,i)=>blockers.push({...b,id:'edge'+i}));
    for(const b of map.collision.blockers)blockers.push(b);
    const presets=map.collision.presets||{};
    ents.forEach((e,n)=>{if(e.noCollision)return;const pr=presets[e.asset.replace(/_\d+$/,'')];if(!pr)return;
      blockers.push({id:(e.id||e.rule+n),shape:'rects',rects:pr.map(r=>[e.x+(e.flip?-r[0]-r[2]:r[0]),e.y+r[1],r[2],r[3]])});});
    return FieldCollision.compileMap(blockers,n=>flags[n]);
  }
  function mount(map,world,options={}) {
    const flags=options.flags||{};
    const t0=performance.now();
    const all=ForestScatter.generate(map),ents=entities(map,all);
    const layerItems=all.filter(e=>e.render==='layer');
    const solid=collision(map,ents,flags);
    world.style.width=map.world.width+'px';world.style.height=map.world.height+'px';world.style.position='relative';
    const cull=FieldCulling.create({chunk:map.culling.chunk,margin:map.culling.margin,maxLiveNodes:map.culling.maxLiveNodes,parent:world});
    for(const e of ents){const [w,h]=pick(SIZE,e.asset,[36,36]);
      cull.add({id:e.id||(e.rule+':'+e.x+','+e.y),x:e.x-w/2,y:e.y-h,w,h,create(){
        const d=document.createElement('div');d.className='forest-ent';d.dataset.asset=e.asset;
        Object.assign(d.style,{position:'absolute',left:e.x-w/2+'px',top:e.y-h+'px',width:w+'px',height:h+'px',zIndex:String(Math.round(e.y)),
          background:pick(COLOR,e.asset,'#668'),borderRadius:/^tree_|^veg_/.test(e.asset)?'50% 50% 20% 20%':'4px',opacity:'.92',pointerEvents:'none'});
        return d;}});}
    const layer=ForestLayer.create({map,parent:world,items:layerItems,chunk:512,margin:1});
    const stats={entities:ents.length,layerItems:layerItems.length,rects:solid.shapes.length,buildMs:Math.round(performance.now()-t0)};
    return {blocked:solid.blocked,solid,cull,layer,stats,flags,
      update(view){layer.update(view);cull.update(view);},
      spawn(id){const s=map.spawns.points[id||map.spawns.default];return {x:s.x-FOOT.ax,y:s.y-FOOT.ay,facing:s.facing};}};
  }
  async function load(url){const r=await fetch(url);if(!r.ok)throw new Error('map load failed: '+url);return r.json();}
  window.ForestLoader=Object.freeze({load,mount,FOOT});
})();
