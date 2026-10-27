/* PortraitBlink — character-independent blink timing. One controller per portrait on screen, one timer at most, no frame loop:
 * the owner is told the new eye state only when it changes (7 times per blink with the v3 sequence).
 *   const b = PortraitBlink.create({seq, gap:[min,max], onState(state), random?, setTimeout?, clearTimeout?, now?})
 *   b.start()  schedule the next blink (no-op if already running)      b.stop()  cancel; if the eyes were closing, report state 0 once
 *   b.blinkNow() start a blink immediately (dev / preview)              b.status  {running, state, nextAt, timers}
 * Timers / random / clock can be injected (Node unit tests drive it with a fake clock). */
(function (root) {
  'use strict';
  function create(o) {
    const st = o.setTimeout || ((f, ms) => setTimeout(f, ms)), ct = o.clearTimeout || (t => clearTimeout(t));
    const rnd = o.random || Math.random, now = o.now || (() => Date.now()), seq = o.seq, gap = o.gap;
    let timer = null, running = false, state = 0, idx = -1, nextAt = 0, timers = 0;
    const arm = (fn, ms) => { timer = st(() => { timer = null; timers--; fn(); }, ms); timers++; };
    const disarm = () => { if (timer !== null) { ct(timer); timer = null; timers--; } };
    const set = s => { if (s !== state) { state = s; o.onState(s); } };
    function schedule() { const g = gap[0] + rnd() * (gap[1] - gap[0]); nextAt = now() + g; arm(begin, g); }
    function begin() { idx = 0; nextAt = 0; step(); }
    function step() {
      if (!running) return;
      if (idx >= seq.length) { idx = -1; set(0); schedule(); return; }
      const [s, ms] = seq[idx++]; set(s); arm(step, ms);
    }
    return {
      start() { if (running) return; running = true; schedule(); },
      stop() { disarm(); running = false; idx = -1; nextAt = 0; set(0); },
      blinkNow() { if (!running) running = true; disarm(); begin(); },
      get status() { return {running, state, nextAt, timers}; }
    };
  }
  const api = Object.freeze({create});
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PortraitBlink = api;
})(typeof window !== 'undefined' ? window : globalThis);
