/* Moss Forest runtime (M4). Hosts the three Moss Forest maps (A1 -> A2 -> A3) inside #forestScene:
 * map switching with fades, click/keyboard movement, culled rendering, treasure, transitions,
 * event zones, the A3 seal and the corruption symbols.
 * Story knowledge lives in moss-forest-story.js and reaches this module only through hooks.
 * Depends on FieldCollision/Movement/Navigation/Camera/Culling and ForestScatter/Layer/Loader. */
(function () {
  'use strict';
  const FOOT={ax:17,ay:42};
  const MAP_BASE='data/maps/';
  const cache=new Map();
  const S={configured:false,active:false,busy:false,map:null,forest:null,mapId:null,x:0,y:0,fx:0,fy:0,target:null,
    flags:{moss_a3_seal_open:false,moss_a3_lou_found:false,moss_a3_lou_rescued:false},opened:new Set(),fired:new Set(),
    inside:new Set(),extra:[],symbols:[],sealNode:null,windNodes:[],louNode:null,treasureNodes:new Map(),
    transitionLatch:true,battleLatch:false,keys:new Map(),frames:0,zones:{rest:null,ambience:null},loopId:0};
  let el={},hooks={};
  const dist=(a,b,c,d)=>Math.hypot(a-c,b-d);
  const $=s=>document.querySelector(s);

  function configure(options){
    el={scene:$(options.scene||'#forestScene'),world:$(options.world||'#forestWorld'),player:$(options.player||'#forestPlayer'),
      fiona:$(options.fiona||'#forestFiona'),label:$(options.label||'#forestLabel'),toast:$(options.toast||'#forestToast'),fade:$(options.fade||'#forestFade')};
    hooks=options.hooks||{};
    el.scene.addEventListener('pointerdown',onPointer);
    addEventListener('keydown',onKeyDown);addEventListener('keyup',e=>S.keys.delete(e.key));addEventListener('blur',()=>S.keys.clear());
    if(window.FieldTimeOfDay)FieldTimeOfDay.configure(el.scene);
    if(window.FieldWeather)FieldWeather.configure(el.scene);   // fog/rain sit under the grade overlay
    if(window.FieldVista)FieldVista.configure(el.scene);   // above the grade overlay (created after it)
    S.configured=true;
  }
  // ---- Aidan field sprite (existing field assets; only present in builds that ship AidanFieldAssets) ----
  const wcache=new Map();   // frames-map -> {dir: walk frame count}: 4-frame painted Aidan today, 6+ after an art drop (tools/field/install_hero_frames.py)
  function walkCount(frames,prefix,dir){let c=wcache.get(frames);if(!c||c.size!==frames.size){c={size:frames.size,n:{}};for(const k of frames.keys()){const m=k.match(/_walk_(down|left|right|up)_(\d+)$/);if(m&&k.startsWith(prefix))c.n[m[1]]=Math.max(c.n[m[1]]||0,+m[2]);}wcache.set(frames,c);}return c.n[dir]||4;}
  const spr={frames:new Map(),visible:null,dir:'down',state:'IDLE',phase:0,since:0,moved:0,px:null,py:null,ready:false};
  function mountPlayerSprite(){
    const A=window.AidanFieldAssets;if(!A||!el.player)return;
    for(const [name,a] of Object.entries(A.frames)){
      const im=new Image();im.className='aidan-field-frame forest-aidan';im.alt='';im.draggable=false;im.hidden=true;im.dataset.src=a.path;
      Object.assign(im.style,{position:'absolute',width:a.width*a.scale+'px',height:a.height*a.scale+'px',left:FOOT.ax-a.anchor[0]*a.scale+'px',top:FOOT.ay-a.anchor[1]*a.scale+'px',pointerEvents:'none'});
      el.player.appendChild(im);spr.frames.set(name,im);
    }
    Promise.all([...spr.frames.values()].map(im=>{im.src=im.dataset.src;return im.decode().catch(()=>{});})).then(()=>{spr.ready=true;el.player.classList.add('forest-sprite');});
  }
  function updateSprite(now){
    if(!spr.frames.size)return;
    if(spr.px!==null){
      const dx=S.x-spr.px,dy=S.y-spr.py,d=Math.hypot(dx,dy);
      if(d>.01&&d<=23){const nx=Math.abs(dx)>=Math.abs(dy)?(dx>0?'right':'left'):(dy>0?'down':'up');
        if(spr.state!=='WALK'||spr.dir!==nx){spr.since=now;spr.phase=0;}spr.dir=nx;spr.state='WALK';spr.moved=now;}
      else if(d>23||now-spr.moved>110){spr.state='IDLE';spr.phase=0;}
      if(spr.state==='WALK')spr.phase=Math.floor((now-spr.since)/(walkCount(spr.frames,'aidan_',spr.dir)>4?75:100))%walkCount(spr.frames,'aidan_',spr.dir);
    }
    spr.px=S.x;spr.py=S.y;
    const name='aidan_'+(spr.state==='WALK'?'walk_'+spr.dir+'_'+String(spr.phase+1).padStart(2,'0'):'idle_'+spr.dir);
    if(spr.visible!==name&&spr.frames.has(name)){if(spr.visible)spr.frames.get(spr.visible).hidden=true;spr.frames.get(name).hidden=!spr.ready;spr.visible=name;}
    else if(spr.visible)spr.frames.get(spr.visible).hidden=!spr.ready;
    if(spr.visible){const f=spr.frames.get(spr.visible);f.style.transform=spr.state==='WALK'?'translateY('+(-Math.abs(Math.sin((now-spr.since)/200*Math.PI))*1.5).toFixed(2)+'px)':'';}   // soft step bob between the 4 painted frames
  }
  // ---- Fiona field sprite: 4 directions x (idle + 6-frame walk), tools/field/make_fiona.py -> js/field/fiona-field-assets.js ----
  const fsp={frames:new Map(),visible:null,dir:'down',walking:false,since:0,moved:0,px:null,py:null,pt:0,ready:false};
  function mountFionaSprite(){
    const A=window.FionaFieldAssets;if(!A||!el.fiona||fsp.frames.size)return;
    for(const [name,a] of Object.entries(A.frames)){
      const im=new Image();im.className='fiona-field-frame';im.alt='';im.draggable=false;im.hidden=true;im.dataset.src=a.path;
      Object.assign(im.style,{position:'absolute',width:a.width*a.scale+'px',height:a.height*a.scale+'px',left:FOOT.ax-a.anchor[0]*a.scale+'px',top:FOOT.ay-a.anchor[1]*a.scale+'px',pointerEvents:'none'});
      el.fiona.appendChild(im);fsp.frames.set(name,im);
    }
    Promise.all([...fsp.frames.values()].map(im=>{im.src=im.dataset.src;return im.decode().catch(()=>{});})).then(()=>{fsp.ready=true;el.fiona.classList.add('fiona-sprite');skinFiona();});
  }
  function updateFiona(now){
    if(!fsp.frames.size)return;
    if(fsp.px!==null){
      const dx=S.fx-fsp.px,dy=S.fy-fsp.py,dt=Math.max(1,now-fsp.pt),d=Math.hypot(dx,dy),v=d/dt*1000;
      if(v>16&&d<60){const nx=Math.abs(dx)>=Math.abs(dy)?(dx>0?'right':'left'):(dy>0?'down':'up');
        if(!fsp.walking||fsp.dir!==nx){fsp.since=now;}fsp.dir=nx;fsp.walking=true;fsp.moved=now;}
      else if(d>=60||now-fsp.moved>140){fsp.walking=false;if(Math.abs(S.x-48-S.fx)<3&&Math.abs(S.y+18-S.fy)<3){const px=S.x-S.fx,py=S.y-S.fy;fsp.dir=Math.abs(px)>Math.abs(py)?(px>0?'right':'left'):(py>0?'down':'up');}}
    }
    fsp.px=S.fx;fsp.py=S.fy;fsp.pt=now;
    const name='fiona_'+(fsp.walking?'walk_'+fsp.dir+'_'+String(Math.floor((now-fsp.since)/105)%walkCount(fsp.frames,'fiona_',fsp.dir)+1).padStart(2,'0'):'idle_'+fsp.dir);
    if(fsp.visible!==name&&fsp.frames.has(name)){if(fsp.visible)fsp.frames.get(fsp.visible).hidden=true;fsp.frames.get(name).hidden=!fsp.ready;fsp.visible=name;}
    else if(fsp.visible)fsp.frames.get(fsp.visible).hidden=!fsp.ready;
  }
  async function loadMap(id){
    if(cache.has(id))return cache.get(id);
    await ForestLoader.loadAssets();
    const map=await ForestLoader.load(MAP_BASE+id+'.json');cache.set(id,map);return map;
  }
  const fadeMs=(t,dflt)=>Math.round(((t&&t.fade&&t.fade[dflt])??.35)*1000);
  function setFade(opacity,ms){
    el.fade.style.transitionDuration=ms+'ms';el.fade.style.opacity=String(opacity);
    return new Promise(r=>setTimeout(r,ms+20));
  }
  function toast(t){hooks.toast?hooks.toast(t):(el.toast.textContent=t,el.toast.style.display='block',clearTimeout(toast.t),toast.t=setTimeout(()=>el.toast.style.display='none',2400));}

  // ---------- map mount / unmount ----------
  function unmount(){
    CAM.token++;CAM.focus=null;CAM.shakeUntil=0;
    if(S.forest)S.forest.destroy();
    if(window.FieldVista)FieldVista.clear();
    if(window.FieldWalkers)FieldWalkers.clear();
    for(const n of S.extra)n.remove();
    S.extra=[];S.symbols=[];S.sealNode=null;S.windNodes=[];S.louNode=null;S.treasureNodes.clear();
    S.forest=null;S.map=null;S.inside.clear();S.zones={rest:null,ambience:null};
  }
  function addNode(cls,x,y,w,h,label,z){
    const d=document.createElement('div');d.className=cls;if(label)d.textContent=label;
    Object.assign(d.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px',zIndex:String(Math.round(z??y+h))});
    d.dataset.box=[x,y,w,h].join(',');
    el.world.appendChild(d);S.extra.push(d);skin(d);return d;
  }
  // Real art for runtime entities (manifest.entity). Bottom-centre anchored over the placeholder box; no art -> placeholder block.
  const SKIN_KEYS=[['forest-treasure',d=>d.classList.contains('open')?'chest_open':'chest_closed'],['forest-symbol',()=>'symbol'],
    ['forest-seal',d=>d.classList.contains('corrupted')?'seal_corrupted':'seal'],['forest-lou',()=>'lou']];
  function skin(d){
    const rule=SKIN_KEYS.find(([c])=>d.classList.contains(c));if(!rule)return;
    const a=ForestLoader.entityArt(rule[1](d)),[x,y,w,h]=d.dataset.box.split(',').map(Number);
    if(!a){d.classList.remove('art');d.style.backgroundImage='';Object.assign(d.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px'});return;}
    d.classList.add('art');d.style.backgroundImage='url("'+a.src+'")';
    Object.assign(d.style,{left:(x+w/2-a.w/2)+'px',top:(y+h-a.h)+'px',width:a.w+'px',height:a.h+'px'});
  }
  function skinFiona(){
    if(fsp.frames.size&&fsp.ready){el.fiona.classList.remove('art');el.fiona.style.backgroundImage='';el.fiona.style.transform='';return;}   // the animated sprite replaces the static entity art
    const a=ForestLoader.entityArt('fiona');if(!a){el.fiona.classList.remove('art');el.fiona.style.backgroundImage='';el.fiona.style.transform='';return;}
    el.fiona.classList.add('art');el.fiona.style.backgroundImage='url("'+a.src+'")';el.fiona.style.width=a.w+'px';el.fiona.style.height=a.h+'px';el.fiona.style.transform='translate('+(17-a.w/2)+'px,'+(42-a.h)+'px)';
  }
  function mount(map){
    S.map=map;S.mapId=map.id;
    FieldNavigation.configure({width:map.world.width,height:map.world.height,grid:32,maxNodes:40000});
    S.forest=ForestLoader.mount(map,el.world,{flags:S.flags});
    if(window.FieldWalkers)FieldWalkers.mount(map,el.world);
    el.label.textContent=(map.displayName&&map.displayName.ja)||'苔むした森';
    for(const t of map.treasurePoints||[]){
      if(t.hint==='none')continue;
      const herb=t.kind==='herb',done=S.opened.has(t.id);   // herb = gathering spot (草むら), same Inventory/treasure plumbing as a chest
      const n=herb?addNode('forest-herb'+(done?' open':''),t.x-20,t.y-26,40,28,done?'':'✿',t.y):addNode('forest-treasure'+(done?' open':''),t.x-24,t.y-36,48,36,done?'□':'▣',t.y);S.treasureNodes.set(t.id,n);
    }
    const prologue=map.story&&map.story.prologue;
    if(prologue){
      for(const sy of prologue.symbols||[]){
        const rec={...sy,node:null,alive:!(hooks.isCleared&&hooks.isCleared(sy.field))};
        if(rec.alive)rec.node=addNode('forest-symbol',sy.x-24,sy.y-62,48,62,'異形',sy.y);
        S.symbols.push(rec);
      }
      const sealB=(map.collision.blockers||[]).find(b=>b.id===(prologue.seal&&prologue.seal.blocker));
      if(sealB&&!S.flags[prologue.seal.flagOnOpen]){
        const r=sealB.rects[0];S.sealNode=addNode('forest-seal',r[0]-8,r[1]-70,r[2]+16,r[3]+70,'ᚠ ᚢ ᚦ',r[1]+r[3]);
        S.sealNode.classList.toggle('corrupted',!(hooks.sealCorrupted&&hooks.sealCorrupted()===false));
      }
    }
    if(window.FieldVista)FieldVista.mount(map.vista);
    refreshWind();
    S.zones={rest:null,ambience:null};
  }
  function refreshWind(){
    for(const n of S.windNodes)n.remove();S.windNodes=[];
    if(S.louNode){S.louNode.remove();S.louNode=null;}
    const map=S.map;if(!map||!S.flags.moss_a3_lou_found)return;
    const path=(map.terrain.paths||[]).find(p=>p.id==='path_hidden_wind');if(!path)return;
    for(let i=0;i<path.points.length-1;i++){
      const [x0,y0]=path.points[i],[x1,y1]=path.points[i+1],len=dist(x0,y0,x1,y1),ang=Math.atan2(y1-y0,x1-x0);
      const n=addNode('forest-windseg',x0,y0-10,len,20,'',y0-5);n.style.transformOrigin='0 50%';n.style.transform=`rotate(${ang}rad)`;S.windNodes.push(n);
    }
    const z=(map.eventZones||[]).find(e=>e.id==='ev_a3_lou_intro');
    if(z){const cx=z.shape.x+z.shape.w/2,cy=z.shape.y+z.shape.h/2;S.louNode=addNode('forest-lou',cx-19,cy-48,38,48,'ルー',cy);}
  }

  // ---------- transitions between maps ----------
  async function enter(options){
    if(!S.configured)throw new Error('MossForest not configured');
    const id=options.map,spawnId=options.spawn;
    S.busy=true;S.active=false;
    if(!spr.frames.size)mountPlayerSprite();   // AidanFieldAssets loads after this module
    mountFionaSprite();
    const map=await loadMap(id);
    skinFiona();
    if(options.flags)Object.assign(S.flags,options.flags);
    const first=!S.map;
    if(!first)await setFade(1,fadeMs(options.transition,'out'));
    el.scene.style.display='block';
    unmount();mount(map);
    let spot;
    const sp0=map.spawns.points[spawnId||map.spawns.default];
    if(options.x!=null&&Number.isFinite(options.x)&&Number.isFinite(options.y)&&options.x>=0&&options.y>=0&&options.x<map.world.width&&options.y<map.world.height&&!S.forest.blocked(options.x,options.y)&&(!options.verifyReachable||reachable(sp0.x-FOOT.ax,sp0.y-FOOT.ay,options.x,options.y))){spot={x:options.x,y:options.y};}
    else{spot={x:sp0.x-FOOT.ax,y:sp0.y-FOOT.ay};}
    S.x=spot.x;S.y=spot.y;spr.px=null;S.target=null;S.fionaHold=false;S.fx=S.x-48;S.fy=S.y+18;S.transitionLatch=true;S.battleLatch=true;S.inside.clear();
    S.keys.clear();render();
    if(window.FieldTimeOfDay){FieldTimeOfDay.configureMap(map);FieldTimeOfDay.set(options.timeOfDay||(map.timeOfDay&&map.timeOfDay.default)||'day',{instant:true});}
    if(window.FieldWeather)FieldWeather.configureMap(map);   // maps without "timeOfDay" always read as day
    el.fade.style.opacity='1';
    await setFade(0,fadeMs(options.transition,'in'));
    S.busy=false;S.active=true;startLoop();
    if(hooks.onEnter)hooks.onEnter(map,spawnId);
    return map;
  }
  // Coarse 32px flood fill from the area entrance with the live collision (used to validate restored positions).
  function reachable(x0,y0,x1,y1){
    const G=32,W=Math.ceil(S.map.world.width/G),H=Math.ceil(S.map.world.height/G),blocked=S.forest.blocked;
    const seen=new Uint8Array(W*H),q=[],cell=(x,y)=>Math.floor(y/G)*W+Math.floor(x/G);
    const start=cell(x0,y0),goal={i:Math.floor(x1/G),j:Math.floor(y1/G)};
    seen[start]=1;q.push(start);
    for(let h=0;h<q.length;h++){
      const c=q[h],i=c%W,j=(c-i)/W;
      if(Math.abs(i-goal.i)<=1&&Math.abs(j-goal.j)<=1)return true;
      for(const [di,dj] of [[1,0],[-1,0],[0,1],[0,-1]]){
        const ni=i+di,nj=j+dj;if(ni<0||nj<0||ni>=W||nj>=H)continue;const n=nj*W+ni;if(seen[n])continue;
        // Sample along the step so walls thinner than one cell (the 18px seal) cannot be hopped over.
        let ok=true;for(const t of [.25,.5,.75,1]){if(blocked((i+di*t)*G,(j+dj*t)*G)){ok=false;break;}}
        if(!ok)continue;seen[n]=1;q.push(n);}
    }
    return false;
  }
  function transitionTo(t){
    if(S.busy)return;
    if(t.toMap==='lind_village'||t.toMap==='TBD'){
      if(hooks.onVillageExit&&hooks.onVillageExit(t))return;   // hook returns true when it handled/blocked it
      return;
    }
    enter({map:t.toMap,spawn:t.toSpawn,transition:t});
  }

  // ---------- geometry helpers ----------
  function inShape(sh,x,y,pad=0){
    if(!sh)return false;
    if(sh.shape==='circle'||sh.r!=null)return dist(x,y,sh.cx,sh.cy)<=sh.r+pad;
    return x>=sh.x-pad&&x<=sh.x+sh.w+pad&&y>=sh.y-pad&&y<=sh.y+sh.h+pad;
  }
  const centerOf=sh=>sh.shape==='circle'||sh.r!=null?{x:sh.cx,y:sh.cy}:{x:sh.x+sh.w/2,y:sh.y+sh.h/2};
  const reqOk=z=>!z.requires||Boolean(S.flags[z.requires.flag])===Boolean(z.requires.is);
  function zoneShape(z){
    if(z.shape)return z.shape;
    if(z.ref){const p=S.map.props.find(q=>q.id===z.ref);if(p)return {shape:'circle',cx:p.x,cy:p.y-30,r:110};}
    return null;
  }

  // ---------- actions ----------
  function fireEvent(z){
    if(z.once){if(S.fired.has(z.id))return;S.fired.add(z.id);}
    if(hooks.onEvent)hooks.onEvent(z,S.map);
  }
  function openTreasure(t){
    const herb=t.kind==='herb';
    if(S.opened.has(t.id)){toast(herb?'ここの草は、もう摘んでしまった。':'宝箱は空だ。');return;}
    if(hooks.canOpenTreasure&&hooks.canOpenTreasure(t)===false)return;   // story-gated chests stay closed (and unclaimed)
    S.opened.add(t.id);
    const n=S.treasureNodes.get(t.id);if(n){n.classList.add('open');n.textContent=herb?'':'□';skin(n);}
    if(hooks.onTreasure)hooks.onTreasure(t,S.map);
  }
  function startBattle(sy){
    if(!sy.alive||S.busy)return;
    S.target=null;FieldNavigation.cancel();S.active=false;
    if(hooks.onSymbol)hooks.onSymbol(sy);
  }
  function interactAt(wx,wy){
    const fx=S.x+FOOT.ax,fy=S.y+FOOT.ay;
    for(const sy of S.symbols){
      if(!sy.alive)continue;
      if(dist(wx,wy,sy.x,sy.y-30)<=75){
        if(dist(fx,fy,sy.x,sy.y)>(sy.interactRadius||210)){toast('異形のゴブリンがこちらを警戒している……。');return true;}
        startBattle(sy);return true;
      }
    }
    for(const t of S.map.treasurePoints||[]){
      if(dist(wx,wy,t.x,t.y-18)<=55){
        if(dist(fx,fy,t.x,t.y)>190){toast(t.kind==='herb'?'草むらには、もう少し近づく必要がある。':'宝箱には、もう少し近づく必要がある。');return true;}
        openTreasure(t);return true;
      }
    }
    for(const z of S.map.eventZones||[]){
      if(z.type!=='interact'||!reqOk(z))continue;
      const sh=zoneShape(z);if(!sh||!inShape(sh,wx,wy,40))continue;
      const c=centerOf(sh);
      if(dist(fx,fy,c.x,c.y)>260){toast('もう少し近づいて調べよう。');return true;}
      fireEvent(z);return true;
    }
    return false;
  }

  // ---------- input ----------
  function onPointer(e){
    if(!S.active||S.busy)return;
    if(e.target.closest('#msg,button,#forestLabel'))return;
    const w=FieldCamera.screenToWorld(el.world,e.clientX,e.clientY);
    if(interactAt(w.x,w.y))return;
    S.target=FieldNavigation.destination(w.x-FOOT.ax,w.y-FOOT.ay,S.forest.blocked);
    if(!S.target)toast('その場所へは進めない。');
  }
  const DIRS={ArrowLeft:[-1,0],a:[-1,0],ArrowRight:[1,0],d:[1,0],ArrowUp:[0,-1],w:[0,-1],ArrowDown:[0,1],s:[0,1]};
  function onKeyDown(e){
    if(!S.active||S.busy||!DIRS[e.key])return;
    S.keys.set(e.key,DIRS[e.key]);S.target=null;FieldNavigation.cancel();
  }

  // ---------- frame loop ----------
  // Cinematic camera (shake / pan) is layered on top of FieldCamera: zoom and clamping are untouched.
  const CAM={focus:null,shakeUntil:0,shakeMs:0,shakeAmp:0,token:0};
  function render(){
    const f=CAM.focus;
    FieldCamera.render(el.world,el.scene,el.player,f?f.x-FOOT.ax:S.x,f?f.y-FOOT.ay:S.y);
    el.player.style.left=S.x+'px';el.player.style.top=S.y+'px';
    const now=performance.now();
    if(now<CAM.shakeUntil){
      const k=(CAM.shakeUntil-now)/CAM.shakeMs,a=CAM.shakeAmp*k*k,t=now/23;
      el.world.style.transform='translate('+(Math.sin(t*1.7)*a).toFixed(2)+'px,'+(Math.cos(t*2.3)*a).toFixed(2)+'px) '+el.world.style.transform;
    }
    if(window.FieldVista)FieldVista.sync(el.world.style.transform);
    const k=1-Math.pow(1-.08,FieldMovement.frameScale||1);if(!S.fionaHold){S.fx+=(S.x-48-S.fx)*k;S.fy+=(S.y+18-S.fy)*k;}   // fionaHold: a scene (FieldChoreo) is placing her
    el.fiona.style.left=S.fx+'px';el.fiona.style.top=S.fy+'px';
    el.player.style.zIndex=String(Math.round(S.y+FOOT.ay));el.fiona.style.zIndex=String(Math.round(S.fy+FOOT.ay));
    el.player.style.display=el.fiona.style.display='block';
    const sc=FieldCamera.scale,rc=el.world.getBoundingClientRect();
    S.forest.update({x:-rc.left/sc,y:-rc.top/sc,width:el.scene.clientWidth/sc,height:el.scene.clientHeight/sc});
  }
  function shake(ms=900,amp=7){CAM.shakeMs=ms;CAM.shakeAmp=amp;CAM.shakeUntil=performance.now()+ms;if(S.forest&&el.scene.style.display!=='none')render();}
  // Pan the camera to a world point, hold, then glide back to the player. Input is locked meanwhile.
  function pan(x,y,{ms=1200,hold=1000}={}){
    if(S.busy||!S.forest)return Promise.resolve(false);
    const token=++CAM.token,wasActive=S.active;S.busy=true;S.target=null;FieldNavigation.cancel();
    const ease=u=>u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2,home=()=>({x:S.x+FOOT.ax,y:S.y+FOOT.ay});
    return new Promise(done=>{
      const leg=(from,to,dur,next)=>{
        const t0=performance.now(),step=now=>{
          if(token!==CAM.token){done(false);return;}
          const u=Math.min(1,(now-t0)/dur),e=ease(u);
          CAM.focus={x:from.x+(to.x-from.x)*e,y:from.y+(to.y-from.y)*e};
          if(S.forest)render();
          if(u<1)requestAnimationFrame(step);else next();
        };requestAnimationFrame(step);
      };
      const finish=()=>{CAM.focus=null;if(token===CAM.token){S.busy=false;S.active=wasActive||S.active;if(S.forest)render();}done(true);};
      leg(home(),{x,y},ms,()=>setTimeout(()=>{if(token!==CAM.token){done(false);return;}leg({x,y},home(),ms,finish);},hold));
    });
  }
  // Hold the camera on a world point (scenes): focus() glides there and STAYS until release() glides back to the player.
  function glide(from,to,ms,token){
    return new Promise(done=>{const t0=performance.now(),ease=u=>u<.5?2*u*u:1-Math.pow(-2*u+2,2)/2;
      const step=now=>{if(token!==CAM.token){done(false);return;}const u=Math.min(1,(now-t0)/ms),e=ease(u);
        CAM.focus={x:from.x+(to.x-from.x)*e,y:from.y+(to.y-from.y)*e};if(S.forest)render();if(u<1)requestAnimationFrame(step);else done(true);};requestAnimationFrame(step);});
  }
  const homePt=()=>({x:S.x+FOOT.ax,y:S.y+FOOT.ay});
  function focus(x,y,{ms=1500}={}){if(!S.forest)return Promise.resolve(false);const token=++CAM.token;return glide(CAM.focus||homePt(),{x,y},ms,token);}
  function release({ms=1200}={}){if(!S.forest||!CAM.focus)return Promise.resolve(true);const token=++CAM.token;return glide(CAM.focus,homePt(),ms,token).then(ok=>{if(ok&&token===CAM.token){CAM.focus=null;if(S.forest)render();}return ok;});}
  function checkZones(){
    const fx=S.x+FOOT.ax,fy=S.y+FOOT.ay;
    for(const t of S.map.transitions||[]){
      if(!t.enabled)continue;
      const inside=inShape(t.rect,fx,fy);
      if(inside&&!S.transitionLatch){S.transitionLatch=true;S.inside.add(t.id);transitionTo(t);return;}
      if(!inside&&S.inside.has(t.id)){S.inside.delete(t.id);}
    }
    if(![...S.map.transitions||[]].some(t=>t.enabled&&inShape(t.rect,fx,fy)))S.transitionLatch=false;
    for(const z of S.map.eventZones||[]){
      if(!reqOk(z))continue;
      const sh=z.shape;if(!sh)continue;
      const inside=inShape(sh,fx,fy),was=S.inside.has(z.id);
      if(inside&&!was){
        S.inside.add(z.id);
        if(z.type==='rest')S.zones.rest=z.id;else if(z.type==='ambienceShift')S.zones.ambience=z.id;
        else if(z.type==='locationCard'||z.type==='trigger'||(z.type==='interact'&&z.eventId))fireEvent(z);
      }else if(!inside&&was){
        S.inside.delete(z.id);
        if(S.zones.rest===z.id)S.zones.rest=null;if(S.zones.ambience===z.id)S.zones.ambience=null;
      }
    }
    let near=false;
    for(const sy of S.symbols){
      if(!sy.alive)continue;
      if(dist(fx,fy,sy.x,sy.y)<=(sy.touchRadius||90)){near=true;if(!S.battleLatch){S.battleLatch=true;startBattle(sy);return;}}
    }
    if(!near)S.battleLatch=false;
  }
  function tick(){
    S.loopId=requestAnimationFrame(tick);
    if(!S.active||S.busy||!S.forest||el.scene.style.display==='none')return;
    const bounds=S.map.world;
    let dx=0,dy=0;S.keys.forEach(d=>{dx+=d[0];dy+=d[1];});dx=Math.sign(dx);dy=Math.sign(dy);
    if(dx||dy){const n=Math.hypot(dx,dy),step=FieldMovement.settings.pointerStep*(FieldMovement.frameScale||1)*streamFactor();
      const r=FieldMovement.advance(S.x,S.y,dx/n*step,dy/n*step,S.forest.blocked,{bounds});S.x=r.x;S.y=r.y;}
    else if(S.target){const r=FieldNavigation.follow(S.x,S.y,S.target,S.forest.blocked);S.x=r.x;S.y=r.y;S.target=r.target;}
    render();updateSprite(performance.now());updateFiona(performance.now());checkZones();S.frames++;
  }
  function streamFactor(){
    const st=S.map&&(S.map.terrain.waters||[]).find(w=>w.kind==='stream');
    return st&&ForestScatter.lineDist(S.x+FOOT.ax,S.y+FOOT.ay,st.points)<st.width/2?.85:1;
  }
  function startLoop(){if(!S.loopId)S.loopId=requestAnimationFrame(tick);}

  // ---------- flags / visibility / persistence ----------
  function setFlag(name,value){
    const was=Boolean(S.flags[name]);S.flags[name]=Boolean(value);
    if(name==='moss_a3_seal_open'&&value&&!was&&S.sealNode){const n=S.sealNode;S.sealNode=null;n.classList.add('opening');shake(1000,8);setTimeout(()=>{n.remove();S.extra=S.extra.filter(x=>x!==n);},1000);}
    if(name==='moss_a3_seal_open'&&!value&&S.map&&!S.sealNode&&S.mapId==='moss_forest_03_ancient_grove'){
      const b=S.map.collision.blockers.find(q=>q.id==='cb_a3_seal');if(b){const r=b.rects[0];S.sealNode=addNode('forest-seal corrupted',r[0]-8,r[1]-70,r[2]+16,r[3]+70,'ᚠ ᚢ ᚦ',r[1]+r[3]);}
    }
    if(name==='moss_a3_lou_found')refreshWind();
  }
  function syncSymbols(){
    for(const sy of S.symbols){const alive=!(hooks.isCleared&&hooks.isCleared(sy.field));
      if(sy.alive&&!alive){sy.alive=false;if(sy.node){sy.node.remove();S.extra=S.extra.filter(x=>x!==sy.node);sy.node=null;}}
      else if(!sy.alive&&alive){sy.alive=true;sy.node=addNode('forest-symbol',sy.x-24,sy.y-62,48,62,'異形',sy.y);}}
    if(S.sealNode&&hooks.sealCorrupted){S.sealNode.classList.toggle('corrupted',hooks.sealCorrupted());skin(S.sealNode);}
  }
  // Choreography adapters (see js/field/field-choreo.js). Aidan: moving S.x/S.y drives his walk animation by itself.
  // Fiona: set() takes her off the follow-the-player easing until release().
  function actor(id){
    if(id==='aidan')return {id,get:()=>({x:S.x+FOOT.ax,y:S.y+FOOT.ay}),set(x,y){S.x=x-FOOT.ax;S.y=y-FOOT.ay;S.target=null;if(S.forest)render();}};
    if(id==='fiona')return {id,get:()=>({x:S.fx+FOOT.ax,y:S.fy+FOOT.ay}),set(x,y){S.fionaHold=true;S.fx=x-FOOT.ax;S.fy=y-FOOT.ay;if(S.forest)render();},
      pose(state,dir){el.fiona.dataset.pose=state;el.fiona.dataset.dir=dir;},release(){S.fionaHold=false;delete el.fiona.dataset.pose;}};
    return null;
  }
  function show(){el.scene.style.display='block';}
  function hide(){S.active=false;S.target=null;S.keys.clear();FieldNavigation.cancel();el.scene.style.display='none';}
  function resume(){show();S.active=true;S.battleLatch=true;S.target=null;syncSymbols();if(S.forest){render();}startLoop();}
  function snapshot(){return {map:S.mapId,x:Math.round(S.x),y:Math.round(S.y),opened:[...S.opened],fired:[...S.fired]};}
  function restoreState(snap){
    S.opened=new Set(Array.isArray(snap&&snap.opened)?snap.opened.filter(x=>typeof x==='string'):[]);
    S.fired=new Set(Array.isArray(snap&&snap.fired)?snap.fired.filter(x=>typeof x==='string'):[]);
  }
  function reset(){S.opened.clear();S.fired.clear();S.map&&unmount();S.flags.moss_a3_seal_open=S.flags.moss_a3_lou_found=S.flags.moss_a3_lou_rescued=false;S.active=false;S.busy=false;}

  window.MossForest=Object.freeze({actor,blocked:(x,y)=>Boolean(S.forest&&S.forest.blocked(x-FOOT.ax,y-FOOT.ay)),shake,pan,focus,release,vista:(id,on,o)=>window.FieldVista?FieldVista.set(id,on,o):false,lock(on){S.busy=Boolean(on);if(on){S.target=null;S.keys.clear();FieldNavigation.cancel();}},fade:(o,ms)=>setFade(o,ms),setTimeOfDay:(n,o)=>window.FieldTimeOfDay?FieldTimeOfDay.set(n,o):false,configure,enter,show,hide,resume,setFlag,syncSymbols,snapshot,restoreState,reset,toast,
    get active(){return S.active;},get busy(){return S.busy;},get mapId(){return S.mapId;},get map(){return S.map;},get flags(){return {...S.flags};},
    get feet(){return {x:S.x+FOOT.ax,y:S.y+FOOT.ay};},get zones(){return {...S.zones};},get opened(){return [...S.opened];},
    get symbolsAlive(){return S.symbols.filter(s=>s.alive).length;},get forest(){return S.forest;},get frames(){return S.frames;},
    get sealNodes(){return el.world?el.world.querySelectorAll('.forest-seal').length:0;},
    teleportFeet(x,y){S.x=x-FOOT.ax;S.y=y-FOOT.ay;S.target=null;S.battleLatch=true;S.transitionLatch=true;},
    goFeet(x,y){S.target=FieldNavigation.destination(x-FOOT.ax,y-FOOT.ay,S.forest.blocked);return Boolean(S.target);},
    get target(){return S.target;},get status(){return FieldNavigation.status;}});
})();
