// Awaited presentation boundaries. No timers here consume resources or advance turns.
(() => {
 const durations=Object.freeze({SHORT:550,SPECIAL:1000});
 const definitions=Object.freeze({
  skill:{actor:'aidan',name:'一閃',type:'SHORT',state:'skill'},
  wind:{actor:'aidan',name:'風の一閃',type:'SPECIAL',state:'wind'},
  windbloom:{actor:'fiona',name:'風花の舞',type:'SHORT',state:'skill'},
  prayer:{actor:'fiona',name:'風の祈り',type:'SHORT',state:'prayer'},
  rune:{actor:'fiona',name:'風の祈り',type:'SHORT',state:'prayer'},
  blessing:{actor:'lou',name:'妖精の祝福',type:'SPECIAL',state:'rune'}
 });
 let epoch=0,queue=Promise.resolve(),pending=new Set(),seen=new Set(),motionOwned=false,setting='FULL';
 const active=new Set();
 function valid(token){return token===PrologueCombat.generation;}
 function cancel(){
  epoch++;for(const finish of [...pending])finish(false);pending.clear();active.clear();queue=Promise.resolve();seen.clear();
  document.body.classList.remove('battlePresentationBusy','wbShake','wbHeavyShake');document.querySelector('#wbImpactLayer')?.replaceChildren();document.querySelectorAll('.skillCutin,.battleBanter,.battleWindEffect,.battleDamageNumber').forEach(e=>e.remove());
 }
 function wait(ms,token,node){return new Promise(resolve=>{
  let done=false,timer;const finish=result=>{if(done)return;done=true;clearTimeout(timer);pending.delete(finish);node?.remove();resolve(result&&valid(token));};
  pending.add(finish);timer=setTimeout(()=>finish(true),ms);
 });}
 function run(job,token=PrologueCombat.generation){
  const cycle=epoch;
  const result=queue.then(async()=>{
   if(cycle!==epoch||!valid(token))return false;
   const lock={};active.add(lock);document.body.classList.add('battlePresentationBusy');
   try{return await job(token)}finally{active.delete(lock);if(!active.size)document.body.classList.remove('battlePresentationBusy');}
  });queue=result.catch(()=>false);return result;
 }
 async function showSkillCutin({actor,skill,type='SHORT',image,duration=durations[type]||550},token=PrologueCombat.generation){
  if(setting==='OFF')return valid(token);
  return run(async t=>{
   const el=document.createElement('div');el.className='skillCutin '+(setting==='SHORT'?'SHORT':type);el.dataset.skill=skill;el.dataset.actor=actor;el.style.setProperty('--cutin-duration',duration+'ms');
   const art=document.createElement('img');art.src=image;art.alt=actor+' — '+skill;
   const name=document.createElement('strong');name.textContent=skill;const rune=document.createElement('span');rune.className='cutinRune';rune.textContent='᚛ ᚃ ᚑ ᚐ ᚈ ᚓ ᚜';
   el.append(rune,art,name);document.body.append(el);
   // Keep the display interval after decode; no first-use flash of an empty panel.
   await art.decode().catch(()=>{});if(!valid(t)){el.remove();return false;}
   return wait(setting==='SHORT'?Math.min(duration,550):duration,t,el);
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
  else if(d.actor==='fiona')WBActors[battle==='normal'?'normalFionaMagic':'raiderFionaMagic']();
  windEffect(battle,d.actor);return run(t=>wait(d.actor==='aidan'?380:330,t),token);
 }
 function log(callback,owned){motionOwned=!!owned;try{return callback()}finally{motionOwned=false;}}
 // Presentation consumes keyboard input while visible; DEV buttons remain usable above it.
 addEventListener('keydown',e=>{if(active.size&&['ArrowLeft','ArrowRight','Enter',' ','Escape'].includes(e.key)){e.preventDefault();e.stopImmediatePropagation();}},true);
 const readout=document.createElement('small');readout.id='normalRuneReadout';document.querySelector('#attackBattle').append(readout);
 window.BattleCutinManager=Object.freeze({showSkillCutin,setMode(value){if(!['FULL','SHORT','OFF'].includes(value))return false;setting=value;return true;},get mode(){return setting},durations});
 window.BattleBanter=Object.freeze({show:banter,get seen(){return [...seen]}});
 window.BattlePresentation=Object.freeze({action,banter,cancel,wait,valid,definition,log,get busy(){return active.size>0},get motionOwned(){return motionOwned},updateRune(value){readout.textContent='RUNE '+value+' / 100'}});
})();
