/* Battle background layer (normal battles). Registry maps an id to an image; assignment is by enemy id.
   No image / unknown id => attribute removed and the existing stage gradient is used (fallback). */
(function(){
 const BG={
  'BG-01':{src:'img/battle/backgrounds/bg_BG-01_main.png',pos:'50% 0%',fore:null}/* fore: bg_BG-01_fore.png (not produced yet) */
 };
 /* Rilde village / grassland / road normal battles (existing enemy ids) */
 const RULES=[[/^(attackGob|northGob)/,'BG-01']];
 const root=()=>document.getElementById('attackBattle'),layer=()=>document.getElementById('battleBg');
 function forEnemy(id){for(const[r,k]of RULES)if(r.test(String(id||'')))return k;return null}
 function apply(key){
  const el=root(),l=layer();if(!el||!l)return;
  const d=key&&BG[key];
  if(!d){el.removeAttribute('data-bg');l.style.backgroundImage='';return}
  l.style.backgroundImage='url("'+d.src+'")';l.style.backgroundPosition=d.pos;el.setAttribute('data-bg',key);
  /* load failure => drop back to the existing stage gradient (only if this key is still the active one) */
  const probe=new Image();probe.onerror=()=>{if(el.getAttribute('data-bg')===key){el.removeAttribute('data-bg');l.style.backgroundImage=''}};probe.src=d.src;
 }
 window.BattleBackground={BG,forEnemy,apply,applyForEnemy:id=>apply(forEnemy(id)),clear:()=>apply(null)};
})();
