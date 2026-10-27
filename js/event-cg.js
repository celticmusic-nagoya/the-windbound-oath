/* EventCG (Issue #70): user-approved event CGs shown inside the existing story scenes, tied to their dialogue lines.
 * - Draw-only: scenario lines, flags, SAVE and battle code are untouched. Lines advance exactly as before (click / tap / keys);
 *   each scene just reports its current line index and this module shows the CG whose line range contains it.
 * - Ranges are anchored by line prefixes (resolved against the scene's own line array) and checked by tests:
 *     ルー初登場  louIntroLines 3-5  -> lou_first
 *     祭壇        altarLines 14-16 -> altar_cg01 (father's sword breaks)   18-20 -> altar_cg02 (風の舞 first cast)
 *                 21-23 -> altar_cg03 (Lou stalls the Raider)               32-35 -> altar_cg04 (oath contract)
 * - altar_cg04 starts with the contract FX fade-out (AltarArt 'out' phase, 3.5 s after the grip) and fades in over the same 1.4 s,
 *   so the light settles into the CG. If the player has already advanced past line 35 by then, it is not shown.
 * - Images are used unmodified (no resampling to disk). A CG that has not loaded, or failed to load, is simply not shown:
 *   the event never waits for it. Images are fetched when their scene starts and released when it ends.
 * - User-adopted landscape 16:9 / portrait 9:16 deliveries are kept byte-for-byte. Both variants load before a CG is shown;
 *   orientation switches only CSS visibility, so rotation never waits for a new request or retains the previous orientation.
 *   The complete image is contained above dialogue on a dark feathered background. DEV hiding is unchanged.
 * - ?eventCg=0 turns the layer off (comparison / rollback). */
(function () {
  'use strict';
  const BASE = 'img/events/';
  const CG = {
    lou_first: {landscape: 'cg01_rue_encounter_landscape_16x9.png', portrait: 'cg01_rue_encounter_portrait_9x16.png', kind: 'soft'},
    altar_cg01: {landscape: 'cg02_fathers_sword_break_landscape_16x9.png', portrait: 'cg02_fathers_sword_break_portrait_9x16.png', kind: 'impact'},
    altar_cg02: {landscape: 'cg03_fiona_wind_dance_landscape_16x9.png', portrait: 'cg03_fiona_wind_dance_portrait_9x16.png', kind: 'normal'},
    altar_cg03: {landscape: 'cg04_rue_intervention_landscape_16x9.png', portrait: 'cg04_rue_intervention_portrait_9x16.png', kind: 'normal'},
    altar_cg04: {landscape: 'cg05_oath_sword_contract_landscape_16x9.png', portrait: 'cg05_oath_sword_contract_portrait_9x16.png', kind: 'climax'}
  };
  const SCENES = {
    louIntro: {scene: 'louIntroScene', text: 'louIntroText', lines: () => (typeof louIntroLines !== 'undefined' ? louIntroLines : []), cues: [
      {cg: 'lou_first', from: 'ルー「あなたたちが', to: 'ルー「ルーだよ。'}]},
    altar: {scene: 'altarScene', text: 'altarText', lines: () => (typeof altarLines !== 'undefined' ? altarLines : []), cues: [
      {cg: 'altar_cg01', from: 'だが次の瞬間、乾いた音とともに', to: '二撃目が迫る'},
      {cg: 'altar_cg02', from: '祈るように伸ばしたフィオナの手', to: '風の舞――'},
      {cg: 'altar_cg03', from: 'ルー「今だよ！', to: 'ルー「エイダン、あの石'},
      {cg: 'altar_cg04', from: 'エイダンが柄を握る', to: 'ルー「風が戻ってきた', after: 'fx-out'}]}
  };
  let disabled = false;
  try { disabled = /[?&]eventCg=(0|off|false)\b/.test(location.search); } catch (e) {}
  const state = {};   // sceneKey -> {index, armed:Set, items:{cg:{el,img,portrait,status}}, shown:{cg:count}}
  const at = (lines, prefix) => lines.findIndex(l => l.startsWith(prefix));
  function ranges(key) {
    const s = SCENES[key], L = s.lines();
    return s.cues.map(c => ({...c, a: at(L, c.from), b: at(L, c.to)}));
  }
  function layer(key) {
    const s = SCENES[key], scene = document.getElementById(s.scene);
    if (!scene) return null;
    let root = scene.querySelector(':scope > .event-cg');
    if (!root) {
      root = document.createElement('div'); root.className = 'event-cg'; root.setAttribute('aria-hidden', 'true'); root.dataset.scene = key;
      const text = document.getElementById(s.text);
      scene.insertBefore(root, text || null);
    }
    return root;
  }
  function item(key, cg) {
    const st = state[key], root = layer(key);
    if (!root) return null;
    if (st.items[cg]) return st.items[cg];
    const d = CG[cg], el = document.createElement('div');
    el.className = 'event-cg-item event-cg-' + d.kind; el.dataset.cg = cg;
    const img = document.createElement('img'), portrait = document.createElement('img'), frame = document.createElement('div'), flash = document.createElement('div');
    img.className = 'event-cg-img event-cg-landscape'; portrait.className = 'event-cg-img event-cg-portrait';
    frame.className = 'event-cg-frame'; flash.className = 'event-cg-flash';
    for (const im of [img, portrait]) { im.alt = ''; im.draggable = false; im.decoding = 'async'; }
    frame.append(img, portrait); el.append(frame, flash); root.append(el);
    const rec = st.items[cg] = {el, img, portrait, status: 'idle'};
    let loaded = 0;
    for (const im of [img, portrait]) {
      im.addEventListener('load', () => {
        if (++loaded === 2 && rec.status !== 'failed') { rec.status = 'ready'; apply(key); }
      });
      im.addEventListener('error', () => { rec.status = 'failed'; el.dataset.failed = '1'; apply(key); });
    }
    return rec;
  }
  function load(key, cg) {
    const rec = item(key, cg); if (!rec || rec.status !== 'idle') return;
    rec.status = 'loading';
    rec.img.src = BASE + CG[cg].landscape; rec.portrait.src = BASE + CG[cg].portrait;
  }
  function fit(key) {
    // the CG area ends just above the scene's text box (whatever its current height)
    const s = SCENES[key], root = layer(key), scene = document.getElementById(s.scene), text = document.getElementById(s.text);
    if (!root || !scene || !text) return;
    const sr = scene.getBoundingClientRect(), tr = text.getBoundingClientRect();
    root.style.setProperty('--cg-bottom', Math.max(0, Math.round(sr.bottom - tr.top + 8)) + 'px');
  }
  function apply(key) {
    const st = state[key]; if (!st || disabled) return;
    fit(key);
    for (const c of ranges(key)) {
      const rec = st.items[c.cg]; if (!rec) continue;
      const inRange = st.index >= c.a && st.index <= c.b && c.a >= 0;
      const want = inRange && (!c.after || st.armed.has(c.cg)) && rec.status === 'ready';
      if (want && !rec.el.classList.contains('on')) { rec.el.classList.add('on'); st.shown[c.cg] = (st.shown[c.cg] || 0) + 1; }
      else if (!want && rec.el.classList.contains('on')) rec.el.classList.remove('on');
    }
    mark();
  }
  // body.eventCgOn while any CG is on screen (CSS hides the DEV button / build label; the dev tools themselves are untouched)
  function mark() { document.body.classList.toggle('eventCgOn', Boolean(document.querySelector('.event-cg-item.on'))); }
  function start(key) {
    if (disabled || !SCENES[key]) return;
    end(key);
    state[key] = {index: 0, armed: new Set(), items: {}, shown: {}};
    for (const c of SCENES[key].cues) load(key, c.cg);
    apply(key);
  }
  function update(key, index) { const st = state[key]; if (!st) return; st.index = index; apply(key); }
  // scene finished: hide at once and release the images (decoded CGs are ~6 MB each)
  function end(key) {
    const st = state[key]; if (!st) return;
    const root = layer(key); if (root) root.replaceChildren();
    delete state[key]; mark();
  }
  function trigger(key, what) {
    const st = state[key]; if (!st) return;
    for (const c of ranges(key)) if (c.after === what && st.index >= c.a && st.index <= c.b) st.armed.add(c.cg);
    apply(key);
  }
  addEventListener('altar-fx-phase', e => { if (e.detail === 'out') trigger('altar', 'fx-out'); });
  addEventListener('resize', () => { for (const k in state) fit(k); });
  window.EventCG = Object.freeze({start, update, end, trigger, CG, SCENES, ranges,
    get disabled() { return disabled; },
    debug: key => { const st = state[key]; return st ? {index: st.index, armed: [...st.armed], shown: {...st.shown},
      status: Object.fromEntries(Object.entries(st.items).map(([k, r]) => [k, r.status])),
      on: Object.entries(st.items).filter(([, r]) => r.el.classList.contains('on')).map(([k]) => k)} : null; }});
})();
