/* BattleMotion: optional multi-frame playback for battle poses (attack etc.).
 * Battle art today = ONE still PNG per state (BATTLE_ASSETS[actor][state]). This module lets a state carry 2..12 delivered
 * frames WITHOUT touching battle calculation or turn flow: BattleActorState.paint() asks BattleMotion.start(); when no
 * frames are installed for that actor/state it returns null and the still image is used exactly as before.
 *
 * Data: img/battle/motion-manifest.json  (written by tools/battle/install_motion_frames.py; hand-editable)
 *   { "base": "img/battle/characters/",
 *     "motions": { "<actor>[:<variant>]": { "<state>": { "dir":"aidan/motion/", "pattern":"aidan_attack_{n}.png",
 *                    "frames":6, "ms":[80,80,100,100,110,110] | 90, "hitFrame":4, "hold":"last" } } } }
 *   - ms        per-frame display time (array) or one number; total should fit the state's duration budget (installer warns)
 *   - hitFrame  1-based frame on which the impact lands. Emits  'battle-motion-hit'  {actor,state,frame,at}  - presentation
 *               hooks (hit flash, shake, number pop) can bind to it. Damage maths is NOT moved: balance stays as it is.
 *   - hold      'last' (default): stay on the final frame until the state returns to rest.
 *               'hide': after the final frame's ms the sprite is hidden (visibility, !important) and 'battle-motion-end' {actor,state,gone} fires; any later paint/stop restores it (KO dissolve).
 *   - variant   e.g. 'wooden' (少年剣士の木剣): BattleMotion.setVariant('aidan','wooden'); falls back to the base actor's motion.
 * API: load(url) · start(img, actor, state) · stop(img) · has(actor,state) · info(actor,state) · setVariant(actor,v) · onHit(fn) */
(function () {
  'use strict';
  let man = null; const variants = {}, runs = new Map(), hitFns = new Set(), cache = new Map();
  const key = (actor, state) => {
    const m = man && man.motions; if (!m) return null;
    const v = variants[actor];
    if (v && m[actor + ':' + v] && m[actor + ':' + v][state]) return [actor + ':' + v, state];
    return m[actor] && m[actor][state] ? [actor, state] : null;
  };
  const def = (actor, state) => { const k = key(actor, state); return k ? man.motions[k[0]][k[1]] : null; };
  const src = (d, n) => man.base + d.dir + d.pattern.replace('{n}', String(n).padStart(2, '0'));
  const msOf = (d, i) => Array.isArray(d.ms) ? d.ms[i] ?? d.ms[d.ms.length - 1] : d.ms;
  function preload(d) {
    for (let n = 1; n <= d.frames; n++) { const u = src(d, n); if (!cache.has(u)) { const im = new Image(); im.decoding = 'async'; im.src = u; cache.set(u, im); im.decode().catch(() => {}); } }
  }
  async function load(url) {
    try {
      const r = await fetch(url); if (!r.ok) throw new Error(r.status);
      const m = await r.json(); if (!m || typeof m.base !== 'string' || typeof m.motions !== 'object') throw new Error('bad manifest');
      man = m; for (const a of Object.values(m.motions)) for (const d of Object.values(a)) if (d && d.frames > 1) preload(d);
      return true;
    } catch (e) { man = null; return false; }   // no manifest = no motion: stills as before
  }
  // A scaled figure is nudged sideways just enough to stay inside the battle screen (manifest `bbox` = widest horizontal extent over all frames, `aspect` = frame w/h).
  // Pure presentation: `translate` is an independent CSS property, cleared by stop().
  function fit(img, d) {
    try {
      img.style.removeProperty('translate');
      if (!d.bbox || !d.aspect || !img.isConnected) return;
      const W = img.offsetWidth, H = img.offsetHeight; if (!W || !H) return;
      const cw = Math.min(W, H * d.aspect), r = img.getBoundingClientRect(), sx = r.width / W;
      const left = r.left + (W - cw) / 2 * sx; let L = left + d.bbox[0] * cw * sx, R = left + d.bbox[1] * cw * sx;
      const host = img.closest('#raiderBattle, #battle') || document.documentElement, hr = host.getBoundingClientRect();
      const lo = Math.max(0, hr.left) + 2, hi = Math.min(document.documentElement.clientWidth, hr.right) - 2;
      // wider than the screen even when centred on it (portrait phone): shrink the scale just enough, never below the unscaled figure
      const w = R - L, room = hi - lo;
      if (w > room) {
        const k = Math.max(1, d.scale * room / w); img.style.setProperty('--motion-scale', k.toFixed(3));
        const r2 = img.getBoundingClientRect(), sx2 = r2.width / W, l2 = r2.left + (W - cw) / 2 * sx2;
        L = l2 + d.bbox[0] * cw * sx2; R = l2 + d.bbox[1] * cw * sx2;
      }
      let dx = 0; if (R > hi) dx = hi - R; if (L + dx < lo) dx = lo - L;
      if (Math.abs(dx) > 0.5) img.style.setProperty('translate', dx.toFixed(1) + 'px 0');
    } catch (e) {}
  }
  function stop(img) {
    const r = runs.get(img); if (r) { clearTimeout(r.timer); runs.delete(img); }
    if (img && img.dataset && img.dataset.motionScale) { delete img.dataset.motionScale; img.style.removeProperty('--motion-scale'); img.style.removeProperty('translate'); }   // per-state apparent-size match (see start)
    if (img && img.dataset && img.dataset.motionGone) { img.style.removeProperty('visibility'); delete img.dataset.motionGone; }   // hold:'hide' is undone by ANY later paint/start/stop (revive, next battle, scene teardown)
  }
  function start(img, actor, state) {
    stop(img);
    const d = def(actor, state); if (!img || !d || !(d.frames > 1)) return null;
    const run = {i: 0, timer: null, t0: performance.now(), at: 0};
    runs.set(img, run);
    // `scale`: delivered frames are cut on a tighter canvas than the legacy stills, so the figure would look smaller/larger than the still it replaces;
    // a constant CSS scale (bottom-centre anchored, see battle-presentation.css) brings the body back to the still's apparent size. Cleared by stop().
    if (d.scale && d.scale !== 1) { img.dataset.motionScale = String(d.scale); img.style.setProperty('--motion-scale', String(d.scale)); fit(img, d); }
    const show = () => {
      if (runs.get(img) !== run) return;
      const n = run.i + 1; img.src = src(d, n); img.dataset.motionFrame = n;
      if (n === (d.hitFrame || 0)) { const detail = {actor, state, frame: n, at: Math.round(performance.now() - run.t0)}; for (const f of hitFns) { try { f(detail); } catch (e) {} } dispatchEvent(new CustomEvent('battle-motion-hit', {detail})); }
      if (run.i < d.frames - 1) { const wait = msOf(d, run.i); run.i++; run.timer = setTimeout(show, wait); }
      else if (d.hold === 'loop') {   // idle: replays from frame 1 for as long as the run is registered; holds the current frame while a dialogue / cinematic / busy beat is open or the user prefers reduced motion
        const tick = () => {
          if (runs.get(img) !== run) return;
          const b = document.body.classList, hold = b.contains('dialogueOpen') || b.contains('actionCinematic') || b.contains('battlePresentationBusy') || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
          if (hold) { run.timer = setTimeout(tick, 250); return; }
          run.i = 0; show();
        };
        run.timer = setTimeout(tick, msOf(d, run.i));
      }
      else if (d.hold === 'first') { run.timer = setTimeout(() => { if (runs.get(img) === run) { img.src = src(d, 1); runs.delete(img); } }, msOf(d, run.i)); }
      else if (d.hold === 'hide') {   // vanish: after the final frame's time the sprite is hidden (KO dissolve); stays registered so stop()/the next start() restores it
        run.timer = setTimeout(() => {
          if (runs.get(img) !== run) return;
          img.style.setProperty('visibility', 'hidden', 'important'); img.dataset.motionGone = '1'; run.timer = null;
          try { dispatchEvent(new CustomEvent('battle-motion-end', {detail: {actor, state, gone: true, at: Math.round(performance.now() - run.t0)}})); } catch (e) {}
        }, msOf(d, run.i));
      }
      else run.timer = null;
    };
    show(); return run;
  }
  function info(actor, state) {
    const d = def(actor, state); if (!d) return null;
    let total = 0, hitAt = null; for (let i = 0; i < d.frames; i++) { if (d.hitFrame === i + 1) hitAt = total; total += msOf(d, i); }
    return {frames: d.frames, totalMs: total, hitFrame: d.hitFrame || null, hitAtMs: hitAt};
  }
  // Read-only description of a registered motion (the SAME definition start() plays): used by the DEV motion test (arena). No playback side effects.
  function frames(actor, state) {
    const d = def(actor, state); if (!d) return null;
    const urls = [], ms = []; for (let i = 0; i < d.frames; i++) { urls.push(src(d, i + 1)); ms.push(msOf(d, i)); }
    return {urls, ms, hitFrame: d.hitFrame || null, hold: d.hold || 'last', scale: d.scale || 1, bbox: d.bbox || null, aspect: d.aspect || null};
  }
  window.BattleMotion = Object.freeze({load, start, stop, has: (a, s) => Boolean(def(a, s)), info, frames, states: a => (man && man.motions && man.motions[a]) ? Object.keys(man.motions[a]) : [],
    hitDelay(actor, state) { const i = info(actor, state); return i && i.hitAtMs != null ? i.hitAtMs : 0; },   // ms from pose start to the blow: for display-only delays of flash / number pop
    setVariant(actor, v) { if (v) variants[actor] = v; else delete variants[actor]; }, onHit(fn) { hitFns.add(fn); return () => hitFns.delete(fn); },
    get loaded() { return Boolean(man); }});
  if (typeof document !== 'undefined') load(new URL('../img/battle/motion-manifest.json', document.currentScript ? document.currentScript.src : location.href).href);
})();
