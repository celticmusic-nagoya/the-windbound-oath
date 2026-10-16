/* BattleAdmissionAdapter (INT-02): the one place that connects Claude's battle start (BattleLoading / BattleOpening / BattlePresentation / PrologueCombat.generation)
 * with Codex's BattleCommandGate.installAdmissionProvider(fn). Spec: INT01F_CLAUDE_ADAPTER_SPEC.md (+ INT01E_CODEX_FINAL_CROSS_REVIEW.md section 3/4).
 *
 * What it answers: "does this input belong to the CURRENT battle request, whose start really succeeded, and whose Opening is over?"  It never starts, resumes or
 * cancels anything, never calls BattleCommandGate from inside the provider (the gate calls the provider), never throws, and is O(1) with no DOM writes.
 * It is ONE layer of five (spec section 1): BattleLoading.frozen, BattlePresentation.busy, this adapter, the engine/RESULT checks and the receipt are independent.
 * `BattlePresentation.acceptingInput === true` alone never opens anything - it is only one input to the phase below.
 *
 * Request ledger `cur` (one entry; a new 'start' replaces it; a notification whose detail.gen is not cur.n is ignored - 'cancelled' of the OLD run arrives after the
 * new run exists, so BattleLoading.status.gen must not be used):
 *   rid         'bl#'+gen                      request id (kept for fallback; never re-issued)
 *   battle      'normal' | 'raider'            Loading kind; must equal the body mode or the gate refuses
 *   startGen    PrologueCombat.generation at 'start'
 *   gen         the combat generation, bound ONLY when the start is verified at ready/fallback (null = not started -> never admitted)
 *   cancelled / startFailed / settled / openingSeen / openingDone / openingGen / reason
 * Start success (INT-02-P0, fail-closed): the terminal 'ready'/'fallback' notification must say started === true (BattleLoading sets it ONLY after the real start function
 * returned normally; it still notifies when resume() threw, with started=false) AND carry combatGen === the current combat generation === startGen+1, AND the structure
 * must hold (body mode is this battle's mode, container displayed, a live target exists). A missing / false / unknown flag, a generation mismatch, a late, duplicate,
 * cancelled or foreign (other gen) notification is NEVER success. The structure alone, a generation bump or an Opening notification prove nothing about the start.
 * Opening omission (skipAllowed) is a separate approved fact: it is only reachable after the start was proven.
 * Without Loading (bypass / absent) the same fact comes from the START BOUNDARY: the start functions call enter(kind) after the Loading gate and done() as their last
 * statement; a boundary that was entered and never completed is 'failed' until the next boundary is entered (sticky: cancel/cleanup does not revive it).
 * Opening end: the 'battle-opening' event carries no completion, so the adapter takes the actors' motion run.done from BattleActorState.motion() and marks the end only
 * when every run settled AND the combat generation is still the one it began in. A battle whose Opening never played is an approved, recorded skip (skipAllowed).
 * Without Loading (window.BattleLoading missing, or the localhost test bypass) there are no notifications: an "implicit" request keyed on the combat generation is used.
 * With Loading present and no request in the ledger the provider returns null -> the gate refuses (a battle that never went through BattleLoading.gate is abnormal). */
(() => {
  'use strict';
  if (window.BattleAdmissionAdapter) return;                   // mount once (script re-evaluation must not add a second owner / listeners)
  const gate = window.BattleCommandGate;
  const has = c => document.body.classList.contains(c);
  const battleOf = () => has('raiderBattleMode') ? 'raider' : has('normalBattleMode') ? 'normal' : null;
  const combatGen = () => window.PrologueCombat ? PrologueCombat.generation : null;
  const displayed = el => Boolean(el && el.getClientRects().length);
  const KINDS = ['normal', 'raider'];
  let cur = null;
  let boundary = null;                                         // implicit mode: the last START BOUNDARY {battle, startGen, done}

  const refresh = () => { try { gate && gate.refresh && gate.refresh(); } catch (e) { } };
  const implicitOK = () => !window.BattleLoading || window.BattleLoading.bypassed === true;

  // ---- start verification (see header) ------------------------------------------------------------------------------------------------------------
  function startVerified(c, proven) {
    try {
      const g = combatGen(), b = battleOf();
      if (!Number.isInteger(proven) || g !== proven) return false;          // the generation the START ITSELF reported (BattleLoading) must still be the current one
      if (!Number.isInteger(g) || g !== c.startGen + 1) return false;       // begin* adds exactly one; resume() threw before it, or another battle intervened
      if (b !== c.battle || !has('battleMode')) return false;
      if (!displayed(document.querySelector(b === 'normal' ? '#attackBattle' : '#raiderBattle'))) return false;
      const t = window.PrologueCombat && PrologueCombat.targets ? PrologueCombat.targets(b) : null;
      return Boolean(t && t.some(e => e.hp() > 0));
    } catch (e) { return false; }
  }

  // ---- notifications ------------------------------------------------------------------------------------------------------------------------------
  function onLoading(ev) {
    const d = ev && ev.detail; if (!d || !Number.isInteger(d.gen)) return;
    if (d.phase === 'start') {
      cur = {rid: 'bl#' + d.gen, n: d.gen, battle: KINDS.includes(d.kind) ? d.kind : null, startGen: combatGen(), gen: null,
             cancelled: false, startFailed: false, failReason: null, settled: false, openingSeen: false, openingDone: false, openingGen: null, reason: null};
    } else if (cur && cur.n === d.gen && !cur.settled) {                    // a stale run's late notification (other gen) is ignored
      if (d.phase === 'cancelled') { cur.cancelled = true; cur.settled = true; }
      else if (d.phase === 'ready' || d.phase === 'fallback') {
        cur.settled = true;
        cur.reason = d.phase === 'fallback' ? String(d.reason || 'unknown') : null;
        const proven = d.started === true && Number.isInteger(d.combatGen) ? d.combatGen : null;     // fail-closed: anything but an explicit true is "not started"
        if (cur.battle && proven !== null && startVerified(cur, proven)) cur.gen = proven; else { cur.startFailed = true; cur.failReason = proven === null ? 'start-not-confirmed:' + String(d.startReason || 'no-flag') : 'start-verification'; }
      }
    }
    refresh();
  }
  function onOpening(ev) {
    const c = cur, d = ev && ev.detail;
    if (!c || c.settled || c.cancelled || !d || d.context !== c.battle) return;   // implicit mode has no ledger entry; a settled/foreign request is ignored
    // 'battle-opening' is dispatched INSIDE resume() (before 'ready'): the request is still unsettled here, which is expected.
    c.openingSeen = true; c.openingDone = false; c.openingGen = combatGen();
    const dones = [];
    try { for (const a of d.actors || []) { const r = window.BattleActorState && BattleActorState.motion(d.context, a); if (r && r.done) dones.push(r.done); } } catch (e) { }
    const end = () => { if (cur === c && !c.startFailed && !c.cancelled && c.openingGen === combatGen() && !c.openingDone) { c.openingDone = true; refresh(); } };   // a late settle of a failed/cancelled/replaced request changes nothing
    if (!dones.length) c.openingDone = true;                                   // nothing observable to wait for: the Presentation hold (L2) still guards the time
    else Promise.all(dones).then(end, end);
    refresh();
  }

  // ---- start boundary (implicit mode: no Loading notifications) -------------------------------------------------------------------------------------
  // enter(kind) is called by the start function right after the Loading gate returned false (so only for the call that really starts); the function it returns is called
  // as the LAST statement. done() counts only if the combat generation moved by exactly one and the mode/container belong to this battle.
  // Ownership (P0-D): the OUTERMOST synchronous start owns the boundary. A start entered while another one is still executing (same synchronous stack, not done) is a re-entry: it
  // may not replace the owner and its completion proves nothing - the owner is marked 'reentered' and can never be proven (fail-closed until the next independent start).
  // Success needs boundary.done AND the same battle kind AND doneGen === the current combat generation.
  function enter(kind) {
    if (!KINDS.includes(kind)) return () => { };
    const owner = boundary;
    if (owner && !owner.done && !owner.settled) { owner.reentered = true; return () => { }; }
    const bd = boundary = {battle: kind, startGen: combatGen(), done: false, doneGen: null, settled: false, reentered: false};
    try { Promise.resolve().then(() => { bd.settled = true; }); } catch (e) { bd.settled = true; }
    return function done() {
      try {
        if (boundary !== bd || bd.done || bd.reentered) return;
        const g = combatGen();
        if (startVerified({battle: bd.battle, startGen: bd.startGen}, g)) { bd.done = true; bd.doneGen = g; refresh(); }
      } catch (e) { }
    };
  }

  // ---- provider (pure) ----------------------------------------------------------------------------------------------------------------------------
  function provider() {
    const b = battleOf(), g = combatGen();
    if (implicitOK()) {                                                     // no Loading notifications exist: the request is the combat generation itself
      if (!b || !Number.isInteger(g)) return null;
      if (boundary && !(boundary.done && !boundary.reentered && boundary.battle === b && boundary.doneGen === g))   // entered but no proof for THIS battle+generation (threw / re-entered / generation moved on): not started
        return {requestId: 'implicit#' + g + ':failed', battle: b, generation: g, phase: 'failed', opening: 'skipped', skipAllowed: false, skipReason: ''};
      return {requestId: 'implicit#' + g, battle: b, generation: g,
              phase: has('battleResultMode') || has('raiderFinishing') ? 'ended' : window.BattlePresentation && BattlePresentation.acceptingInput === true ? 'input' : 'opening',
              opening: 'skipped', skipAllowed: true, skipReason: window.BattleLoading ? 'loading-bypassed' : 'loading-absent'};
    }
    const c = cur; if (!c || !c.battle) return null;
    let phase;
    if (c.cancelled) phase = 'cancelled';
    else if (c.startFailed) phase = 'failed';
    else if (window.BattleLoading.active) phase = 'loading';
    else if (!b) phase = 'idle';
    else if (c.gen === null) phase = 'prepared';
    else if (has('battleResultMode') || has('raiderFinishing')) phase = 'ended';
    else if (g !== c.gen) phase = 'idle';                                    // a different battle began without this request: never admit
    else if (c.openingSeen && !c.openingDone) phase = 'opening';
    else if (!(window.BattlePresentation && BattlePresentation.acceptingInput === true)) phase = 'opening';
    else phase = 'input';
    return {requestId: c.rid, battle: c.battle, generation: c.gen, phase,
            opening: c.openingSeen ? (c.openingDone ? 'completed' : 'pending') : 'skipped',
            skipAllowed: !c.openingSeen,
            skipReason: c.openingSeen ? '' : c.reason ? 'fallback:' + c.reason : 'opening-not-played'};
  }
  const safeProvider = () => { try { return provider(); } catch (e) { return null; } };

  window.addEventListener('battle-loading', onLoading);
  window.addEventListener('battle-opening', onOpening);
  window.BattleAdmissionAdapter = Object.freeze({
    provider: safeProvider,
    enter,
    get request() { return cur ? Object.assign({}, cur) : null; }              // read-only copy (tests / diagnostics)
  });
  if (gate && gate.installAdmissionProvider) gate.installAdmissionProvider(safeProvider);   // once; re-installing would clear the gate's context history
  else { try { console.warn('BattleAdmissionAdapter: BattleCommandGate missing - battle commands are not gated'); } catch (e) { } }
})();
