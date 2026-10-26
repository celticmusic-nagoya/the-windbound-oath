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
 * - Layout: landscape shows the whole CG (contain) above the text box; portrait uses a taller cover box with a per-CG focus so
 *   faces / the broken sword / Lou / the oath sword stay visible. A dimmed copy of the same image fills the margins.
 * - ?eventCg=0 turns the layer off (comparison / rollback). */
(function () {
  'use strict';
  const BASE = 'assets/images/events/';
  const CG = {
    lou_first: {file: 'moss_lou_first_meeting_cg_v1.png', focus: 60, kind: 'soft'},
    altar_cg01: {file: 'moss_altar_cg01_father_sword_break_v1.png', focus: 40, kind: 'impact'},
    altar_cg02: {file: 'moss_altar_cg02_wind_dance_first_v1.png', focus: 42, kind: 'normal'},
    altar_cg03: {file: 'moss_altar_cg03_lou_stall_v1.png', focus: 47, kind: 'normal'},
    altar_cg04: {file: 'moss_altar_cg04_oath_contract_v1.png', focus: 48, kind: 'climax'}
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
  const state = {};   // sceneKey -> {index, armed:Set, items:{cg:{root,img,back,status}}, shown:{cg:count}}
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
    el.style.setProperty('--cg-focus', d.focus + '%');
    const back = document.createElement('img'), img = document.createElement('img'), frame = document.createElement('div'), flash = document.createElement('div');
    back.className = 'event-cg-back'; img.className = 'event-cg-img'; frame.className = 'event-cg-frame'; flash.className = 'event-cg-flash';
    for (const im of [back, img]) { im.alt = ''; im.draggable = false; im.decoding = 'async'; }
    frame.append(img); el.append(back, frame, flash); root.append(el);
    const rec = st.items[cg] = {el, img, back, status: 'idle'};
    img.addEventListener('load', () => { rec.status = 'ready'; apply(key); });
    img.addEventListener('error', () => { rec.status = 'failed'; el.dataset.failed = '1'; apply(key); });
    return rec;
  }
  function load(key, cg) {
    const rec = item(key, cg); if (!rec || rec.status !== 'idle') return;
    rec.status = 'loading'; const src = BASE + CG[cg].file;
    rec.img.src = src; rec.back.src = src;
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
  }
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
    delete state[key];
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
