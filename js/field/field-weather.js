/* Weather for field scenes: drifting fog layers + rain particles on a screen-space overlay (#forestWeather, under the time-of-day grade).
 * Not saved: weather is DERIVED from map data + story state, so it can never get stuck.
 * Map data (optional):  "weather":{"default":"fog","rules":[{"when":<TalkConditions condition>,"set":"clear","ms":5000}, ...]}
 *   The LAST rule whose `when` holds wins, else `default`; maps without "weather" are clear. Rules are re-evaluated about once a second
 *   (flags, story stage, seal, quests...), so a quest step lifts the fog on its own: "fog" -> "mist" -> "clear" (the sun beams of
 *   FieldTimeOfDay come back as the fog goes: occlusion = fog * .8 + rain * .5).
 * Presets: clear / mist / fog (thick) / rain / storm / smoke (dark haze + falling ash).   API: configure(sceneEl) · configureMap(map) · set(name,{ms,instant}) (manual, until next
 *   configureMap) · refresh({instant}) · get current / level ({fog,rain}) / presets */
(function () {
  'use strict';
  const PRESETS = Object.freeze({clear: {fog: 0, rain: 0}, mist: {fog: .38, rain: 0}, fog: {fog: .85, rain: 0}, rain: {fog: .25, rain: .75}, storm: {fog: .35, rain: 1}, smoke: {fog: .3, rain: 0, ash: 1}});   // smoke: dark haze + drifting ash and embers (Rilde Village after the attack)
  const MAX_DROPS = 260, reduce = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion:reduce)').matches;
  let fogSmoke = null, root = null, L = {}, cur = 'clear', cfg = null, manual = false, poll = 0, raf = 0, last = 0, drops = [], ctx2d = null;
  const lvl = {fog: 0, rain: 0, ash: 0}, tgt = {fog: 0, rain: 0, ash: 0}, rate = {fog: 0, rain: 0, ash: 0}, MAX_FLAKES = 90; let flakes = [];
  function mk(cls, tag) { const d = document.createElement(tag || 'div'); d.className = cls; root.appendChild(d); return d; }
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  // tileable fractal value noise -> soft white cloud texture
  function fogTexture(size, seed, cells, rgb) {
    rgb = rgb || [232, 240, 238];
    const r = rng(seed), grids = [];
    for (let o = 0; o < 3; o++) { const n = cells << o, g = []; for (let i = 0; i < n * n; i++) g.push(r()); grids.push({n, g}); }
    const c = document.createElement('canvas'); c.width = c.height = size; const g = c.getContext('2d'), im = g.createImageData(size, size);
    const sm = t => t * t * (3 - 2 * t);
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
      let v = 0, amp = .55, tot = 0;
      grids.forEach(({n, g: gr}) => { const fx = x / size * n, fy = y / size * n, x0 = Math.floor(fx) % n, y0 = Math.floor(fy) % n, x1 = (x0 + 1) % n, y1 = (y0 + 1) % n, tx = sm(fx - Math.floor(fx)), ty = sm(fy - Math.floor(fy));
        const a = gr[y0 * n + x0], b = gr[y0 * n + x1], c2 = gr[y1 * n + x0], d = gr[y1 * n + x1]; v += (a + (b - a) * tx + (c2 - a) * ty + (a - b - c2 + d) * tx * ty) * amp; tot += amp; amp *= .5; });
      v = Math.max(0, (v / tot - .32) * 1.9); const i = (y * size + x) * 4; im.data[i] = rgb[0]; im.data[i + 1] = rgb[1]; im.data[i + 2] = rgb[2]; im.data[i + 3] = Math.min(255, v * 255);
    }
    g.putImageData(im, 0, 0); return c.toDataURL('image/png');
  }
  function configure(scene) {
    cancelAnimationFrame(raf); clearInterval(poll);
    if (root && root.parentNode) root.remove();
    root = document.createElement('div'); root.id = 'forestWeather'; root.setAttribute('aria-hidden', 'true');
    L = {fogA: mk('wx-fog wx-fog-a'), fogB: mk('wx-fog wx-fog-b'), dim: mk('wx-dim'), rain: mk('wx-rain', 'canvas')};
    try { root.style.setProperty('--wx-fog-a', 'url(' + fogTexture(256, 7, 4) + ')'); root.style.setProperty('--wx-fog-b', 'url(' + fogTexture(256, 91, 3) + ')'); fogSmoke = {a: 'url(' + fogTexture(256, 7, 4, [58, 50, 50]) + ')', b: 'url(' + fogTexture(256, 91, 3, [74, 62, 58]) + ')', w: {a: 'url(' + fogTexture(256, 7, 4) + ')', b: 'url(' + fogTexture(256, 91, 3) + ')'}}; } catch (e) { /* no canvas: haze only */ }
    scene.insertBefore(root, scene.querySelector('#forestTod') || null);
    ctx2d = L.rain.getContext('2d'); drops = []; flakes = []; lvl.fog = lvl.rain = lvl.ash = tgt.fog = tgt.rain = tgt.ash = 0; paint();
    poll = setInterval(() => { if (cfg && !manual) refresh(); }, 1000);
  }
  function paint() {
    if (!root) return;
    L.fogA.style.opacity = Math.min(1, lvl.fog * 1.05).toFixed(3); L.fogB.style.opacity = Math.min(1, lvl.fog * .8).toFixed(3);
    root.style.setProperty('--wx-fogb', lvl.fog > .5 ? 'block' : 'none');   // the second cloud layer only matters in thick fog (cheaper mist/rain)
    root.style.setProperty('--wx-dim', lvl.rain > .05 || lvl.ash > .05 ? 'block' : 'none');
    L.dim.style.opacity = (lvl.rain * .26 + lvl.fog * .1 + lvl.ash * .3).toFixed(3);
    root.dataset.weather = cur;
    if (window.FieldTimeOfDay) FieldTimeOfDay.setOcclusion(Math.min(1, lvl.fog * .8 + lvl.rain * .5 + lvl.ash * .25), {instant: true});
  }
  function resizeRain() { const w = Math.max(1, root.clientWidth || innerWidth), h = Math.max(1, root.clientHeight || innerHeight); if (L.rain.width !== w || L.rain.height !== h) { L.rain.width = w; L.rain.height = h; } }
  function frame(now) {
    const dt = Math.min(.1, (now - last) / 1000); last = now;
    let moving = false;
    for (const k of ['fog', 'rain', 'ash']) { const d = tgt[k] - lvl[k]; if (Math.abs(d) > 1e-4) { moving = true; const st = rate[k] * dt; lvl[k] = Math.abs(d) <= st ? tgt[k] : lvl[k] + Math.sign(d) * st; } else lvl[k] = tgt[k]; }
    if (moving) paint();
    drawRain(dt);
    if (moving || lvl.rain > 0 || lvl.ash > 0 || drops.length || flakes.length) raf = requestAnimationFrame(frame); else raf = 0;
  }
  function drawRain(dt) {
    resizeRain(); const w = L.rain.width, h = L.rain.height; ctx2d.clearRect(0, 0, w, h);
    const want = reduce ? 0 : Math.round(MAX_DROPS * lvl.rain);
    while (drops.length < want) drops.push({x: Math.random() * (w + 200) - 100, y: Math.random() * -h, v: 640 + Math.random() * 380, len: 14 + Math.random() * 20, a: .4 + Math.random() * .4});
    if (drops.length > want) drops.length = want;
    ctx2d.lineWidth = 1.7; const slant = .22;
    for (const d of drops) {
      d.y += d.v * dt; d.x += d.v * slant * dt;
      if (d.y > h) { d.y = -d.len; d.x = Math.random() * (w + 200) - 100; }
      ctx2d.strokeStyle = 'rgba(205,222,240,' + d.a.toFixed(2) + ')'; ctx2d.beginPath(); ctx2d.moveTo(d.x, d.y); ctx2d.lineTo(d.x - d.len * slant, d.y - d.len); ctx2d.stroke();
    }
    drawAsh(dt, w, h);
  }
  // ash flakes (dark, slow, swaying) and a few rising/falling embers
  function drawAsh(dt, w, h) {
    const want = reduce ? 0 : Math.round(MAX_FLAKES * lvl.ash);
    while (flakes.length < want) flakes.push({x: Math.random() * w, y: Math.random() * h, v: 22 + Math.random() * 44, r: .8 + Math.random() * 1.9, ph: Math.random() * 6.28, ember: Math.random() < .22});
    if (flakes.length > want) flakes.length = want;
    for (const f of flakes) {
      f.y += f.v * dt; f.ph += dt * 1.4; f.x += Math.sin(f.ph) * 18 * dt + 10 * dt;
      if (f.y > h + 4) { f.y = -4; f.x = Math.random() * w; } if (f.x > w + 4) f.x = -4;
      ctx2d.fillStyle = f.ember ? 'rgba(255,150,60,.85)' : 'rgba(34,28,28,.6)'; ctx2d.beginPath(); ctx2d.arc(f.x, f.y, f.ember ? f.r * .8 : f.r, 0, 6.2832); ctx2d.fill();
    }
  }
  function apply(name, opt = {}) {
    const p = PRESETS[name]; if (!p || !root) return false;
    cur = name; const ms = opt.instant ? 0 : (opt.ms ?? 3000);
    for (const k of ['fog', 'rain', 'ash']) { const v = p[k] || 0; tgt[k] = v; rate[k] = ms ? Math.abs(v - lvl[k]) / (ms / 1000) : 1e9; }
    if (fogSmoke) { const f = name === 'smoke' ? fogSmoke : fogSmoke.w; root.style.setProperty('--wx-fog-a', f.a); root.style.setProperty('--wx-fog-b', f.b); }
    last = performance.now(); if (!raf) raf = requestAnimationFrame(frame);
    if (opt.instant) { lvl.fog = tgt.fog; lvl.rain = tgt.rain; lvl.ash = tgt.ash; paint(); }
    root.dataset.weather = name;
    window.dispatchEvent(new CustomEvent('field-weather', {detail: {name, instant: Boolean(opt.instant)}}));
    return true;
  }
  function stateCtx() {
    return {flag: n => Boolean(window.FieldTalk && FieldTalk.flag(n)) || Boolean(window.MossForestStory && MossForestStory.flagsNow && MossForestStory.flagsNow()[n]),
      stage: () => (typeof storyStage === 'number' ? storyStage : 0), sealOpen: () => Boolean(window.PrologueProgress && PrologueProgress.count() >= 3),
      treasure: id => Boolean(window.MossForest && MossForest.opened && MossForest.opened.includes(id)), item: id => (window.Inventory ? Inventory.count(id) : 0),
      talked: id => Boolean(window.FieldTalk && FieldTalk.seenEntry && FieldTalk.seenEntry(id)), quest: id => (window.Quest ? Quest.state(id) : null)};
  }
  function evaluate() {
    if (!cfg) return 'clear'; let name = cfg.default || 'clear', ms;
    const c = stateCtx(); for (const r of cfg.rules || []) if (window.TalkConditions && TalkConditions.test(r.when, c)) { name = r.set; ms = r.ms; }
    return {name, ms};
  }
  function refresh(opt = {}) {
    if (!root) return cur; const e = cfg ? evaluate() : {name: 'clear'};
    if (e.name !== cur) apply(e.name, {instant: opt.instant, ms: e.ms ?? cfg?.ms ?? 5000}); return cur;
  }
  function configureMap(map) {
    cfg = map && map.weather ? map.weather : null; manual = false;
    const e = cfg ? evaluate() : {name: 'clear'}; apply(PRESETS[e.name] ? e.name : 'clear', {instant: true});
  }
  function set(name, opt = {}) { manual = true; return apply(name, opt); }
  window.FieldWeather = Object.freeze({configure, configureMap, set, refresh, presets: PRESETS, get current() { return cur; }, get level() { return {...lvl}; }, get target() { return {...tgt}; }});
})();
