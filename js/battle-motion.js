// Presentation facade. Combat timing and damage remain owned by the existing engine.
(() => {
  'use strict';
  const actions=Object.freeze(['idle','attack','skill','hit','defend','ko','victory','cast','item','entry']);
  const normalAttack=Object.freeze({expectedFrames:6,impactFrame:3,hitStopCandidateMs:70});
  window.BattleMotion=Object.freeze({
    actions,normalAttack,
    begin:selector=>BattleIdleMotion.begin(selector),
    stop:selector=>BattleIdleMotion.stop(selector),
    onState:(selector,actor,state)=>BattleIdleMotion.onState(selector,actor,state),
    // No speculative URLs or partial playback. A future renderer must explicitly take ownership.
    prepareAttack(frames){
      if(!Array.isArray(frames)||frames.length!==normalAttack.expectedFrames)
        return Object.freeze({ready:false,presentation:'legacy',reason:'missing-or-incomplete'});
      if(!frames.every(image=>image instanceof HTMLImageElement&&image.complete&&image.naturalWidth>0))
        return Object.freeze({ready:false,presentation:'legacy',reason:'not-loaded'});
      return Object.freeze({ready:true,presentation:'legacy',reason:'renderer-not-connected',frames:Object.freeze([...frames]),...normalAttack});
    },
    get status(){return BattleIdleMotion.status;}
  });
})();
