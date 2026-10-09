/* Lind world rendering only. Movement/collision coordinates remain unscaled.
 * QA choices are session-only; normal field/battle rendering stays at 1.00x. */
(function () {
  'use strict';
  // QA limits are provisional. Release/device defaults remain undecided.
  // Future SETTINGS/storage adapters can use this config and setScale; no persistence here.
  const config = Object.freeze({
    defaultScale: 1,
    qaScales: Object.freeze([1,1.15,1.20,1.25,1.28,1.30,1.35,
      1.40,1.45,1.50,1.55,1.60,1.70,1.80,1.90,2.00,2.10]),
    release: Object.freeze({minScale:null,defaultScale:null,maxScale:null,step:null,
      desktopDefault:null,mobileLandscapeDefault:null,mobilePortraitDefault:null})
  });
  const scales = config.qaScales;
  let review = false, selected = config.defaultScale, select = null, toolbar = null;
  const effectiveScale = () => review ? selected : config.defaultScale;
  function render(world, viewport, player, x, y) {
    const scale = effectiveScale(), view=viewport.getBoundingClientRect();
    const screenWidth=review ? Math.min(viewport.clientWidth,Math.max(0,window.innerWidth-view.left)) : viewport.clientWidth;
    const screenHeight=review ? Math.min(viewport.clientHeight,Math.max(0,window.innerHeight-view.top)) : viewport.clientHeight;
    const width=screenWidth/scale, height=screenHeight/scale;
    const topInset=review&&toolbar&&!toolbar.hidden ? Math.min(screenHeight/2,
      Math.max(0,toolbar.getBoundingClientRect().bottom-view.top)) : 0;
    // Preserve the established non-review camera; review centers the actor's body.
    const focusX=x+(review?17:0), focusY=y+(review?22:0);
    const left=Math.max(0,Math.min(Math.max(0,world.offsetWidth-width),focusX-width/2));
    const top=Math.max(0,Math.min(Math.max(0,world.offsetHeight-height),focusY-(screenHeight+topInset)/(2*scale)));
    world.style.transform=`translate(${-left*scale}px,${-top*scale}px) scale(${scale})`;
    player.style.left=x+'px'; player.style.top=y+'px';
  }
  function screenToWorld(world, x, y) {
    const rect=world.getBoundingClientRect(), scale=rect.width/world.offsetWidth;
    return {x:(x-rect.left)/scale,y:(y-rect.top)/scale};
  }
  function worldToScreen(world, x, y) {
    const rect=world.getBoundingClientRect(), scale=rect.width/world.offsetWidth;
    return {x:rect.left+x*scale,y:rect.top+y*scale};
  }
  function refresh() { if (typeof window.camera==='function') window.camera(); }
  function setScale(value) {
    const next=Number(value);
    if (!review || !scales.includes(next)) return false;
    selected=next;if(select)select.value=String(next);refresh();return true;
  }
  function setReviewActive(value) { review=Boolean(value);refresh(); }
  function mount(controls) {
    if (!window.WINDBOUND_DEV) return;
    toolbar=controls;
    const label=document.createElement('label');label.className='lind-camera-controls';label.append('カメラ ');
    select=document.createElement('select');select.id='lindCameraScale';select.setAttribute('aria-label','フィールドカメラ倍率');
    scales.forEach(scale=>{const option=document.createElement('option');option.value=String(scale);option.textContent=scale.toFixed(2)+'x';select.append(option);});
    select.value=String(selected);select.onchange=()=>setScale(select.value);label.append(select);
    // Share the existing Wind Stone row rather than expanding the toolbar.
    const stone=controls.querySelector('.lind-stone-controls');
    if(stone){const row=document.createElement('div');row.className='lind-camera-row';stone.before(row);row.append(stone,label);}
    else controls.append(label);
  }
  window.FieldCamera=Object.freeze({render,screenToWorld,worldToScreen,setScale,setReviewActive,mount,scales,config,
    get scale(){return effectiveScale();},get selectedScale(){return selected;},get reviewActive(){return review;}});
})();
