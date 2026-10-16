// One action-target contract shared by attack, skills and items.
(() => {
 const q=s=>document.querySelector(s);
 function allies(battle){const r=battle==='raider';return [
  {id:'aidan',name:'エイダン',node:r?'#rbAidan':'#bAidan2',hp:()=>r?rbHP:aahp,active:window.PrologueCombat?.activeAlly(battle,'aidan')!==false},
  {id:'fiona',name:'フィオナ',node:r?'#rbFiona':'#bFiona2',hp:()=>r?rbFHP:normalFHP,active:window.PrologueCombat?.activeAlly(battle,'fiona')!==false}
 ];}
 function enemies(battle){return window.PrologueCombat?.targets(battle)||[{id:'enemy',name:battle==='raider'?'ゴブリンレイダー':'異常化ゴブリン',node:battle==='raider'?'#raiderSprite':'#bGob',hp:()=>battle==='raider'?rbBoss:gghp}];}
 function type(kind){return ['atk','skill','windbloom'].includes(kind)?'enemy_single':kind==='wind'?'enemy_all':kind==='heal'?'ally_single':['prayer','rune','winddance'].includes(kind)?'none':'self';}
 function request(battle,kind,actor,submit,item,receipt){
  const gate=window.BattleCommandGate;receipt ||= gate?.issue(battle);
  if(!receipt||!gate.valid(receipt,battle)||actor!==gate.snapshot(battle).actor||BattleTargetSelector.active)return false;
  const t=item==='potion'?'ally_single':item==='ether'?'ally_single':type(kind);
  const ui=window.BattleUIState,tx=ui?.beginTargets(battle);
  if(ui&&!tx)return false;
  if(!ui){if(battle==='normal')setNormalCommandDrawer(false);else setRaiderCommandDrawer(false);}
  const opened=BattleTargetSelector.open({type:t,battle,actor,candidates:t.startsWith('enemy')?enemies(battle):allies(battle).filter(x=>item!=='ether'||x.id==='fiona'),label:item?'アイテムの対象を選択':'行動の対象を選択',onConfirm:value=>{if(!gate.valid(receipt,battle))return;if(ui)ui.confirmTargets(battle,tx,submit,value);else submit(value)},onCancel:()=>{gate.revoke(receipt);if(ui)ui.cancelTargets(battle,tx);else if(battle==='normal')setNormalCommandDrawer(true);else setRaiderCommandDrawer(true)}});
  if(ui){if(!opened){gate.revoke(receipt);ui.cancelTargets(battle,tx);}else ui.sync(battle);}
  return opened;
 }
 function item(battle,k){
  if(window.BattlePresentation?.busy||(battle==='normal'?attackBattleBusy:rbBusy)||BattleTargetSelector.active)return;
  if(!battleItems[k])return;
  const receipt=window.BattleCommandGate?.issue(battle);if(!receipt)return false;
  const actor=battle==='normal'?normalActor:rbActor;
  return request(battle,'item',actor,target=>{
   if(!battleItems[k])return;
   BattleCommandGate.commit(receipt,{who:actor,kind:'item',item:k,target});
  },k,receipt);
 }
 function applyItem(battle,a){
  const r=battle==='raider',ally=allies(battle).find(x=>x.id===a.target);
  if(a.used||!ally||ally.active===false||ally.hp()<=0||!battleItems[a.item])return false;
  a.used=true;battleItems[a.item]--;
  if(a.item==='potion'){
   if(a.target==='aidan'){if(r)rbHP=Math.min(120,rbHP+45);else aahp=Math.min(100,aahp+45)}
   else {if(r)rbFHP=Math.min(105,rbFHP+45);else normalFHP=Math.min(90,normalFHP+45)}
  }else if(a.target==='fiona'){if(r)rbFMP=Math.min(36,rbFMP+12);else normalFMP=Math.min(30,normalFMP+12)}
  return true;
 }
 window.BattleActionTargets=Object.freeze({request,item,applyItem,allies,enemies,type});
})();
