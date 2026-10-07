// v0.58 production bridge
(() => {
  const $ = (s) => document.querySelector(s);
  // Result overlay owns the screen while open.
  const result = $('#battleResult');
  if (result) new MutationObserver(() => {
    document.body.classList.toggle('battleResultMode', getComputedStyle(result).display !== 'none');
  }).observe(result,{attributes:true,attributeFilter:['style','class']});
  // Correct any stale generic defeat copy while the Raider battle is active/finishing.
  const banner = $('#battleBanner');
  if (banner) new MutationObserver(() => {
    if ((document.body.classList.contains('raiderBattleMode') || document.body.classList.contains('raiderFinishing')) && /異常化ゴブリンを倒した/.test(banner.textContent||'')) {
      banner.textContent = 'ゴブリン・レイダーを倒した！';
    }
  }).observe(banner,{childList:true,subtree:true,characterData:true});
})();
