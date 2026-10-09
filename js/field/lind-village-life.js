/* Small occupation-specific DEV routines. Shared NPC update owns the clock. */
(function () {
  'use strict';
  if(!window.WINDBOUND_DEV)return;
  const routines={
    farmer_male:{kind:'WORKER',speed:3,offsets:[[18,0],[0,0]],rests:[9,13]},
    farmer_female:{kind:'WORKER',speed:2.6,offsets:[[-12,4],[0,0]],rests:[12,17]},
    caretaker:{kind:'WORKER',speed:3.2,offsets:[[0,-12],[0,0]],rests:[11,19]},
    young_man:{kind:'LOCAL_WALKER',speed:5,offsets:[[-18,8],[0,0]],rests:[7,11]},
    young_woman:{kind:'LOCAL_WALKER',speed:4.3,offsets:[[18,8],[0,0]],rests:[10,14]},
    merchant:{kind:'SHOP',speed:2,offsets:[[5,0],[0,0]],rests:[18,27]},
    innkeeper:{kind:'SHOP',speed:2,offsets:[[-5,0],[0,0]],rests:[23,31]},
    elder_man:{kind:'ELDERLY',speed:1.8,offsets:[[4,0],[0,0]],rests:[24,32]},
    elder_woman:{kind:'ELDERLY',speed:1.6,offsets:[[-4,0],[0,0]],rests:[29,38]}
  };
  function attach(a,config,phase=0) {
    a.life={...config,origin:{x:a.x,y:a.footY},index:0,rest:config.rests[0]+phase,
      elapsed:0,blocked:0,arrivals:0};a.element.dataset.routine=config.kind;
  }
  function mount(actors) {actors.forEach((a,i)=>{if(routines[a.id]||a.routine)attach(a,routines[a.id]||a.routine,i*1.7);});}
  function update(seconds) {
    const api=window.LindFieldNPCs;
    api.actors.filter(a=>a.life).forEach(a=>{
      const r=a.life;r.elapsed+=seconds;a.elapsed+=seconds;
      if(a.interactionPause){a.state='IDLE';return;}
      if(r.rest>0){
        r.rest=Math.max(0,r.rest-seconds);a.state=r.kind==='WORKER'?'WORK':'IDLE';
        // A glance at the end of a rest, without oscillating the whole body.
        if(r.rest>0&&r.rest<2)a.direction=r.index%2?-1:1;
        return;
      }
      const offset=r.offsets[r.index],goal={x:r.origin.x+offset[0],y:r.origin.y+offset[1]};
      if(Math.hypot(goal.x-a.x,goal.y-a.footY)<.5){
        r.arrivals++;r.rest=r.rests[r.index];r.index=(r.index+1)%r.offsets.length;
        r.blocked=0;a.state='IDLE';return;
      }
      const moved=api.moveToward(a,goal,r.speed,seconds);a.state=moved?'WALK':'IDLE';
      r.blocked=moved?0:r.blocked+seconds;
      // Occupied space means wait/return, never force a placement through it.
      if(r.blocked>3){r.index=(r.index+1)%r.offsets.length;r.rest=5;r.blocked=0;}
    });
  }
  window.LindVillageLife=Object.freeze({mount,attach,update});
})();
