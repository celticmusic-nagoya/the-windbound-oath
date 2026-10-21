// Cached idle artwork only. State, damage, resources and WAAPI motion remain engine-owned.
(() => {
  'use strict';
  const records=new Map(),cache=new Map(),profiles=new Map();
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let raf=null;
  // Cosmetic randomness must never consume the battle's critical/encounter RNG.
  let seed=crypto.getRandomValues(new Uint32Array(1))[0];
  const range=(min,max)=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return min+seed/4294967296*(max-min);};
  profiles.set('breathe',r=>{
    r.cycles++;
    const steps=[{frame:0,hold:range(1300,1900)},{frame:1,hold:range(850,1150)},
      {frame:0,hold:range(1100,1600)},{frame:2,hold:range(850,1150)},{frame:0,hold:range(1300,2100)}];
    if(r.cycles>=r.specialAfter){
      steps.push({frame:0,hold:range(2000,4000)},{frame:3,hold:range(1200,1900)},{frame:0,hold:range(1800,2400)});
      r.cycles=0;r.specialAfter=Math.floor(range(3,6));
    }
    return steps;
  });
  // Fixed-rate sequential loop (Lou): assets.fps frames per second, 1->2->...->N->1.
  // assets.ms (optional) gives each frame its own duration in ms; otherwise assets.fps is used.
  profiles.set('loop',r=>{const base=1000/(r.assets.fps||6),ms=r.assets.ms;return r.assets.frames.map((_,i)=>({frame:i,hold:ms&&ms[i]>0?ms[i]:base}));});
  // Layered idle (Fiona v3): one MASTER still + breathing transform + eye-region blink overlays. No frame steps; r.blink holds the cosmetic blink schedule.
  profiles.set('layered',r=>{const b=r.assets.layered.blink;r.blink={start:-1e9,next:range(b.minGap,b.maxGap)/1000,state:0};return [{frame:0,hold:1e12}];});
  function currentContext(){return document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null;}
  function eligible(r){return r.enabled&&r.state==='idle'&&r.context===currentContext();}
  function still(r){return reduced.matches&&r.assets.ignoreReduced!==true;}
  function paused(){return document.hidden||document.body.classList.contains('battlePresentationBusy')||document.body.classList.contains('dialogueOpen')||document.body.classList.contains('actionCinematic');}
  function reset(r,now=performance.now()){
    r.cycles=0;r.specialAfter=Math.floor(range(3,6));r.steps=profiles.get(r.assets.type)(r);
    r.step=0;r.frame=0;r.from=0;r.started=now;r.lastDraw=-1;r.transition=false;
  }
  function preload(assets){
    if(cache.has(assets))return cache.get(assets);
    const entry={images:[],ready:false};cache.set(assets,entry);
    if(assets.layered){
      const L=assets.layered,load=async path=>{const image=new Image();image.src=path;await image.decode();return image;};
      entry.promise=(async()=>{
        const master=await load(L.master),eyes={};
        for(const [id,e] of Object.entries(L.eyes))eyes[id]=await Promise.all(e.files.map(load));
        entry.layers={master,eyes};entry.comp=document.createElement('canvas');entry.comp.width=L.size[0];entry.comp.height=L.size[1];entry.compState=-1;entry.images=[master];entry.ready=true;refresh();
      })().catch(()=>{entry.failed=true;});
      return entry;
    }
    entry.promise=Promise.all(assets.frames.map(async frame=>{
      const image=new Image();image.src=frame.path;await image.decode();return image;
    })).then(images=>{entry.images=images;entry.ready=true;refresh();}).catch(()=>{entry.failed=true;});
    return entry;
  }
  function mount(r){
    if(r.canvas)return;
    r.image=document.querySelector(r.selector);r.host=r.image?.parentElement;if(!r.host)return;
    r.canvas=document.createElement('canvas');r.canvas.className='battle-idle-canvas';r.canvas.hidden=true;
    r.canvas.setAttribute('aria-hidden','true');r.host.append(r.canvas);r.ctx=r.canvas.getContext('2d');
    r.resize=new ResizeObserver(()=>{measure(r);if(eligible(r)&&r.entry?.ready)draw(r,performance.now(),true)});
    r.resize.observe(r.host);measure(r);
  }
  function measure(r){
    if(!r.canvas)return;
    const size=getComputedStyle(r.host),width=parseFloat(size.width)||r.host.clientWidth,height=parseFloat(size.height)||r.host.clientHeight;if(!width||!height)return;
    const density=Math.min(devicePixelRatio||1,2);
    r.canvas.width=Math.round(width*density);r.canvas.height=Math.round(height*density);
    r.width=width;r.height=height;r.densityX=r.canvas.width/width;r.densityY=r.canvas.height/height;
    const style=getComputedStyle(r.image);r.canvas.style.filter=style.filter;r.canvas.style.imageRendering=style.imageRendering;
    r.fit=Math.min(width/r.assets.width,height/r.assets.height);r.lastDraw=-1;
  }
  // MASTER + eye overlays at master resolution, redrawn only when the blink state changes. State 0 = untouched MASTER (overlay layers never drawn).
  function compose(entry,assets,state){
    if(entry.compState===state)return entry.comp;
    const L=assets.layered,c=entry.comp.getContext('2d');c.clearRect(0,0,L.size[0],L.size[1]);c.drawImage(entry.layers.master,0,0);
    entry.drawn=[];
    if(state>0)for(const [id,e] of Object.entries(L.eyes)){const si=state-1;c.drawImage(entry.layers.eyes[id][si],e.box[0],e.box[1]);entry.drawn.push([id,si+1]);}
    entry.compState=state;return entry.comp;
  }
  // Pose at time t (s): advances the blink schedule in k, returns {state, ph, wave}. Pure w.r.t. the DOM (also driven by the QA probe with a controlled clock).
  function layeredPose(L,k,t){
    const B=L.breath;
    if(t>0&&t>=k.next&&t-k.start>=blinkMs(L)/1000){k.start=t;k.next=t+range(L.blink.minGap,L.blink.maxGap)/1000;}
    let state=0,ms=(t-k.start)*1000;
    if(ms>=0)for(const [st,d] of L.blink.seq){if(ms<d){state=st;break;}ms-=d;}
    const ph=(t%B.cycle)/B.cycle,wave=(1-Math.cos(ph*2*Math.PI))/2;
    return {state,ph,wave};
  }
  let trace=null;   // QA: when an array, every real layered draw is appended (clock, blink start, eye state, overlays actually drawn, breath)
  function drawLayered(r,now){
    const L=r.assets.layered,B=L.breath,k=r.blink,t=still(r)?0:(now-r.started)/1000;
    const {state,ph,wave}=layeredPose(L,k,t);
    k.state=state;k.phase=ph;k.wave=wave;
    const ctx=r.ctx,s=r.fit,a=B.amp,W=L.size[0],H=L.size[1],ox=B.origin[0]*W,oy=B.origin[1]*H;
    ctx.setTransform(r.densityX,0,0,r.densityY,0,0);ctx.clearRect(0,0,r.width,r.height);ctx.globalAlpha=1;
    ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
    // virtual 1034x678 frame (bottom-centre in the slot) -> anchor -> master px; the breathing transform is applied to the master + eye layers together
    ctx.translate((r.width-r.assets.width*s)/2,r.height-r.assets.height*s);ctx.scale(s,s);ctx.translate(r.assets.anchor[0],r.assets.anchor[1]);
    ctx.scale(L.scale,L.scale);ctx.translate(-L.foot[0],-L.foot[1]);
    ctx.translate(ox,oy-wave*B.ty*a*H);ctx.scale(1+wave*B.sx*a,1+wave*B.sy*a);ctx.translate(-ox,-oy);
    ctx.drawImage(compose(r.entry,r.assets,state),0,0);
    if(trace)trace.push({ctx:r.context,t,start:k.start,state,drawn:r.entry.drawn.map(x=>x.join(':')).join(','),wave,ph,still:still(r),now});
    ctx.setTransform(1,0,0,1,0,0);
    r.lastDraw=r.frame;r.canvas.dataset.frame='0';window.BattleFacing?.paint(r.canvas,r.actor,'idle');
  }
  function blinkMs(L){return L.blink.seq.reduce((n,x)=>n+x[1],0);}
  function draw(r,now,force=false){
    if(!r.ctx||!r.entry?.ready||!r.width)return;
    if(r.assets.layered)return drawLayered(r,now);
    const mix=still(r)?1:Math.min(1,(now-r.started)/220);
    if(!force&&!r.transition&&r.lastDraw===r.frame)return;
    const ctx=r.ctx;ctx.setTransform(r.densityX,0,0,r.densityY,0,0);ctx.clearRect(0,0,r.width,r.height);
    const paint=(index,opacity)=>{
      const f=r.assets.frames[index],s=r.fit;ctx.globalAlpha=opacity;
      ctx.drawImage(r.entry.images[index],(r.width-r.assets.width*s)/2+(r.assets.anchor[0]-f.anchor[0])*s,
        r.height-r.assets.height*s+(r.assets.anchor[1]-f.anchor[1])*s,r.assets.width*s,r.assets.height*s);
    };
    // Linear source crossfade without a transparency dip: outgoing + incoming.
    if(r.transition&&mix<1){ctx.globalCompositeOperation='source-over';paint(r.from,1-mix);ctx.globalCompositeOperation='lighter';paint(r.frame,mix);ctx.globalCompositeOperation='source-over';}
    else {paint(r.frame,1);r.transition=false;}
    ctx.globalAlpha=1;r.lastDraw=r.frame;
    r.canvas.dataset.frame=String(r.frame);window.BattleFacing?.paint(r.canvas,r.actor,'idle');
  }
  function hide(r){if(r.canvas)r.canvas.hidden=true;r.host?.classList.remove('battle-idle-active');r.showing=false;}
  function refresh(){
    const now=performance.now();let running=false;
    for(const r of records.values()){
      if(!eligible(r)){hide(r);continue;}
      r.entry=preload(r.assets);if(!r.entry.ready)continue;
      mount(r);if(!r.canvas)continue;
      if(!r.showing){reset(r,now);measure(r);r.canvas.hidden=false;r.host.classList.add('battle-idle-active');r.showing=true;draw(r,now,true);}
      if(paused()||still(r)){
        // Reduced motion switched ON mid-animation: snap to the rest pose once. Layered idle keeps r.frame at 0 for its whole life, so it needs its own one-shot flag
        // (otherwise a closed-eye state / breathing transform of the moment stays frozen on screen).
        if(still(r)&&(r.frame!==0||(r.assets.layered&&!r.stillDone))){reset(r,now);draw(r,now,true);r.stillDone=true;}
        // Finish a crossfade once, then freeze the pose while dialogue/cut-in owns presentation.
        if(r.transition){r.transition=false;draw(r,now,true);}
        r.wasPaused=true;
      }else {r.stillDone=false;if(r.wasPaused){reset(r,now);draw(r,now,true);r.wasPaused=false;}running=true;}
    }
    if(running&&raf===null)raf=requestAnimationFrame(tick);
    if(!running&&raf!==null){cancelAnimationFrame(raf);raf=null;}
  }
  function tick(now){
    raf=null;let running=false;
    for(const r of records.values()){
      if(!eligible(r)||!r.showing||paused()||still(r))continue;
      running=true;
      if(now-r.started>=r.steps[r.step].hold){
        r.step++;if(r.step>=r.steps.length){r.steps=profiles.get(r.assets.type)(r);r.step=0;}
        r.from=r.frame;r.frame=r.steps[r.step].frame;r.started=now;r.transition=r.from!==r.frame&&r.actor!=='forest_bat'&&r.assets.crossfade!==false;   // bat wing poses differ too much to crossfade (additive blend ghosts the wings): hard cut
      }
      draw(r,now);
    }
    if(running)raf=requestAnimationFrame(tick);else refresh();
  }
  window.BattleIdleMotion=Object.freeze({
    register({context,actor,selector,assets}){
      if(!profiles.has(assets.type)||records.has(selector+'|'+actor))return false;
      records.set(selector+'|'+actor,{context,actor,selector,assets,enabled:false,state:null,showing:false});return true;
    },
    ready(selector){const r=[...records.values()].find(q=>q.selector===selector&&q.enabled);return r&&eligible(r)?preload(r.assets).promise.then(()=>cache.get(r.assets).ready):Promise.resolve(false);},
    defineType(name,sequenceFactory){if(profiles.has(name)||typeof sequenceFactory!=='function')return false;profiles.set(name,sequenceFactory);return true;},
    // Several actors can share a battle slot (the enemy slot holds goblin / slime / bat / boar art in turn): a record only runs while its own actor is painted there.
    begin(selector,actor){for(const r of records.values())if(r.selector===selector){const mine=!actor||r.actor===actor;r.enabled=mine;if(!mine)r.state=null;hide(r);if(mine)reset(r);}refresh();},
    stop(selector){for(const r of records.values())if(r.selector===selector){r.enabled=false;hide(r);}refresh();},
    onState(selector,actor,state){for(const r of records.values()){if(r.selector!==selector)continue;if(r.actor!==actor){if(r.state!==null){r.state=null;hide(r);}continue;}const changed=r.state!==state;r.state=state;if(changed)hide(r);}refresh();},
    get status(){return {scheduled:raf!==null,reducedMotion:reduced.matches,cacheCount:cache.size,actors:[...records.values()].map(r=>({context:r.context,actor:r.actor,state:r.state,enabled:r.enabled,showing:r.showing,frame:r.frame,transition:r.transition,fit:r.fit,canvasCount:r.canvas?1:0,layer:r.assets.layered&&r.blink?{eye:r.blink.state,phase:r.blink.phase,wave:r.blink.wave}:null}))};},
    // Test/QA helpers (read-only w.r.t. the game): trace of real draws, and the real pose function with a controlled clock.
    traceStart(){trace=[];},traceStop(){const t=trace||[];trace=null;return t;},
    probeLayered(actor,blinkStart,t){const r=[...records.values()].find(q=>q.actor===actor&&q.assets.layered);if(!r)return null;return layeredPose(r.assets.layered,{start:blinkStart,next:1e9},t);},
    // Test/QA helper: the full-resolution composite of a layered actor in a given eye state (0 = MASTER). Read-only copy.
    layeredFrame(actor,state){const r=[...records.values()].find(q=>q.actor===actor&&q.assets.layered);if(!r)return null;const e=preload(r.assets);if(!e.ready)return null;const c=document.createElement('canvas'),L=r.assets.layered;c.width=L.size[0];c.height=L.size[1];const ctx=c.getContext('2d');ctx.drawImage(compose(e,r.assets,state),0,0);return c;}
  });
  BattleIdleMotion.register({context:'normal',actor:'aidan',selector:'#bAidan2 img',assets:BATTLE_IDLE_ASSETS.aidan});
  BattleIdleMotion.register({context:'raider',actor:'aidan',selector:'#rbAidan img',assets:BATTLE_IDLE_ASSETS.aidan});
  // Fiona: 6-frame idle loop (normal and raider battles).
  BattleIdleMotion.register({context:'normal',actor:'fiona',selector:'#bFiona2 img',assets:BATTLE_IDLE_ASSETS.fiona});
  BattleIdleMotion.register({context:'raider',actor:'fiona',selector:'#rbFiona img',assets:BATTLE_IDLE_ASSETS.fiona});
  // Forest Bat (enemy): idle flap on whichever battle slot holds a bat (records only act while the slot's actor is 'forest_bat').
  for(const actor of ['forest_bat','leafy_boar'])for(const selector of ['#bGob img','#normalEnemy1 .prologueSprite img','#normalEnemy2 .prologueSprite img'])BattleIdleMotion.register({context:'normal',actor,selector,assets:BATTLE_IDLE_ASSETS[actor]});
  // Lou (raider battle only): floating idle loop on the party slot.
  BattleIdleMotion.register({context:'raider',actor:'lou',selector:'#rbLou img',assets:BATTLE_IDLE_ASSETS.lou});
  new MutationObserver(refresh).observe(document.body,{attributes:true,attributeFilter:['class']});
  document.addEventListener('visibilitychange',refresh);reduced.addEventListener('change',refresh);
})();
