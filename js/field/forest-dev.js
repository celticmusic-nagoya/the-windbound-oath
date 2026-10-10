/* Dev harness for Moss Forest maps: keyboard + click-to-move on the shared field modules. */
(async function () {
  'use strict';
  const q=new URLSearchParams(location.search),mapUrl=q.get('map')||'../data/maps/moss_forest_01_sunlit_path.json';
  const world=document.getElementById('world'),viewport=document.getElementById('viewport'),player=document.getElementById('player'),hud=document.getElementById('hud');
  await ForestLoader.loadAssets();
  const map=await ForestLoader.load(mapUrl);
  const flags={moss_a3_seal_open:false,moss_a3_lou_found:false};
  (q.get('flags')||'').split(',').filter(Boolean).forEach(n=>flags[n]=true);
  const f=ForestLoader.mount(map,world,{flags});
  FieldNavigation.configure({width:map.world.width,height:map.world.height,grid:32,maxNodes:40000});
  const s=f.spawn();let px=s.x,py=s.y,target=null;const keys={};
  addEventListener('keydown',e=>{keys[e.key.toLowerCase()]=true;target=null;FieldNavigation.cancel();});addEventListener('keyup',e=>keys[e.key.toLowerCase()]=false);
  viewport.addEventListener('pointerdown',e=>{const w=FieldCamera.screenToWorld(world,e.clientX,e.clientY);
    target=FieldNavigation.destination(w.x-17,w.y-42,f.blocked);});
  // Seal placeholder (one node, shown only while closed) + dev stand-ins for the 3 corruption symbols.
  const prologue=map.story&&map.story.prologue,sealB=map.collision.blockers.find(b=>b.id==='cb_a3_seal');
  let sealNode=null,symbols=[];
  function mkNode(cls,x,y,w,h,bg,label){const d=document.createElement('div');d.className=cls;d.textContent=label||'';
    Object.assign(d.style,{position:'absolute',left:x+'px',top:y+'px',width:w+'px',height:h+'px',background:bg,zIndex:String(Math.round(y+h)),pointerEvents:'none',font:'10px sans-serif',color:'#fff'});world.appendChild(d);return d;}
  function syncSeal(){const want=sealB&&!flags.moss_a3_seal_open;
    if(want&&!sealNode){const r=sealB.rects[0];sealNode=mkNode('forest-seal',r[0],r[1]-60,r[2],r[3]+60,'#6b4fa0cc','seal');}
    else if(!want&&sealNode){sealNode.remove();sealNode=null;}}
  if(prologue&&prologue.symbols)symbols=prologue.symbols.map(sy=>({...sy,alive:!flags['sym_'+sy.id+'_done'],node:null}));
  function syncSymbols(){let done=0;for(const sy of symbols){
      if(sy.alive&&!sy.node)sy.node=mkNode('forest-symbol',sy.x-20,sy.y-60,40,60,'#b0307a',sy.field);
      if(!sy.alive){done++;if(sy.node){sy.node.remove();sy.node=null;}}}
    return done;}
  function touchSymbols(){for(const sy of symbols)if(sy.alive&&Math.hypot(px+17-sy.x,py+42-sy.y)<=sy.touchRadius){sy.alive=false;}
    const n=syncSymbols();if(n>=3&&!flags.moss_a3_seal_open)api.setFlag('moss_a3_seal_open',true);}
  const stream=map.terrain.waters.find(w=>w.kind==='stream');
  function tick(){
    let dx=(keys.d||keys.arrowright?1:0)-(keys.a||keys.arrowleft?1:0),dy=(keys.s||keys.arrowdown?1:0)-(keys.w||keys.arrowup?1:0);
    if(dx||dy){const n=Math.hypot(dx,dy),step=FieldMovement.settings.pointerStep*(inStream()?.85:1);
      const r=FieldMovement.advance(px,py,dx/n*step,dy/n*step,f.blocked,{bounds:map.world});px=r.x;py=r.y;}
    else if(target){const r=FieldNavigation.follow(px,py,target,f.blocked);px=r.x;py=r.y;target=r.target;}
    FieldCamera.render(world,viewport,player,px,py);
    const sc=FieldCamera.scale,vw=viewport.clientWidth/sc,vh=viewport.clientHeight/sc;
    const rc=world.getBoundingClientRect(),vx=-rc.left/sc,vy=-rc.top/sc;
    f.update({x:vx,y:vy,width:vw,height:vh});
    if(symbols.length&&api.frames%6===0)touchSymbols();
    player.style.zIndex=String(Math.round(py+42));player.style.display='block';
    api.frames++;hud.textContent=`feet ${Math.round(px+17)},${Math.round(py+42)}  nodes ${f.cull.stats.live} (peak ${f.cull.stats.peak}/${map.culling.maxLiveNodes})  canvases ${f.layer.stats.canvases}  rects ${f.stats.rects}\nWASD/arrows or click`;
    requestAnimationFrame(tick);}
  function inStream(){const fx=px+17,fy=py+42;return stream&&ForestScatter.lineDist(fx,fy,stream.points)<stream.width/2;}
  const api=window.ForestDev={frames:0,map,forest:f,get pos(){return {x:px,y:py,fx:px+17,fy:py+42};},
    setFlag(n,v){flags[n]=Boolean(v);syncSeal();},
    get flags(){return {...flags};},get symbolsLeft(){return symbols.filter(s=>s.alive).length;},
    defeatSymbol(i){if(symbols[i]){symbols[i].alive=false;touchSymbols();}},
    get sealNodes(){return document.querySelectorAll('.forest-seal').length;},
    teleportFeet(x,y){px=x-17;py=y-42;target=null;},
    goFeet(x,y){target=FieldNavigation.destination(x-17,y-42,f.blocked);return Boolean(target);},
    get target(){return target;},get status(){return FieldNavigation.status;}};
  syncSeal();syncSymbols();
  requestAnimationFrame(tick);
})();
