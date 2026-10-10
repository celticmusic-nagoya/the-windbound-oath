/* Time-of-day mood for field scenes (day / dusk / night). A screen-space overlay on top of the world, so it is
 * independent of map art: colour grade (multiply tint), sun/moon glow, vignette and a starfield.
 * Maps opt in with  "timeOfDay": {"default":"day"}  ; the story or the player switches with set(name,{ms}).
 * Not saved: time of day is derived (story stage / the player's own choice) and never blocks anything.
 * API: configure(sceneEl) · set(name,{ms,instant}) · cycle() · get current · presets */
(function () {
  'use strict';
  const NAMES = ['day', 'dusk', 'night'];
  // opacity of each overlay layer per preset
  const PRESETS = Object.freeze({
    day:   {tintDusk: 0,   tintNight: 0,   glowDusk: 0,   glowNight: 0,   vignette: 0,   vigColor: '0,0,0',     stars: 0},
    dusk:  {tintDusk: .62, tintNight: 0,   glowDusk: 1,   glowNight: 0,   vignette: .55, vigColor: '70,25,70',   stars: .12},
    night: {tintDusk: 0,   tintNight: .82, glowDusk: 0,   glowNight: 1,   vignette: .6,  vigColor: '4,10,34',    stars: 1}
  });
  let root = null, cur = 'day', layers = {};
  function mk(cls, parent) { const d = document.createElement('div'); d.className = cls; parent.appendChild(d); return d; }
  function drawStars(canvas) {
    const w = canvas.width = Math.max(1, canvas.clientWidth || innerWidth), h = canvas.height = Math.max(1, canvas.clientHeight || innerHeight);
    const ctx = canvas.getContext('2d'); ctx.clearRect(0, 0, w, h);
    let a = 20261010; const rnd = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    for (let i = 0; i < 170; i++) {
      const x = rnd() * w, y = rnd() * h * .92, r = .5 + rnd() * rnd() * 1.9, al = .35 + rnd() * .65;
      ctx.fillStyle = 'rgba(' + (225 + (rnd() * 30 | 0)) + ',' + (230 + (rnd() * 25 | 0)) + ',255,' + al.toFixed(2) + ')';
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill();
    }
  }
  function configure(scene) {
    if (root && root.parentNode) root.remove();
    root = document.createElement('div'); root.id = 'forestTod'; root.setAttribute('aria-hidden', 'true');
    layers = {tintDusk: mk('tod-tint tod-tint-dusk', root), tintNight: mk('tod-tint tod-tint-night', root),
      glowDusk: mk('tod-glow tod-glow-dusk', root), glowNight: mk('tod-glow tod-glow-night', root), vignette: mk('tod-vignette', root)};
    layers.stars = document.createElement('canvas'); layers.stars.className = 'tod-stars'; root.appendChild(layers.stars);
    scene.appendChild(root); addEventListener('resize', () => { if (cur === 'night') drawStars(layers.stars); });
    apply(cur, true);
  }
  function apply(name, instant, ms) {
    if (!root) return;
    const p = PRESETS[name]; root.style.setProperty('--tod-ms', (instant ? 0 : (ms ?? 1600)) + 'ms');
    if (name === 'night') drawStars(layers.stars);
    for (const [k, v] of Object.entries(p)) if (k !== 'vigColor') layers[k].style.opacity = String(v);
    layers.vignette.style.background = 'radial-gradient(ellipse at 50% 45%,rgba(' + p.vigColor + ',0) 38%,rgba(' + p.vigColor + ',.85) 100%)';
    root.dataset.tod = name;
  }
  function set(name, opt = {}) {
    if (!PRESETS[name]) return false;
    cur = name; apply(name, Boolean(opt.instant), opt.ms); return true;
  }
  const cycle = opt => { const n = NAMES[(NAMES.indexOf(cur) + 1) % NAMES.length]; set(n, opt); return n; };
  window.FieldTimeOfDay = Object.freeze({configure, set, cycle, names: NAMES, presets: PRESETS, get current() { return cur; }});
})();
