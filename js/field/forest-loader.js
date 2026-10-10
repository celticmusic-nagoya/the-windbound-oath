/* Moss Forest map runtime (M1). Builds collision, chunk layer and culled entity nodes from a
 * runtime JSON produced by tools/moss/export_runtime.py. Depends on FieldCollision, FieldCulling,
 * ForestScatter, ForestLayer. Knows nothing about Lind, story saves or battle. */
(function () {
  'use strict';
  const FOOT={ax:17,ay:42};   // actor top-left = feet - (17,42)
  const SIZE=[[/^tree_log/,[180,26]],[/^prop_bridge_wood/,[110,230]],[/^prop_root_arch/,[240,200]],[/^fx_/,[160,190]],[/^tree_.*_L/,[96,140]],[/^tree_.*_M/,[70,104]],[/^tree_/,[60,90]],[/^rock_L/,[60,40]],[/^rock_M/,[44,28]],[/^rock_/,[30,20]],
    [/^veg_shrub/,[40,30]],[/^prop_/,[40,36]],[/^anc_/,[44,56]]];
  const COLOR=[[/^tree_log/,'#7a5a34'],[/^prop_bridge/,'#c8955a'],[/^fx_/,'#cfe9f566'],[/^tree_/,'#2f6b34'],[/^rock_/,'#8b8b84'],[/^veg_shrub/,'#3f8a3a'],[/^prop_/,'#8a5a2b'],[/^anc_/,'#9aa3a8']];
  const pick=(table,a,d)=>{for(const [re,v] of table)if(re.test(a))return v;return d;};
  // ---- art manifest (img/field/moss/manifest.json): real assets override stand-ins; missing -> coloured placeholder ----
  const ROOT=document.currentScript?new URL('../../',document.currentScript.src).href:'';   // dev/ pages resolve assets too
  const art={manifest:null,images:new Map(),ground:null,loading:null};
  function compile(rules){return (rules||[]).map(r=>({re:new RegExp(r.match),r}));}
  function resolve(list,asset){for(const {re,r} of list)if(re.test(asset))return r.file?r:null;return null;}
  function img(file){
    if(art.images.has(file))return art.images.get(file);
    const im=new Image();im.decoding='async';im.src=ROOT+art.manifest.base+file;art.images.set(file,im);return im;
  }
  async function loadAssets(){
    if(art.loading)return art.loading;
    art.loading=(async()=>{
      try{
        const r=await fetch(ROOT+'img/field/moss/manifest.json');if(!r.ok)throw new Error('no manifest');
        const m=await r.json();art.manifest=m;art.node=compile(m.node);art.layer=compile(m.layer);
        const files=new Set([m.ground.grass,m.ground.dirt,...[...m.node,...m.layer,...Object.values(m.entity||{})].filter(x=>x&&x.file).map(x=>x.file)]);
        await Promise.all([...files].map(async f=>{const im=img(f);try{await im.decode();}catch(e){art.images.delete(f);}}));
        art.ground={grass:art.images.get(m.ground.grass)||null,dirt:art.images.get(m.ground.dirt)||null,tile:m.ground.tile||384};
      }catch(e){art.manifest=null;art.ground=null;}   // no art: everything falls back to placeholders
    })();
    return art.loading;
  }
  // Runtime entities that are not map assets (chest, symbol, seal, Lou, Fiona): manifest.entity[key] = {file,w,h}
  function entityArt(key){if(!art.manifest)return null;const r=art.manifest.entity&&art.manifest.entity[key];const im=r&&r.file&&art.images.get(r.file);return im?{src:im.src,w:r.w,h:r.h}:null;}
  function nodeArt(asset){if(!art.manifest)return null;const r=resolve(art.node,asset);const im=r&&art.images.get(r.file);return im?{im,w:r.w,h:r.h}:null;}
  function layerArt(asset){if(!art.manifest)return null;const r=resolve(art.layer,asset);const im=r&&art.images.get(r.file);return im?{im,w:r.w,h:r.h}:null;}
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
    for(const e of ents){
      const sp=nodeArt(e.asset),[w,h]=sp?[sp.w,sp.h]:pick(SIZE,e.asset,[36,36]);
      cull.add({id:e.id||(e.rule+':'+e.x+','+e.y),x:e.x-w/2,y:e.y-h,w,h,create(){
        const d=document.createElement(sp?'img':'div');d.className='forest-ent';d.dataset.asset=e.asset;
        Object.assign(d.style,{position:'absolute',left:e.x-w/2+'px',top:e.y-h+'px',width:w+'px',height:h+'px',zIndex:String(e.z!=null?e.z:Math.round(e.y)),pointerEvents:'none'});
        if(sp){d.src=sp.im.src;d.draggable=false;d.alt='';if(e.flip||((e.x*7+e.y*13)|0)%2)d.style.transform='scaleX(-1)';}
        else Object.assign(d.style,{background:pick(COLOR,e.asset,'#668'),borderRadius:/^tree_|^veg_/.test(e.asset)?'50% 50% 20% 20%':'4px',opacity:'.92'});
        return d;}});}
    const layer=ForestLayer.create({map,parent:world,items:layerItems,chunk:512,margin:1,ground:art.manifest?art.ground:null,sprite:layerArt});
    const stats={entities:ents.length,layerItems:layerItems.length,rects:solid.shapes.length,buildMs:Math.round(performance.now()-t0)};
    function destroy(){cull.clear();layer.destroy();world.querySelectorAll('.forest-ent,.forest-chunk').forEach(n=>n.remove());}
    return {blocked:solid.blocked,solid,cull,layer,stats,flags,destroy,
      update(view){layer.update(view);cull.update(view);},
      spawn(id){const s=map.spawns.points[id||map.spawns.default];return {x:s.x-FOOT.ax,y:s.y-FOOT.ay,facing:s.facing};}};
  }
  async function load(url){const r=await fetch(url);if(!r.ok)throw new Error('map load failed: '+url);return r.json();}
  window.ForestLoader=Object.freeze({load,loadAssets,entityArt,mount,FOOT,get art(){return art;}});
})();
