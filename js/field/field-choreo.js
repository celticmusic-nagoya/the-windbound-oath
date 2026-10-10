/* FieldChoreo: time-based movement for cutscene actors (engine-independent, Hz-independent: positions come from the clock).
 * An ACTOR is any object  { get():{x,y}  feet position,  set(x,y),  pose?(state,dir) }  - 'state' is 'walk' while it moves and
 * 'idle' when it arrives (dir = 'left'|'right'|'up'|'down'). Adapters: MossForest.actor('aidan'|'fiona') for the forest/cliff
 * engine (Aidan's walk animation follows from the movement itself; Fiona's pose is exposed as data-pose / data-dir for her art).
 * API (all return Promise<boolean> = reached/finished, false when cancelled):
 *   moveTo(actor,{x,y},{ms|speed, ease, blocked, face})   glide to a point; walk -> idle on arrival (face: dir to end on)
 *   approach(a,b,{ms, gap=48, share=.5, ease, blocked})    both walk toward each other until their feet are `gap` px apart
 *                                                            (share = how much of the distance `a` covers; 1 = only a moves)
 *   all(...promises) · cancelAll()
 * `blocked(x,y)` (optional): stops the mover at its last free point, so choreography can never push an actor through a wall. */
(function () {
  'use strict';
  let epoch = 0;
  const ease = {linear: u => u, inOut: u => (u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2), out: u => 1 - (1 - u) * (1 - u)};
  const dirOf = (dx, dy) => (Math.abs(dx) >= Math.abs(dy) ? (dx >= 0 ? 'right' : 'left') : (dy >= 0 ? 'down' : 'up'));
  function glide(actor, to, {ms, speed, ease: e = 'inOut', blocked, face} = {}) {
    const token = epoch, from = actor.get(), dx = to.x - from.x, dy = to.y - from.y, len = Math.hypot(dx, dy);
    const dur = ms ?? (speed ? len / speed * 1000 : 800), fn = ease[e] || ease.inOut, dir = dirOf(dx, dy);
    if (len < .5) { actor.pose && actor.pose('idle', face || dir); return Promise.resolve(true); }
    return new Promise(resolve => {
      let last = from, t0 = null;
      const finish = (ok, at) => { actor.pose && actor.pose('idle', face || dir); resolve(ok); };
      const step = now => {
        if (token !== epoch) { actor.pose && actor.pose('idle', dir); resolve(false); return; }
        if (t0 === null) { t0 = now; actor.pose && actor.pose('walk', dir); }
        const u = Math.min(1, (now - t0) / dur), k = fn(u), x = from.x + dx * k, y = from.y + dy * k;
        if (blocked && blocked(x, y)) { finish(false, last); return; }   // never through a wall
        actor.set(x, y); last = {x, y};
        if (u < 1) requestAnimationFrame(step); else finish(true, last);
      };
      requestAnimationFrame(step);
    });
  }
  const moveTo = glide;
  function approach(a, b, {ms = 1200, gap = 48, share = .5, ease: e = 'inOut', blocked} = {}) {
    const pa = a.get(), pb = b.get(), dx = pb.x - pa.x, dy = pb.y - pa.y, d = Math.hypot(dx, dy);
    if (d <= gap + .5) { a.pose && a.pose('idle', dirOf(dx, dy)); b.pose && b.pose('idle', dirOf(-dx, -dy)); return Promise.resolve(true); }
    const travel = d - gap, ux = dx / d, uy = dy / d, ta = travel * share, tb = travel - ta;
    return all(
      ta > .5 ? glide(a, {x: pa.x + ux * ta, y: pa.y + uy * ta}, {ms, ease: e, blocked, face: dirOf(dx, dy)}) : Promise.resolve((a.pose && a.pose('idle', dirOf(dx, dy)), true)),
      tb > .5 ? glide(b, {x: pb.x - ux * tb, y: pb.y - uy * tb}, {ms, ease: e, blocked, face: dirOf(-dx, -dy)}) : Promise.resolve((b.pose && b.pose('idle', dirOf(-dx, -dy)), true)));
  }
  const all = (...ps) => Promise.all(ps).then(r => r.every(Boolean));
  window.FieldChoreo = Object.freeze({moveTo, approach, all, cancelAll() { epoch++; }, ease});
})();
