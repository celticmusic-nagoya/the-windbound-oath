/* BattleOpening: the one-shot battle-start pose. Aidan draws his sword ('draw'), Fiona readies her staff ('ready'); both start together,
 * never loop, and hand back to the normal rest pose (Aidan's idle motion / Fiona's still) through BattleActorState's own timers.
 * Input stays locked for the longer of the two motions via BattlePresentation.hold() (the shared presentation lock: released by its timer,
 * by BattlePresentation.cancel() and therefore by any new battle / battle end). Presentation only - no battle number, order or UI structure is touched.
 * Failure policy: a missing manifest / frame set, a hidden actor or a thrown error just skips that actor; the lock can never outlive its timer. */
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
      let hold = 0, started = [];
      for (const [actor, state] of CASTS) {
        const info = BattleMotion.has(actor, state) && BattleMotion.info(actor, state);
        if (!info || !visible(context, actor)) continue;
        try { if (BattleActorState.set(actor, state, { battle: context, duration: info.totalMs })) { started.push(actor); hold = Math.max(hold, info.totalMs); } } catch (e) { }
      }
      if (!started.length) return false;
      if (window.BattlePresentation && BattlePresentation.hold) BattlePresentation.hold(hold, gen).catch(() => {});
      window.dispatchEvent(new CustomEvent('battle-opening', { detail: { context, actors: started, ms: hold } }));
      return started;
    } catch (e) { return false; }
  }
  window.BattleOpening = Object.freeze({ play, get states() { return CASTS.map(c => c.slice()); } });
})();
