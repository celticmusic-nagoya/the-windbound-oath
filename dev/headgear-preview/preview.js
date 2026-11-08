/* Isolated HEADGEAR-LAYER-02 candidate-only preview. No production hooks. */
(function () {
  'use strict';
  const direction=document.getElementById('direction');
  const size=document.getElementById('size');
  const move=document.getElementById('move');
  const reduced=document.getElementById('reduced');
  const status=document.getElementById('status');
  const container=document.getElementById('sprite');
  const media=window.matchMedia('(prefers-reduced-motion: reduce)');
  let wrapper=null, raf=0, start=0;
  // No candidate sprites are committed yet. Keep preview empty rather than
  // misrepresenting the official design or silently using legacy artwork.
  const candidate=null;
  function refresh(){
    if(!candidate){
      container.replaceChildren();
      wrapper=null;
      status.textContent='BLOCKED: 正式照合済みの4方向RGBA候補・頭装備レイヤーは未登録です。';
      return;
    }
    try{
      const layers=window.FieldHeadgearRenderer.plan(candidate.base,candidate.layers,direction.value);
      wrapper=window.FieldHeadgearRenderer.render(document,container,layers,{width:candidate.width,height:candidate.height});
      const scale=Number(size.value)/candidate.height;
      wrapper.style.zoom=String(scale);
      status.textContent='候補表示中（正式採用ではありません）';
    }catch(e){container.replaceChildren();wrapper=null;status.textContent='BLOCKED: '+e.message;}
  }
  function frame(t){
    if(wrapper){
      const m=window.FieldSpriteMotion.sample({kind:'player',moving:move.checked,time:(t-start)/1000,reducedMotion:reduced.checked||media.matches});
      wrapper.style.transform='translate3d('+m.x+'px,'+m.y+'px,0) rotate('+m.sway+'deg) scale('+m.scale+')';
    }
    raf=requestAnimationFrame(frame);
  }
  for(const el of [direction,size,move,reduced])el.addEventListener('change',refresh);
  refresh();
  raf=requestAnimationFrame(t=>{start=t;frame(t);});
  window.addEventListener('pagehide',()=>cancelAnimationFrame(raf),{once:true});
})();
