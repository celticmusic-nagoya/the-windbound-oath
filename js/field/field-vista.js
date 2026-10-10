/* FieldVista: world-anchored far-away scenery that is revealed by the story (e.g. the burning village seen from the cliff).
 * Lives in its OWN layer above the time-of-day grade (#forestTod) and mirrors the world transform every frame, so a fire
 * keeps glowing at night instead of being tinted blue by the grade. Pure CSS/DOM (no image assets): when real art exists,
 * a map vista entry may carry {image:'file.png'} to use it instead of the procedural kind.
 * Map data:  "vista":[{"id":"village_fire","kind":"village_fire","x":..,"y":..,"w":..,"h":..,"seed":5}]  (world px, top-left)
 * API: configure(scene) · mount(defs) · clear() · set(id,on,{ms}) · sync(transform) · isOn(id) */
(function () {
  'use strict';
  let layer = null; const nodes = new Map();
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const div = (cls, parent, css) => { const d = document.createElement('div'); d.className = cls; if (css) Object.assign(d.style, css); if (parent) parent.appendChild(d); return d; };
  function villageFire(def) {
    const r = rng(def.seed || 1), root = div('vista-node vista-village-fire', null, {left: def.x + 'px', top: def.y + 'px', width: def.w + 'px', height: def.h + 'px'});
    div('vf-glow', root);
    const n = 8, houses = [];
    for (let i = 0; i < n; i++) {   // loose cluster, back rows smaller
      const row = i % 3, w = 54 - row * 8 + r() * 14, h = 38 - row * 5 + r() * 10;
      const x = 20 + (i / n) * (def.w - 120) + r() * 30, y = def.h * (.38 + row * .17) + r() * 14;
      const hs = div('vf-house', root, {left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px'});
      div('vf-roof', hs, {borderLeftWidth: w * .58 + 'px', borderRightWidth: w * .58 + 'px', borderBottomWidth: h * .6 + 'px', left: -w * .08 + 'px', top: -h * .6 + 'px'});
      div('vf-window', hs, {left: w * .2 + 'px', top: h * .3 + 'px'}); div('vf-window', hs, {left: w * .62 + 'px', top: h * .3 + 'px', animationDelay: r() * 2 + 's'});
      houses.push({x, y, w, h});
    }
    for (const hs of houses) {
      const fl = 2 + (r() * 2 | 0);
      for (let k = 0; k < fl; k++) {
        const fw = 14 + r() * 16, fh = 26 + r() * 40;
        div('vf-flame', root, {left: hs.x + r() * hs.w - fw / 2 + 'px', top: hs.y - fh * .55 + r() * hs.h * .5 + 'px', width: fw + 'px', height: fh + 'px', animationDuration: .5 + r() * .5 + 's', animationDelay: -r() + 's'});
      }
      if (r() < .6) div('vf-smoke', root, {left: hs.x + hs.w * .3 + 'px', top: hs.y - 150 + 'px', animationDuration: 6 + r() * 4 + 's', animationDelay: -r() * 6 + 's'});
    }
    for (let i = 0; i < 16; i++) div('vf-ember', root, {left: 40 + r() * (def.w - 80) + 'px', top: def.h * .4 + r() * 40 + 'px', animationDuration: 2.2 + r() * 2.5 + 's', animationDelay: -r() * 4 + 's'});
    return root;
  }
  const KINDS = {village_fire: villageFire};
  function configure(scene) {
    if (layer && layer.parentNode) layer.remove();
    layer = div('forestVista', null); layer.id = 'forestVista'; layer.setAttribute('aria-hidden', 'true'); scene.appendChild(layer); nodes.clear();
  }
  function mount(defs) {
    clear(); if (!layer) return;
    for (const d of defs || []) {
      const make = KINDS[d.kind]; if (!make || nodes.has(d.id)) continue;
      const n = make(d); n.dataset.vista = d.id; n.style.display = 'none'; layer.appendChild(n); nodes.set(d.id, n);
    }
  }
  function clear() { for (const n of nodes.values()) n.remove(); nodes.clear(); }
  function set(id, on, {ms = 1500} = {}) {
    const n = nodes.get(id); if (!n) return false;
    n.style.transition = 'opacity ' + ms + 'ms ease';
    if (on) { n.style.display = 'block'; void n.offsetWidth; n.style.opacity = '1'; }
    else { n.style.opacity = '0'; setTimeout(() => { if (n.style.opacity === '0') n.style.display = 'none'; }, ms + 30); }
    return true;
  }
  const sync = t => { if (layer) layer.style.transform = t; };
  window.FieldVista = Object.freeze({configure, mount, clear, set, sync, isOn: id => { const n = nodes.get(id); return Boolean(n && n.style.opacity === '1'); }, get ids() { return [...nodes.keys()]; }});
})();
