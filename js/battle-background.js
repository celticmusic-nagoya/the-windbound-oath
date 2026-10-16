/* Battle background layer. Registry maps an id to a main image (+ optional foreground); the id is chosen by AREA first, then by enemy id.
   Normal battles (#attackBattle): BG-01 (village/grass/road enemies by id) and BG-02 (moss forest only - the field area decides, never the enemy kind alone).
   Boss battle (#raiderBattle, BG-03): applyRaider()/clearRaider() build their own layers inside #raiderBattle; the call from startRaiderBattle is wired in index.html at integration time.
   Layers: main background (z0, under everything) ... foreground overlay (above the units, below HUD/COMMAND/log, pointer-events:none). Main and foreground share ONE box and ONE
   cover/position rule so a screen ratio can never shift one against the other.
   No image / unknown id => attributes removed and the existing stage gradient is used (fallback). Presentation only: no battle number/logic is touched. */
(function(){
 const DIR='img/battle/backgrounds/';
 const BG={
  'BG-01':{src:DIR+'bg_BG-01_main.png',fore:DIR+'bg_BG-01_fore.png',pos:'50% 0%'},
  'BG-02':{src:DIR+'bg_BG-02_main.png',fore:DIR+'bg_BG-02_fore.png',pos:'50% 0%'},
  'BG-03':{src:DIR+'bg_BG-03_main.png',fore:DIR+'bg_BG-03_fore.png',pos:'50% 0%'}
 };
 /* 1) enemy-id rules that do not depend on the area: Rilde village / grassland / road normal battles (existing enemy ids) */
 const RULES=[[/^(attackGob|northGob)/,'BG-01']];
 /* 2) area rules: an enemy id only maps to the area's background while the battle is fought IN that area. The same enemy appearing in another area stays unassigned. */
 const AREA_RULES={moss_forest:[[/^(mossSlime|forestBat|leafyBoar|forestGob|fieldGob)/,'BG-02']]};
 /* Area context. The field that starts a battle says WHERE it starts it: noteArea(mapId,enemyId) right before startAttackBattle (moss-forest-story hooks). The note is one-shot and bound to that
    enemy id (and expires), so it cannot leak into a later battle; a battle with no matching note has no area (BG-02 enemies stay unassigned - e.g. the same enemy in another area).
    The scene is already hidden when startAttackBattle applies the background, so the visible-scene state cannot be used. setAreaProvider() replaces the source for future areas/tests. */
 const AREA_OF_MAP=[[/^moss_forest_/,'moss_forest']];
 let note=null,areaProvider=id=>{
  if(!note)return null;const n=note;if(n.id!==String(id||'')||Date.now()-n.t>15000)return null;return n.area;
 };
 function noteArea(mapId,enemyId){
  let a=null;for(const[r,k]of AREA_OF_MAP)if(r.test(String(mapId||'')))a=k;
  note=a?{area:a,id:String(enemyId||''),t:Date.now()}:null;
 }
 const root=()=>document.getElementById('attackBattle'),layer=()=>document.getElementById('battleBg');
 function areaOf(id){try{return areaProvider(id)||null}catch(e){return null}}
 function forEnemy(id,area){
  const s=String(id||'');for(const[r,k]of RULES)if(r.test(s))return k;
  const a=area===undefined?areaOf(s):area;if(a&&AREA_RULES[a])for(const[r,k]of AREA_RULES[a])if(r.test(s))return k;
  return null;
 }
 /* one layer pair per battle root; created on demand (no index.html change needed for the normal battle foreground) */
 function ensureFore(){
  const el=root();if(!el)return null;let f=document.getElementById('battleFg');if(f)return f;
  const st=el.querySelector(':scope>.v2BattleStage');if(!st)return null;
  f=document.createElement('div');f.id='battleFg';f.setAttribute('aria-hidden','true');st.appendChild(f);return f;
 }
 function load(key,el,l,f,d){
  /* load failure of the main image => back to the stage gradient (only if this key is still the active one); a failed foreground alone just drops the overlay */
  const probe=new Image();probe.onerror=()=>{if(el.getAttribute('data-bg')===key){el.removeAttribute('data-bg');l.style.backgroundImage='';if(f)f.style.backgroundImage=''}};probe.src=d.src;
  if(f&&d.fore){const fp=new Image();fp.onerror=()=>{if(el.getAttribute('data-bg')===key)f.style.backgroundImage=''};fp.src=d.fore}
 }
 function apply(key){
  const el=root(),l=layer();if(!el||!l)return;
  const d=key&&BG[key];const f=document.getElementById('battleFg')||(d&&d.fore?ensureFore():null);
  if(!d){el.removeAttribute('data-bg');l.style.backgroundImage='';if(f)f.style.backgroundImage='';return}
  l.style.backgroundImage='url("'+d.src+'")';l.style.backgroundPosition=d.pos;el.setAttribute('data-bg',key);
  if(f){f.style.backgroundImage=d.fore?'url("'+d.fore+'")':'';f.style.backgroundPosition=d.pos}
  load(key,el,l,f,d);
 }
 /* ---- boss battle (BG-03). Own layers inside #raiderBattle; not connected to startRaiderBattle yet (index.html integration step). ---- */
 const rroot=()=>document.getElementById('raiderBattle');
 function raiderLayers(){
  const el=rroot();if(!el)return null;let b=document.getElementById('rbBg'),f=document.getElementById('rbFg');
  if(!b){b=document.createElement('div');b.id='rbBg';b.setAttribute('aria-hidden','true');el.insertBefore(b,el.firstChild)}
  if(!f){f=document.createElement('div');f.id='rbFg';f.setAttribute('aria-hidden','true');el.appendChild(f)}
  return {el,b,f};
 }
 function applyRaider(key){
  const k=key||'BG-03',d=BG[k],L=raiderLayers();if(!L)return;
  if(!d){clearRaider();return}
  L.b.style.backgroundImage='url("'+d.src+'")';L.b.style.backgroundPosition=d.pos;L.f.style.backgroundImage=d.fore?'url("'+d.fore+'")':'';L.f.style.backgroundPosition=d.pos;L.el.setAttribute('data-bg',k);
  const probe=new Image();probe.onerror=()=>{if(L.el.getAttribute('data-bg')===k)clearRaider()};probe.src=d.src;
 }
 function clearRaider(){const el=rroot();if(!el)return;el.removeAttribute('data-bg');for(const id of ['rbBg','rbFg']){const n=document.getElementById(id);if(n)n.style.backgroundImage=''}}
 window.BattleBackground={BG,RULES,AREA_RULES,forEnemy,areaOf,setAreaProvider:fn=>{if(typeof fn==='function')areaProvider=fn},apply,applyForEnemy:id=>{const k=forEnemy(id);note=null;apply(k)},noteArea,clear:()=>apply(null),applyRaider,clearRaider};
})();
