/* FieldScene: tiny data-driven scene runner for field cutscenes (see js/field/scene-data.js for the step vocabulary).
 * play(id) -> Promise<boolean>. A scene is atomic: it is not saved mid-way; progress between scenes is storyStage.
 * Depends (at call time) on FieldTalk, MossForest, FieldTimeOfDay. hooks: FieldScene.hook(name, fn). */
(function () {
  'use strict';
  const hooks = new Map(); let running = null;
  const valid=r=>r===running&&!r.cancelled&&(r.generation===undefined||window.LoadCoordinator.current(r.generation))&&r.map===MossForest.enterCount;
  const wait = (ms,r) => new Promise(resolve=>{const stop=()=>{clearTimeout(timer);r.cleanups.delete(stop);resolve();};const timer=setTimeout(stop,ms);r.cleanups.add(stop);});
  function cancel(){
    const r=running;if(!r)return Promise.resolve();const talkId=r.talk;r.cancelled=true;running=null;MossForest.lock(false);
    for(const stop of [...r.cleanups])stop();
    if(talkId)window.FieldTalk?.cancel(talkId);
    window.FieldChoreo?.cancelAll();r.abort();return r.done;
  }
  const stageOk = (req) => { if (req == null) return true; const s = typeof storyStage === 'number' ? storyStage : 0; return Array.isArray(req) ? s >= req[0] && s <= req[1] : s === req; };
  function talk(id,r) {
    r.talk=id;
    return new Promise(resolve => {
      const stop=()=>{removeEventListener('field-talk-end',on);r.cleanups.delete(stop);r.talk=null;resolve();};
      const on = e => { if (e.detail && e.detail.id === id) stop(); };
      r.cleanups.add(stop);
      addEventListener('field-talk-end', on);
      if (!FieldTalk.talk(id, {source: 'scene'})) { stop(); console.warn('[FieldScene] no conversation', id); resolve(); }
    });
  }
  async function step(s,r) {
    if ('lock' in s) { MossForest.lock(s.lock); return; }
    if (s.talk) return talk(s.talk,r);
    if (s.fade) { await MossForest.fade(s.fade.to, s.fade.ms); return; }
    if (s.tod) { FieldTimeOfDay.set(s.tod.set, s.tod); return s.tod.instant ? undefined : wait(s.tod.ms ?? 1600,r); }
    if (s.vista) { MossForest.vista(s.vista.id, s.vista.on, {ms: s.vista.ms}); return; }
    if (s.approach) { const A = MossForest.actor(s.approach.a), B = MossForest.actor(s.approach.b); return FieldChoreo.approach(A, B, {...s.approach, blocked: MossForest.blocked}); }
    if (s.move) { const A = MossForest.actor(s.move.actor); return FieldChoreo.moveTo(A, s.move, {...s.move, blocked: MossForest.blocked}); }
    if (s.follow) { const A = MossForest.actor(s.follow); A.release && A.release(); return; }   // hand an actor back to the normal follow behaviour
    if (s.focus) { await MossForest.focus(s.focus.x, s.focus.y, s.focus); return; }
    if (s.release) { await MossForest.release(s.release); return; }
    if (s.pan) { MossForest.lock(false); await MossForest.pan(s.pan.x, s.pan.y, s.pan); if(valid(r))MossForest.lock(true); return; }
    if (s.shake) { MossForest.shake(s.shake.ms, s.shake.amp); return wait(s.shake.ms * .6,r); }
    if (s.wait) return wait(s.wait,r);
    if (s.set) { for (const [k, v] of Object.entries(s.set)) FieldTalk.setFlag(k, v); return; }
    if ('stage' in s) { storyStage = s.stage; return; }
    if (s.call) { const h = hooks.get(s.call); if (h) await h(); else console.warn('[FieldScene] no hook', s.call); }
  }
  async function play(id) {
    const sc = typeof id === 'object' && id ? id : FieldSceneData.scenes[id];   // an inline definition is allowed (tests / dev)
    if (!sc || running || !stageOk(sc.requireStage)) return false;
    const r={id:typeof id==='string'?id:'(inline)',generation:window.LoadCoordinator?.generation,map:MossForest.enterCount,cancelled:false,cleanups:new Set()};
    r.cancelledPromise=new Promise(resolve=>r.abort=resolve);r.done=new Promise(resolve=>r.finish=resolve);running=r;
    try { for (const s of sc.steps) {if(!valid(r))return false;await Promise.race([step(s,r),r.cancelledPromise]);if(!valid(r))return false;}return true; }
    finally {for(const stop of [...r.cleanups])stop();if(running===r)running=null;r.finish();}

  }
  window.FieldScene = Object.freeze({play, cancel, hook: (n, f) => hooks.set(n, f), get running() { return running?.id||null; }});
})();
