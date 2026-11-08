/* FIELD-VISUAL-OVERHAUL-03: deterministic presentation-only sprite motion.
 * No DOM, timers, movement/collision, SAVE or production sprite registration. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.FieldSpriteMotion = api;
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';
  const TAU = Math.PI * 2;
  const finite = (n, fallback) => typeof n === 'number' && Number.isFinite(n) ? n : fallback;
  const profiles = Object.freeze({
    player: Object.freeze({frequency: 2.4, bounce: 3, sway: 1, pulse: 0}),
    companion: Object.freeze({frequency: 2.2, bounce: 2.5, sway: 1.2, pulse: 0}),
    npc: Object.freeze({frequency: 1.8, bounce: 2, sway: .7, pulse: 0}),
    enemy: Object.freeze({frequency: 1.5, bounce: 1.4, sway: 1, pulse: .035}),
    fairy: Object.freeze({frequency: 1.6, bounce: 4, sway: 1.5, pulse: .015})
  });
  const still = () => ({x: 0, y: 0, sway: 0, scale: 1});
  function sample(options) {
    const o = options && typeof options === 'object' ? options : {};
    if (o.reducedMotion) return still();
    const kind = Object.prototype.hasOwnProperty.call(profiles, o.kind) ? o.kind : 'npc';
    const p = profiles[kind];
    const moving = o.moving === true;
    // time is in seconds, phase in cycles; all effects are visual only.
    const time = finite(o.time, 0);
    const phase = finite(o.phase, 0);
    const angle = TAU * (time * p.frequency + phase);
    const airborne = kind === 'fairy';
    const bounce = moving || airborne ? p.bounce * (airborne ? Math.sin(angle) : Math.max(0, Math.sin(angle))) : 0;
    const sway = moving || airborne ? p.sway * Math.sin(angle - TAU / 4) : 0;
    const pulse = kind === 'enemy' || kind === 'fairy' ? p.pulse * Math.sin(angle) : 0;
    return {x: 0, y: -bounce, sway, scale: 1 + pulse};
  }
  return Object.freeze({profiles, sample});
});
