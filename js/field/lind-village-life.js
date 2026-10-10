/* Small occupation-specific DEV routines. Shared NPC update owns the clock. */
(function () {
  'use strict';
  if(!window.WINDBOUND_DEV)return;
  let emmaMode='current';
  const emmaProfiles={
    natural:{kind:'EMMA',speed:1.4,offsets:[[12,-2],[0,0]],rests:[12,20],workDuration:4},
    active:{kind:'EMMA',speed:1.6,offsets:[[18,-2],[0,0]],rests:[8,14],workDuration:5}
  };
  function setEmmaMode(mode){
    if(!['current','natural','active'].includes(mode))return false;
    if(mode===emmaMode)return true;
    emmaMode=mode;
    const a=window.LindFieldNPCs?.actors.find(a=>a.id==='emma');
    if(a?.life){
      // Keep the original home and current logical position. No teleport through obstacles.
      const origin={...a.life.origin};
      attach(a,mode==='current'?a.routine:emmaProfiles[mode]);a.life.origin=origin;
      a.life.index=1;a.state='IDLE';
    }
    return true;
  }
  function attach(a,config,phase=0) {
    a.life={...config,origin:{x:a.x,y:a.footY},index:0,rest:config.rests[0]+phase,
      elapsed:0,blocked:0,arrivals:0,workTime:0};a.element.dataset.routine=config.kind;
  }
  function mount(actors) {actors.forEach((a,i)=>{if(a.routine)attach(a,a.id==='emma'&&emmaMode!=='current'?emmaProfiles[emmaMode]:a.routine,i*1.7);});}   // routines: lind-npc-registry.js
  function update(seconds) {
    const api=window.LindFieldNPCs;
    api.actors.filter(a=>a.life).forEach(a=>{
      const r=a.life;r.elapsed+=seconds;a.elapsed+=seconds;
      if(a.interactionPause){a.state='IDLE';return;}
      if(r.rest>0){
        r.rest=Math.max(0,r.rest-seconds);r.workTime=Math.max(0,r.workTime-seconds);
        a.state=(r.kind==='WORKER'||r.kind==='EMMA'&&r.workDuration)&&r.workTime>0?'WORK':'IDLE';
        // A glance at the end of a rest, without oscillating the whole body.
        if(r.rest>0&&r.rest<2)a.direction=r.index%2?-1:1;
        return;
      }
      const offset=r.offsets[r.index],goal={x:r.origin.x+offset[0],y:r.origin.y+offset[1]};
      if(Math.hypot(goal.x-a.x,goal.y-a.footY)<.5){
        r.arrivals++;r.workTime=r.workDuration||1.4;r.rest=r.rests[r.index];r.index=(r.index+1)%r.offsets.length;
        r.blocked=0;a.state='IDLE';return;
      }
      const moved=api.moveToward(a,goal,r.speed,seconds);a.state=moved?'WALK':'IDLE';
      r.blocked=moved?0:r.blocked+seconds;
      // Occupied space means wait/return, never force a placement through it.
      if(r.blocked>3){r.index=(r.index+1)%r.offsets.length;r.rest=5;r.blocked=0;}
    });
  }
  window.LindVillageLife=Object.freeze({mount,attach,update,setEmmaMode,get emmaMode(){return emmaMode;}});
})();
