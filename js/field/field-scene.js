/* FieldScene: tiny data-driven scene runner for field cutscenes (see js/field/scene-data.js for the step vocabulary).
 * play(id) -> Promise<boolean>. A scene is atomic: it is not saved mid-way; progress between scenes is storyStage.
 * Depends (at call time) on FieldTalk, MossForest, FieldTimeOfDay. hooks: FieldScene.hook(name, fn). */
(function () {
  'use strict';
  const hooks = new Map(); let running = null;
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const stageOk = (req) => { if (req == null) return true; const s = typeof storyStage === 'number' ? storyStage : 0; return Array.isArray(req) ? s >= req[0] && s <= req[1] : s === req; };
  function talk(id) {
    return new Promise(resolve => {
      const on = e => { if (e.detail && e.detail.id === id) { removeEventListener('field-talk-end', on); resolve(); } };
      addEventListener('field-talk-end', on);
      if (!FieldTalk.talk(id, {source: 'scene'})) { removeEventListener('field-talk-end', on); console.warn('[FieldScene] no conversation', id); resolve(); }
    });
  }
  async function step(s) {
    if ('lock' in s) { MossForest.lock(s.lock); return; }
    if (s.talk) return talk(s.talk);
    if (s.fade) { await MossForest.fade(s.fade.to, s.fade.ms); return; }
    if (s.tod) { FieldTimeOfDay.set(s.tod.set, s.tod); return s.tod.instant ? undefined : wait(s.tod.ms ?? 1600); }
    if (s.vista) { MossForest.vista(s.vista.id, s.vista.on, {ms: s.vista.ms}); return; }
    if (s.approach) { const A = MossForest.actor(s.approach.a), B = MossForest.actor(s.approach.b); return FieldChoreo.approach(A, B, {...s.approach, blocked: MossForest.blocked}); }
    if (s.move) { const A = MossForest.actor(s.move.actor); return FieldChoreo.moveTo(A, s.move, {...s.move, blocked: MossForest.blocked}); }
    if (s.follow) { const A = MossForest.actor(s.follow); A.release && A.release(); return; }   // hand an actor back to the normal follow behaviour
    if (s.focus) { await MossForest.focus(s.focus.x, s.focus.y, s.focus); return; }
    if (s.release) { await MossForest.release(s.release); return; }
    if (s.pan) { MossForest.lock(false); await MossForest.pan(s.pan.x, s.pan.y, s.pan); MossForest.lock(true); return; }
    if (s.shake) { MossForest.shake(s.shake.ms, s.shake.amp); return wait(s.shake.ms * .6); }
    if (s.wait) return wait(s.wait);
    if (s.set) { for (const [k, v] of Object.entries(s.set)) FieldTalk.setFlag(k, v); return; }
    if ('stage' in s) { storyStage = s.stage; return; }
    if (s.call) { const h = hooks.get(s.call); if (h) await h(); else console.warn('[FieldScene] no hook', s.call); }
  }
  async function play(id) {
    const sc = typeof id === 'object' && id ? id : FieldSceneData.scenes[id];   // an inline definition is allowed (tests / dev)
    if (!sc || running || !stageOk(sc.requireStage)) return false;
    running = typeof id === 'string' ? id : '(inline)';
    try { for (const s of sc.steps) await step(s); }
    finally { running = null; }
    return true;
  }
  window.FieldScene = Object.freeze({play, hook: (n, f) => hooks.set(n, f), get running() { return running; }});
})();
