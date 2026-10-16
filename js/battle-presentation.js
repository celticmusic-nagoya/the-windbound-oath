// Awaited presentation boundaries. No timers here consume resources or advance turns.
(() => {
 const durations=Object.freeze({SHORT:1250,SPECIAL:2000});   // full-mode display time; setting 'SHORT' still caps at SHORT_CAP
 const definitions=Object.freeze({
  skill:{actor:'aidan',name:'一閃',type:'SHORT',state:'skill'},
  wind:{actor:'aidan',name:'風の一閃',type:'SPECIAL',state:'wind'},
  windbloom:{actor:'fiona',name:'風花の舞',type:'SHORT',state:'skill'},
  prayer:{actor:'fiona',name:'風の祈り',type:'SHORT',state:'prayer'},
  rune:{actor:'fiona',name:'風の祈り',type:'SHORT',state:'prayer'},
  blessing:{actor:'lou',name:'妖精の祝福',type:'SPECIAL',state:'rune'}
 });
 const SHORT_CAP=550;
 let epoch=0,queue=Promise.resolve(),pending=new Set(),seen=new Set(),motionOwned=false,setting='FULL';
 const active=new Set();
 // Owned input locks (BattleLoading): separate from `active` so cancel() - which a battle start calls - can never drop them. Released only by their own owner.
 const locks=new Set();
 const syncBusy=()=>document.body.classList.toggle('battlePresentationBusy',active.size>0||locks.size>0);
 function valid(token){return token===PrologueCombat.generation;}
 function cancel(){
  epoch++;for(const finish of [...pending])finish(false);pending.clear();active.clear();queue=Promise.resolve();seen.clear();
  document.body.classList.remove('wbShake','wbHeavyShake');syncBusy();document.querySelector('#wbImpactLayer')?.replaceChildren();document.querySelectorAll('.skillCutin,.battleBanter,.battleWindEffect,.battleDamageNumber').forEach(e=>e.remove());
 }
 function wait(ms,token,node){return new Promise(resolve=>{
  let done=false,timer;const finish=result=>{if(done)return;done=true;clearTimeout(timer);pending.delete(finish);node?.remove();resolve(result&&valid(token));};
  pending.add(finish);timer=setTimeout(()=>finish(true),ms);
 });}
 function run(job,token=PrologueCombat.generation){
  const cycle=epoch;
  const result=queue.then(async()=>{
   if(cycle!==epoch||!valid(token))return false;
   const lock={};active.add(lock);syncBusy();
   try{return await job(token)}finally{active.delete(lock);syncBusy();}
  });queue=result.catch(()=>false);return result;
 }
 // Input hold that starts at once (not queued behind banter): shares the presentation lock, so cancel() / a new battle releases it. Used by BattleOpening.
 // `until` (optional Promise): the lock also waits for it after the minimum `ms` (cancel()/new battle still release at once).
 function hold(ms,token=PrologueCombat.generation,until){
  const lock={};active.add(lock);syncBusy();
  const release=()=>{active.delete(lock);syncBusy();};
  return wait(ms,token).then(r=>r&&until?Promise.resolve(until).then(()=>r&&valid(token),()=>r&&valid(token)):r).then(r=>{release();return r;},e=>{release();throw e;});
 }
 async function showSkillCutin({actor,skill,type='SHORT',image,duration=durations[type]||550},token=PrologueCombat.generation){
  if(setting==='OFF')return valid(token);
  return run(async t=>{
   const effectiveDuration=setting==='SHORT'?Math.min(duration,SHORT_CAP):duration;
   const el=document.createElement('div');el.className='skillCutin '+(setting==='SHORT'?'SHORT':type);el.dataset.skill=skill;el.dataset.actor=actor;el.style.setProperty('--cutin-duration',effectiveDuration+'ms');
   const art=document.createElement('img');art.src=image;art.alt=actor+' — '+skill;
   const name=document.createElement('strong');name.textContent=skill;const rune=document.createElement('span');rune.className='cutinRune';rune.textContent='᚛ ᚃ ᚑ ᚐ ᚈ ᚓ ᚜';
   el.append(rune,art,name);document.body.append(el);
   // Keep the display interval after decode; no first-use flash of an empty panel.
   await art.decode().catch(()=>{});if(!valid(t)){el.remove();return false;}
   return wait(effectiveDuration,t,el);
  },token);
 }
 function banter(key,lines,battle,token=PrologueCombat.generation){
  if(seen.has(key)||!valid(token))return Promise.resolve(false);seen.add(key);
  return run(async t=>{
   const box=document.createElement('aside');box.className='battleBanter';box.dataset.key=key;box.setAttribute('role','status');
   for(const text of lines.slice(0,2)){const line=document.createElement('p');line.textContent=text;box.append(line);}document.body.append(box);
   return wait(lines.length>1?1500:1100,t,box);
  },token);
 }
 // Owned input lock: lock(owner) -> {release()}. Counts as busy (every command guard that reads BattlePresentation.busy sees it) and is NOT cleared by cancel().
 // Each call returns its own handle; release() is idempotent and removes ONLY that handle, so an old owner can never release a newer owner's lock.
 function lock(owner){
  const handle=Object.freeze({owner:String(owner||'lock'),release(){if(!locks.has(handle))return false;locks.delete(handle);syncBusy();return true;},get held(){return locks.has(handle)}});
  locks.add(handle);syncBusy();return handle;
 }
 // The single public command-acceptance condition for battle input: no presentation / opening hold, no owned lock and no BattleLoading in progress.
 const blockers=()=>{const b=[];if(window.BattleLoading&&BattleLoading.active)b.push('loading');if(locks.size)b.push(...[...locks].map(l=>'lock:'+l.owner));if(active.size)b.push('presentation');return b;};
 function definition(kind){return definitions[kind];}
 function windEffect(battle,actor){
  const host=document.querySelector(battle==='normal'?(actor==='aidan'?'#bAidan2':'#bFiona2'):actor==='lou'?'#rbLou':actor==='aidan'?'#rbAidan':'#rbFiona');
  if(!host)return;const r=host.getBoundingClientRect(),el=document.createElement('div');el.className='battleWindEffect';el.style.left=r.left+'px';el.style.top=r.top+'px';el.style.width=r.width+'px';el.style.height=r.height+'px';document.body.append(el);setTimeout(()=>el.remove(),800);
 }
 async function action(battle,kind,token=PrologueCombat.generation){
  const d=definition(kind);if(!d)return valid(token);
  if(!await showSkillCutin({actor:d.actor,skill:d.name,type:d.type,image:BATTLE_CUTINS[kind==='rune'?'prayer':kind]},token))return false;
  if(!valid(token)||['ko','victory'].includes(BattleActorState.get(battle,d.actor)))return false;
  BattleActorState.set(d.actor,d.state,{battle,duration:d.actor==='aidan'?1200:1100});
  if(d.actor==='aidan')WBActors[battle==='normal'?'normalAidan':'raiderAidan']();
  else if(d.actor==='fiona')WBActors[battle==='normal'?'normalFionaMagic':'raiderFionaMagic'](kind);
  windEffect(battle,d.actor);return run(t=>wait(d.actor==='aidan'?380:330,t),token);
 }
 function log(callback,owned){motionOwned=!!owned;try{return callback()}finally{motionOwned=false;}}
 // Presentation consumes keyboard input while visible; DEV buttons remain usable above it.
 addEventListener('keydown',e=>{if(active.size&&['ArrowLeft','ArrowRight','Enter',' ','Escape'].includes(e.key)){e.preventDefault();e.stopImmediatePropagation();}},true);
 const readout=document.createElement('small');readout.id='normalRuneReadout';document.querySelector('#attackBattle').append(readout);
 window.BattleCutinManager=Object.freeze({showSkillCutin,setMode(value){if(!['FULL','SHORT','OFF'].includes(value))return false;setting=value;return true;},get mode(){return setting},durations});
 window.BattleBanter=Object.freeze({show:banter,get seen(){return [...seen]}});
 window.BattlePresentation=Object.freeze({action,banter,cancel,wait,hold,lock,valid,definition,log,get busy(){return active.size>0||locks.size>0},get acceptingInput(){return blockers().length===0},get inputBlockers(){return blockers()},get motionOwned(){return motionOwned},updateRune(value){readout.textContent='RUNE '+value+' / 100'}});
})();
