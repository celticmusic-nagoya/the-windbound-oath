/* AltarArt (Issue #70): the official altar art and the contract-activation FX inside #altarScene.
 * - Both images share one box (#altarArt) and the same 1536x1024 canvas, so the FX stays on the altar floor rune circle
 *   exactly as aligned in the asset (no per-image offsets, no scaling difference). Images are used unmodified.
 * - The art is fetched only when the altar scene starts (the altar PNG is ~3.3 MB), then fades in once decoded.
 * - contract(): called on the line where Aidan grips the hilt. The FX fades in, holds, then fades out; it is never shown
 *   outside that moment. reset() hides it at once (scene start / scene end / replays).
 * Scenario text, flags, SAVE and the A3 map are untouched: this file only draws. */
(function () {
  'use strict';
  const FX_IN_MS = 900, FX_HOLD_MS = 2600, FX_OUT_MS = 1400;
  let timers = [], phase = 'idle';
  const box = () => document.getElementById('altarArt');
  function clear() { timers.forEach(clearTimeout); timers = []; }
  function setPhase(p) {
    phase = p; const b = box(); if (!b) return;
    b.classList.toggle('fx-on', p === 'in' || p === 'hold');
    b.classList.toggle('fx-hold', p === 'hold');
    b.dataset.fx = p;
    try { dispatchEvent(new CustomEvent('altar-fx-phase', {detail: p})); } catch (e) {}   // EventCG starts the contract CG on 'out'
  }
  function prepare() {
    const b = box(); if (!b) return;
    for (const im of b.querySelectorAll('img[data-src]')) {
      if (!im.getAttribute('src')) {
        im.addEventListener('load', () => im.classList.add('ready'), {once: true});
        im.src = im.dataset.src;
        if (im.complete && im.naturalWidth) im.classList.add('ready');
      }
    }
  }
  function reset() { clear(); setPhase('idle'); }
  function contract() {
    clear(); prepare(); setPhase('in');
    timers.push(setTimeout(() => setPhase('hold'), FX_IN_MS));
    timers.push(setTimeout(() => setPhase('out'), FX_IN_MS + FX_HOLD_MS));
    timers.push(setTimeout(() => setPhase('idle'), FX_IN_MS + FX_HOLD_MS + FX_OUT_MS));
  }
  window.AltarArt = Object.freeze({prepare, reset, contract, get phase() { return phase; },
    TIMING: Object.freeze({inMs: FX_IN_MS, holdMs: FX_HOLD_MS, outMs: FX_OUT_MS})});
})();
