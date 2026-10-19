/* Lou-only faint (lou_faint) — KO-substitute state, confirmed 2026-10-16 (docs/battle/lou-faint/).
   NOT a general status effect (general_stun is an unadopted future candidate; no BattleStatus type is added).
   Pure state + independent RNG. Battle flow hooks live in prologue-combat.js. No counts/probabilities are exposed to the DOM/log. */
(() => {
  let fainted = false, count = 0, justFainted = false, draws = 0, seed0 = 0;
  let fixed = null, scriptSrc = null, script = null, rng = null;
  const dev = () => window.WINDBOUND_DEV === true;
  function mulberry32(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function entropy() {
    try { const a = new Uint32Array(1); crypto.getRandomValues(a); return a[0]; } catch (e) {
      let h = 2166136261 ^ Date.now(); const p = (typeof performance !== 'undefined' ? performance.now() : 0) * 1000 | 0;
      h = Math.imul(h ^ p, 16777619); return h >>> 0;
    }
  }
  function guardDev() { if (!dev()) { fixed = null; scriptSrc = null; script = null; } }
  function reseed() { guardDev(); seed0 = fixed != null ? fixed : entropy(); rng = mulberry32(seed0); script = scriptSrc ? scriptSrc.slice() : null; }
  function next() {
    guardDev(); if (!rng) reseed();
    draws++;
    if (script && script.length) return script.shift();
    return rng();
  }
  function badge() { try { document.querySelector('#rbLou')?.classList.toggle('louFainted', fainted); } catch (e) {} }
  function reset() { fainted = false; count = 0; justFainted = false; draws = 0; reseed(); badge(); }
  // Smash (破砕斬) executed: only when Lou is not already fainted; one draw (<0.33 => faint).
  function judge() {
    if (fainted) return false;
    if (next() < 0.33) { fainted = true; count = 0; justFainted = true; badge(); return true; }
    return false;
  }
  // End of every round (after the defeat check). Returns 'none' | 'still' | 'wake'.
  function advance() {
    if (!fainted) return 'none';
    if (justFainted) { justFainted = false; return 'still'; }
    count++;
    let wake = false;
    if (count >= 3) wake = true; else if (count === 2) wake = next() < 0.5;
    if (wake) { fainted = false; count = 0; badge(); return 'wake'; }
    return 'still';
  }
  const api = {
    reset, judge, advance,
    get fainted() { return fainted; },
    // DEV-only controls (ignored and cleared when WINDBOUND_DEV is off)
    fixSeed(n) { if (!dev()) return false; fixed = n >>> 0; scriptSrc = null; reseed(); return true; },
    setScript(list) { if (!dev()) return false; scriptSrc = list.slice(); script = list.slice(); return true; },
    clearFixed() { fixed = null; scriptSrc = null; script = null; reseed(); },
    get draws() { return draws; }
  };
  window.BattleLouFaint = Object.freeze(api);
})();
