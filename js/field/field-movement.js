/* Lind field movement tuning. Battle motion and other maps are independent. */
(function () {
  'use strict';
  const multiplier=1.25;
  const settings=Object.freeze({multiplier,pointerStep:4*multiplier,keyboardStep:18*multiplier,
    anchorX:17,anchorY:42,arrivalRadius:3,microStep:2,cornerRadius:12});
  // Frame clock: per-frame step sizes are authored for 60 Hz. frameScale = frame time / (1/60 s), updated once
  // per animation frame by this module's own loop (it is loaded first, so it runs before consumers each frame).
  // Consumers multiply per-frame steps by frameScale, so 60/120/144 Hz all move at the same px/s.
  let frameScale=1,lastNow=null;
  function tickClock(now) {
    if(lastNow!==null)frameScale=Math.max(.1,Math.min(3,Math.min(now-lastNow,100)/(1000/60)));
    lastNow=now;
  }
  if(typeof requestAnimationFrame==='function'){const loop=now=>{tickClock(now);requestAnimationFrame(loop);};requestAnimationFrame(loop);}
  const clock={get scale(){return frameScale;},set(value){frameScale=Number(value)||1;lastNow=null;}};
  function advance(x,y,dx,dy,blocked,options={}) {
    // Map bounds are injectable; the default is the Lind world so existing callers are unchanged.
    const maxX=options.bounds?.width??2160,maxY=options.bounds?.height??1500;
    const distance=Math.hypot(dx,dy),steps=Math.max(1,Math.ceil(distance/2));
    const startX=x,startY=y;
    let collided=false,assisted=0,lastProgress=false;
    const budget=options.assist===false?0:Math.min(3,distance*.15);
    for(let i=0;i<steps;i++) {
      const nx=Math.max(0,Math.min(maxX,x+dx/steps));
      const ny=Math.max(0,Math.min(maxY,y+dy/steps));
      const beforeX=x,beforeY=y;
      if(!blocked(nx,ny)){x=nx;y=ny;}
      else {
        collided=true;
        // Each axis is swept independently: a blocked component does not
        // discard the other component or tunnel through a corner.
        if(nx!==x&&!blocked(nx,y))x=nx;
        if(ny!==y&&!blocked(x,ny))y=ny;
      }
      if(x===beforeX&&y===beforeY&&assisted<budget&&(dx===0)!==(dy===0)) {
        const horizontal=dy===0,forward=Math.sign(horizontal?dx:dy)*settings.microStep;
        let correction=0;
        for(let offset=1;offset<=settings.cornerRadius&&!correction;offset++)for(const sign of [-1,1]) {
          let clear=true;
          for(let n=1;n<=offset;n++)if(blocked(horizontal?x:x+n*sign,horizontal?y+n*sign:y)){clear=false;break;}
          if(clear&&!blocked(horizontal?x+forward:x+offset*sign,horizontal?y+offset*sign:y+forward)){
            correction=sign;break;
          }
        }
        if(correction) {
          const amount=Math.min(.5,budget-assisted)*correction;
          const ax=horizontal?x:x+amount,ay=horizontal?y+amount:y;
          if(ax>=0&&ax<=maxX&&ay>=0&&ay<=maxY&&!blocked(ax,ay)){
            x=ax;y=ay;assisted+=Math.abs(amount);
          }
        }
      }
      lastProgress=x!==beforeX||y!==beforeY;
    }
    return {x,y,stopped:!lastProgress||Math.hypot(x-startX,y-startY)<.001,collided,assisted};
  }
  window.FieldMovement=Object.freeze({settings,advance,clock,get frameScale(){return frameScale;}});
})();
