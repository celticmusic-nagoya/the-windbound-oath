/* Aidan walk heading: turns the player's per-frame displacement into a sprite set.
 * 's' side (left/right art), 'v' straight up/down (frontal / back art), 'd' diagonal (3/4 art 'dl'/'ul', painted facing left; right = mirrored by the caller).
 * Smoothed vector + hysteresis so a path jitter never flickers between sets. Presentation only - never touches movement. */
(function () {
  'use strict';
  // Art map for the diagonals (swap point for dedicated art). Up diagonals reuse the confirmed back-walk set unmirrored
  // (the old 'ul' set never alternated feet). Down diagonals likewise reuse the front-walk set (the 12-frame 'dl' set is kept as spare art). To restore dedicated art: ul -> {art:'ul', mirror:true}, dl -> {art:'dl', mirror:true}.
  const ART = {dl: {art: 'down', mirror: false}, ul: {art: 'up', mirror: false}};
  function art(dir, flip) { const a = ART[dir]; return a ? {dir: a.art, flip: !!flip && a.mirror} : {dir, flip: !!flip}; }
  function create() {
    let vx = 0, vy = 0, mode = null;
    function classify(t) {                       // t: angle from horizontal in degrees (0 = sideways, 90 = straight up/down)
      if (mode === 'v') return t >= 54 ? 'v' : (t >= 34 ? 'd' : 's');
      if (mode === 's') return t <= 34 ? 's' : (t < 54 ? 'd' : 'v');
      if (mode === 'd') return t >= 62 ? 'v' : (t <= 28 ? 's' : 'd');
      return t >= 58 ? 'v' : (t <= 32 ? 's' : 'd');
    }
    return {
      reset() { vx = 0; vy = 0; mode = null; },
      step(dx, dy) {
        vx = vx * .55 + dx * .45; vy = vy * .55 + dy * .45;
        const t = Math.atan2(Math.abs(vy), Math.abs(vx)) * 180 / Math.PI; mode = classify(t);
        const down = vy > 0, right = vx > 0;
        if (mode === 's') return {dir: right ? 'right' : 'left', flip: false};
        if (mode === 'v') return {dir: down ? 'down' : 'up', flip: false};
        return {dir: down ? 'dl' : 'ul', flip: right};
      },
      idleDir(dir) { return dir === 'dl' ? 'down' : dir === 'ul' ? 'up' : dir; }
    };
  }
  window.AidanHeading = Object.freeze({create, art});
})();
