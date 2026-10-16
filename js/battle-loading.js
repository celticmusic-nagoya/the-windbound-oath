/* BL-01 BattleLoading: a short "戦闘準備中…" screen between the battle trigger and the battle scene.
 *
 * Flow: gate(kind,key,resume) is called at the top of startAttackBattle / startRaiderBattle. It takes over the call, shows the overlay, prepares
 * the assets the battle needs in its first seconds (below), waits for BOTH the minimum display time AND the assets, then calls resume() - the
 * original start function - once. Nothing about the battle (maths, order, AI, motion speed) is touched; Loading only precedes it.
 *
 * Assets are shared with the existing machinery, never decoded twice:
 *   idle canvas sets  -> BattleIdleMotion.prepare()  (same cache / in-flight requests / bounded retry as begin(); the decode recovery stays)
 *   opening motions   -> BattleMotion.prepare()       (same per-URL decode jobs as the manifest preload)
 *   stills / backdrop -> this module's per-URL job map (successful Images are kept so the browser's decoded copy stays warm)
 * Not preloaded (lazy): attack / damage / guard / KO / skill art, cut-ins, reinforcements. They load when first used, as before.
 *
 * States: idle -> preparing -> ready | failed (fallback: the battle still starts) ; preparing -> cancelled. Order at the end of a run: settle (state) -> resume -> notify.
 * A loading generation id and a per-run settled flag make a stale run harmless: only the current run may settle, resume or notify (once). */
(() => {
  'use strict';
  const LIMITS = {minMs: 400, maxMs: 6000};                 // minimum display / hard stop (the battle starts anyway and the idle recovery takes over)
  const STILL_TRIES = 3, STILL_BACKOFF = [150, 400];
  const decoded = new Map(), jobs = new Map();                // url -> Image (success) / in-flight job (shared)
  let gen = 0, pass = null, current = null, last = null;   // pass: the one-shot ticket of the run that is resuming (see conclude / gate)
  const status = {state: 'idle', kind: null, key: null, gen: 0, units: {total: 0, done: 0}, failed: [], fallback: false, shownMs: 0, reason: null, runs: 0};

  // Test-only bypass: honoured ONLY when the flag is exactly `true` AND the page is served from a local origin, and it is read ONCE at load (an init script
  // must set it before this file runs). On the published site it can never be on, and nothing can flip it mid-play.
  const LOCAL = ['localhost', '127.0.0.1', '[::1]', '::1', ''].includes(location.hostname);
  const BYPASS = window.WINDBOUND_NO_BATTLE_LOADING === true && LOCAL;
  if (BYPASS) { try { console.info('BattleLoading: bypassed (test mode)'); } catch (e) { } }
  const noLoading = () => BYPASS;
  const hasMotion = (a, s) => Boolean(window.BattleMotion && BattleMotion.loaded && BattleMotion.has(a, s));

  // ---- requirements --------------------------------------------------------------------------------------------------------------------------
  // Mirrors PrologueCombat.beginNormal's enemy choice (read-only knowledge of the ids; battle logic is not touched).
  function enemyTypes(id) {
    id = String(id || '');
    const n = Math.max(1, Math.min(3, +id.slice(-1) || 1));
    if (/^mossSlime\d$/.test(id)) return ['moss_slime'];
    if (/^forestBat\d$/.test(id)) return ['forest_bat'];
    if (/^leafyBoar\d$/.test(id)) return ['leafy_boar'];
    if (/^fieldGob\d$/.test(id)) return ['goblin'];
    return ['goblin', 'tainted_goblin'];
  }
  function requirements(kind, id) {
    const A = window.BATTLE_ASSETS || {}, I = window.BATTLE_IDLE_ASSETS || {};
    const stills = [], idle = [], motions = [];
    const still = (actor, state) => { const u = A[actor] && A[actor][state]; if (u && !stills.includes(u)) stills.push(u); };
    const idleSet = actor => { const s = I[actor]; if (s && !idle.some(x => x.name === actor)) idle.push({name: actor, assets: s}); };
    still('aidan', 'idle'); still('fiona', 'idle'); idleSet('aidan'); idleSet('fiona');
    for (const [a, s] of [['aidan', 'draw'], ['fiona', 'ready']]) if (hasMotion(a, s)) motions.push([a, s]);
    let backdrop = null;
    if (kind === 'raider') {
      still('goblin_raider', 'idle'); still('lou', 'idle'); idleSet('lou');
    } else {
      for (const t of enemyTypes(id)) { still(t, 'idle'); if (t !== 'aidan') idleSet(t); }
      const key = window.BattleBackground && BattleBackground.forEnemy(id);
      backdrop = key && BattleBackground.BG[key] ? BattleBackground.BG[key].src : null;
      if (backdrop) stills.push(backdrop);
    }
    return {stills, idle, motions};
  }

  // ---- shared per-URL image jobs ---------------------------------------------------------------------------------------------------------------
  function startStill(url) {
    const job = (async () => {
      for (let attempt = 1; attempt <= STILL_TRIES; attempt++) {
        const im = new Image(); im.decoding = 'async';          // a fresh <Image> per attempt (a rejected decode() is never reused)
        try { im.src = url; await im.decode(); decoded.set(url, im); return true; }
        catch (e) { if (attempt < STILL_TRIES) await new Promise(r => setTimeout(r, STILL_BACKOFF[Math.min(attempt - 1, STILL_BACKOFF.length - 1)])); }
      }
      return false;
    })();
    jobs.set(url, job); job.then(() => { if (jobs.get(url) === job) jobs.delete(url); });
    return job;
  }
  // Asset-level state (decoded / in-flight jobs) is shared by URL; the success/failure VERDICT belongs to the caller: a caller that merely joined an
  // in-flight job started by an earlier (cancelled / timed-out) Loading and sees it fail gets one fresh job of its own before it reports a failure.
  async function loadStill(url) {
    if (decoded.has(url)) return true;
    const joined = jobs.has(url);
    let ok = await (joined ? jobs.get(url) : startStill(url));
    if (!ok && joined && !decoded.has(url)) ok = await (jobs.get(url) || startStill(url));
    return ok || decoded.has(url);
  }

  // ---- overlay ----------------------------------------------------------------------------------------------------------------------------------
  let el = null, bar = null, count = null;
  function ensureOverlay() {
    if (el && el.isConnected) return el;
    if (!document.getElementById('battleLoadingStyle')) {
      const css = document.createElement('style'); css.id = 'battleLoadingStyle';
      css.textContent = `
#battleLoading{position:fixed;inset:0;z-index:2147483000;display:none;align-items:center;justify-content:center;flex-direction:column;gap:clamp(10px,2.4vh,18px);
 background:radial-gradient(ellipse at 50% 42%,#1d2a26 0%,#0f1614 62%,#070b0a 100%);color:#d9d2b8;font-family:inherit;touch-action:none;user-select:none;-webkit-user-select:none;
 padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);opacity:0;transition:opacity .14s ease-out}
#battleLoading.isOn{display:flex}#battleLoading.isShown{opacity:1}
#battleLoading .blKnot{width:clamp(56px,13vmin,96px);height:clamp(56px,13vmin,96px);opacity:.82}
#battleLoading .blKnot ellipse,#battleLoading .blKnot circle{stroke:#b9a46a;stroke-width:2.6}
#battleLoading .blText{font-size:clamp(15px,3.6vmin,22px);letter-spacing:.18em}
#battleLoading .blBar{width:clamp(150px,36vmin,280px);height:3px;background:#2c3a35;border-radius:2px;overflow:hidden}
#battleLoading .blBar i{display:block;height:100%;width:0;background:#b9a46a;transition:width .12s linear}
#battleLoading .blCount{font-size:11px;color:#8d9a90;letter-spacing:.12em;min-height:1em}
@media (prefers-reduced-motion:no-preference){#battleLoading .blKnot{animation:blSlow 9s linear infinite}}
@keyframes blSlow{to{transform:rotate(360deg)}}
body.battleLoading{overflow:hidden}`;
      document.head.append(css);
    }
    el = document.createElement('div'); el.id = 'battleLoading'; el.setAttribute('role', 'status'); el.setAttribute('aria-live', 'polite');
    el.innerHTML = '<svg class="blKnot" viewBox="0 0 100 100" aria-hidden="true"><g fill="none"><ellipse cx="50" cy="33" rx="15" ry="26"/>' +
      '<ellipse cx="50" cy="33" rx="15" ry="26" transform="rotate(120 50 50)"/><ellipse cx="50" cy="33" rx="15" ry="26" transform="rotate(240 50 50)"/><circle cx="50" cy="50" r="34" opacity=".45"/></g></svg>' +
      '<div class="blText">戦闘準備中…</div><div class="blBar"><i></i></div><div class="blCount"></div>';
    document.body.append(el); bar = el.querySelector('.blBar i'); count = el.querySelector('.blCount');
    return el;
  }
  function show() { ensureOverlay(); el.classList.add('isOn'); void el.offsetWidth; el.classList.add('isShown'); document.body.classList.add('battleLoading'); progress(); }
  function hide() { document.body.classList.remove('battleLoading'); if (el) { el.classList.remove('isShown', 'isOn'); } }
  function progress() {
    const {total, done} = status.units;
    if (bar) bar.style.width = (total ? Math.round(done / total * 100) : 0) + '%';   // real finished/total units only, never a fake estimate
    if (count) count.textContent = total ? done + ' / ' + total : '';
  }

  // ---- common input condition ------------------------------------------------------------------------------------------------------------------
  // frozen = Loading is preparing. Pointer/touch/mouse: the overlay covers the screen. Keyboard (also Bluetooth pads, which Android delivers as keys): keydown is
  // stopped in the capture phase below. Gamepad API: navigator.getGamepads() reports no pad while frozen, so ANY poller (present or future) sees nothing;
  // after Loading ends it stays masked until every button/axis is released (max 800 ms), so a button still held from Loading cannot fire a command.
  const frozen = () => status.state === 'preparing';
  let padMaskUntil = 0, padMasked = false;
  const realGetGamepads = typeof navigator.getGamepads === 'function' ? navigator.getGamepads.bind(navigator) : null;
  if (realGetGamepads) {
    const anyActive = pads => pads.some(p => p && (p.buttons.some(b => b.pressed || b.value > 0.3) || p.axes.some(a => Math.abs(a) > 0.5)));
    try {
      Object.defineProperty(navigator, 'getGamepads', {configurable: true, writable: true, value: function getGamepads() {
        const pads = realGetGamepads();
        if (frozen()) { padMasked = true; padMaskUntil = performance.now() + 800; return []; }
        if (padMasked) {
          if (performance.now() < padMaskUntil && anyActive(Array.from(pads || []))) return [];
          padMasked = false;
        }
        return pads;
      }});
    } catch (e) { }
  }
  // Input is frozen while Loading: the overlay swallows pointer/touch; keys that start an action are swallowed here (key-ups still pass so nothing sticks).
  function swallowKey(e) { if (status.state === 'preparing') { e.preventDefault(); e.stopImmediatePropagation(); } }
  window.addEventListener('keydown', swallowKey, true);

  // ---- run --------------------------------------------------------------------------------------------------------------------------------------
  // One run = one battle request. Its life: preparing -> settled (ready | failed | cancelled) -> [resume the real start function] -> notified.
  //   settle():  commit the final state (status / last / overlay) - the ONLY place a run ends; the first call wins, so a run settles and notifies once.
  //   resume:    the original start function runs with a one-shot pass ticket bound to this run's (kind,key); the ticket dies when resume returns.
  //   notify():  the 'battle-loading' ready / fallback / cancelled event, dispatched AFTER everything above, built from the RUN (never from the shared status,
  //              which a newer run may already own), once per run. A listener therefore always sees a consistent state and may start another battle normally.
  // The Loading owns a BattlePresentation lock (input closed) from gate() until resume() has returned, i.e. until BattleOpening has taken over with its own hold.
  const emit = (phase, run, extra) => window.dispatchEvent(new CustomEvent('battle-loading', {detail: Object.assign({phase, kind: run.kind, key: run.key, gen: run.gen}, extra)}));
  function releaseLock(run) { if (run.lock) { const l = run.lock; run.lock = null; try { l.release(); } catch (e) { } } }
  function settle(run, state, reason) {
    if (run !== current || run.settled) return false;         // a newer run owns the screen / already settled: this one must not start or announce anything
    run.settled = true; current = null; status.state = state; status.reason = reason || null; status.fallback = state === 'failed'; status.failed = run.failed.slice();
    status.shownMs = Math.round(performance.now() - run.t0); last = Object.assign({}, status, {units: Object.assign({}, status.units), failed: status.failed.slice()});
    run.final = {phase: state === 'ready' ? 'ready' : state === 'failed' ? 'fallback' : 'cancelled', shownMs: status.shownMs, failed: status.failed.slice(), reason: reason || null};
    hide();
    return true;
  }
  function notify(run) { if (!run.final || run.notified) return false; run.notified = true; emit(run.final.phase, run, {shownMs: run.final.shownMs, failed: run.final.failed, reason: run.final.reason,
    started: run.started === true, combatGen: run.started === true ? run.startedCombatGen : null, startReason: run.started === true ? null : (run.startReason || 'not-started')}); return true; }
  function conclude(run, state, reason, resume) {
    if (!settle(run, state, reason)) return false;
    if (!resume) { releaseLock(run); notify(run); return true; }   // cancelled: nothing starts
    const ticket = pass = {gen: run.gen, kind: run.kind, key: run.key};
    // INT-02-P0: `run.started` becomes true ONLY after the real start function returned normally; a throw leaves it false (the finally below still notifies, so the
    // listener learns "ready, but NOT started"). Contract: resume is synchronous. A thenable result cannot be confirmed here -> counts as NOT started (fail-closed).
    const real = resume;
    resume = () => {
      const r = real();
      if (r && typeof r.then === 'function') { run.startReason = 'async-resume'; return r; }
      run.started = true; run.startedCombatGen = window.PrologueCombat ? PrologueCombat.generation : null; return r;
    };
    try { resume(); }
    finally { if (pass === ticket) pass = null; releaseLock(run); notify(run); }
    return true;
  }
  async function execute(run, resume) {
    const tasks = [];
    // Results are recorded on THIS run only. A run that is no longer `current` (cancelled / superseded / already fallen back) can still receive late results,
    // but they land in its own run.failed and never touch the shared status or a newer Loading.
    const track = (name, promise) => {
      if (run === current) { status.units.total++; progress(); }
      return promise.then(r => {
        if (r === false || (r && r.ok === false) || (r && r.ready === false)) run.failed.push(...(r && r.failed && r.failed.length ? r.failed : [name]));
        if (run === current) { status.units.done++; progress(); }
        return r;
      });
    };
    status.units = {total: 0, done: 0};
    const req = requirements(run.kind, run.key);
    for (const u of req.stills) tasks.push(track(u, loadStill(u)));
    for (const s of req.idle) tasks.push(track('idle:' + s.name, window.BattleIdleMotion && BattleIdleMotion.prepare ? BattleIdleMotion.prepare(s.assets) : Promise.resolve(true)));
    // Opening motions depend on the manifest: it is prepared from the START of this Loading (ensure() = no wait when it is already ready) and the motion units are
    // added once it is ready. A manifest that failed (404 / parse / network / own 5 s fetch limit) is a recorded failure -> fallback, never a silent "ready".
    tasks.push(track('manifest', (async () => {
      if (!window.BattleMotion || !BattleMotion.ensure) return true;
      let r = await BattleMotion.ensure();
      if (r.state !== 'ready' && r.joined) r = await BattleMotion.ensure();     // joined another (cancelled / earlier) load that failed: one attempt of its own
      if (r.state !== 'ready') return {ok: false, failed: ['manifest:' + (r.reason || 'failed')]};
      await Promise.all(requirements(run.kind, run.key).motions.map(([a, s]) => track('motion:' + a + ':' + s, BattleMotion.prepare(a, s))));
      return true;
    })()));
    progress();
    const minDone = new Promise(r => setTimeout(r, LIMITS.minMs));
    const timeout = new Promise(r => setTimeout(() => r('timeout'), LIMITS.maxMs));
    const outcome = await Promise.race([Promise.all([Promise.all(tasks), minDone]).then(() => 'loaded'), timeout]);
    if (run !== current) return;                              // cancelled / superseded while waiting
    if (window.PrologueCombat && PrologueCombat.generation !== run.combatGen) return conclude(run, 'cancelled', 'another battle began');
    const timedOut = outcome === 'timeout';
    if (timedOut) { const left = status.units.total - status.units.done; run.failed.push('timeout:' + left + ' unit(s) unfinished'); }
    const ok = !timedOut && !run.failed.length;
    const why = ok ? null : timedOut ? 'timeout' : run.failed.some(f => /^manifest:/.test(f)) ? 'manifest' : 'load failure';
    if (!ok) { try { console.warn('BattleLoading: starting with incomplete assets (' + why + '):', run.failed.join(', ')); } catch (e) { } }
    // The minimum display is always honoured, also on a fast failure.
    const left = LIMITS.minMs - (performance.now() - run.t0); if (left > 0) await new Promise(r => setTimeout(r, left));
    conclude(run, ok ? 'ready' : 'failed', why, resume);
  }
  function gate(kind, key, resume) {
    // The resumed call of the run that is resuming right now: ONE call with exactly its (kind,key) passes, once. Any other start request - another battle,
    // or the same one again - is an ordinary new request below, whether it arrives during resume or from a notification listener.
    if (pass && pass.kind === kind && pass.key === key) { pass = null; return false; }
    if (noLoading() || !document.body) return false;
    if (current && current.kind === kind && current.key === key) return true;   // same battle requested again while preparing: ignore
    const old = current; if (old) settle(old, 'cancelled', 'superseded');        // commit the old run first; its event follows once the new run exists
    if (old) releaseLock(old);
    const run = current = {kind, key, gen: ++gen, t0: performance.now(), combatGen: window.PrologueCombat ? PrologueCombat.generation : 0, failed: [], settled: false, notified: false, final: null, lock: null};
    run.lock = window.BattlePresentation && BattlePresentation.lock ? BattlePresentation.lock('loading#' + run.gen) : null;
    Object.assign(status, {state: 'preparing', kind, key, gen: run.gen, units: {total: 0, done: 0}, failed: run.failed, fallback: false, shownMs: 0, reason: null}); status.runs++;
    show();
    if (old) notify(old);
    if (current === run) emit('start', run, {});
    execute(run, resume).catch(e => { try { console.warn('BattleLoading failed unexpectedly:', e); } catch (_) { } if (run === current) conclude(run, 'failed', 'exception', resume); });
    return true;
  }
  function cancel(reason) { if (current) conclude(current, 'cancelled', reason || 'cancelled'); }
  addEventListener('pagehide', () => cancel('pagehide'));

  window.BattleLoading = Object.freeze({
    gate, cancel, requirements,
    setLimits(o) { if (o && o.minMs >= 0) LIMITS.minMs = o.minMs; if (o && o.maxMs > 0) LIMITS.maxMs = o.maxMs; return Object.assign({}, LIMITS); },
    get limits() { return Object.assign({}, LIMITS); },
    get active() { return Boolean(current); },
    get frozen() { return frozen(); },
    get bypassed() { return BYPASS; },
    get status() { return Object.assign({}, status, {units: Object.assign({}, status.units), failed: status.failed.slice(), last}); }
  });
})();
