/* TitleScreen (TITLE-01): PHASE 01 title screen shown on every normal start.
 *  - ?title=0 (tests / dev) or ?legacyVillage=1 skips it. Nothing else in the boot sequence changes: NEW GAME runs the existing opening (index.html startAtHome -> RildeVillage.startOpening).
 *  - NEW GAME: when a save exists, asks for confirmation first (cancel -> back to the title, storage untouched). Starting a new game itself never writes storage.
 *  - CONTINUE: DISABLED. The existing LOAD cannot restore a saved position safely from a cold start (stages 0-8 route to the legacy DOM village, 13-15 to legacy scenes);
 *    canContinue() is the single switch to enable it once a safe restore exists. No save data is read or changed here.
 *  - OPTIONS: opens the existing system menu on its SETTINGS tab (other tabs hidden while on the title, so SAVE cannot overwrite a save from here). No new settings.
 *  - GALLERY: disabled ("未実装").
 *  - Keys: while active this module owns the keyboard (registered before InputManager, capture phase); the rest of the page is inert.
 * Extending: add an entry to PHASES (bg / logo) for PHASE 02/03; no unlock logic exists here. */
(function () {
  'use strict';
  const SAVE_FALLBACK = 'windbound_oath_v028';
  const PHASES = Object.freeze({ '01': Object.freeze({ bg: 'img/title/phase01_background.png', logo: 'img/title/title_logo_v3.png' }) });
  let query; try { query = new URLSearchParams(location.search); } catch (e) { query = new URLSearchParams(); }
  const skip = query.get('title') === '0' || query.get('legacyVillage') === '1';
  let active = !skip, mode = 'menu', pending = null, started = false, phase = '01';
  const $ = s => document.querySelector(s);
  if (active) document.documentElement.classList.add('title-on');

  const saveKey = () => { try { return typeof SAVE_KEY !== 'undefined' ? SAVE_KEY : SAVE_FALLBACK; } catch (e) { return SAVE_FALLBACK; } };
  const hasSave = () => { try { return !!localStorage.getItem(saveKey()); } catch (e) { return false; } };
  const canContinue = () => false;   // see header: no safe cold-start restore of a saved position yet

  let el = null;
  const btns = () => [...el.querySelectorAll('.title-menu .ts-btn')];
  const enabled = () => btns().filter(b => !b.disabled);
  function select(b) { btns().forEach(x => x.classList.toggle('is-sel', x === b)); if (b) b.focus({ preventScroll: true }); }
  // Everything except the title (and the system menu, which OPTIONS opens) is made inert while the title is up.
  let inerted = [];
  function inertOthers(on) {
    if (!on) { inerted.forEach(c => c.removeAttribute('inert')); inerted = []; return; }
    const menu = $('#systemMenu');
    const walk = node => { for (const c of [...node.children]) { if (c === el || c === menu) continue; if (menu && c.contains(menu)) walk(c); else { c.setAttribute('inert', ''); inerted.push(c); } } };
    walk(document.body);
  }

  function finish() {
    if (started) return; started = true; active = false; mode = 'menu';
    inertOthers(false); el.removeAttribute('inert');
    document.documentElement.classList.remove('title-on', 'title-options');
    el.hidden = true;
    const cb = pending; pending = null;
    try { if (cb) cb(); } catch (e) { console.error(e); }
  }
  function showConfirm(on) {
    const c = el.querySelector('.title-confirm'); c.hidden = !on; mode = on ? 'confirm' : 'menu';
    el.querySelector('.title-content').toggleAttribute('inert', on);
    if (on) c.querySelector('[data-title-action="confirm-cancel"]').focus({ preventScroll: true });
    else select(el.querySelector('[data-title-action="new-game"]'));
  }
  function newGame() { if (hasSave()) showConfirm(true); else finish(); }
  function options() {
    const menu = $('#systemMenu'); if (!menu || !$('#menuOpen')) return;
    mode = 'options'; document.documentElement.classList.add('title-options'); el.setAttribute('inert', '');
    $('#menuOpen').click(); const t = $('[data-stab="settings"]'); if (t) t.click();
    const mo = new MutationObserver(() => {
      if (getComputedStyle(menu).display !== 'none') return;
      mo.disconnect(); mode = 'menu'; document.documentElement.classList.remove('title-options'); el.removeAttribute('inert');
      select(el.querySelector('[data-title-action="options"]'));
    });
    mo.observe(menu, { attributes: true, attributeFilter: ['style', 'class'] });
    const f = menu.querySelector('#systemBody button:not([disabled])') || menu.querySelector('#systemClose'); if (f) f.focus({ preventScroll: true });
  }
  const ACTIONS = { 'new-game': newGame, options, 'confirm-ok': finish, 'confirm-cancel': () => showConfirm(false) };

  function onKey(e) {
    if (!active || mode === 'options') return;
    const k = e.key, onBtn = e.target && e.target.closest && e.target.closest('#title-screen button');
    if (mode === 'confirm') {
      if (k === 'Escape') { e.preventDefault(); e.stopImmediatePropagation(); showConfirm(false); return; }
    } else if (k === 'ArrowDown' || k === 'ArrowUp') {
      e.preventDefault(); const l = enabled(); if (!l.length) { e.stopImmediatePropagation(); return; }
      const i = l.indexOf(document.activeElement); select(l[(i + (k === 'ArrowDown' ? 1 : l.length - 1)) % l.length]);
      e.stopImmediatePropagation(); return;
    }
    if ((k === 'Enter' || k === ' ') && onBtn) { e.stopImmediatePropagation(); return; }   // native button activation; the game key layer never sees it
    if (k === 'Tab') return;                                                               // focus stays inside (rest of page is inert)
    e.preventDefault(); e.stopImmediatePropagation();
  }
  window.addEventListener('keydown', onKey, true);
  window.addEventListener('keyup', e => { if (active && mode !== 'options' && e.key !== 'Tab') e.stopImmediatePropagation(); }, true);

  function init() {
    el = $('#title-screen'); if (!el) { active = false; document.documentElement.classList.remove('title-on'); return; }
    if (!active) { el.hidden = true; return; }
    inertOthers(true);
    el.addEventListener('click', e => { const b = e.target.closest('[data-title-action]'); if (!b || b.disabled) return; const f = ACTIONS[b.dataset.titleAction]; if (f) f(); });
    el.addEventListener('pointerover', e => { const b = e.target.closest('.title-menu .ts-btn'); if (b && !b.disabled && mode === 'menu') btns().forEach(x => x.classList.toggle('is-sel', x === b)); });
    const c = el.querySelector('[data-title-action="continue"]'); c.disabled = !canContinue();
    select(el.querySelector('[data-title-action="new-game"]'));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();

  window.TitleScreen = Object.freeze({
    PHASES, get phase() { return phase; },
    active: () => active, get mode() { return mode; }, canContinue, hasSave,
    // index.html startAtHome: run the existing opening now, or after NEW GAME is chosen on the title
    begin(cb) { if (active && !started) pending = cb; else cb(); }
  });
})();
