/* DEV-only interpolation comparison. No image processing, actor geometry or timers. */
(function () {
  'use strict';
  if(!window.WINDBOUND_DEV)return;
  const controls=document.getElementById('lindReviewControls');
  if(!controls)return;
  const label=document.createElement('label');
  label.append('キャラクター画質（試験） ');
  const select=document.createElement('select');
  select.id='lindCharacterRendering';select.setAttribute('aria-label','キャラクター画質（試験）');
  for(const [value,text]of [['original','原表示'],['smooth','HD prototype · Aidan／Emma／農夫']]){
    const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);
  }
  label.append(select);controls.append(label);
  let mode='original';
  function setMode(next){
    if(!['original','smooth'].includes(next))return false;
    mode=next;select.value=next;document.body.dataset.lindCharacterRendering=next;return true;
  }
  select.addEventListener('change',()=>setMode(select.value));setMode('original');
  window.LindCharacterRendering=Object.freeze({setMode,actors:Object.freeze(['aidan','emma','farmer_male']),
    get mode(){return mode;}});
})();
