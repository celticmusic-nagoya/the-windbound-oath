// Incremental encounter roster. Existing engine owns COMMAND, resources, motion and results.
(() => {
 const q=s=>document.querySelector(s);
 const stats=Object.freeze({goblin:{hp:100,atk:12,def:10,spd:10,cri:0},tainted_goblin:{hp:190,atk:15,def:11.5,spd:11.5,cri:0}});
 let generation=0,roundNumber=1,impact=null,callFlags=[false,false],enragePending=false,lastSupportRound=0,blessingUsed=false,normalRune=0,enrageFlow=null;
 const rosters={normal:[],raider:[]};
 const victories=new Map();
 function claimVictory(b){if(victories.get(b)===generation)return false;victories.set(b,generation);return true;}
 function instantKill(b){
  if(!window.WINDBOUND_DEV||!document.body.classList.contains(b==='normal'?'normalBattleMode':'raiderBattleMode')||!alive(b).length||victories.get(b)===generation)return false;
  generation++;window.BattlePresentation?.cancel();BattleTargetSelector.cancel();
  q('#devPanel').style.display='none';q('#normalItems').classList.remove('isOpen');
  if(b==='normal'){normalActs=[];attackBattleBusy=true;setNormalCommandDrawer(false)}else{rbActs=[];rbQueued=false;rbBusy=true;setRaiderCommandDrawer(false)}
  koAll(b);if(b==='normal'){updateAttackBattle();finishAttackBattle()}else{updateRaider();finishRaider()}
  return true;
 }
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
  generation++;window.BattlePresentation?.cancel();window.BattleFacing?.set('NORMAL');normalRune=0;roundNumber=1;BattleStatus.clear('normal');BattleTargetSelector.reset('normal');clean('normal');impact=null;
  const types=id==='attackGob1'?['goblin','goblin']:['goblin','goblin','tainted_goblin'];
  rosters.normal=types.map((t,i)=>makeEnemy('normal',t,i));
  document.body.classList.toggle('soloRescue',id==='attackGob1');
  sync('normal');window.BattlePartyLayout?.refresh('normal');window.BattlePresentation?.updateRune(normalRune);
  if(id==='attackGob2')window.BattlePresentation?.banter('tainted-first',['エイダン「こいつ……さっきの奴らと違う！」','フィオナ「この魔力……普通じゃない……！」'],'normal');
 }
 function activeAlly(b,id){return !(b==='normal'&&currentGoblin==='attackGob1'&&id==='fiona');}
 function name(e){if(e.type==='goblin_raider')return 'ゴブリンレイダー';return e.type==='goblin'?'ゴブリン':'異常化ゴブリン';}
 function targets(b){if(!rosters[b].length)return null;return rosters[b].map(e=>({id:e.id,name:name(e),node:e.node,hp:()=>e.hp}));}
 function syncLogic(b){
  if(b==='raider')rbAdds=alive(b).filter(e=>e.extra).length;
  if(b==='normal')gghp=rosters.normal.reduce((n,e)=>n+Math.max(0,e.hp),0);
 }
 function sync(b){
  syncLogic(b);
  rosters[b].forEach(e=>{
   if(!e.pend)e.shown=e.hp;   // a pending delayed hit keeps the bar at the pre-hit value until the blow frame
   BattleActorState.sync(b,e.key);
   const text=name(e)+' HP '+Math.max(0,e.shown)+' / '+e.maxHp;
   if(b==='normal'&&!e.extra){q('#v2EnemyName').textContent=name(e);q('#v2GTxt').textContent=text;q('#v2GHP').style.width=Math.max(0,e.shown/e.maxHp*100)+'%'}
   else if(e.extra)q('#'+e.unit+' .prologueEnemyHud').textContent=text;
  });
 }
 // Hit sync: HP / KO / state are LOGIC and apply at once; only the presentation (hit pose, flash, HP bar, banner number, crit pop) may wait for the
 // blow frame of a delivered attack motion (BattleMotion.hitDelay). No motion installed -> delay 0 -> identical to before.
 function hitDelay(who,a){return !a||a.presented||!window.BattleMotion?0:Math.max(0,Math.min(600,BattleMotion.hitDelay(who,'attack')||0));}
 function later(ms,fn){if(ms<=0){fn();return;}const g=generation;setTimeout(()=>{if(g===generation)fn();},ms);}
 function damage(e,n,b,delay=0){
  if(!e||e.hp<=0)return false;e.hp=Math.max(0,e.hp-n);syncLogic(b);
  e.pend=(e.pend||0)+(delay>0?1:0);
  later(delay,()=>{if(delay>0)e.pend=Math.max(0,(e.pend||1)-1);BattleActorState.set(e.key,e.hp?'damage':'ko',{battle:b,duration:e.hp?520:undefined});v2Hit(e.unit);sync(b);});
  return true;
 }
 function koAll(b){for(const e of rosters[b]){e.hp=0;BattleActorState.set(e.key,'ko',{battle:b})}sync(b);}
 function log(b,t,owned=false){BattlePresentation.log(()=>{if(b==='normal')showBattleBanner(t,1050);else showRaiderBattleLog(t)},owned)}
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
   if(normalFMP<6)return;normalFMP-=6;const gained=Math.min(28,100-normalRune);normalRune+=gained;BattlePresentation.updateRune(normalRune);
   log(b,'フィオナの「風の祈り」！ RUNE +'+gained,true);return;
  }
  const e=rosters[b].find(e=>e.id===a.target);
  // Never auto-retarget a dead selected enemy; refund action resources instead.
  if(!e||e.hp<=0){log(b,'選んだ敵は倒れている。');return}
  impact=e.unit;
  let n=who==='aidan'?(a.kind==='skill'?55:34):20;
  n=BattleStatus.damage(b,who,e.id,Math.round(n*10/e.def));
  if(a.kind==='windbloom'){if(normalFMP<8)return;normalFMP-=8;n=windbloomDamage(b,e)}
  else if(a.kind==='skill'){if(aatp<30)return;aatp-=30}else if(who==='aidan')aatp=Math.min(100,aatp+15);
  const hit=BattleCritical.resolve(a,n);
  if(!a.presented&&hit.critical)BattleActorState.set(who,'attack',{battle:b,duration:(who==='aidan'?820:680)+100});else if(!a.presented)BattleActorState.action(who,'attack',{battle:b});const dl=hitDelay(who,a);damage(e,hit.damage,b,dl);hit.delay=dl;
  later(dl,()=>{log(b,(who==='aidan'?(a.kind==='skill'?'一閃！':'エイダンの攻撃！'):(a.kind==='windbloom'?'フィオナの「風花の舞」！':'フィオナの攻撃！'))+(hit.critical?' 会心の一撃！':'')+' '+name(e)+'に'+hit.damage+'のダメージ！',a.presented);
  BattleCriticalPresentation.show(b,who,e,hit);});return hit;
 }
 const sleep=ms=>new Promise(r=>setTimeout(r,ms));
 function canPresent(b,a){
  if((b==='normal'?(a.who==='aidan'?aahp:normalFHP):(a.who==='aidan'?rbHP:rbFHP))<=0)return false;
  const mp=b==='normal'?normalFMP:rbFMP,tp=b==='normal'?aatp:rbTP;
  if(a.kind==='skill'&&tp<30||a.kind==='windbloom'&&mp<8||['prayer','rune'].includes(a.kind)&&mp<6||a.kind==='wind'&&rbRune<100)return false;
  return !['skill','windbloom'].includes(a.kind)||rosters[b].some(e=>e.id===a.target&&e.hp>0);
 }
 // Small, explicitly MAG-based wind spell: MP8, MAG ×2; no critical or RUNE gain.
 function windbloomDamage(b,e){return Math.max(1,Math.round(charStats('fiona').mag*2*10/e.def/BattleStatus.multiplier(b,e.id,'def')));}
 async function situationalBanter(b,token){
  if(token!==generation)return;
  const hp=b==='normal'?normalFHP:rbFHP,max=b==='normal'?90:105;
  if(activeAlly(b,'fiona')&&hp>0&&hp<=max*.3)await BattlePresentation.banter('fiona-danger',['エイダン「フィオナ、無理するな！」','フィオナ「大丈夫……まだ、支えられる！」'],b,token);
  if(b==='raider'&&rbRune>=100&&rbBoss>0)await BattlePresentation.banter('rune-ready',['フィオナ「風の力が満ちてる……！」','ルー「今だよ、誓いの剣に力を！」'],b,token);
  if(enrageFlow&&b==='raider')await enrageFlow;
 }

 async function round(b,actions){
  const token=generation;if(b==='normal')attackBattleBusy=true;else rbBusy=true;const statusStart=BattleStatus.snapshot(b);
  if(b==='normal')setNormalCommandDrawer(false);else setRaiderCommandDrawer(false);q('#normalItems').classList.remove('isOpen');
  for(const a of [...actions]){if(token!==generation)return;await situationalBanter(b,token);if(token!==generation)return;
   if(BattlePresentation.definition(a.kind)&&canPresent(b,a)){impact=rosters[b].find(e=>e.id===a.target)?.unit||(a.kind==='wind'?'raiderSprite':impact);if(!await BattlePresentation.action(b,a.kind,token))return;a.presented=true;}
   if(token!==generation)return;const hit=heroAction(b,a);later(hit?.delay||0,()=>{if(b==='normal')updateAttackBattle();else updateRaider();});await situationalBanter(b,token);await sleep(hit?.critical?1000:900);if(token!==generation)return;if(b==='normal'?!alive(b).length:rbBoss<=0){if(b==='normal')finishAttackBattle();else finishRaider();return}}
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
   const el=q(e.node);el?.classList.add('corruptionPulse');setTimeout(()=>el?.classList.remove('corruptionPulse'),800);await sleep(850);await BattlePresentation.banter('corruption-first',['フィオナ「力を削がれてる……あの魔力に気をつけて！」'],b,token);return;
  }
  const hits=skill==='frenzy'?2:1;
  for(let i=0;i<hits;i++){
   if(token!==generation||!e.hp)return;
   if(!e.extra)WBActors.normalEnemy();else WBActors.enemyAt(e.unit);
   let n=BattleStatus.damage(b,e.id,target,Math.round(e.atk/2*(hits===2?.6:1)));
   if(target==='aidan'?normalGuardA:normalGuardF)n=Math.ceil(n/2);
   if(target==='aidan')aahp=Math.max(0,aahp-n);else normalFHP=Math.max(0,normalFHP-n);
   BattleActorState.set(target,'damage',{battle:b,duration:360});v2Float(target==='aidan'?'floatAidan':'floatFiona','-'+n);log(b,name(e)+(hits===2?'の《狂爪連撃》！ '+(i+1)+'/2':'の攻撃！')+' '+n+'ダメージ。');updateAttackBattle();await sleep(850);await situationalBanter(b,token);
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
  generation++;window.BattlePresentation?.cancel();window.BattleFacing?.set('NORMAL');enrageFlow=null;impact=null;callFlags=[false,false];enragePending=false;lastSupportRound=0;blessingUsed=false;BattleStatus.clear('raider');BattleTargetSelector.reset('raider');clean('raider');
  const boss={id:'raider_enemy_0',key:'goblin_raider',type:'goblin_raider',maxHp:1250,def:10,cri:0,extra:false,unit:'raiderSprite',node:'#raiderSprite',get hp(){return rbBoss},set hp(n){rbBoss=n}};
  rosters.raider=[boss];BattleActorState.register('raider',boss.key,boss.type,'#raiderSprite img',()=>[rbBoss,1250]);sync('raider');window.BattlePartyLayout?.refresh('raider');
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
   if(rbFMP<6)return;rbFMP-=6;const gained=Math.min(28,100-rbRune);rbRune+=gained;log('raider','フィオナの「風の祈り」！ RUNE +'+gained,true);return;
  }
  if(a.kind==='wind'){
   if(rbRune<100)return;rbRune=0;rbQueued=false;
   for(const e of alive('raider'))damage(e,e.extra?e.hp:BattleStatus.damage('raider',who,e.id,255),'raider');
   log('raider','誓いの剣――「風の一閃」！ 増援と破砕斬の構えを吹き飛ばした！',true);return;
  }
  const e=rosters.raider.find(e=>e.id===a.target);if(!e||e.hp<=0){log('raider','選んだ敵は倒れている。');return}
  impact=e.unit;let n=who==='aidan'?(a.kind==='skill'?68:42):22;
  n=BattleStatus.damage('raider',who,e.id,Math.round(n*10/e.def));
  if(a.kind==='windbloom'){if(rbFMP<8)return;rbFMP-=8;n=windbloomDamage('raider',e)}
  else if(who==='aidan'){if(a.kind==='skill'){if(rbTP<30)return;rbTP-=30;rbRune=Math.min(100,rbRune+14)}else{rbTP=Math.min(100,rbTP+15);rbRune=Math.min(100,rbRune+9)}}else rbRune=Math.min(100,rbRune+7);
  const hit=BattleCritical.resolve(a,n);
  if(!a.presented&&hit.critical)BattleActorState.set(who,'attack',{battle:'raider',duration:(who==='aidan'?820:680)+100});else if(!a.presented)BattleActorState.action(who,'attack',{battle:'raider'});const dl=hitDelay(who,a);damage(e,hit.damage,'raider',dl);hit.delay=dl;
  later(dl,()=>{log('raider',(who==='aidan'?(a.kind==='skill'?'エイダンの「一閃」！':'エイダンの攻撃！'):(a.kind==='windbloom'?'フィオナの「風花の舞」！':'フィオナが杖で応戦！'))+(hit.critical?' 会心の一撃！':'')+' '+name(e)+'に'+hit.damage+'のダメージ！',a.presented);
  BattleCriticalPresentation.show('raider',who,e,hit);});return hit;
 }
 async function supply(e){
  const token=generation;
  if(e.hp<=0||rbBoss<=0||e.bornRound>=rbRound)return false;
  BattleActorState.set(e.key,'corruption',{battle:'raider',duration:1500});
  const gained=Math.min(100,1250-rbBoss);rbBoss+=gained;
  const from=q(e.node)?.getBoundingClientRect(),to=q('#raiderSprite')?.getBoundingClientRect();
  if(from&&to){const line=document.createElement('div');line.className='corruptionSupply';const x=from.left+from.width/2,y=from.top+from.height/2,dx=to.left+to.width/2-x,dy=to.top+to.height/2-y;line.style.left=x+'px';line.style.top=y+'px';line.style.width=Math.hypot(dx,dy)+'px';line.style.rotate=Math.atan2(dy,dx)+'rad';document.body.append(line);setTimeout(()=>line.remove(),850)}
  log('raider','異常化ゴブリンの《穢れの供給》！ レイダーの傷が塞がる！ HP +'+gained);updateRaider();await sleep(900);if(token!==generation)return false;await BattlePresentation.banter('supply-first',['エイダン「あいつを先に倒さないと、傷が塞がってしまう！」'],'raider',token);return token===generation;
 }
 async function addAction(e){
  if(e.hp<=0||e.bornRound>=rbRound||rbBoss<=0)return;
  const skill=['supply','burst','frenzy','attack'][e.actions++%4],target=rbHP/120<=rbFHP/105?'aidan':'fiona',token=generation;
  if(skill==='supply'&&rbBoss<1250)return supply(e);
  BattleActorState.set(e.key,skill==='burst'?'corruption':'attack',{battle:'raider',duration:skill==='frenzy'?2300:1500});await sleep(680);
  if(token!==generation||e.hp<=0||rbBoss<=0)return;
  if(skill==='burst'){BattleStatus.apply({battle:'raider',target,type:'atk_down',magnitude:.2,remainingTurns:3,source:e.id});log('raider','異常化ゴブリンの《腐蝕の波動》！ 攻撃力が低下した！');await sleep(850);await BattlePresentation.banter('corruption-first',['フィオナ「力を削がれてる……あの魔力に気をつけて！」'],'raider',token);return}
  const hits=skill==='frenzy'?2:1;
  for(let i=0;i<hits;i++){
   if(token!==generation||e.hp<=0||rbBoss<=0)return;WBActors.enemyAt(e.unit);
   let n=BattleStatus.damage('raider',e.id,target,Math.round(e.atk/2*(hits===2?.6:1)));if(target==='aidan'?rbGuardA:rbGuardF)n=Math.ceil(n/2);
   if(target==='aidan')rbHP=Math.max(0,rbHP-n);else rbFHP=Math.max(0,rbFHP-n);BattleActorState.set(target,'damage',{battle:'raider',duration:360});log('raider','異常化ゴブリン'+(hits===2?'の《狂爪連撃》 '+(i+1)+'/2':'の攻撃')+'！ '+n+'ダメージ。');updateRaider();await sleep(850);
  }
 }
 async function enemyRaider(statusStart){
  const token=generation;rbBusy=true;if(rbBoss<=0)return;
  await situationalBanter('raider',token);if(token!==generation||rbBoss<=0)return;
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
  updateRaider();await sleep(950);if(call>=0&&callFlags[call])await BattlePresentation.banter('call-first',['ルー「あの紫のゴブリン……気をつけて！」'],'raider',token);await situationalBanter('raider',token);
  for(const e of alive('raider').filter(e=>e.extra)){if(token!==generation||rbBoss<=0)return;await addAction(e);}
  if(token!==generation||rbBoss<=0)return;
  support();await situationalBanter('raider',token);if(token!==generation||rbBoss<=0)return;
  rbGuardA=rbGuardF=false;BattleActorState.endGuard('raider');BattleActorState.endGuard('raider','fiona');BattleStatus.tick('raider',statusStart);
  if(rbHP<=0||rbFHP<=0){log('raider','パーティーが崩れた……。ルーの風が時間を巻き戻す。');BattleActorState.action('lou','blessing',{battle:'raider'});setTimeout(()=>{if(token===generation)startRaiderBattle()},1200);return}
  rbRound++;rbActor='aidan';rbActs=[];rbBusy=false;updateRaider();
 }


 function buffParty(type){for(const ally of BattleActionTargets.allies('raider'))if(ally.active!==false&&ally.hp()>0)BattleStatus.apply({battle:'raider',target:ally.id,type,magnitude:.15,remainingTurns:3,source:'lou'});}
 function support(force){
  if(rbBoss<=0||BattleActorState.get('raider','lou')==='victory')return false;
  if(force==='blessing')return finalBlessing();
  if(rbRound-lastSupportRound<2)return false;
  const danger=rbHP>0&&rbHP<42||rbFHP>0&&rbFHP<38;
  if(!danger&&rbRound-lastSupportRound<3)return false;
  lastSupportRound=rbRound;
  if(danger){BattleActorState.action('lou','heal',{battle:'raider'});if(rbHP>0)rbHP=Math.min(120,rbHP+12);if(rbFHP>0)rbFHP=Math.min(105,rbFHP+12);log('raider','ルーの《妖精の癒し》！ HP +12');}
  else {BattleActorState.action('lou','blessing',{battle:'raider'});buffParty('def_up');log('raider','ルーの《風の加護》！ DEF +15%（3ターン）');}
  return true;
 }
 async function finalBlessing(){
  if(blessingUsed||rbBoss<=0)return false;blessingUsed=true;const token=generation;
  await BattlePresentation.banter('enrage-cooperation',['ルー「大丈夫、ルーもいるよ！　みんなに、風の祝福を！」'],'raider',token);
  if(token!==generation||rbBoss<=0)return false;
  if(!await BattlePresentation.action('raider','blessing',token)||token!==generation||rbBoss<=0)return false;
  enragePending=false;lastSupportRound=rbRound;buffParty('atk_up');buffParty('def_up');
  log('raider','ルーの《妖精の祝福》！ ATK / DEF +15%（3ターン）');updateRaider();return true;
 }
 function enrageMoment(){
  if(blessingUsed||enragePending)return;enragePending=true;
  const flow=finalBlessing();enrageFlow=flow;flow.finally(()=>{if(enrageFlow===flow)enrageFlow=null;});
 }


 window.PrologueCombat=Object.freeze({stats,claimVictory,instantKill,beginNormal,beginRaider,targets,sync,round,enemyRound,koAll,activeAlly,totalMax:b=>rosters[b].reduce((n,e)=>n+e.maxHp,0),impactTarget:()=>impact,get generation(){return generation},get enemies(){return rosters},get normalRune(){return normalRune},get roundNumber(){return roundNumber},cancel(){generation++;window.BattlePresentation?.cancel();BattleTargetSelector.cancel()},damage,performEnemy,skillFor,spawn,supply,addAction,pendingCall,get callFlags(){return [...callFlags]},enrageMoment,support,get enragePending(){return enragePending}});
})();
