/* BattleOpening: the one-shot battle-start pose. Aidan draws his sword ('draw'), Fiona readies her staff ('ready'); both start together,
 * never loop, and hand back to the normal rest pose (Aidan's idle motion / Fiona's still) through BattleActorState's own timers.
 * Input stays locked via BattlePresentation.hold() (the shared presentation lock) until both motions are complete - every frame shown, the
 * last one for its full time and rendered at least once (Issue #50) - and never shorter than the longer motion. It is released by
 * BattlePresentation.cancel() (any new battle / battle end) or by hold()'s safety cap. Presentation only - no battle number, order or UI structure is touched.
 * Failure policy: a missing manifest / frame set, a hidden actor or a thrown error just skips that actor; the lock can never outlive hold()'s cap. */
(() => {
  'use strict';
  const CASTS = [['aidan', 'draw'], ['fiona', 'ready']];
  const played = new Map();                                   // context -> PrologueCombat.generation already opened (no double play per battle start)
  const generation = () => window.PrologueCombat ? PrologueCombat.generation : 0;
  const visible = (context, actor) => {
    const img = document.querySelector(actor === 'aidan' ? (context === 'raider' ? '#rbAidan img' : '#bAidan2 img') : (context === 'raider' ? '#rbFiona img' : '#bFiona2 img'));
    return Boolean(img && img.getClientRects().length);
  };
  function play(context) {
    try {
      if (context !== 'normal' && context !== 'raider') return false;
      const gen = generation();
      if (played.get(context) === gen) return false;
      played.set(context, gen);
      if (!window.BattleMotion || !BattleMotion.loaded || !window.BattleActorState) return false;
      let hold = 0, started = [], finished = [];
      for (const [actor, state] of CASTS) {
        const info = BattleMotion.has(actor, state) && BattleMotion.info(actor, state);
        if (!info || !visible(context, actor)) continue;
        // waitMotion: every frame is shown and the last one for its full time before the rest pose (Issue #50); onDone fires once
        // when the pose has returned to rest - or false if it was cut short (new battle, battle end, KO) - so the lock never waits forever.
        let doneFn = null; const done = new Promise(resolve => { doneFn = resolve; });
        try {
          if (BattleActorState.set(actor, state, { battle: context, duration: info.totalMs, waitMotion: true, onDone: doneFn })) {
            started.push(actor); finished.push(done); hold = Math.max(hold, info.totalMs);
          }
        } catch (e) { }
      }
      if (!started.length) return false;
      // Input stays locked until BOTH motions are complete (never shorter than the longer motion; capped inside hold()).
      if (window.BattlePresentation && BattlePresentation.hold) BattlePresentation.hold(hold, gen, Promise.all(finished)).catch(() => {});
      window.dispatchEvent(new CustomEvent('battle-opening', { detail: { context, actors: started, ms: hold } }));
      return started;
    } catch (e) { return false; }
  }
  window.BattleOpening = Object.freeze({ play, get states() { return CASTS.map(c => c.slice()); } });
})();
