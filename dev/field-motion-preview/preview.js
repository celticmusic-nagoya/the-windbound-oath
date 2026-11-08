/* Isolated DEV preview: never loaded by the game. */
(function () {
  'use strict';
  const sprites = Array.from(document.querySelectorAll('.sprite'));
  const toggle = document.getElementById('toggle');
  const reduced = document.getElementById('reduced');
  const media = window.matchMedia('(prefers-reduced-motion: reduce)');
  let running = true;
  let raf = 0;
  let last = 0;
  let elapsed = 0;
  toggle.addEventListener('click', () => {
    running = !running;
    toggle.textContent = '動作: ' + (running ? 'ON' : 'OFF');
    toggle.setAttribute('aria-pressed', String(running));
  });
  function frame(now) {
    if (document.hidden) { last = now; raf = requestAnimationFrame(frame); return; }
    if (last) elapsed += Math.min(.1, Math.max(0, (now - last) / 1000));
    last = now;
    const off = reduced.checked || media.matches;
    for (const el of sprites) {
      const kind = el.dataset.kind;
      const m = window.FieldSpriteMotion.sample({kind, moving:running, time:elapsed, reducedMotion:off});
      el.style.transform = 'translate3d(' + m.x + 'px,' + m.y + 'px,0) rotate(' + m.sway + 'deg) scale(' + m.scale + ')';
    }
    raf = requestAnimationFrame(frame);
  }
  raf = requestAnimationFrame(frame);
  window.addEventListener('pagehide', () => cancelAnimationFrame(raf), {once:true});
})();
