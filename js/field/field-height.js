/* FieldHeight (Phase 1 prototype): height levels for the JSON-map field runtime.
 * Opt-in per map through `map.height`; a map without it never touches this module, so existing maps are unchanged.
 *
 *   map.height = {
 *     levelHeight: 56,                                   // visual rise of one level, px
 *     levels: { "1": { walk: [[x,y,w,h],...] } },       // level>0 may only stand inside these rects (+ connectors that touch the level)
 *     connectors: [{ id, rect:[x,y,w,h], axis:'x'|'y', fromEnd:'min'|'max', from:0, to:1, zone:.22 }],   // stairs / ramps
 *     overpasses: [{ id, level:1, rect:[x,y,w,h], fade:'deck' }],                                            // level-N floors that cover lower ground
 *     visuals: [{ id, kind:'rect'|'poly', rect|pts, color, z, fade?, stripes?, label? }]                      // placeholder art, absolute visual coords
 *   }
 *   map.collision.blockers[].levels = [n,...]            // the blocker only applies at those levels (omitted = every level)
 *
 * Coordinates are the collision "feet basis" used by FieldCollision.compileMap. Functions taking (x,y) use the ACTOR TOP-LEFT,
 * like FieldMovement.advance / blocked(); the feet point is (x+17, y+42) and the foot box is 22x10 (FieldCollision.footprint).
 * A level is runtime state (the actor's), never derived from XY alone: a bridge deck and the path under it share XY.
 */
(function () {
  'use strict';
  const AX = 17, AY = 42, BOX = { x: 6, y: 32, w: 22, h: 10 };
  const inR = (px, py, r) => px >= r[0] && px <= r[0] + r[2] && py >= r[1] && py <= r[1] + r[3];

  function create(spec, solid) {
    const H = spec.levelHeight || 56;
    const walk = new Map(Object.entries(spec.levels || {}).map(([k, v]) => [Number(k), v.walk || []]));
    const conns = (spec.connectors || []).map(c => ({ zone: .22, ...c }));
    const decks = spec.overpasses || [];
    const maxLevel = Math.max(0, ...walk.keys(), ...conns.map(c => Math.max(c.from, c.to)));
    const st = { level: 0, under: null };
    const feet = (x, y) => [x + AX, y + AY];

    // progress 0..1 along a connector from its `from` end to its `to` end
    function progress(c, fx, fy) {
      const [x, y, w, h] = c.rect, a = c.axis === 'x';
      const t = a ? (fx - x) / w : (fy - y) / h;
      return Math.max(0, Math.min(1, c.fromEnd === 'max' ? 1 - t : t));
    }
    function connectorAt(fx, fy) { for (const c of conns) if (inR(fx, fy, c.rect)) return c; return null; }

    // The level the actor stands on after moving to (x,y), given the level it had. Inside a connector's end zones the level is forced.
    function levelAt(x, y, level) {
      const [fx, fy] = feet(x, y), c = connectorAt(fx, fy);
      if (!c) return level;
      const t = progress(c, fx, fy);
      if (t <= c.zone) return c.from;
      if (t >= 1 - c.zone) return c.to;
      return (level === c.from || level === c.to) ? level : c.from;
    }
    // Is the foot box fully on walkable ground of `level`? Level 0 is decided by blockers alone.
    function inWalk(x, y, level) {
      if (level === 0) return true;
      const rs = (walk.get(level) || []).concat(conns.filter(c => c.from === level || c.to === level).map(c => c.rect));
      for (const px of [x + BOX.x, x + BOX.x + BOX.w]) for (const py of [y + BOX.y, y + BOX.y + BOX.h]) {
        if (!rs.some(r => inR(px, py, r))) return false;
      }
      return true;
    }
    // Blocked for an explicit level (the level is NOT re-derived): used for destinations and planner nodes.
    function blockedAtLevel(x, y, level) { return !inWalk(x, y, level) || solid.blocked(x, y, level); }
    // The live predicate every existing caller (movement, navigation, monsters) already uses: the actor's own level, refreshed by connectors.
    function blocked(x, y) { return blockedAtLevel(x, y, levelAt(x, y, st.level)); }

    // Visual lift (px, positive = up) of a sprite standing at (x,y): constant per level, interpolated across a connector.
    function lift(x, y, level) {
      const [fx, fy] = feet(x, y), c = connectorAt(fx, fy);
      if (c && (level === c.from || level === c.to)) { const t = progress(c, fx, fy); return H * (c.from + (c.to - c.from) * t); }
      return H * level;
    }
    // Which overpass (if any) covers the feet of a level-0 actor: it is "under" it and must be drawn beneath its floor.
    function overpassOver(x, y, level) {
      const [fx, fy] = feet(x, y);
      return level < 1 ? decks.find(d => inR(fx, fy, d.rect)) || null : null;
    }
    function commit(x, y) { st.level = levelAt(x, y, st.level); st.under = overpassOver(x, y, st.level); return st.level; }

    // Tapping a point: which level does the player mean? The visible, topmost walkable one - except that a player standing under an
    // overpass keeps their own level for points under that same overpass (the deck is drawn faded there).
    function pickLevel(x, y) {
      const ok = [];
      for (let l = 0; l <= maxLevel; l++) if (!blockedAtLevel(x, y, l)) ok.push(l);
      if (!ok.length) return -1;
      if (st.under && ok.includes(st.level) && overpassOver(x, y, st.level)) return st.level;
      return ok[ok.length - 1];
    }
    // Level reached at the end of a straight segment, following the connector rules; -1 if blocked on the way.
    function segment(a, la, b) {
      const n = Math.max(1, Math.ceil(Math.hypot(b.x - a.x, b.y - a.y) / 2));
      let l = la;
      for (let i = 1; i <= n; i++) {
        const x = a.x + (b.x - a.x) * i / n, y = a.y + (b.y - a.y) * i / n;
        l = levelAt(x, y, l);
        if (blockedAtLevel(x, y, l)) return -1;
      }
      return l;
    }
    // Level-aware A*: nodes are (grid cell, level). Smoothing keeps a vertex only if the same level chain is reproduced.
    function plan(start, goal, opts = {}) {
      const grid = opts.grid || 16, maxNodes = opts.maxNodes || 60000, W = (opts.width || 2400), Hh = (opts.height || 1600);
      const cols = Math.floor(W / grid) + 1, rows = Math.floor(Hh / grid) + 1, L = maxLevel + 1;
      const t0 = performance.now(), la = st.level, lg = goal.level == null ? 0 : goal.level;
      const pt = id => { const c = Math.floor(id / L); return { x: (c % cols) * grid, y: Math.floor(c / cols) * grid, l: id % L }; };
      const idOf = (cx, cy, l) => (cy * cols + cx) * L + l;
      const heur = p => Math.hypot(p.x - goal.x, p.y - goal.y);
      const nodes = new Map(), heap = [];
      const push = n => { heap.push(n); let i = heap.length - 1; while (i) { const p = (i - 1) >> 1; if (heap[p].f <= n.f) break; heap[i] = heap[p]; i = p; } heap[i] = n; };
      const pop = () => { const first = heap[0], last = heap.pop(); if (heap.length) { let i = 0; while (i * 2 + 1 < heap.length) { let c = i * 2 + 1; if (c + 1 < heap.length && heap[c + 1].f < heap[c].f) c++; if (heap[c].f >= last.f) break; heap[i] = heap[c]; i = c; } heap[i] = last; } return first; };
      const direct = segment(start, la, goal);
      if (direct === lg) return { path: [{ x: goal.x, y: goal.y, level: lg }], expanded: 0, ms: performance.now() - t0 };
      const sx = Math.round(start.x / grid), sy = Math.round(start.y / grid);
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const cx = sx + dx, cy = sy + dy; if (cx < 0 || cy < 0 || cx >= cols || cy >= rows) continue;
        const p = { x: cx * grid, y: cy * grid }, l = segment(start, la, p); if (l < 0) continue;
        const id = idOf(cx, cy, l), g = Math.hypot(p.x - start.x, p.y - start.y), n = { id, g, f: g + heur(p), parent: null };
        if (!nodes.has(id) || nodes.get(id).g > g) { nodes.set(id, n); push(n); }
      }
      let found = null, expanded = 0;
      while (heap.length && expanded < maxNodes) {
        const n = pop(); if (nodes.get(n.id) !== n || n.closed) continue; n.closed = true; expanded++;
        const p = pt(n.id);
        if (heur(p) <= grid * 2 && segment(p, p.l, goal) === lg) { found = n; break; }
        const cx = Math.floor(n.id / L) % cols, cy = Math.floor(Math.floor(n.id / L) / cols);
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          if (!dx && !dy) continue; const nx = cx + dx, ny = cy + dy; if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
          const q = { x: nx * grid, y: ny * grid }, l = segment(p, p.l, q); if (l < 0) continue;
          const id = idOf(nx, ny, l), other = nodes.get(id), g = n.g + Math.hypot(dx, dy) * grid;
          if (other && (other.closed || other.g <= g)) continue;
          const nn = { id, g, f: g + heur(q), parent: n }; nodes.set(id, nn); push(nn);
        }
      }
      if (!found) return { path: null, expanded, ms: performance.now() - t0 };
      const raw = [{ x: goal.x, y: goal.y, l: lg }]; for (let n = found; n; n = n.parent) raw.unshift(pt(n.id));
      const out = []; let from = { x: start.x, y: start.y }, fl = la;
      for (let i = 0; i < raw.length;) {
        let j = i; while (j + 1 < raw.length && segment(from, fl, raw[j + 1]) === raw[j + 1].l) j++;
        out.push({ x: raw[j].x, y: raw[j].y, level: raw[j].l }); from = raw[j]; fl = raw[j].l; i = j + 1;
      }
      return { path: out, expanded, ms: performance.now() - t0 };
    }

    // ---- placeholder visuals (absolute visual coordinates, z already decided by the map data) ----
    let nodes = [];
    function mount(world) {
      for (const v of spec.visuals || []) {
        const d = document.createElement('div'); d.className = 'forest-height-piece'; d.dataset.piece = v.id; if (v.fade) d.dataset.fade = v.fade;
        const s = d.style; s.position = 'absolute'; s.pointerEvents = 'none'; s.zIndex = String(v.z); s.background = v.stripes
          ? `repeating-linear-gradient(${v.stripes}deg, ${v.color} 0 10px, rgba(0,0,0,.28) 10px 13px)` : v.color;
        if (v.kind === 'poly') {
          const xs = v.pts.map(p => p[0]), ys = v.pts.map(p => p[1]), x0 = Math.min(...xs), y0 = Math.min(...ys), w = Math.max(...xs) - x0, h = Math.max(...ys) - y0;
          s.left = x0 + 'px'; s.top = y0 + 'px'; s.width = w + 'px'; s.height = h + 'px';
          s.clipPath = 'polygon(' + v.pts.map(p => (p[0] - x0) + 'px ' + (p[1] - y0) + 'px').join(',') + ')';
        } else { const r = v.rect; s.left = r[0] + 'px'; s.top = r[1] + 'px'; s.width = r[2] + 'px'; s.height = r[3] + 'px'; if (v.round) s.borderRadius = v.round; }
        if (v.opacity != null) s.opacity = String(v.opacity);
        if (v.label) { d.textContent = v.label; s.color = '#fff'; s.font = '600 12px sans-serif'; s.textAlign = 'center'; s.display = 'flex'; s.alignItems = 'center'; s.justifyContent = 'center'; }
        world.appendChild(d); nodes.push(d);
      }
    }
    function fade(group, on) { for (const d of nodes) if (d.dataset.fade === group) d.style.opacity = on ? '.42' : (d.dataset.baseOpacity || ''); }
    function destroy() { for (const d of nodes) d.remove(); nodes = []; }
    function setLevel(l) { st.level = Number.isFinite(l) ? l : 0; }
    function serialize(x, y) { return { x: Math.round(x), y: Math.round(y), level: st.level }; }
    // Fallback when a position is saved without a level: the highest level whose walkable ground holds the foot box, preferring ground over an overpass underside.
    function derive(x, y) { for (let l = maxLevel; l >= 0; l--) if (l === 0 ? true : inWalk(x, y, l) && !solid.blocked(x, y, l)) return l; return 0; }
    return { spec, levelHeight: H, maxLevel, get level() { return st.level; }, get under() { return st.under; }, blocked, blockedAtLevel, levelAt, lift, commit, pickLevel, plan, mount, fade, destroy, setLevel, serialize, derive, overpassOver, connectorAt };
  }
  window.FieldHeight = Object.freeze({ create });
})();
