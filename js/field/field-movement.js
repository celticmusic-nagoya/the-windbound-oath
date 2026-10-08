/* Lind field movement tuning. Battle motion and other maps are independent. */
(function () {
  'use strict';
  const multiplier=1.25;
  const settings=Object.freeze({multiplier,pointerStep:4*multiplier,keyboardStep:18*multiplier});
  function advance(x,y,dx,dy,blocked) {
    const distance=Math.hypot(dx,dy),steps=Math.max(1,Math.ceil(distance/2));
    let stopped=false;
    for(let i=0;i<steps;i++) {
      const nx=Math.max(0,Math.min(2160,x+dx/steps));
      const ny=Math.max(0,Math.min(1500,y+dy/steps));
      if(nx===x&&ny===y){stopped=true;break;}
      if(blocked(nx,ny)){stopped=true;break;}
      x=nx;y=ny;
    }
    return {x,y,stopped};
  }
  window.FieldMovement=Object.freeze({settings,advance});
})();
