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
  for(const [value,text]of [['original','Original'],['smooth','Smooth HD'],['crisp','Crisp HD · 表示解像度描画']]){
    const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);
  }
  label.append(select);controls.append(label);
  const scopeLabel=document.createElement('label');scopeLabel.append('適用対象（試験） ');
  const scope=document.createElement('select');scope.setAttribute('aria-label','画質の適用対象');
  for(const [value,text]of [['representatives','Aidan／Emma／農夫'],['all','全キャラクター／NPC']]){
    const option=document.createElement('option');option.value=value;option.textContent=text;scope.append(option);
  }
  scopeLabel.append(scope);controls.append(scopeLabel);
  scope.addEventListener('change',()=>document.body.dataset.lindRenderingScope=scope.value);
  document.body.dataset.lindRenderingScope='representatives';
  const emmaLabel=document.createElement('label');emmaLabel.append('Emmaの生活動作（試験） ');
  const emma=document.createElement('select');emma.setAttribute('aria-label','Emmaの生活動作（試験）');
  for(const value of ['current','natural','active']){const option=document.createElement('option');
    option.value=value;option.textContent=value.toUpperCase();emma.append(option);}
  emmaLabel.append(emma);controls.append(emmaLabel);
  emma.addEventListener('change',()=>window.LindVillageLife?.setEmmaMode(emma.value));
  let mode='original';
  function setMode(next){
    if(!['original','smooth','crisp'].includes(next))return false;
    mode=next;select.value=next;document.body.dataset.lindCharacterRendering=next;return true;
  }
  select.addEventListener('change',()=>setMode(select.value));setMode('original');
  window.LindCharacterRendering=Object.freeze({setMode,actors:Object.freeze(['aidan','emma','farmer_male']),
    get mode(){return mode;}});
})();
