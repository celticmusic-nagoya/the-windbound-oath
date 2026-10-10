/* DEV-only display-resolution sampling. Original PNGs, logical coordinates and scale
 * remain untouched. One reusable canvas per visible actor, no independent clock. */
(function(){
  'use strict';
  if(!window.WINDBOUND_DEV)return;
  const entries=new Map();let pending=false;
  const representative=e=>e.closest('#player')||['emma','farmer_male'].includes(e.closest('[data-npc-id]')?.dataset.npcId);
  function clear(){for(const {img,canvas}of entries.values()){img.classList.remove('lind-crisp-source');canvas.remove();}entries.clear();}
  function render(){
    pending=false;
    if(!document.body.classList.contains('lindFieldReview')||document.body.dataset.lindCharacterRendering!=='crisp'){clear();return;}
    const all=document.body.dataset.lindRenderingScope==='all';
    const images=[...document.querySelectorAll('#player > .aidan-field-frame:not([hidden]),.lind-field-npc img:not([hidden])')]
      .filter(e=>(all||representative(e))&&e.complete&&e.naturalWidth);
    const active=new Set(images.map(img=>img.parentElement));
    for(const [actor,{img,canvas}]of entries)if(!active.has(actor)){img.classList.remove('lind-crisp-source');canvas.remove();entries.delete(actor);}
    const zoom=window.FieldCamera?.scale||1,dpr=window.devicePixelRatio||1;
    for(const img of images){
      const actor=img.parentElement;let entry=entries.get(actor);
      if(!entry){const canvas=document.createElement('canvas');canvas.className='lind-crisp-frame';canvas.setAttribute('aria-hidden','true');img.after(canvas);entry={canvas,key:'',img};entries.set(actor,entry);}
      if(entry.img!==img){entry.img.classList.remove('lind-crisp-source');entry.img=img;}
      const {canvas}=entry;
      const w=parseFloat(img.style.width),h=parseFloat(img.style.height);if(!(w>0&&h>0))continue;
      const pw=Math.max(1,Math.round(w*zoom*dpr)),ph=Math.max(1,Math.round(h*zoom*dpr));
      const key=img.currentSrc+'|'+pw+'|'+ph;
      if(entry.key!==key){canvas.width=pw;canvas.height=ph;const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';ctx.drawImage(img,0,0,pw,ph);entry.key=key;}
      // Canvas occupies exactly the same world-space rectangle as its source.
      for(const prop of ['left','top','width','height'])if(canvas.style[prop]!==img.style[prop])canvas.style[prop]=img.style[prop];
      if(!img.classList.contains('lind-crisp-source'))img.classList.add('lind-crisp-source');
    }
  }
  function schedule(){if(!pending){pending=true;queueMicrotask(render);}}
  const observer=new MutationObserver(records=>{
    if(records.some(r=>r.target===document.body||r.target===document.getElementById('world')||
      r.target.matches?.('.aidan-field-frame,.lind-field-npc img,.lind-field-npc')||
      r.type==='childList'&&[...r.addedNodes].some(n=>n.nodeType===1&&n.matches?.('.lind-field-npc,.aidan-field-frame'))))schedule();
  });
  observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['style','hidden','class','data-lind-character-rendering','data-lind-rendering-scope','data-state']});
  window.addEventListener('resize',schedule);
  window.LindCrispRenderer=Object.freeze({refresh:schedule,get count(){return entries.size;}});
})();
