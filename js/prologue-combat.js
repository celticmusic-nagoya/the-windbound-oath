// Incremental encounter roster. Existing engine owns COMMAND, resources, motion and results.
(() => {
 const q=s=>document.querySelector(s);
 const stats=Object.freeze({goblin:{hp:100,atk:12,def:10,spd:10},tainted_goblin:{hp:190,atk:15,def:11.5,spd:11.5}});
 let generation=0,roundNumber=1,impact=null,callFlags=[false,false],enragePending=false;
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
 function name(e){if(e.type==='goblin_raider')return 'ゴブリンレイダー';return e.type==='goblin'?'ゴブリン':'異常化ゴブリン';}
 function targets(b){if(!rosters[b].length)return null;return rosters[b].map(e=>({id:e.id,name:name(e),node:e.node,hp:()=>e.hp}));}
 function sync(b){
  rosters[b].forEach(e=>{
   BattleActorState.sync(b,e.key);
   const text=name(e)+' HP '+Math.max(0,e.hp)+' / '+e.maxHp;
   if(b==='normal'&&!e.extra){q('#v2EnemyName').textContent=name(e);q('#v2GTxt').textContent=text;q('#v2GHP').style.width=Math.max(0,e.hp/e.maxHp*100)+'%'}
   else if(e.extra)q('#'+e.unit+' .prologueEnemyHud').textContent=text;
  });
  if(b==='raider')rbAdds=alive(b).filter(e=>e.extra).length;
  if(b==='normal')gghp=rosters.normal.reduce((n,e)=>n+Math.max(0,e.hp),0);
 }
 function damage(e,n,b){if(!e||e.hp<=0)return false;e.hp=Math.max(0,e.hp-n);BattleActorState.set(e.key,e.hp?'damage':'ko',{battle:b,duration:e.hp?520:undefined});v2Hit(e.unit);sync(b);return true;}
 function koAll(b){for(const e of rosters[b]){e.hp=0;BattleActorState.set(e.key,'ko',{battle:b})}sync(b);}
 function log(b,t){if(b==='normal')showBattleBanner(t,1050);else showRaiderBattleLog(t)}
 function heroAction(b,a){
  if(b==='raider')return heroRaider(a);
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
  if(b==='normal')setNormalCommandDrawer(false);else setRaiderCommandDrawer(false);q('#normalItems').classList.remove('isOpen');
  for(const a of [...actions]){if(token!==generation)return;heroAction(b,a);if(b==='normal')updateAttackBattle();else updateRaider();await sleep(900);if(b==='normal'?!alive(b).length:rbBoss<=0){if(b==='normal')finishAttackBattle();else finishRaider();return}}
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
  if(b==='raider')return enemyRaider(statusStart);
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

 function beginRaider(){
  generation++;impact=null;callFlags=[false,false];enragePending=false;BattleStatus.clear('raider');BattleTargetSelector.reset('raider');clean('raider');
  const boss={id:'raider_enemy_0',key:'goblin_raider',type:'goblin_raider',maxHp:1250,def:10,extra:false,unit:'raiderSprite',node:'#raiderSprite',get hp(){return rbBoss},set hp(n){rbBoss=n}};
  rosters.raider=[boss];BattleActorState.register('raider',boss.key,boss.type,'#raiderSprite img',()=>[rbBoss,1250]);sync('raider');
 }
 function spawn(){
  const i=rosters.raider.length,e={id:'raider_enemy_'+i,key:'reinforcement_'+i,type:'tainted_goblin',...stats.tainted_goblin,maxHp:stats.tainted_goblin.hp,extra:true,bornRound:rbRound,unit:'raiderAdd'+i,node:'#raiderAdd'+i+' .prologueSprite',actions:0};
  const el=document.createElement('div');el.id=e.unit;el.className='prologueEnemy raiderAdd slot'+i;el.innerHTML='<div class="prologueEnemyHud"></div><div class="prologueSprite"><img alt="異常化ゴブリン"></div>';q('#raiderBattle').append(el);
  rosters.raider.push(e);BattleActorState.register('raider',e.key,e.type,e.node+' img',()=>[e.hp,e.maxHp]);sync('raider');return e;
 }
 function pendingCall(){return rbBoss>0?callFlags.findIndex((called,i)=>!called&&rbBoss<=[820,500][i]):-1;}
 function heroRaider(a){
  const who=a.who;if((who==='aidan'?rbHP:rbFHP)<=0)return;
  if(a.kind==='item'){log('raider',BattleActionTargets.applyItem('raider',a)?'アイテムを使った。':'対象が倒れている。アイテムは使わなかった。');return}
  if(a.kind==='guard'){
   if(who==='aidan'){rbGuardA=true;rbTP=Math.min(100,rbTP+10)}else rbGuardF=true;
   rbRune=Math.min(100,rbRune+10);BattleActorState.set(who,'guard',{battle:'raider'});log('raider','防御した。RUNE +10');return;
  }
  if(a.kind==='heal'){
   if(rbFMP<8||!BattleActionTargets.allies('raider').some(x=>x.id===a.target&&x.hp()>0))return;
   rbFMP-=8;rbRune=Math.min(100,rbRune+8);if(a.target==='aidan')rbHP=Math.min(120,rbHP+48);else rbFHP=Math.min(105,rbFHP+48);
   BattleActorState.action('fiona','heal',{battle:'raider'});log('raider','フィオナの「ヒール」！ HP +48');return;
  }
  if(a.kind==='rune'){
   if(rbFMP<6)return;rbFMP-=6;rbRune=Math.min(100,rbRune+28);BattleActorState.action('fiona','prayer',{battle:'raider'});log('raider','フィオナの「風の祈り」！');return;
  }
  if(a.kind==='wind'){
   if(rbRune<100)return;rbRune=0;rbQueued=false;
   for(const e of alive('raider'))damage(e,e.extra?e.hp:BattleStatus.damage('raider',who,e.id,255),'raider');
   log('raider','誓いの剣――「風の一閃」！ 増援と破砕斬の構えを吹き飛ばした！');return;
  }
  const e=rosters.raider.find(e=>e.id===a.target);if(!e||e.hp<=0){log('raider','選んだ敵は倒れている。');return}
  impact=e.unit;let n=who==='aidan'?(a.kind==='skill'?68:42):22;
  n=BattleStatus.damage('raider',who,e.id,Math.round(n*10/e.def));
  if(who==='aidan'){if(a.kind==='skill'){if(rbTP<30)return;rbTP-=30;rbRune=Math.min(100,rbRune+14)}else{rbTP=Math.min(100,rbTP+15);rbRune=Math.min(100,rbRune+9)}}else rbRune=Math.min(100,rbRune+7);
  BattleActorState.action(who,'attack',{battle:'raider'});damage(e,n,'raider');
  log('raider',who==='aidan'?(a.kind==='skill'?'エイダンの「一閃」！':'エイダンの攻撃！'):'フィオナが杖で応戦！');
 }
 async function supply(e){
  if(e.hp<=0||rbBoss<=0||e.bornRound>=rbRound)return false;
  BattleActorState.set(e.key,'corruption',{battle:'raider',duration:1500});
  const gained=Math.min(100,1250-rbBoss);rbBoss+=gained;
  const from=q(e.node)?.getBoundingClientRect(),to=q('#raiderSprite')?.getBoundingClientRect();
  if(from&&to){const line=document.createElement('div');line.className='corruptionSupply';const x=from.left+from.width/2,y=from.top+from.height/2,dx=to.left+to.width/2-x,dy=to.top+to.height/2-y;line.style.left=x+'px';line.style.top=y+'px';line.style.width=Math.hypot(dx,dy)+'px';line.style.rotate=Math.atan2(dy,dx)+'rad';document.body.append(line);setTimeout(()=>line.remove(),850)}
  log('raider','異常化ゴブリンの《穢れの供給》！ レイダーの傷が塞がる！ HP +'+gained);updateRaider();await sleep(900);return true;
 }
 async function addAction(e){
  if(e.hp<=0||e.bornRound>=rbRound||rbBoss<=0)return;
  const skill=['supply','burst','frenzy','attack'][e.actions++%4],target=rbHP/120<=rbFHP/105?'aidan':'fiona',token=generation;
  if(skill==='supply'&&rbBoss<1250)return supply(e);
  BattleActorState.set(e.key,skill==='burst'?'corruption':'attack',{battle:'raider',duration:skill==='frenzy'?2300:1500});await sleep(680);
  if(token!==generation||e.hp<=0||rbBoss<=0)return;
  if(skill==='burst'){BattleStatus.apply({battle:'raider',target,type:'atk_down',magnitude:.2,remainingTurns:3,source:e.id});log('raider','異常化ゴブリンの《腐蝕の波動》！ 攻撃力が低下した！');await sleep(850);return}
  const hits=skill==='frenzy'?2:1;
  for(let i=0;i<hits;i++){
   if(token!==generation||e.hp<=0||rbBoss<=0)return;WBActors.enemyAt(e.unit);
   let n=BattleStatus.damage('raider',e.id,target,Math.round(e.atk/2*(hits===2?.6:1)));if(target==='aidan'?rbGuardA:rbGuardF)n=Math.ceil(n/2);
   if(target==='aidan')rbHP=Math.max(0,rbHP-n);else rbFHP=Math.max(0,rbFHP-n);BattleActorState.set(target,'damage',{battle:'raider',duration:360});log('raider','異常化ゴブリン'+(hits===2?'の《狂爪連撃》 '+(i+1)+'/2':'の攻撃')+'！ '+n+'ダメージ。');updateRaider();await sleep(850);
  }
 }
 async function enemyRaider(statusStart){
  const token=generation;rbBusy=true;if(rbBoss<=0)return;
  const call=pendingCall(),phase=rbPhase();
  const pose=rbQueued?'smash':call>=0?'horn':'attack';
  await v53raider(pose,800);if(token!==generation||rbBoss<=0)return;
  if(rbQueued){
   WBActors.raiderEnemy();const base=phase===3?48:42;
   let da=BattleStatus.damage('raider','raider_enemy_0','aidan',base),df=BattleStatus.damage('raider','raider_enemy_0','fiona',base-6);if(rbGuardA)da=Math.ceil(da/2);if(rbGuardF)df=Math.ceil(df/2);
   rbHP=Math.max(0,rbHP-da);rbFHP=Math.max(0,rbFHP-df);rbQueued=false;BattleActorState.set('aidan','damage',{battle:'raider',duration:360});BattleActorState.set('fiona','damage',{battle:'raider',duration:360});log('raider','レイダーの「破砕斬」！ エイダン '+da+' / フィオナ '+df+' ダメージ！');
  }else if(call>=0){callFlags[call]=true;spawn();log('raider','レイダーが角笛を吹いた！ 異常化ゴブリンが現れた。');}
  else if(rbRound%3===0||(phase===3&&rbRound%2===0)){rbQueued=true;log('raider','レイダーが巨大な戦斧を振りかぶった――次のラウンド、「破砕斬」が来る！');}
  else{
   WBActors.raiderEnemy();const target=rbHP<=rbFHP?'aidan':'fiona';let n=BattleStatus.damage('raider','raider_enemy_0',target,(phase===1?21:phase===2?27:32)+rbAdds*3);if(target==='aidan'?rbGuardA:rbGuardF)n=Math.ceil(n/2);
   if(target==='aidan')rbHP=Math.max(0,rbHP-n);else rbFHP=Math.max(0,rbFHP-n);BattleActorState.set(target,'damage',{battle:'raider',duration:360});log('raider','レイダーが'+(target==='aidan'?'エイダン':'フィオナ')+'を狙う！ '+n+'ダメージ。');
  }
  updateRaider();await sleep(950);
  for(const e of alive('raider').filter(e=>e.extra)){if(token!==generation||rbBoss<=0)return;await addAction(e);}
  if(token!==generation||rbBoss<=0)return;
  // Preserved support baseline until the support-policy checkpoint.
  if((rbHP<42||rbFHP<38)&&rbRound%3===0){BattleActorState.action('lou','heal',{battle:'raider'});if(rbHP>0)rbHP=Math.min(120,rbHP+12);if(rbFHP>0)rbFHP=Math.min(105,rbFHP+12);log('raider','ルーの風が二人を包む！ HP +12');}
  rbGuardA=rbGuardF=false;BattleActorState.endGuard('raider');BattleActorState.endGuard('raider','fiona');BattleStatus.tick('raider',statusStart);
  if(rbHP<=0||rbFHP<=0){log('raider','パーティーが崩れた……。ルーの風が時間を巻き戻す。');BattleActorState.action('lou','blessing',{battle:'raider'});setTimeout(()=>{if(token===generation)startRaiderBattle()},1200);return}
  rbRound++;rbActor='aidan';rbActs=[];rbBusy=false;updateRaider();
 }

 window.PrologueCombat=Object.freeze({stats,beginNormal,beginRaider,targets,sync,round,enemyRound,koAll,activeAlly,totalMax:b=>rosters[b].reduce((n,e)=>n+e.maxHp,0),impactTarget:()=>impact,get enemies(){return rosters},get roundNumber(){return roundNumber},cancel(){generation++;BattleTargetSelector.cancel()},damage,performEnemy,skillFor,spawn,supply,addAction,pendingCall,get callFlags(){return [...callFlags]},enrageMoment(){enragePending=true},get enragePending(){return enragePending}});
})();
