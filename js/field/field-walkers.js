/* Town walkers: NPC props that patrol a short path with a 6-frame walk cycle (tools/moss/make_npcs.py).
 * Map JSON (optional):  "walkers":[{"id","look","x","y","path":[[dx,dy],...],"speed":26,"rest":[2,4]}]
 *   look  -> manifest node rule npc_slot_<look> with {walk:{file:"...{n}.png",frames:6}}; x,y = feet of the home position.
 * Pure presentation: the interact zone of the NPC stays at its home point. Walkers pause while the player stands close (<56px).
 * API: mount(map, worldEl) · clear() · update(sec) (called by the runtime loop) · get list */
(function () {
  'use strict';
  let list = [], layer = null, last = 0, raf = 0;
  const FPS = 7;
  function rule(look) { const m = window.ForestLoader && ForestLoader.art && ForestLoader.art.manifest; return m && (m.node || []).find(r => new RegExp(r.match).test('npc_slot_' + look)); }
  function mount(map, world) {
    clear();
    const ws = (map && map.walkers) || []; if (!ws.length) return;
    layer = document.createElement('div'); layer.className = 'forest-walkers'; world.appendChild(layer);
    const base = ForestLoader.art.manifest.base || '';
    for (const w of ws) {
      const r = rule(w.look); if (!r || !r.walk) continue;
      const el = document.createElement('img'); el.className = 'forest-walker'; el.draggable = false; el.alt = '';
      Object.assign(el.style, {position: 'absolute', width: r.w + 'px', height: r.h + 'px', pointerEvents: 'none'});
      const frames = [base + r.file]; for (let n = 1; n <= r.walk.frames; n++) { frames.push(base + r.walk.file.replace('{n}', String(n).padStart(2, '0'))); }
      frames.forEach(f => { const i = new Image(); i.src = f; });
      const pts = [[w.x, w.y], ...(w.path || []).map(p => [w.x + p[0], w.y + p[1]])];
      const rec = {id: w.id, look: w.look, el, frames, w: r.w, h: r.h, pts, i: 1, x: w.x, y: w.y, dir: 1, speed: w.speed || 26, rest: w.rest || [2, 4], wait: 1 + Math.random() * 2, clock: 0, state: 'idle', home: [w.x, w.y]};
      layer.appendChild(el); list.push(rec); draw(rec);
    }
    if (list.length) { last = performance.now(); raf = requestAnimationFrame(tick); }
  }
  function draw(r) {
    const walking = r.state === 'walk';
    const src = walking ? r.frames[1 + Math.floor(r.clock * FPS) % (r.frames.length - 1)] : r.frames[0];
    if (r.el.dataset.src !== src) { r.el.dataset.src = src; r.el.src = src; }
    Object.assign(r.el.style, {left: r.x - r.w / 2 + 'px', top: r.y - r.h + 'px', zIndex: String(Math.round(r.y)), transform: r.dir < 0 ? 'scaleX(-1)' : 'none'});
  }
  function update(sec) {
    const me = window.MossForest && MossForest.snapshot ? MossForest.snapshot() : null;
    for (const r of list) {
      if (r.pts.length < 2) continue;
      const near = me && Math.hypot((me.x + 17) - r.x, (me.y + 42) - r.y) < 56;
      if (near) { r.state = 'idle'; draw(r); continue; }
      if (r.wait > 0) { r.wait -= sec; r.state = 'idle'; draw(r); continue; }
      const g = r.pts[r.i], dx = g[0] - r.x, dy = g[1] - r.y, d = Math.hypot(dx, dy), step = Math.min(d, r.speed * sec);
      if (d < .5) { r.i = (r.i + 1) % r.pts.length; r.wait = r.rest[0] + Math.random() * (r.rest[1] - r.rest[0]); r.state = 'idle'; draw(r); continue; }
      r.x += dx / d * step; r.y += dy / d * step; if (Math.abs(dx) > .3) r.dir = dx > 0 ? 1 : -1; r.clock += sec; r.state = 'walk'; draw(r);
    }
  }
  function tick(now) { update(Math.min(.1, (now - last) / 1000)); last = now; raf = requestAnimationFrame(tick); }
  function clear() { cancelAnimationFrame(raf); raf = 0; list = []; if (layer) { layer.remove(); layer = null; } }
  window.FieldWalkers = Object.freeze({mount, clear, update, get list() { return list; }});
})();
