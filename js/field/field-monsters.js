/* Field monsters: enemies that actually live on the map (symbol encounters).  Replaces "walk N steps -> random fight" in normal exploration:
 *   see the enemy -> avoid / approach -> it notices you -> touch -> the existing battle.
 *
 * Map JSON (optional, any map):  "monsters":[{"id":"a1_slime_hollow","type":"moss_slime","x":1320,"y":3420}]      x,y = feet of the home position
 *   optional per-monster overrides of any MONSTER_TYPES field (e.g. "detect":300), and "group":1 (enemies in the battle it starts).
 *
 * One shared update loop (the runtime tick calls update(sec)); no per-monster rAF / timers.  Monsters far from the player are not simulated.
 * Movement reuses the map collision (ctx.blocked) and FieldMovement.advance; contact is measured foot-to-foot.  The battle itself is started by
 * the runtime (ctx.engage -> hooks.onMonster -> startAttackBattle), so there is no second battle pipeline.
 *
 * States:  wander (idle/patrol around home) -> alert (short reaction) -> chase -> return (back home) -> wander
 *          engage (touched: ~0.25s reaction, then the battle) -> engaged (battle running; resolve(won) afterwards) -> gone
 *
 * All behaviour numbers live in MONSTER_TYPES below; the AI code has no tuning constants of its own.
 * Adding a type later (boar: straight charge, flyer: ignores some terrain, big: guards a territory) = a new row + an optional `movement` branch.
 * Units: px and px/s of map space.  The player's pointer-walk is ~300 px/s, so speed 45 = very slow, 150 = half the player's pace.
 */
(function () {
  'use strict';
  const MONSTER_TYPES = Object.freeze({
    // Weak, slow, easy to avoid: slow to notice, short chase, gives up quickly.  "A creature that wanders over because it is curious."
    moss_slime: Object.freeze({
      name: 'モススライム', movement: 'wander',
      speed: 45,          // chase speed
      wanderSpeed: 28,    // idle drifting
      returnSpeed: 45,    // walking back home after giving up
      detect: 260,        // notices the player inside this distance (feet to feet)
      chaseMax: 200,      // gives up after following this far from where the chase began
      touch: 44,          // contact radius (feet to feet)
      leash: 360,         // never farther than this from home
      lose: 420,          // player farther than this -> chase ends
      wanderRadius: 90, rest: [1.5, 3.5],
      alertTime: .55, engageDelay: .28, reaggro: 2.5, hop: 10,
      respawn: 'reenter', battle: 'moss_slime',
      art: Object.freeze({dir: 'img/field/monsters/moss_slime/', file: 'moss_slime_walk_{n}.png', frames: 6, w: 260, h: 200, feet: 6, scale: .5, fps: 6, faces: 1})
    }),
    // Vampiric flyer (battle: drains HP).  Hovers and keeps flapping; quicker than the slime, jumpier, and it tires of the chase sooner than a goblin.
    // movement 'flyer' currently only changes the drawing (hover + constant flap); it still respects the map collision.
    forest_bat: Object.freeze({
      name: 'フォレストバット', movement: 'flyer',
      speed: 120, wanderSpeed: 55, returnSpeed: 100, detect: 340, chaseMax: 520, touch: 50, leash: 700, lose: 560,
      wanderRadius: 140, rest: [.6, 1.6],
      alertTime: .35, engageDelay: .25, reaggro: 2, hop: 8,
      respawn: 'reenter', battle: 'forest_bat',
      art: Object.freeze({dir: 'img/field/monsters/forest_bat/', file: 'forest_bat_idle_{n}.png', frames: 4, w: 320, h: 214, feet: 0, scale: .5, fps: 9, faces: 1, always: true, air: 34})
    }),
    // Hostile and quick: notices from farther away, reacts faster, chases farther - but slower than the player, so distance / terrain shakes it off.
    goblin: Object.freeze({
      name: 'ゴブリン', movement: 'patrol',
      speed: 150, wanderSpeed: 60, returnSpeed: 110, detect: 420, chaseMax: 700, touch: 56, leash: 900, lose: 640,
      wanderRadius: 160, rest: [1, 2.5],
      alertTime: .3, engageDelay: .25, reaggro: 2, hop: 6,
      respawn: 'reenter', battle: 'goblin',
      art: null   // no field art yet -> the generic symbol placeholder is drawn
    })
  });
  const ACTIVE_RANGE = 1600;   // monsters farther than this from the player are not simulated
  const STUCK_SECONDS = 1.2;   // a chaser that cannot make progress this long gives up
  const HOME_ARRIVE = 8;

  let list = [], layer = null, ctx = null, clock = 0;

  function typeOf(def) { return Object.freeze({...(MONSTER_TYPES[def.type] || {}), ...def.tune}); }
  function mount(map, world, context) {
    clear();
    const defs = (map && map.monsters) || [];
    ctx = context || null;
    if (!defs.length || !ctx) return;
    layer = document.createElement('div'); layer.className = 'forest-monsters'; world.appendChild(layer);
    for (const d of defs) {
      if (!MONSTER_TYPES[d.type] || (ctx.slain && ctx.slain.has(d.id))) continue;
      const t = typeOf(d);
      const rec = {id: d.id, type: d.type, t, group: d.group || 1, x: d.x, y: d.y, home: [d.x, d.y], state: 'wander', sub: 'rest', wait: 1 + Math.random() * 2,
        goal: null, dir: 1, clock: Math.random() * 3, timer: 0, noAggro: 0, chaseFrom: null, stuck: 0, el: null, frames: null, shown: ''};
      rec.el = makeEl(rec); layer.appendChild(rec.el); list.push(rec); draw(rec, true);
    }
  }
  function makeEl(m) {
    const a = m.t.art;
    if (!a) { const d = document.createElement('div'); d.className = 'forest-symbol forest-monster ph'; d.textContent = m.t.name; Object.assign(d.style, {position: 'absolute', width: '48px', height: '62px', pointerEvents: 'none'}); return d; }
    m.frames = []; for (let n = 1; n <= a.frames; n++) { const f = a.dir + a.file.replace('{n}', String(n).padStart(2, '0')); m.frames.push(f); const i = new Image(); i.src = f; }
    const e = document.createElement('img'); e.className = 'forest-monster'; e.draggable = false; e.alt = '';
    Object.assign(e.style, {position: 'absolute', width: a.w * a.scale + 'px', height: a.h * a.scale + 'px', pointerEvents: 'none'});
    return e;
  }
  function draw(m, force) {
    const a = m.t.art, w = a ? a.w * a.scale : 48, h = a ? a.h * a.scale : 62, pad = a ? a.feet * a.scale : 0;
    let src = '';
    if (a) {
      const moving = m.moving && m.state !== 'engaged';
      src = moving ? m.frames[Math.floor(m.clock * a.fps) % a.frames] : m.frames[0];
      if (m.el.dataset.src !== src) { m.el.dataset.src = src; m.el.src = src; }
    }
    const lift = a && a.air ? a.air + Math.sin(m.clock * 3) * 4 : 0;   // flyers hover above their ground point
    const hop = m.hopT > 0 ? -Math.abs(Math.sin(m.hopT * Math.PI)) * m.t.hop : 0;
    const flip = (a ? a.faces : 1) * m.dir < 0 ? -1 : 1;
    const sig = Math.round(m.x) + ',' + Math.round(m.y) + ',' + Math.round(lift) + ',' + Math.round(hop * 2) + ',' + flip + ',' + src;
    if (!force && sig === m.shown) return; m.shown = sig;
    const s = m.el.style;
    s.left = Math.round(m.x - w / 2) + 'px'; s.top = Math.round(m.y - h + pad - lift) + 'px'; s.zIndex = String(Math.round(m.y));
    s.transform = 'translateY(' + hop.toFixed(1) + 'px)' + (flip < 0 ? ' scaleX(-1)' : '');
  }
  function face(m, tx) { if (Math.abs(tx - m.x) > .5) m.dir = tx > m.x ? 1 : -1; }
  // One movement step toward (gx,gy) through the real collision; returns the distance actually travelled.
  function moveToward(m, gx, gy, speed, sec) {
    const dx = gx - m.x, dy = gy - m.y, d = Math.hypot(dx, dy); if (d < .5) return 0;
    const step = Math.min(d, speed * sec), ax = m.x - ctx.foot.ax, ay = m.y - ctx.foot.ay;
    const r = ctx.advance(ax, ay, dx / d * step, dy / d * step);
    const nx = r.x + ctx.foot.ax, ny = r.y + ctx.foot.ay, moved = Math.hypot(nx - m.x, ny - m.y);
    m.x = nx; m.y = ny; face(m, gx); m.clock += sec; return moved;
  }
  function pickWanderGoal(m) {
    for (let i = 0; i < 8; i++) {
      const a = Math.random() * Math.PI * 2, r = (.3 + Math.random() * .7) * m.t.wanderRadius, x = m.home[0] + Math.cos(a) * r, y = m.home[1] + Math.sin(a) * r;
      if (!ctx.blocked(x - ctx.foot.ax, y - ctx.foot.ay)) return [x, y];
    }
    return null;
  }
  function setState(m, s) { m.state = s; m.timer = 0; m.stuck = 0; m.moving = false; }

  function think(m, sec, P, dP, now) {
    const t = m.t, st = m.state;
    if (m.hopT > 0) m.hopT = Math.max(0, m.hopT - sec / .45);
    // contact (feet to feet) from any active state
    if (st !== 'engage' && st !== 'engaged' && dP <= t.touch && ctx.canEngage()) { setState(m, 'engage'); m.hopT = 1; face(m, P.x); return; }
    if (st === 'wander') {
      m.moving = false;
      if (dP <= t.detect && now >= m.noAggro && ctx.canEngage()) { setState(m, 'alert'); m.hopT = 1; face(m, P.x); return; }
      if (m.sub === 'rest') { m.wait -= sec; if (m.wait <= 0) { m.goal = pickWanderGoal(m); m.sub = m.goal ? 'walk' : 'rest'; m.wait = t.rest[0] + Math.random() * (t.rest[1] - t.rest[0]); } return; }
      const mv = moveToward(m, m.goal[0], m.goal[1], t.wanderSpeed, sec); m.moving = mv > 0;
      if (mv < .05 || Math.hypot(m.goal[0] - m.x, m.goal[1] - m.y) < 2) { m.sub = 'rest'; m.moving = false; }
    } else if (st === 'alert') {
      m.moving = false; face(m, P.x); m.timer += sec;
      if (m.timer >= t.alertTime) { if (dP <= t.detect * 1.3) { setState(m, 'chase'); m.chaseFrom = [m.x, m.y]; } else { setState(m, 'wander'); m.sub = 'rest'; } }
    } else if (st === 'chase') {
      const mv = moveToward(m, P.x, P.y, t.speed, sec); m.moving = mv > 0;
      m.stuck = mv < t.speed * sec * .25 ? m.stuck + sec : 0;
      const far = Math.hypot(m.x - m.chaseFrom[0], m.y - m.chaseFrom[1]) > t.chaseMax || Math.hypot(m.x - m.home[0], m.y - m.home[1]) > t.leash || dP > t.lose;
      if (far || m.stuck > STUCK_SECONDS) { setState(m, 'return'); m.noAggro = now + t.reaggro * 1000; }
    } else if (st === 'return') {
      const mv = moveToward(m, m.home[0], m.home[1], t.returnSpeed, sec); m.moving = mv > 0;
      m.stuck = mv < .05 ? m.stuck + sec : 0;
      if (Math.hypot(m.home[0] - m.x, m.home[1] - m.y) <= HOME_ARRIVE) { setState(m, 'wander'); m.sub = 'rest'; m.wait = 1; }
      else if (m.stuck > STUCK_SECONDS * 2.5) { m.x = m.home[0]; m.y = m.home[1]; setState(m, 'wander'); m.sub = 'rest'; }
    } else if (st === 'engage') {
      m.moving = false; face(m, P.x); m.timer += sec;
      if (m.timer >= t.engageDelay) {
        if (ctx.canEngage() && ctx.engage(m)) { m.state = 'engaged'; m.timer = 0; }
        else { setState(m, 'return'); m.noAggro = now + t.reaggro * 1000; }
      }
    } else if (st === 'engaged') {
      m.moving = false; m.timer += sec;   // the scene is normally hidden here; if the battle never reports back, release after a moment
      if (m.timer > 2) { setState(m, 'return'); m.noAggro = now + 3000; }
    }
  }
  function update(sec) {
    if (!list.length || !ctx) return;
    const P = ctx.player(), now = performance.now(); clock += sec;
    for (const m of list) {
      if (m.state === 'gone') continue;
      const dP = Math.hypot(P.x - m.x, P.y - m.y);
      if (dP > ACTIVE_RANGE) {   // far off-screen: not simulated; one that was mid-chase/return is simply back at its post
        if (m.state === 'chase' || m.state === 'return' || m.state === 'alert') { m.x = m.home[0]; m.y = m.home[1]; setState(m, 'wander'); m.sub = 'rest'; draw(m, true); }
        continue;
      }
      think(m, Math.min(sec, .1), P, dP, now);
      if (m.t.art && m.t.art.always && m.state !== 'engaged') { m.clock += Math.min(sec, .1); m.moving = true; }   // flyers never stop flapping
      draw(m);
    }
  }
  // After the battle: won -> the monster is gone (until the map is entered again); otherwise it walks back home.
  function resolve(won) {
    for (const m of list) {
      if (m.state !== 'engaged') continue;
      if (won) { m.state = 'gone'; m.el.remove(); if (ctx.slain) ctx.slain.add(m.id); }
      else { m.x = m.home[0]; m.y = m.home[1]; setState(m, 'wander'); m.sub = 'rest'; m.noAggro = performance.now() + 3000; draw(m, true); }
    }
    list = list.filter(m => m.state !== 'gone');
  }
  function clear() { list = []; ctx = null; if (layer) { layer.remove(); layer = null; } }
  window.FieldMonsters = Object.freeze({MONSTER_TYPES, mount, clear, update, resolve, get list() { return list; }});
})();
