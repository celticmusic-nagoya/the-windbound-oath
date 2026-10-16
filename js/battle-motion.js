/* BattleMotion: optional multi-frame playback for battle poses (attack etc.).
 * Battle art today = ONE still PNG per state (BATTLE_ASSETS[actor][state]). This module lets a state carry 2..12 delivered
 * frames WITHOUT touching battle calculation or turn flow: BattleActorState.paint() asks BattleMotion.start(); when no
 * frames are installed for that actor/state it returns null and the still image is used exactly as before.
 *
 * Data: img/battle/motion-manifest.json  (written by tools/battle/install_motion_frames.py; hand-editable)
 *   { "base": "img/battle/characters/",
 *     "motions": { "<actor>[:<variant>]": { "<state>": { "dir":"aidan/motion/", "pattern":"aidan_attack_{n}.png",
 *                    "frames":6, "ms":[80,80,100,100,110,110] | 90, "hitFrame":4, "hold":"last" } } } }
 *   - ms        per-frame display time (array) or one number; total should fit the state's duration budget (installer warns)
 *   - hitFrame  1-based frame on which the impact lands. Emits  'battle-motion-hit'  {actor,state,frame,at}  - presentation
 *               hooks (hit flash, shake, number pop) can bind to it. Damage maths is NOT moved: balance stays as it is.
 *   - hold      'last' (default): stay on the final frame until the state returns to rest.
 *   - variant   e.g. 'wooden' (少年剣士の木剣): BattleMotion.setVariant('aidan','wooden'); falls back to the base actor's motion.
 * API: load(url) · ensure() · manifestState · prepare(actor,state) · start(img, actor, state) · stop(img) · has(actor,state) · info(actor,state) · setVariant(actor,v) · onHit(fn)
 * Completion: the run returned by start() carries  run.done  (Promise, never rejects) and  run.finished  (boolean).
 *   done resolves ONCE with a frozen {completed, reason, frames, ms}:
 *     completed:true  reason:'complete'  every frame was shown and the last frame's own display time has elapsed
 *     completed:false reason:'stopped'   stop(img) was called            | 'replaced'  a newer start() took over the same <img>
 *   BattleActorState waits on it so a pose is never handed back to rest while its last frame is still due. */
(function () {
  'use strict';
  let man = null; const variants = {}, runs = new Map(), hitFns = new Set(), cache = new Map();
  const key = (actor, state) => {
    const m = man && man.motions; if (!m) return null;
    const v = variants[actor];
    if (v && m[actor + ':' + v] && m[actor + ':' + v][state]) return [actor + ':' + v, state];
    return m[actor] && m[actor][state] ? [actor, state] : null;
  };
  const def = (actor, state) => { const k = key(actor, state); return k ? man.motions[k[0]][k[1]] : null; };
  const src = (d, n) => man.base + d.dir + d.pattern.replace('{n}', String(n).padStart(2, '0'));
  const msOf = (d, i) => Array.isArray(d.ms) ? d.ms[i] ?? d.ms[d.ms.length - 1] : d.ms;
  // Frame decoding is shared per URL: ONE in-flight/successful job per frame. A failed job is dropped (never cached) so the next request uses a fresh <Image>.
  const jobs = new Map();
  function frame(u) {
    if (jobs.has(u)) return jobs.get(u);
    const im = new Image(); im.decoding = 'async'; im.src = u; cache.set(u, im);
    const job = im.decode().then(() => im);
    jobs.set(u, job);
    job.catch(() => { if (jobs.get(u) === job) { jobs.delete(u); cache.delete(u); } });
    return job;
  }
  function preload(d) { for (let n = 1; n <= d.frames; n++) frame(src(d, n)).catch(() => {}); }
  // BattleLoading (BL-01): resolve once every frame of actor/state is decoded; failed frames are re-requested with a fresh <Image> (bounded). Never rejects.
  const PREPARE_TRIES = 3, PREPARE_BACKOFF = [150, 400];
  async function prepare(actor, state) {
    const d = def(actor, state); if (!d || !(d.frames > 1)) return {ok: true, frames: 0, failed: []};
    const urls = []; for (let n = 1; n <= d.frames; n++) urls.push(src(d, n));
    let pending = urls;
    for (let attempt = 1; ; attempt++) {
      const res = await Promise.allSettled(pending.map(frame));
      pending = pending.filter((_, i) => res[i].status !== 'fulfilled');
      if (!pending.length) return {ok: true, frames: urls.length, failed: [], attempts: attempt};
      if (attempt >= PREPARE_TRIES) return {ok: false, frames: urls.length, failed: pending, attempts: attempt};
      await new Promise(r => setTimeout(r, PREPARE_BACKOFF[Math.min(attempt - 1, PREPARE_BACKOFF.length - 1)]));
    }
  }
  // ---- manifest state ----------------------------------------------------------------------------------------------------------------------
  // unloaded -> loading -> ready | failed.  `loaded` (= ready) is kept for the existing callers. A failed manifest records WHY (http / parse / network / timeout);
  // ensure() starts a new bounded attempt when the last one failed (BattleLoading calls it once per battle start), and never rejects.
  const MANIFEST_MS = 5000;                                   // one fetch is abandoned after this (BattleLoading's own limit is 6 s)
  let mstate = 'unloaded', mreason = null, murl = null, mjob = null, mseq = 0;
  async function fetchManifest(url, seq) {
    const ctl = typeof AbortController === 'function' ? new AbortController() : null;
    const timer = setTimeout(() => { if (ctl) ctl.abort(); }, MANIFEST_MS);
    let reason = null, m = null;
    try {
      let r; try { r = await fetch(url, ctl ? {signal: ctl.signal} : undefined); } catch (e) { throw new Error(ctl && ctl.signal.aborted ? 'timeout' : 'network'); }
      if (!r.ok) throw new Error('http ' + r.status);
      try { m = await r.json(); } catch (e) { throw new Error(ctl && ctl.signal.aborted ? 'timeout' : 'parse'); }
      if (!m || typeof m.base !== 'string' || typeof m.motions !== 'object') throw new Error('parse');
    } catch (e) { reason = String(e && e.message || e); m = null; }
    clearTimeout(timer);
    if (seq !== mseq) return {state: mstate, reason: mreason, stale: true};   // a newer load() owns the state
    if (m) { man = m; mstate = 'ready'; mreason = null; for (const a of Object.values(m.motions)) for (const d of Object.values(a)) if (d && d.frames > 1) preload(d); }
    else { man = null; mstate = 'failed'; mreason = reason; }   // no manifest = no motion: stills as before
    return {state: mstate, reason: mreason};
  }
  function startLoad(url) {
    murl = url || murl; const seq = ++mseq; mstate = 'loading'; mreason = null;
    return mjob = fetchManifest(murl, seq);
  }
  async function load(url) { return (await startLoad(url)).state === 'ready'; }
  // Resolves {state:'ready'|'failed', reason, joined} - never rejects. ready: no wait at all. loading: joins the in-flight fetch (joined:true: if that one fails the caller
  // may ask again for its own attempt). failed / unloaded: starts a fresh attempt.
  function ensure() {
    if (mstate === 'ready') return Promise.resolve({state: 'ready', reason: null, joined: false});
    const joined = mstate === 'loading' && Boolean(mjob);
    const job = joined ? mjob : startLoad();
    return job.then(r => r.stale ? ensure() : ({state: r.state === 'ready' ? 'ready' : 'failed', reason: r.reason, joined}));
  }
  function halt(img, reason) { const r = runs.get(img); if (r) { clearTimeout(r.timer); runs.delete(img); r.settle(false, reason); } }
  const stop = img => halt(img, 'stopped');
  function start(img, actor, state) {
    halt(img, 'replaced');
    const d = def(actor, state); if (!img || !d || !(d.frames > 1)) return null;
    const run = {i: 0, timer: null, t0: performance.now(), at: 0, finished: false, done: null, settle: null};
    run.done = new Promise(resolve => {   // settle() is idempotent: the first call wins, so a run can never report twice
      run.settle = (completed, reason) => { if (run.finished) return; run.finished = true; resolve(Object.freeze({completed, reason, frames: d.frames, ms: Math.round(performance.now() - run.t0)})); };
    });
    runs.set(img, run);
    const show = () => {
      if (runs.get(img) !== run) return;
      const n = run.i + 1; img.src = src(d, n); img.dataset.motionFrame = n;
      if (n === (d.hitFrame || 0)) { const detail = {actor, state, frame: n, at: Math.round(performance.now() - run.t0)}; for (const f of hitFns) { try { f(detail); } catch (e) {} } dispatchEvent(new CustomEvent('battle-motion-hit', {detail})); }
      if (run.i < d.frames - 1) { const wait = msOf(d, run.i); run.i++; run.timer = setTimeout(show, wait); }
      else if (d.hold === 'first') { run.timer = setTimeout(() => { if (runs.get(img) === run) { img.src = src(d, 1); runs.delete(img); run.settle(true, 'complete'); } }, msOf(d, run.i)); }
      else run.timer = setTimeout(() => { run.timer = null; if (runs.get(img) === run) run.settle(true, 'complete'); }, msOf(d, run.i));   // hold:'last' - the frame stays; only the completion is announced
    };
    show(); return run;
  }
  function info(actor, state) {
    const d = def(actor, state); if (!d) return null;
    let total = 0, hitAt = null; for (let i = 0; i < d.frames; i++) { if (d.hitFrame === i + 1) hitAt = total; total += msOf(d, i); }
    return {frames: d.frames, totalMs: total, hitFrame: d.hitFrame || null, hitAtMs: hitAt};
  }
  window.BattleMotion = Object.freeze({load, start, stop, prepare, has: (a, s) => Boolean(def(a, s)), info,
    hitDelay(actor, state) { const i = info(actor, state); return i && i.hitAtMs != null ? i.hitAtMs : 0; },   // ms from pose start to the blow: for display-only delays of flash / number pop
    setVariant(actor, v) { if (v) variants[actor] = v; else delete variants[actor]; }, onHit(fn) { hitFns.add(fn); return () => hitFns.delete(fn); },
    ensure, get loaded() { return Boolean(man); }, get manifestState() { return mstate; }, get manifestError() { return mreason; }});
  if (typeof document !== 'undefined') startLoad(new URL('../img/battle/motion-manifest.json', document.currentScript ? document.currentScript.src : location.href).href);
})();
