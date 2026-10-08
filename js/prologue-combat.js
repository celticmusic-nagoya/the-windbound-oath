// Incremental encounter roster. Existing engine owns COMMAND, resources, motion and results.
(() => {
 const q=s=>document.querySelector(s);
 const stats=Object.freeze({goblin:{hp:100,atk:12,def:10,spd:10},tainted_goblin:{hp:190,atk:15,def:11.5,spd:11.5}});
 let generation=0,roundNumber=1,impact=null;
 const rosters={normal:[],raider:[]};
 const alive=b=>rosters[b].filter(e=>e.hp>0);
 function clean(b){
  rosters[b].forEach(e=>{BattleActorState.unregister(b,e.key);if(e.extra)q('#'+e.unit)?.remove()});rosters[b]=[];
 }
 function makeEnemy(b,type,i){
  const e={id:b+'_enemy_'+i,key:'enemy_'+i,type,...stats[type],maxHp:stats[type].hp,extra:i>0,unit:i===0?'v2GobUnit':'normalEnemy'+i,node:i===0?'#bGob':'#normalEnemy'+i+' .prologueSprite'};
  if(e.extra){const el=document.createElement('div');el.id=e.unit;el.className='prologueEnemy slot'+i;el.innerHTML='<div class="prologueEnemyHud"></div><div class="prologueSprite"><img></div>';q('#attackBattle').append(el)}
  q(e.node+' img').alt=type==='goblin'?'ゴブリン':'異常化ゴブリン';
  BattleActorState.register(b,e.key,type,e.node+' img',()=>[e.hp,e.maxHp]);return e;
 }
 function beginNormal(id){
  generation++;roundNumber=1;BattleStatus.clear('normal');BattleTargetSelector.reset('normal');clean('normal');impact=null;
  const types=id==='attackGob1'?['goblin','goblin']:['goblin','goblin','tainted_goblin'];
  rosters.normal=types.map((t,i)=>makeEnemy('normal',t,i));
  document.body.classList.toggle('soloRescue',id==='attackGob1');
  sync('normal');
 }
 function activeAlly(b,id){return !(b==='normal'&&currentGoblin==='attackGob1'&&id==='fiona');}
 function name(e){return e.type==='goblin'?'ゴブリン':'異常化ゴブリン';}
 function targets(b){if(!rosters[b].length)return null;return rosters[b].map(e=>({id:e.id,name:name(e),node:e.node,hp:()=>e.hp}));}
 function sync(b){
  rosters[b].forEach(e=>{
   BattleActorState.sync(b,e.key);
   const text=name(e)+' HP '+Math.max(0,e.hp)+' / '+e.maxHp;
   if(!e.extra){q('#v2EnemyName').textContent=name(e);q('#v2GTxt').textContent=text;q('#v2GHP').style.width=Math.max(0,e.hp/e.maxHp*100)+'%'}
   else q('#'+e.unit+' .prologueEnemyHud').textContent=text;
  });
  if(b==='normal')gghp=rosters.normal.reduce((n,e)=>n+Math.max(0,e.hp),0);
 }
 function damage(e,n,b){if(!e||e.hp<=0)return false;e.hp=Math.max(0,e.hp-n);BattleActorState.set(e.key,e.hp?'damage':'ko',{battle:b,duration:e.hp?520:undefined});v2Hit(e.unit);sync(b);return true;}
 function koAll(b){for(const e of rosters[b]){e.hp=0;BattleActorState.set(e.key,'ko',{battle:b})}sync(b);}
 function log(b,t){if(b==='normal')showBattleBanner(t,1050);else showRaiderBattleLog(t)}
 function heroAction(b,a){
  if(b!=='normal')return;
  const who=a.who,hp=who==='aidan'?aahp:normalFHP;
  if(hp<=0)return;
  if(a.kind==='item'){const used=BattleActionTargets.applyItem(b,a);log(b,used?'アイテムを使った。':'対象が倒れている。アイテムは使わなかった。');return}
  if(a.kind==='guard'){
   if(who==='aidan'){normalGuardA=true;aatp=Math.min(100,aatp+10)}else normalGuardF=true;
   BattleActorState.set(who,'guard',{battle:b});log(b,'防御した。');return;
  }
  if(a.kind==='heal'){
   const target=BattleActionTargets.allies(b).find(x=>x.id===a.target&&x.hp()>0);if(!target||normalFMP<8)return;
   normalFMP-=8;BattleActorState.action('fiona','heal',{battle:b});
   if(a.target==='aidan')aahp=Math.min(100,aahp+42);else normalFHP=Math.min(90,normalFHP+42);
   log(b,'フィオナの「ヒール」！ HP +42');return;
  }
  if(a.kind==='prayer'){
   if(normalFMP<6)return;normalFMP-=6;for(const id of ['aidan','fiona'])if(id==='aidan'&&aahp>0)aahp=Math.min(100,aahp+8);else if(id==='fiona'&&normalFHP>0)normalFHP=Math.min(90,normalFHP+8);
   BattleActorState.action('fiona','prayer',{battle:b});log(b,'フィオナの「風の祈り」！');return;
  }
  const e=rosters[b].find(e=>e.id===a.target);
  // Never auto-retarget a dead selected enemy; refund action resources instead.
  if(!e||e.hp<=0){log(b,'選んだ敵は倒れている。');return}
  impact=e.unit;
  let n=who==='aidan'?(a.kind==='skill'?55:34):20;
  n=BattleStatus.damage(b,who,e.id,Math.round(n*10/e.def));
  if(a.kind==='skill'){if(aatp<30)return;aatp-=30}else if(who==='aidan')aatp=Math.min(100,aatp+15);
  BattleActorState.action(who,'attack',{battle:b});damage(e,n,b);
  log(b,who==='aidan'?(a.kind==='skill'?'一閃！':'エイダンの攻撃！'):'フィオナの攻撃！');
 }
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 async function round(b,actions){
  const token=generation;const statusStart=BattleStatus.snapshot(b);
  setNormalCommandDrawer(false);q('#normalItems').classList.remove('isOpen');
  for(const a of [...actions]){if(token!==generation)return;heroAction(b,a);updateAttackBattle();await sleep(900);if(!alive(b).length){finishAttackBattle();return}}
  if(token===generation)await enemyRound(b,statusStart);
 }
 function skillFor(e){
  if(e.type!=='tainted_goblin')return 'attack';
  const pattern=currentGoblin==='forestGob1'?['burst','attack','attack']:currentGoblin==='forestGob3'?['burst','frenzy','attack']:['attack','burst','frenzy','attack'];
  const n=e.actions||0;e.actions=n+1;return pattern[n%pattern.length];
 }
 async function performEnemy(b,e,skill){
  const token=generation;
  const target=activeAlly(b,'fiona')&&normalFHP/90<aahp/100?'fiona':'aidan';
  BattleActorState.set(e.key,skill==='burst'?'corruption':'attack',{battle:b,duration:skill==='frenzy'?2300:1500});await sleep(680);
  if(token!==generation||!e.hp)return;
  if(skill==='burst'){
   BattleStatus.apply({battle:b,target,type:'atk_down',magnitude:.20,remainingTurns:3,source:e.id});
   log(b,'異常化ゴブリンの《腐蝕の波動》！ '+(target==='aidan'?'エイダン':'フィオナ')+'の攻撃力が低下した！');
   const el=q(e.node);el?.classList.add('corruptionPulse');setTimeout(()=>el?.classList.remove('corruptionPulse'),800);await sleep(850);return;
  }
  const hits=skill==='frenzy'?2:1;
  for(let i=0;i<hits;i++){
   if(token!==generation||!e.hp)return;
   if(!e.extra)WBActors.normalEnemy();else WBActors.enemyAt(e.unit);
   let n=BattleStatus.damage(b,e.id,target,Math.round(e.atk/2*(hits===2?.6:1)));
   if(target==='aidan'?normalGuardA:normalGuardF)n=Math.ceil(n/2);
   if(target==='aidan')aahp=Math.max(0,aahp-n);else normalFHP=Math.max(0,normalFHP-n);
   BattleActorState.set(target,'damage',{battle:b,duration:360});v2Float(target==='aidan'?'floatAidan':'floatFiona','-'+n);log(b,name(e)+(hits===2?'の《狂爪連撃》！ '+(i+1)+'/2':'の攻撃！')+' '+n+'ダメージ。');updateAttackBattle();await sleep(850);
  }
 }
 async function enemyRound(b,statusStart=BattleStatus.snapshot(b)){
  const token=generation;attackBattleBusy=true;
  for(const e of alive(b)){
   if(token!==generation||!e.hp)return;
   await performEnemy(b,e,skillFor(e));
  }
  if(token!==generation)return;
  normalGuardA=normalGuardF=false;BattleActorState.endGuard(b);BattleActorState.endGuard(b,'fiona');
  if(aahp<=0||normalFHP<=0){log(b,'態勢を立て直した……。');aahp=Math.max(35,aahp);normalFHP=Math.max(32,normalFHP);BattleActorState.recover(b);BattleActorState.recover(b,'fiona')}
  BattleStatus.tick(b,statusStart);roundNumber++;normalActor='aidan';normalActs=[];attackBattleBusy=false;updateAttackBattle();
 }
 window.PrologueCombat=Object.freeze({stats,beginNormal,targets,sync,round,enemyRound,koAll,activeAlly,totalMax:b=>rosters[b].reduce((n,e)=>n+e.maxHp,0),impactTarget:()=>impact,get enemies(){return rosters},get roundNumber(){return roundNumber},cancel(){generation++;BattleTargetSelector.cancel()},damage,performEnemy,skillFor});
})();
