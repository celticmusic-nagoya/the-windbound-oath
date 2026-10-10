/* FieldBgm: map-driven background music. Maps name their track in  "audio":{"bgm":{"id":"bgm_rilde_day"}}  and the runtime calls play(id) on every map change
 * (stop() when the field scene is hidden). There are no recorded tracks in the repo yet, so the Rilde Village tracks are small procedural WebAudio pieces
 * (seeded, deterministic note choice); a recorded-file loader can replace PROFILES[id] later without touching maps or story code.
 * Browsers only start audio after a user gesture: play() before that is remembered and starts on the first pointer/key press.
 * Not saved except the player's mute choice (localStorage 'windbound.bgm' = 'off'). Never blocks anything; every failure degrades to silence.
 * API: play(id,{ms}) · stop({ms}) · setMuted(bool) · toggle() · get current/playing/muted/profiles · profiles */
(function () {
  'use strict';
  const KEY = 'windbound.bgm', VOL = .26;
  let ctx = null, master = null, cur = null, active = null, muted = false, unlocked = false, started = false;
  try { muted = localStorage.getItem(KEY) === 'off'; } catch (e) { /* private mode */ }
  const hz = n => 440 * Math.pow(2, (n - 69) / 12);   // midi -> Hz
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  function ensure() {
    if (ctx) return ctx;
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return null;
    try { ctx = new AC(); master = ctx.createGain(); master.gain.value = muted ? 0 : VOL; master.connect(ctx.destination); } catch (e) { ctx = null; }
    return ctx;
  }
  // ---- building blocks (all take a destination bus) ----
  function tone(bus, f, t, dur, o = {}) {
    const osc = ctx.createOscillator(), g = ctx.createGain(), lp = ctx.createBiquadFilter();
    osc.type = o.type || 'triangle'; osc.frequency.value = f; if (o.detune) osc.detune.value = o.detune;
    lp.type = 'lowpass'; lp.frequency.value = o.lp || 2400;
    const a = o.attack ?? .01, peak = o.gain ?? .12;
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(.0008, t + dur);
    osc.connect(lp); lp.connect(g); g.connect(bus); osc.start(t); osc.stop(t + dur + .05); return osc;
  }
  let noiseBuf = null;
  function noise() { if (noiseBuf) return noiseBuf; const n = ctx.sampleRate * 2, b = ctx.createBuffer(1, n, ctx.sampleRate), d = b.getChannelData(0), r = rng(9); for (let i = 0; i < n; i++) d[i] = r() * 2 - 1; return (noiseBuf = b); }
  function pop(bus, t, o = {}) {   // a fire crackle: very short filtered noise burst
    const s = ctx.createBufferSource(), hp = ctx.createBiquadFilter(), g = ctx.createGain();
    s.buffer = noise(); hp.type = 'highpass'; hp.frequency.value = o.hp || 1800;
    g.gain.setValueAtTime(o.gain ?? .1, t); g.gain.exponentialRampToValueAtTime(.001, t + (o.dur || .05));
    s.connect(hp); hp.connect(g); g.connect(bus); s.start(t, Math.random() * 1.5, (o.dur || .05) + .02);
  }
  function bed(bus, lpHz, gain, lfoHz) {   // continuous filtered noise (wind / far fire) with a slow swell; returns stop()
    const s = ctx.createBufferSource(), lp = ctx.createBiquadFilter(), g = ctx.createGain(), lfo = ctx.createOscillator(), lg = ctx.createGain();
    s.buffer = noise(); s.loop = true; lp.type = 'lowpass'; lp.frequency.value = lpHz; g.gain.value = gain;
    lfo.frequency.value = lfoHz; lg.gain.value = gain * .6; lfo.connect(lg); lg.connect(g.gain);
    s.connect(lp); lp.connect(g); g.connect(bus); s.start(); lfo.start();
    return () => { try { s.stop(); lfo.stop(); } catch (e) { /* already stopped */ } };
  }
  function echo(bus, time, fb, wet) {   // returns the input node; wet copy goes to bus
    const input = ctx.createGain(), d = ctx.createDelay(1), f = ctx.createGain(), w = ctx.createGain();
    d.delayTime.value = time; f.gain.value = fb; w.gain.value = wet;
    input.connect(bus); input.connect(d); d.connect(f); f.connect(d); d.connect(w); w.connect(bus); return input;
  }
  function loop(fn, ms = 120, ahead = .45) {   // look-ahead scheduler: fn(tFrom, tTo) schedules every event inside the window
    let next = ctx.currentTime + .05; const id = setInterval(() => { if (!ctx) return; const to = ctx.currentTime + ahead; if (next < ctx.currentTime) next = ctx.currentTime; while (next < to) next = fn(next); }, ms);
    return () => clearInterval(id);
  }
  // ---- the three Rilde Village tracks ----
  // D mixolydian-ish pentatonic: D E F# A B (+ high D E), a light pluck melody over a soft drone; 76 bpm
  function village_day(bus) {
    const R = rng(1013), wet = echo(bus, .36, .34, .5), scale = [62, 64, 66, 69, 71, 74, 76, 78], stops = [];
    let i = 3, step = 0;
    stops.push(loop(t => {
      const beat = 60 / 76 / 2;
      if (step % 8 === 0) { tone(bus, hz(50), t, 3.4, {type: 'sine', gain: .06, attack: .15, lp: 500}); tone(bus, hz(57), t + .02, 3.2, {type: 'sine', gain: .035, attack: .2, lp: 500}); }
      if (R() < (step % 2 ? .38 : .78)) { i = Math.max(0, Math.min(scale.length - 1, i + [-2, -1, -1, 0, 1, 1, 2][Math.floor(R() * 7)])); tone(wet, hz(scale[i]), t, 1.1, {gain: .1, lp: 2600}); if (R() < .2) tone(wet, hz(scale[i] - 12), t + beat * .5, .9, {gain: .05, lp: 1500}); }
      step++; return t + beat;
    }));
    return () => stops.forEach(s => s());
  }
  // slower, warmer, with a crackling hearth: used indoors
  function village_home(bus) {
    const R = rng(2207), wet = echo(bus, .45, .4, .55), scale = [50, 52, 54, 57, 59, 62, 64], stops = []; let i = 2, step = 0;
    const fire = bed(bus, 900, .012, .13);
    stops.push(loop(t => {
      const beat = 60 / 56;
      if (step % 4 === 0) tone(bus, hz(38), t, 4.6, {type: 'sine', gain: .07, attack: .3, lp: 400});
      if (R() < .55) { i = Math.max(0, Math.min(scale.length - 1, i + [-1, 0, 1, 2][Math.floor(R() * 4)])); tone(wet, hz(scale[i] + 12), t, 1.6, {gain: .08, lp: 1700}); }
      for (let k = 0; k < 3; k++) if (R() < .5) pop(bus, t + R() * beat, {gain: .035 + R() * .05, hp: 2200 + R() * 2000});
      step++; return t + beat;
    }, 140));
    return () => { stops.forEach(s => s()); fire(); };
  }
  // after the attack: a low unresolved drone (D + Ab), distant bells, ash-wind and a crackling fire
  function village_ruin(bus) {
    const R = rng(777), wet = echo(bus, .62, .5, .6), stops = []; let step = 0;
    const wind = bed(bus, 520, .03, .07), fire = bed(bus, 2400, .008, .31);
    const d1 = ctx.createOscillator(), d2 = ctx.createOscillator(), dg = ctx.createGain(), dl = ctx.createBiquadFilter(), lfo = ctx.createOscillator(), lg = ctx.createGain();
    d1.type = d2.type = 'sawtooth'; d1.frequency.value = hz(38); d2.frequency.value = hz(44.1); dl.type = 'lowpass'; dl.frequency.value = 260; dg.gain.value = .05;
    lfo.frequency.value = .09; lg.gain.value = .03; lfo.connect(lg); lg.connect(dg.gain);
    d1.connect(dl); d2.connect(dl); dl.connect(dg); dg.connect(bus); d1.start(); d2.start(); lfo.start();
    stops.push(loop(t => {
      const beat = .8;
      if (step % 9 === 0 && R() < .8) { const n = [74, 75, 69, 70, 62][Math.floor(R() * 5)]; tone(wet, hz(n), t, 4.2, {type: 'sine', gain: .09, attack: .02, lp: 3000}); tone(wet, hz(n) * 2.76, t, 2.2, {type: 'sine', gain: .025, attack: .02, lp: 5000}); }
      for (let k = 0; k < 2; k++) if (R() < .6) pop(bus, t + R() * beat, {gain: .05 + R() * .07, hp: 1600 + R() * 2400, dur: .03 + R() * .07});
      step++; return t + beat;
    }, 150));
    return () => { stops.forEach(s => s()); fire(); wind(); try { d1.stop(); d2.stop(); lfo.stop(); } catch (e) { /* stopped */ } };
  }
  const PROFILES = Object.freeze({bgm_rilde_day: village_day, bgm_rilde_home: village_home, bgm_rilde_ruin: village_ruin});
  // ---- control ----
  function stopActive(ms) {
    const a = active; active = null; if (!a || !ctx) return;
    const t = ctx.currentTime; a.bus.gain.cancelScheduledValues(t); a.bus.gain.setValueAtTime(a.bus.gain.value, t); a.bus.gain.linearRampToValueAtTime(0, t + ms / 1000);
    a.stop(); setTimeout(() => { try { a.bus.disconnect(); } catch (e) { /* gone */ } }, ms + 200);
  }
  function startProfile(id, ms) {
    if (!ctx || ctx.state !== 'running' || !PROFILES[id]) return false;
    const bus = ctx.createGain(); bus.gain.setValueAtTime(0, ctx.currentTime); bus.gain.linearRampToValueAtTime(1, ctx.currentTime + ms / 1000); bus.connect(master);
    try { active = {id, bus, stop: PROFILES[id](bus)}; started = true; } catch (e) { active = null; return false; }
    return true;
  }
  function apply(ms) {
    if (!ctx || !unlocked) return;
    if (active && active.id === cur) return;
    stopActive(ms); if (cur) startProfile(cur, ms);
  }
  function unlock() {
    if (unlocked) return; const c = ensure(); if (!c) return;
    c.resume().then(() => { unlocked = true; apply(1500); }).catch(() => {});
    removeEventListener('pointerdown', unlock, true); removeEventListener('keydown', unlock, true);
  }
  addEventListener('pointerdown', unlock, true); addEventListener('keydown', unlock, true);
  function play(id, o = {}) {
    const next = id && PROFILES[id] ? id : null;
    if (next === cur) return; cur = next; apply(o.ms ?? 1500);
    window.dispatchEvent(new CustomEvent('field-bgm', {detail: {id: cur}}));
  }
  function stop(o = {}) { cur = null; stopActive(o.ms ?? 900); window.dispatchEvent(new CustomEvent('field-bgm', {detail: {id: null}})); }
  function setMuted(m) {
    muted = Boolean(m); try { localStorage.setItem(KEY, muted ? 'off' : 'on'); } catch (e) { /* ignore */ }
    if (master) master.gain.linearRampToValueAtTime(muted ? 0 : VOL, ctx.currentTime + .2);
    return muted;
  }
  window.FieldBgm = Object.freeze({play, stop, setMuted, toggle: () => setMuted(!muted), profiles: Object.keys(PROFILES),
    get current() { return cur; }, get playing() { return Boolean(active && ctx && ctx.state === 'running' && !muted); }, get muted() { return muted; }, get started() { return started; }, get unlocked() { return unlocked; }});
})();
