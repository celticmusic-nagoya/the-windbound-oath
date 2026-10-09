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
  function currentContext(){return document.body.classList.contains('raiderBattleMode')?'raider':document.body.classList.contains('normalBattleMode')?'normal':null;}
  function eligible(r){return r.enabled&&r.state==='idle'&&r.context===currentContext();}
  function paused(){return document.hidden||document.body.classList.contains('battlePresentationBusy')||document.body.classList.contains('dialogueOpen')||document.body.classList.contains('actionCinematic');}
  function reset(r,now=performance.now()){
    r.cycles=0;r.specialAfter=Math.floor(range(3,6));r.steps=profiles.get(r.assets.type)(r);
    r.step=0;r.frame=0;r.from=0;r.started=now;r.lastDraw=-1;r.transition=false;
  }
  function preload(assets){
    if(cache.has(assets))return cache.get(assets);
    const entry={images:[],ready:false};cache.set(assets,entry);
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
  function draw(r,now,force=false){
    if(!r.ctx||!r.entry?.ready||!r.width)return;
    const mix=reduced.matches?1:Math.min(1,(now-r.started)/220);
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
      if(paused()||reduced.matches){
        if(reduced.matches&&r.frame!==0){reset(r,now);draw(r,now,true);}
        // Finish a crossfade once, then freeze the pose while dialogue/cut-in owns presentation.
        if(r.transition){r.transition=false;draw(r,now,true);}
        r.wasPaused=true;
      }else {if(r.wasPaused){reset(r,now);draw(r,now,true);r.wasPaused=false;}running=true;}
    }
    if(running&&raf===null)raf=requestAnimationFrame(tick);
    if(!running&&raf!==null){cancelAnimationFrame(raf);raf=null;}
  }
  function tick(now){
    raf=null;let running=false;
    for(const r of records.values()){
      if(!eligible(r)||!r.showing||paused()||reduced.matches)continue;
      running=true;
      if(now-r.started>=r.steps[r.step].hold){
        r.step++;if(r.step>=r.steps.length){r.steps=profiles.get(r.assets.type)(r);r.step=0;}
        r.from=r.frame;r.frame=r.steps[r.step].frame;r.started=now;r.transition=r.from!==r.frame;
      }
      draw(r,now);
    }
    if(running)raf=requestAnimationFrame(tick);else refresh();
  }
  window.BattleIdleMotion=Object.freeze({
    register({context,actor,selector,assets}){
      if(!profiles.has(assets.type)||records.has(selector))return false;
      records.set(selector,{context,actor,selector,assets,enabled:false,state:null,showing:false});return true;
    },
    ready(selector){const r=records.get(selector);return r&&eligible(r)?preload(r.assets).promise.then(()=>cache.get(r.assets).ready):Promise.resolve(false);},
    defineType(name,sequenceFactory){if(profiles.has(name)||typeof sequenceFactory!=='function')return false;profiles.set(name,sequenceFactory);return true;},
    begin(selector){const r=records.get(selector);if(r){r.enabled=true;hide(r);reset(r);refresh();}},
    stop(selector){const r=records.get(selector);if(r){r.enabled=false;hide(r);refresh();}},
    onState(selector,actor,state){const r=records.get(selector);if(!r||r.actor!==actor)return;const changed=r.state!==state;r.state=state;if(changed)hide(r);refresh();},
    get status(){return {scheduled:raf!==null,reducedMotion:reduced.matches,cacheCount:cache.size,actors:[...records.values()].map(r=>({context:r.context,actor:r.actor,state:r.state,enabled:r.enabled,showing:r.showing,frame:r.frame,transition:r.transition,fit:r.fit,canvasCount:r.canvas?1:0}))};}
  });
  BattleIdleMotion.register({context:'normal',actor:'aidan',selector:'#bAidan2 img',assets:BATTLE_IDLE_ASSETS.aidan});
  BattleIdleMotion.register({context:'raider',actor:'aidan',selector:'#rbAidan img',assets:BATTLE_IDLE_ASSETS.aidan});
  new MutationObserver(refresh).observe(document.body,{attributes:true,attributeFilter:['class']});
  document.addEventListener('visibilitychange',refresh);reduced.addEventListener('change',refresh);
})();
