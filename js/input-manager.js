// InputManager: one capture-phase keyboard layer for the whole game (PC full keyboard support).
// States: FIELD / DIALOGUE / SCENE / MENU / BATTLE_COMMAND / BATTLE_SUBMENU / BATTLE_TARGET / BATTLE_ANIMATION / RESULT.
// Keys: arrows move / select, Enter + Space confirm / talk / investigate, Esc cancel / back, Tab switches the menu area, M opens / closes the menu, Q opens the quest journal.
// One press = one action: key-repeat never confirms. Typing in form fields never triggers shortcuts. Mouse / touch handlers are untouched (every action is a click on the existing control).
// Battle target selection owns its own keys (js/battle-target-selector.js), field conversations theirs (js/field/field-talk.js); the manager only stays out of their way.
(function () {
  'use strict';
  const $ = s => document.querySelector(s);
  const NAV = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
  const isField = t => t && (/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName) || t.isContentEditable);
  const shown = el => { if (!el) return false; const c = getComputedStyle(el); if (c.display === 'none' || c.visibility === 'hidden') return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const SCENES = ['#cinema', '#returnScene', '#escapeScene', '#louIntroScene', '#altarScene', '#aftermathScene', '#fortScene', '#prologueEnd'];
  function topScene() { let best = null, bz = -Infinity; for (const s of SCENES) { const e = $(s); if (!shown(e)) continue; const z = +getComputedStyle(e).zIndex || 0; if (z >= bz) { bz = z; best = e; } } return best; }
  const MENUS = ['#shopModal', '#systemMenu', '#questMenu'];
  const g = name => { try { return (0, eval)('typeof ' + name + '!=="undefined"?' + name + ':undefined'); } catch (e) { return undefined; } };
  let lastConfirm = -1e9;
  let kb = false;                       // the last input was a key (focus rings / auto focus only then)
  let face = [0, 1];                    // last arrow direction (old-world interaction facing)
  const hold = { normal: false, raider: false };   // COMMAND was collapsed by hand: stay collapsed until the next turn

  const pcLike = () => matchMedia('(hover:hover) and (pointer:fine)').matches;
  const inBattle = () => document.body.classList.contains('battleMode');
  const mode = () => document.body.classList.contains('raiderBattleMode') ? 'raider' : document.body.classList.contains('normalBattleMode') ? 'normal' : null;
  const drawer = m => m === 'raider' ? $('#rbCmd') : $('#normalBattleCmd');
  const drawerOpen = m => { const d = drawer(m); return Boolean(d && !d.hidden && shown(d)); };
  const setDrawer = (m, open) => { try { m === 'raider' ? g('setRaiderCommandDrawer')(open) : g('setNormalCommandDrawer')(open); } catch (e) { } };
  const itemsOpen = () => { const b = $('#normalItems'); return Boolean(b && b.classList.contains('isOpen') && shown(b)); };
  const animating = () => Boolean((window.BattlePresentation && BattlePresentation.busy) || document.body.classList.contains('battlePresentationBusy') || document.body.classList.contains('actionCinematic') || (mode()==='normal'?g('attackBattleBusy'):mode()==='raider'?g('rbBusy'):false));

  function state() {
    if (window.LindFieldReview && LindFieldReview.active) return { name: 'REVIEW' };
    if (window.BattleTargetSelector && BattleTargetSelector.active) return { name: 'BATTLE_TARGET' };
    for (const s of MENUS) { const e = $(s); if (shown(e)) return { name: 'MENU', root: e, id: s }; }
    if (window.FieldTalk && FieldTalk.active) return { name: 'DIALOGUE', own: true };
    if (inBattle()) {
      const res = $('#battleResult');
      if (shown(res)) return { name: 'RESULT', root: res };
      { const e = topScene(); if (e) return { name: 'SCENE', root: e }; }
      const m = mode();
      if (animating()) return { name: 'BATTLE_ANIMATION' };
      if (itemsOpen()) return { name: 'BATTLE_SUBMENU', root: $('#normalItems') };
      if (m) return { name: 'BATTLE_COMMAND', root: drawerOpen(m) ? drawer(m) : null, mode: m };
      return { name: 'BATTLE_ANIMATION' };
    }
    const msg = $('#msg'); if (shown(msg) && msg.textContent.trim()) return { name: 'DIALOGUE', root: msg };
    { const e = topScene(); if (e) return { name: 'SCENE', root: e }; }
    return { name: 'FIELD' };
  }

  // ---- focus helpers (buttons inside a panel) ----
  const buttons = root => [...root.querySelectorAll('button:not([disabled]),[role="button"]:not([aria-disabled="true"])')].filter(shown);
  const isClose = b => /Close$/.test(b.id) || b.classList.contains('drawerClose');
  function focusFirst(root) { const b = buttons(root), f = b.find(x => !isClose(x)) || b[0]; if (f) { f.focus({ preventScroll: true }); return f; } return null; }
  function centre(e) { const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }
  function spatial(root, key) {
    const all = buttons(root); if (!all.length) return;
    const cur = all.includes(document.activeElement) ? document.activeElement : null;
    if (!cur) { focusFirst(root); return; }
    const [cx, cy] = centre(cur), v = key === 'ArrowUp' ? [0, -1] : key === 'ArrowDown' ? [0, 1] : key === 'ArrowLeft' ? [-1, 0] : [1, 0];
    let best = null, bs = Infinity;
    for (const b of all) {
      if (b === cur) continue; const [x, y] = centre(b), dx = x - cx, dy = y - cy, along = dx * v[0] + dy * v[1], side = Math.abs(dx * v[1]) + Math.abs(dy * v[0]);
      if (along <= 2) continue; const s = along + side * 2.2; if (s < bs) { bs = s; best = b; }
    }
    if (!best && (key === 'ArrowUp' || key === 'ArrowDown')) { const i = all.indexOf(cur); best = all[(i + (key === 'ArrowDown' ? 1 : all.length - 1)) % all.length]; }
    if (best) best.focus({ preventScroll: true });
  }
  const BACK = '[data-shop-close],[data-ni="close"],[data-ri="close"],[data-back],.backBtn';
  function back(root) {
    const own = [...root.querySelectorAll(BACK)].filter(shown)[0]; if (own) { own.click(); return true; }
    const by = buttons(root).find(b => /^(戻る|閉じる|キャンセル|やめる)/.test(b.textContent.trim()) && !b.id.endsWith('Close')); if (by) { by.click(); return true; }
    return false;
  }
  const TABS = '[data-stab],.journalTabs button';
  let lastTab = null;
  document.addEventListener('focusin', e => { if (e.target.matches && e.target.matches(TABS)) lastTab = e.target; });
  function tabArea(root) { return [...root.querySelectorAll(TABS)].filter(shown); }
  function menuKey(e, st) {
    const root = st.root, k = e.key;
    if (k === 'Escape' || k === 'm' || k === 'M') {
      if (k === 'Escape' && back(root)) return;
      const close = root.id === 'questMenu' ? $('#menuClose') : root.id === 'systemMenu' ? $('#systemClose') : root.querySelector('[data-shop-close]');
      if (close) close.click(); return;
    }
    if (k === 'Tab') {
      const tabs = tabArea(root), inTabs = tabs.includes(document.activeElement);
      if (inTabs) { const body = buttons(root).filter(b => !tabs.includes(b) && !/Close$/.test(b.id)); (body[0] || tabs[0]).focus({ preventScroll: true }); }
      else { (tabs.find(t => t === lastTab) || tabs.find(t => t.classList.contains('on') || t.classList.contains('active') || t.getAttribute('aria-selected') === 'true') || tabs[0] || focusFirst(root))?.focus({ preventScroll: true }); }
      return;
    }
    if (NAV.includes(k)) {
      const tabs = tabArea(root), i = tabs.indexOf(document.activeElement);
      if (i >= 0 && (k === 'ArrowLeft' || k === 'ArrowRight')) { tabs[(i + (k === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length].focus({ preventScroll: true }); return; }
      spatial(root, k); return;
    }
    if (k === 'Enter' || k === ' ') activate(root);
  }
  function activate(root) {
    const a = document.activeElement;
    if (a && root.contains(a) && a.matches('button,[role="button"]')) { if (!a.disabled) a.click(); return; }
    focusFirst(root);
  }

  // ---- battle COMMAND ----
  function commandKey(e, st) {
    const m = st.mode, k = e.key;
    if (!st.root) {                                   // collapsed: any navigation / confirm key brings it back
      if (NAV.includes(k) || k === 'Enter' || k === ' ') { hold[m] = false; setDrawer(m, true); const d = drawer(m); if (d) focusFirst(d); }
      if (k === 'Tab') $(m==='raider'?'#rbCommandToggle':'#normalCommandToggle')?.focus({preventScroll:true});
      return;
    }
    if (k === 'Escape') { hold[m] = true; setDrawer(m, false); return; }
    if (NAV.includes(k)) { spatial(st.root, k); return; }
    if (k === 'Enter' || k === ' ') activate(st.root);
  }

  // ---- field interaction ----
  function oldWorldInteract() {
    const inside = shown($('#inside')), pl = $(inside ? '#inPlayer' : '#player'); if (!pl) return false;
    const [px, py] = centre(pl), sel = inside ? '#inside .furn,#inside .door,#inside .npc,#innKeeper,#innTraveler' : '#world .npc,#world .fisher,#world .door';
    let best = null, bs = Infinity;
    for (const el of document.querySelectorAll(sel)) {
      if (!shown(el)) continue; const [x, y] = centre(el), dx = x - px, dy = y - py, d = Math.hypot(dx, dy); if (d > 190) continue;
      const c = d < 1 ? 1 : (dx * face[0] + dy * face[1]) / (d * Math.hypot(face[0], face[1]));
      if (c < -.25 && d > 70) continue; const s = d * (1.7 - .7 * c); if (s < bs) { bs = s; best = el; }
    }
    if (best) { best.click(); return true; } return false;
  }
  function fieldKey(e) {
    const k = e.key;
    if (k === 'Enter' || k === ' ' || k === 'e' || k === 'E') {
      if (e.repeat) { e.preventDefault(); return; }
      if (shown($('#inside'))) { e.preventDefault(); oldWorldInteract(); return; }
      if (window.MossForest && MossForest.active && !MossForest.busy) { e.preventDefault(); MossForest.interactNearest(); return; }
      if (g('forestActive')) return;
      e.preventDefault(); oldWorldInteract(); return;
    }
    if (k === 'm' || k === 'M') { if (e.repeat) return; e.preventDefault(); $('#menuOpen')?.click(); return; }
    if (k === 'q' || k === 'Q') { if (e.repeat) return; const b = $('#menuBtn'); if (b) { e.preventDefault(); b.click(); } return; }
    if (NAV.includes(k)) { face = k === 'ArrowUp' ? [0, -1] : k === 'ArrowDown' ? [0, 1] : k === 'ArrowLeft' ? [-1, 0] : [1, 0]; }
    if (k === ' ') e.preventDefault();
  }

  // Held arrows for the indoor room (it has no key movement of its own): index.html's inMove() asks for the vector each frame.
  const held = new Set();
  const DIRV = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0] };
  function heldVector() {
    if (!held.size || state().name !== 'FIELD') return null;
    let x = 0, y = 0; held.forEach(k => { x += DIRV[k][0]; y += DIRV[k][1]; }); const l = Math.hypot(x, y); return l ? [x / l, y / l] : null;
  }
  addEventListener('keyup', e => held.delete(e.key), true);
  addEventListener('blur', () => held.clear());

  function onKey(e) {
    if (e.ctrlKey || e.altKey || e.metaKey) return;
    if (isField(e.target)) return;
    kb = true; document.body.classList.add('kbNav');
    const st = state(), k = e.key;
    // two separate confirm presses inside one frame are one intent (no double page / double action); a human double tap is always slower
    if ((k === 'Enter' || k === ' ') && st.name !== 'FIELD' && !st.own && st.name !== 'BATTLE_TARGET') {
      const now = performance.now(); if (now - lastConfirm < 60) { e.preventDefault(); e.stopImmediatePropagation(); return; } lastConfirm = now;
    }
    switch (st.name) {
      case 'REVIEW': case 'BATTLE_TARGET': return;
      case 'DIALOGUE':
        if (st.own) return;                           // FieldTalk handles its own keys (arrows over choices, Enter once per press)
        if (k === 'Enter' || k === ' ' || k === 'Escape') { e.preventDefault(); e.stopImmediatePropagation(); if (!e.repeat) st.root.click(); return; }
        if (NAV.includes(k)) { e.preventDefault(); e.stopImmediatePropagation(); } return;
      case 'SCENE': case 'RESULT': {
        if (k === 'Enter' || k === ' ') { e.preventDefault(); e.stopImmediatePropagation(); if (e.repeat) return; const c = st.name === 'RESULT' ? ($('#resultContinue') || st.root) : st.root; (shown(c) ? c : st.root).click(); return; }
        if (NAV.includes(k) || k === 'Escape' || k === 'Tab') { e.preventDefault(); e.stopImmediatePropagation(); } return;
      }
      case 'BATTLE_ANIMATION':
        if (NAV.includes(k) || k === 'Enter' || k === ' ' || k === 'Escape' || k === 'Tab') { e.preventDefault(); e.stopImmediatePropagation(); } return;
      case 'MENU':
        if (NAV.includes(k) || k === 'Enter' || k === ' ' || k === 'Escape' || k === 'Tab' || k === 'm' || k === 'M') { e.preventDefault(); e.stopImmediatePropagation(); if (e.repeat && k !== 'ArrowUp' && k !== 'ArrowDown' && k !== 'ArrowLeft' && k !== 'ArrowRight') return; menuKey(e, st); } return;
      case 'BATTLE_SUBMENU':
        if (k === 'Escape') { e.preventDefault(); e.stopImmediatePropagation(); if (!e.repeat) back(st.root); return; }
        if (NAV.includes(k)) { e.preventDefault(); e.stopImmediatePropagation(); spatial(st.root, k); return; }
        if (k === 'Enter' || k === ' ') { e.preventDefault(); e.stopImmediatePropagation(); if (!e.repeat) activate(st.root); return; }
        if (k === 'Tab') e.preventDefault(); return;
      case 'BATTLE_COMMAND':
        if (NAV.includes(k) || k === 'Enter' || k === ' ' || k === 'Escape' || k === 'Tab') { e.preventDefault(); e.stopImmediatePropagation(); if (e.repeat && !NAV.includes(k)) return; commandKey(e, st); } return;
      case 'FIELD':
        // arrows never move the hero while a story message / scene owns the screen (handled above); in the field they pass through to the movement code
        if (DIRV[e.key]) held.add(e.key);
        fieldKey(e); return;
    }
  }
  addEventListener('keydown', onKey, true);
  // Space / Enter on a focused button would click it natively on keyup / keydown as well: the capture handler above already consumed those keys where it matters.
  addEventListener('keyup', e => { if (e.key === ' ' && !isField(e.target) && state().name !== 'FIELD') e.preventDefault(); }, true);
  addEventListener('pointerdown', () => { kb = false; document.body.classList.remove('kbNav'); }, true);

  // UI-02 owns input views. Focus repair never changes drawer state.
  function autoOpen(m) { return window.BattleUIState?.snapshot(m).status==='commands'; }
  document.addEventListener('focusin',()=>{const st=state();if(kb&&st.root&&!st.root.contains(document.activeElement))focusFirst(st.root);});
  setInterval(() => {   // keyboard users always have a focused control in an open menu
    if (!kb) return; const st = state();
    if (st.name === 'MENU' && !st.root.contains(document.activeElement)) { const t = tabArea(st.root); (t.find(x => /on|active/.test(x.className) || x.getAttribute('aria-selected') === 'true') || focusFirst(st.root) || t[0])?.focus?.({ preventScroll: true }); }
  }, 200);

  window.InputManager = Object.freeze({ heldVector, state: () => state().name, autoOpen, get keyboard() { return kb; } });
})();
