// One action-target contract shared by attack, skills and items.
(() => {
 const q=s=>document.querySelector(s);
 function allies(battle){const r=battle==='raider';return [
  {id:'aidan',name:'エイダン',node:r?'#rbAidan':'#bAidan2',hp:()=>r?rbHP:aahp},
  {id:'fiona',name:'フィオナ',node:r?'#rbFiona':'#bFiona2',hp:()=>r?rbFHP:normalFHP}
 ];}
 function enemies(battle){return window.PrologueCombat?.targets(battle)||[{id:'enemy',name:battle==='raider'?'ゴブリンレイダー':'異常化ゴブリン',node:battle==='raider'?'#raiderSprite':'#bGob',hp:()=>battle==='raider'?rbBoss:gghp}];}
 function type(kind){return ['atk','skill'].includes(kind)?'enemy_single':kind==='wind'?'enemy_all':kind==='heal'?'ally_single':kind==='prayer'?'ally_all':kind==='rune'?'none':'self';}
 function request(battle,kind,actor,submit,item){
  const t=item==='potion'?'ally_single':item==='ether'?'ally_single':type(kind);
  if(battle==='normal')setNormalCommandDrawer(false);else setRaiderCommandDrawer(false);
  return BattleTargetSelector.open({type:t,battle,actor,candidates:t.startsWith('enemy')?enemies(battle):allies(battle),label:item?'アイテムの対象を選択':'行動の対象を選択',onConfirm:submit,onCancel:()=>{if(battle==='normal')setNormalCommandDrawer(true);else setRaiderCommandDrawer(true)}});
 }
 function item(battle,k){
  if((battle==='normal'?attackBattleBusy:rbBusy)||BattleTargetSelector.active)return;
  if(!battleItems[k])return;
  const actor=battle==='normal'?normalActor:rbActor;
  request(battle,'item',actor,target=>{
   if(!battleItems[k])return;
   const action={who:actor,kind:'item',item:k,target};
   q('#normalItems').classList.remove('isOpen');q('#normalItems').style.display='none';
   if(battle==='normal'){normalActs.push(action);advanceNormalActor();}
   else{rbActs.push(action);if(actor==='aidan'){rbActor='fiona';updateRaider()}else{rbBusy=true;resolvePartyRound()}}
  },k);
 }
 function applyItem(battle,a){
  const r=battle==='raider',ally=allies(battle).find(x=>x.id===a.target);
  if(a.used||!ally||ally.hp()<=0||!battleItems[a.item])return false;
  a.used=true;battleItems[a.item]--;
  if(a.item==='potion'){
   if(a.target==='aidan'){if(r)rbHP=Math.min(120,rbHP+45);else aahp=Math.min(100,aahp+45)}
   else {if(r)rbFHP=Math.min(105,rbFHP+45);else normalFHP=Math.min(90,normalFHP+45)}
  }else if(a.target==='fiona'){if(r)rbFMP=Math.min(36,rbFMP+12);else normalFMP=Math.min(30,normalFMP+12)}
  return true;
 }
 window.BattleActionTargets=Object.freeze({request,item,applyItem,allies,enemies,type});
})();
