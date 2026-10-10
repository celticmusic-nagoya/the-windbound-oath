/* Time-of-day mood for field scenes (day / dusk / night). A screen-space overlay on top of the world, so it is
 * independent of map art: colour grade (multiply tint), sun/moon glow, vignette and a starfield.
 * Maps opt in with  "timeOfDay": {"default":"day"}  ; the story or the player switches with set(name,{ms}).
 * Presets: day / dusk / night (cycle()) and ember (post-attack smoke light, set by map data only).
 * Not saved: time of day is derived (story stage / the player's own choice) and never blocks anything.
 * Canopy layers (forest maps opt in with  "timeOfDay":{"default":"day","canopy":true | {beams,dapple,leaves,moss}} , values 0..1 scale each layer):
 *   beams  - light shafts through the canopy      dapple - 木漏れ日, drifting sun spots on the ground
 *   leaves - swaying leaf-shadow silhouettes      moss   - moss mottling creeping in from the screen edges
 * beams/dapple are dimmed by weather (FieldWeather.occlusion: fog/rain hide the sun, so they return when the fog lifts).
 * API: configure(sceneEl) · configureMap(map) · set(name,{ms,instant}) · cycle() · setCanopy(true|obj|false) · setOcclusion(0..1,{ms}) · get current/canopy/occlusion · presets */
(function () {
  'use strict';
  const NAMES = ['day', 'dusk', 'night'];
  // opacity of each overlay layer per preset
  const PRESETS = Object.freeze({
    day:   {tintDusk: 0,   tintNight: 0,   glowDusk: 0,   glowNight: 0,   vignette: 0,   vigColor: '0,0,0',     stars: 0, beams: .6,  dapple: .55, leaves: .4,  moss: .3,  beamColor: '255,246,200'},
    dusk:  {tintDusk: .62, tintNight: 0,   glowDusk: 1,   glowNight: 0,   vignette: .55, vigColor: '70,25,70',   stars: .12, beams: .5, dapple: .3,  leaves: .35, moss: .25, beamColor: '255,170,100'},
    // ember: the burnt village (Rilde Village after the attack): smoky brown-red evening, no sun, heavy vignette. Not part of cycle().
    ember: {tintDusk: .5,  tintNight: .34, glowDusk: 0,   glowNight: 0,   vignette: .7,  vigColor: '48,12,8',  stars: 0, beams: 0, dapple: 0, leaves: .15, moss: .25, beamColor: '255,150,90'},
    night: {tintDusk: 0,   tintNight: .82, glowDusk: 0,   glowNight: 1,   vignette: .6,  vigColor: '4,10,34',    stars: 1, beams: .14, dapple: 0,  leaves: .2,  moss: .3,  beamColor: '150,180,255'}
  });
  const CANOPY_KEYS = ['beams', 'dapple', 'leaves', 'moss'];
  let root = null, cur = 'day', layers = {}, canopy = null, occlusion = 0, occMs = 1600;
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
  // ---- procedural, tileable textures (deterministic; no image files) ----
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function tile(size, seed, draw) {
    const c = document.createElement('canvas'); c.width = c.height = size; const g = c.getContext('2d'), r = rng(seed);
    const items = []; draw(items, r);
    for (const it of items) for (const ox of [-size, 0, size]) for (const oy of [-size, 0, size]) it(g, ox, oy);   // wrap so the tile repeats seamlessly
    return c.toDataURL('image/png');
  }
  function textures() {
    const dapple = tile(384, 11, (items, r) => { for (let i = 0; i < 30; i++) { const x = r() * 384, y = r() * 384, rx = 12 + r() * 30, ry = rx * (.55 + r() * .4), rot = r() * 3.14, a = .35 + r() * .45;
      items.push((g, ox, oy) => { g.save(); g.translate(x + ox, y + oy); g.rotate(rot); g.scale(1, ry / rx); const gr = g.createRadialGradient(0, 0, 0, 0, 0, rx); gr.addColorStop(0, 'rgba(255,250,220,' + a + ')'); gr.addColorStop(.6, 'rgba(255,240,190,' + (a * .5) + ')'); gr.addColorStop(1, 'rgba(255,240,190,0)'); g.fillStyle = gr; g.beginPath(); g.arc(0, 0, rx, 0, 6.2832); g.fill(); g.restore(); }); } });
    const leaves = tile(512, 29, (items, r) => { for (let i = 0; i < 44; i++) { const x = r() * 512, y = r() * 512, L = 22 + r() * 40, W = L * (.3 + r() * .2), rot = r() * 6.28, a = .35 + r() * .35, hue = 95 + r() * 40;
      items.push((g, ox, oy) => { g.save(); g.translate(x + ox, y + oy); g.rotate(rot); g.fillStyle = 'hsla(' + hue + ',45%,12%,' + a + ')'; g.beginPath(); g.moveTo(-L / 2, 0); g.quadraticCurveTo(0, -W, L / 2, 0); g.quadraticCurveTo(0, W, -L / 2, 0); g.fill(); g.restore(); }); } });
    const moss = tile(256, 53, (items, r) => { for (let i = 0; i < 160; i++) { const x = r() * 256, y = r() * 256, rad = 2 + r() * 9, lum = 22 + r() * 22, a = .1 + r() * .3;
      items.push((g, ox, oy) => { g.fillStyle = 'hsla(' + (82 + r() * 30) + ',50%,' + lum + '%,' + a + ')'; g.beginPath(); g.arc(x + ox, y + oy, rad, 0, 6.2832); g.fill(); }); } });
    return {dapple, leaves, moss};
  }
  let tex = null;
  function configure(scene) {
    if (root && root.parentNode) root.remove();
    root = document.createElement('div'); root.id = 'forestTod'; root.setAttribute('aria-hidden', 'true');
    layers = {tintDusk: mk('tod-tint tod-tint-dusk', root), tintNight: mk('tod-tint tod-tint-night', root),
      glowDusk: mk('tod-glow tod-glow-dusk', root), glowNight: mk('tod-glow tod-glow-night', root), vignette: mk('tod-vignette', root)};
    layers.moss = mk('tod-canopy tod-moss', root); layers.leavesB = mk('tod-canopy tod-leaves tod-leaves-b', root); layers.leaves = mk('tod-canopy tod-leaves tod-leaves-a', root);
    layers.dapple = mk('tod-canopy tod-dapple', root); layers.beams = mk('tod-canopy tod-beams', root);
    for (let i = 0; i < 5; i++) { const b = document.createElement('i'); b.style.setProperty('--i', i); layers.beams.appendChild(b); }
    layers.stars = document.createElement('canvas'); layers.stars.className = 'tod-stars'; root.appendChild(layers.stars);
    if (!tex) { try { tex = textures(); } catch (e) { tex = {}; } }
    for (const k of Object.keys(tex)) root.style.setProperty('--tex-' + k, 'url(' + tex[k] + ')');
    scene.appendChild(root); addEventListener('resize', () => { if (cur === 'night') drawStars(layers.stars); });
    apply(cur, true);
  }
  function apply(name, instant, ms) {
    if (!root) return;
    const p = PRESETS[name]; root.style.setProperty('--tod-ms', (instant ? 0 : (ms ?? 1600)) + 'ms');
    if (name === 'night') drawStars(layers.stars);
    for (const [k, v] of Object.entries(p)) if (k !== 'vigColor' && !CANOPY_KEYS.includes(k) && k !== 'beamColor') layers[k].style.opacity = String(v);
    applyCanopy(p);
    layers.vignette.style.background = 'radial-gradient(ellipse at 50% 45%,rgba(' + p.vigColor + ',0) 38%,rgba(' + p.vigColor + ',.85) 100%)';
    root.dataset.tod = name;
  }
  // effective canopy opacity = preset * map scale (0 when the map has none) * weather (beams/dapple only)
  function applyCanopy(p) {
    if (!root) return; p = p || PRESETS[cur];
    const sun = 1 - occlusion;
    for (const k of CANOPY_KEYS) {
      const scale = canopy ? (canopy[k] ?? 1) : 0, w = k === 'beams' ? sun * sun : k === 'dapple' ? sun : 1;
      const o = p[k] * scale * w; layers[k].style.opacity = String(o.toFixed(3)); layers[k].style.visibility = o < .02 ? 'hidden' : '';   // hidden layers cost nothing (fog hides the sun)
    }
    root.style.setProperty('--beam-rgb', p.beamColor);
    layers.beams.style.display = layers.dapple.style.display = layers.leaves.style.display = layers.leavesB.style.display = layers.moss.style.display = canopy ? '' : 'none';
  }
  function setCanopy(v) { canopy = !v ? null : v === true ? {} : {...v}; applyCanopy(); return canopy; }
  function setOcclusion(v, opt = {}) {
    occlusion = Math.max(0, Math.min(1, Number(v) || 0)); occMs = opt.ms ?? 1600;
    if (root) { root.style.setProperty('--tod-ms', (opt.instant ? 0 : occMs) + 'ms'); applyCanopy(); }
    return occlusion;
  }
  function configureMap(map) { const t = map && map.timeOfDay; setCanopy(t && t.canopy); }
  function set(name, opt = {}) {
    if (!PRESETS[name]) return false;
    cur = name; apply(name, Boolean(opt.instant), opt.ms); return true;
  }
  const cycle = opt => { const n = NAMES[(NAMES.indexOf(cur) + 1) % NAMES.length]; set(n, opt); return n; };
  window.FieldTimeOfDay = Object.freeze({configure, configureMap, set, cycle, setCanopy, setOcclusion, names: NAMES, presets: PRESETS, get current() { return cur; }, get canopy() { return canopy; }, get occlusion() { return occlusion; }});
})();
