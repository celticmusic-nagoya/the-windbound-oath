/* ForestEffects (MOSS-02): draws the `effects` already defined in the Moss Forest map data (light shafts, the A3 wind-seal fx,
 * spring / rune / fairy glows) as culled DOM nodes. Map-independent: it only reads map.effects, a live flag object and the
 * FieldCulling instance of the mounted map, so off-screen effects have no DOM node and their CSS animation stops.
 *  - `when: {flag, is}` shows an effect only while flags[flag] === is (e.g. the seal fx disappears once moss_a3_seal_open).
 *  - Depth: GROUND_DETAIL -> just above the ground chunks (z 1); standing effects (seal fx, fairy glow) sort with actors by
 *    their base y; other FOREGROUND effects (light) sit above actors.
 *  - Art: the delivered seal frames art/fx_seal_01-04.png (manifest base); light / glows are CSS gradients (no image files).
 *  - Assets this renderer does not know (A2 waterfall spray, mist, soft shadow) are skipped exactly as before.
 *  - `blend` (add/screen/multiply) is recorded as data-blend but not applied: CSS blend modes made the whole world re-blend
 *    every frame (+4-7 ms per frame under 4x CPU throttling); plain alpha keeps the cost within noise.
 *  - ?forestFx=0 turns the layer off (comparison / rollback). prefers-reduced-motion keeps static, non-pulsing effects. */
(function () {
  'use strict';
  const SEAL_FRAMES = ['art/fx_seal_01.png', 'art/fx_seal_02.png', 'art/fx_seal_03.png', 'art/fx_seal_04.png'];
  // kind -> appearance. w/h are world px; anchor 'center' or 'bottom' (bottom-centre on x,y); depth 'top' | 'ground' | 'stand'.
  const CATALOG = {
    fx_light_shaft_01: {kind: 'shaft', w: 300, h: 640, tilt: -16, anchor: 'bottom', depth: 'top'},
    fx_light_shaft_02: {kind: 'shaft', w: 220, h: 540, tilt: -14, anchor: 'bottom', depth: 'top'},
    fx_light_shaft_03: {kind: 'shaft', w: 260, h: 580, tilt: -18, anchor: 'bottom', depth: 'top'},
    // The seal frames are a ground rune circle with rising light: stand it on the barrier's base line, just in front of the gate.
    fx_seal_barrier: {kind: 'seal', w: 180, h: 179, anchor: 'bottom', dy: 62, depth: 'stand', frames: SEAL_FRAMES},
    fx_spring_glow: {kind: 'spring', w: 380, h: 220, anchor: 'center', depth: 'ground'},
    fx_rune_glow: {kind: 'rune', w: 150, h: 84, anchor: 'center', depth: 'ground'},
    fx_fairy_glow: {kind: 'fairy', w: 150, h: 150, anchor: 'center', depth: 'stand'}
  };
  let disabled = false;
  try { disabled = /[?&]forestFx=(0|off|false)\b/.test(location.search); } catch (e) {}
  const shown = (e, flags) => !e.when || Boolean(flags && flags[e.when.flag]) === Boolean(e.when.is);
  function create({map, cull, flags, base}) {
    const live = new Map(), stats = {defined: 0, supported: 0, created: 0, skipped: []};
    const list = disabled ? [] : (map.effects || []);
    stats.defined = (map.effects || []).length;
    for (const e of list) {
      const c = CATALOG[e.asset];
      if (!c) { stats.skipped.push(e.asset); continue; }
      stats.supported++;
      const x = e.x - c.w / 2, y = (c.anchor === 'bottom' ? e.y - c.h : e.y - c.h / 2) + (c.dy || 0);
      const z = c.depth === 'ground' ? 1 : c.depth === 'stand' ? Math.round(y + c.h) : 100000;
      cull.add({id: 'fx:' + e.id, x, y, w: c.w, h: c.h, create() {
        const d = document.createElement('div');
        d.className = 'forest-fx forest-fx-' + c.kind; d.dataset.fx = e.id; d.setAttribute('aria-hidden', 'true');
        Object.assign(d.style, {left: x + 'px', top: y + 'px', width: c.w + 'px', height: c.h + 'px', zIndex: String(z)});
        d.style.setProperty('--fx-alpha', String(e.alpha ?? 1));
        const pulse = e.anim && e.anim.pulse;
        if (pulse) { d.style.setProperty('--fx-period', (pulse.period || 8) + 's'); d.style.setProperty('--fx-amp', String(pulse.amp || .05)); d.classList.add('fx-pulse'); }
        if (c.tilt) d.style.setProperty('--fx-tilt', c.tilt + 'deg');
        if (e.blend) d.dataset.blend = e.blend;
        if (c.frames) for (let i = 0; i < c.frames.length; i++) {
          const im = document.createElement('img'); im.src = base + c.frames[i]; im.alt = ''; im.draggable = false; im.decoding = 'async';
          im.style.animationDelay = (-0.18 * (c.frames.length - i)) + 's'; d.append(im);
        }
        d.hidden = !shown(e, flags());
        live.set(e.id, {node: d, def: e}); stats.created++;
        return d;
      }});
    }
    // Re-evaluate `when` after a flag change. A seal fx leaving because the seal opened fades out with the existing 1s opening.
    function refresh(changed) {
      for (const [id, rec] of live) {
        const {node, def} = rec;
        if (!node.isConnected) { live.delete(id); continue; }
        const want = shown(def, flags());
        if (want && node.hidden) { node.classList.remove('fx-ending'); node.hidden = false; }
        else if (!want && !node.hidden && !node.classList.contains('fx-ending')) {
          if (changed && def.when && def.when.flag === changed) { node.classList.add('fx-ending'); setTimeout(() => { if (!shown(def, flags())) node.hidden = true; node.classList.remove('fx-ending'); }, 1000); }
          else node.hidden = true;
        }
      }
    }
    return Object.freeze({refresh, get stats() { return {...stats, live: [...live.values()].filter(r => r.node.isConnected).length}; }});
  }
  window.ForestEffects = Object.freeze({create, CATALOG, SEAL_FRAMES, get disabled() { return disabled; }});
})();
