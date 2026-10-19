/* ARENA-MOTION-01 / DEV Motion Test (arena).
 * Independent preview of every battle motion, opened from the DEV MONSTER ARENA panel ("モーションテスト") or ?dev=1&motiontest=1.
 *  - Uses the SAME data as the game: BattleMotion (img/battle/motion-manifest.json), BATTLE_ASSETS (stills), BATTLE_IDLE_ASSETS (idle loops),
 *    BattleFacing (mirroring). No motion is defined here. data/dev/motion-test-config.json only lists characters / slots / delivered-but-unusable material.
 *  - Preview-only controller (play / pause / stop / restart / loop / frame step / speed). It owns its own <img>; it never calls BattleActorState,
 *    never starts a battle, never writes save data, inventory, HP, TP or event flags, and never touches localStorage.
 * Status per motion (computed, not declared): 多コマ実装済み = BattleMotion/idle frames the game really plays; 静止画のみ = still only;
 *   素材納品済み・未実装 / 正式採用待ち = config 'extra' (delivered material the game cannot use yet); 未納品 = nothing. */
(() => {
  'use strict';
  const LABEL = {impl: '多コマ実装済み', still: '静止画のみ', delivered: '素材納品済み・未実装', pending: '正式採用待ち', none: '未納品'};
  const STATE_JA = {draw: '抜刀(開幕)', ready: '構え(開幕)', entry: '登場', idle: '待機', attack: '攻撃', skill: 'スキル', wind: '風の一閃', charge: '溜め', item: 'アイテム', guard: '防御', evade: '回避', damage: '被弾', low_hp: '瀕死', ko: 'KO', victory: '勝利', winddance: '風の舞', prayer: '風の祈り', heal: '回復', blessing: '加護', rune: 'ルーン', call: '呼び声', corruption: '異常化', enrage: '激昂'};
  const SCRIPT = document.currentScript && document.currentScript.src;
  let cfg = null, root = null, loading = null;
  const S = {char: null, row: null, cur: null, idx: 0, playing: false, loop: false, returnIdle: true, speed: 1, timer: null, phase: '', warn: [], foot: null, gone: false, seq: 0};
  const cache = new Map();   // url -> {foot, w, h, ok}

  // ---------- data (shared with the game) ----------
  function idleDef(actor) {
    const a = window.BATTLE_IDLE_ASSETS && BATTLE_IDLE_ASSETS[actor];
    if (a && a.frames && a.frames.length > 1) {
      const base = 1000 / (a.fps || 6);
      return {kind: 'frames', urls: a.frames.map(f => f.path), ms: a.frames.map((_, i) => (a.ms && a.ms[i] > 0) ? a.ms[i] : (a.type === 'breathe' ? 900 : base)), hold: 'last', hitFrame: null, source: 'BATTLE_IDLE_ASSETS'};
    }
    return null;
  }
  function resolve(actor, state) {
    if (state === 'idle') { const i = idleDef(actor); if (i) return i; }
    const f = window.BattleMotion && BattleMotion.frames(actor, state);
    if (f && f.urls.length > 1) return {kind: 'frames', ...f, source: 'BattleMotion'};
    const still = window.BATTLE_ASSETS && BATTLE_ASSETS[actor] && BATTLE_ASSETS[actor][state];
    return still ? {kind: 'still', urls: [still], ms: [1000], hold: 'last', hitFrame: null, source: 'BATTLE_ASSETS'} : null;
  }
  const statusOf = d => !d ? 'none' : d.kind === 'frames' ? 'impl' : 'still';

  function rowsFor(ch) {
    const used = new Set(), slots = [];
    for (const slot of cfg.slots) {
      const rows = [];
      for (const state of (ch.states[slot.id] || [])) {
        used.add(state);
        const d = resolve(ch.actor, state); let status = statusOf(d);
        if (slot.id === 'ko_dissolve' && !(d && d.kind === 'frames' && d.hold === 'hide')) status = 'none';   // dissolve = hold:'hide' only
        rows.push({slot: slot.id, state, label: (STATE_JA[state] || state) + (slot.id === 'ko' && d && d.hold === 'hide' ? '（消滅あり）' : ''), status, def: status === 'none' ? null : d});
      }
      for (const x of ((ch.extra || {})[slot.id] || [])) rows.push({slot: slot.id, state: null, label: x.label, status: x.status, note: x.note, def: null});
      if (!rows.length) rows.push({slot: slot.id, state: null, label: (ch.notes && ch.notes[slot.id]) || '素材なし', status: 'none', def: null});
      slots.push({slot, rows});
    }
    // motions registered in the manifest but not placed in a slot appear automatically
    const auto = (window.BattleMotion ? BattleMotion.states(ch.actor) : []).filter(s => !used.has(s));
    if (auto.length) slots.push({slot: {id: 'auto', label: 'その他（自動検出）'}, rows: auto.map(state => { const d = resolve(ch.actor, state); return {slot: 'auto', state, label: STATE_JA[state] || state, status: statusOf(d), def: d}; })});
    return slots;
  }

  // ---------- image metrics (foot line) ----------
  function measure(url) {
    if (cache.has(url)) return Promise.resolve(cache.get(url));
    return new Promise(res => {
      const im = new Image();
      im.onload = () => {
        let foot = null;
        try {
          const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
          const x = c.getContext('2d', {willReadFrequently: true}); x.drawImage(im, 0, 0);
          const a = x.getImageData(0, 0, c.width, c.height).data;
          outer: for (let y = c.height - 1; y >= 0; y--) for (let px = 0; px < c.width; px++) if (a[(y * c.width + px) * 4 + 3] > 16) { foot = y; break outer; }
        } catch (e) {}
        const r = {ok: true, foot, w: im.naturalWidth, h: im.naturalHeight}; cache.set(url, r); res(r);
      };
      im.onerror = () => { const r = {ok: false, foot: null, w: 0, h: 0}; cache.set(url, r); res(r); };
      im.src = url;
    });
  }

  // ---------- UI ----------
  const $ = s => root.querySelector(s);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
  function build() {
    root = document.createElement('div'); root.id = 'motionTest'; root.setAttribute('role', 'dialog'); root.setAttribute('aria-label', 'モーションテスト');
    root.innerHTML = `<div class="mtHead"><h3>モーションテスト <small>DEV専用・セーブ/所持品/HP/TP/フラグ不変</small></h3><button type="button" data-mt="close">× 閉じる</button></div>
<div class="mtBody"><div class="mtStageWrap"><div class="mtStage"><img class="mtImg" alt="" draggable="false"><div class="mtFoot on"><span></span></div><div class="mtBadgeGone">消滅（非表示）</div></div></div>
<div class="mtPanel"><div class="mtCtlBox"><div class="mtCtl"><button type="button" data-mt="play">▶ 再生</button><button type="button" data-mt="pause">⏸ 一時停止</button><button type="button" data-mt="stop">⏹ 停止</button><button type="button" data-mt="restart">⟲ 最初から</button></div>
<div class="mtCtl"><button type="button" data-mt="prev">◀ コマ戻</button><button type="button" data-mt="next">コマ進 ▶</button><button type="button" data-mt="loop">ループ: OFF</button><button type="button" data-mt="ret">待機復帰: ON</button></div>
<div class="mtCtl">速度 <button type="button" data-speed="0.5">0.5x</button><button type="button" data-speed="1" class="on">1x</button><button type="button" data-speed="2">2x</button><button type="button" data-mt="footbtn">足元ガイド: ON</button></div>
<div class="mtInfo" data-mt="info"></div><div class="mtFrames" data-mt="frames"></div><div class="mtInfo mtWarn" data-mt="warn"></div></div><h4>キャラクター</h4><div class="mtChips" data-mt="chars"></div><h4>モーション</h4><div data-mt="rows"></div>
</div></div>`;
    document.body.appendChild(root);
    root.addEventListener('click', onClick);
    new ResizeObserver(() => placeFoot()).observe($('.mtStage'));
    $('.mtImg').addEventListener('error', onImgError);
  }
  function renderChars() {
    $('[data-mt=chars]').innerHTML = cfg.characters.map(c => `<button type="button" class="mtChip${S.char === c.id ? ' on' : ''}" data-char="${c.id}">${esc(c.label)}</button>`).join('');
  }
  function renderRows() {
    const ch = cfg.characters.find(c => c.id === S.char); if (!ch) return;
    S.rows = rowsFor(ch);
    $('[data-mt=rows]').innerHTML = S.rows.map(g => `<div class="mtSlot">${esc(g.slot.label)}</div>` + g.rows.map((r, i) =>
      `<button type="button" class="mtRow${S.row && S.row.slot === r.slot && S.row.label === r.label ? ' on' : ''}" data-slot="${r.slot}" data-i="${i}" data-status="${r.status}" ${r.state ? `data-state="${r.state}"` : ''}><span>${esc(r.label)}</span><span class="mtBadge ${r.status}">${LABEL[r.status]}</span></button>`).join('')).join('');
  }
  function onClick(e) {
    const t = e.target.closest('button'); if (!t) return;
    if (t.dataset.char) return selectChar(t.dataset.char);
    if (t.dataset.slot) { const g = S.rows.find(g => g.slot.id === t.dataset.slot); return selectRow(g.rows[+t.dataset.i]); }
    if (t.dataset.speed) { S.speed = +t.dataset.speed; root.querySelectorAll('[data-speed]').forEach(b => b.classList.toggle('on', b === t)); return; }
    switch (t.dataset.mt) {
      case 'close': return close();
      case 'play': return play(false);
      case 'pause': return pause();
      case 'stop': return stop();
      case 'restart': return play(true);
      case 'next': return step(1);
      case 'prev': return step(-1);
      case 'loop': S.loop = !S.loop; return refreshToggles();
      case 'ret': S.returnIdle = !S.returnIdle; return refreshToggles();
      case 'footbtn': $('.mtFoot').classList.toggle('on'); return refreshToggles();
    }
  }
  function refreshToggles() {
    $('[data-mt=loop]').textContent = 'ループ: ' + (S.loop ? 'ON' : 'OFF'); $('[data-mt=loop]').classList.toggle('on', S.loop);
    $('[data-mt=ret]').textContent = '待機復帰: ' + (S.returnIdle ? 'ON' : 'OFF'); $('[data-mt=ret]').classList.toggle('on', S.returnIdle);
    const f = $('.mtFoot').classList.contains('on'); $('[data-mt=footbtn]').textContent = '足元ガイド: ' + (f ? 'ON' : 'OFF'); $('[data-mt=footbtn]').classList.toggle('on', f);
    $('[data-mt=play]').classList.toggle('on', S.playing); $('[data-mt=pause]').disabled = !S.playing;
  }

  // ---------- selection ----------
  function selectChar(id) {
    halt(); S.char = id; S.row = null; S.cur = null; S.warn = []; renderChars(); renderRows();
    const idle = S.rows.find(g => g.slot.id === 'idle').rows[0];
    selectRow(idle && idle.def ? idle : (S.rows.flatMap(g => g.rows).find(r => r.def) || null));
  }
  function selectRow(r) {
    halt(); S.row = r; S.warn = []; S.idx = 0; S.phase = ''; S.gone = false; renderRows();
    const info = $('[data-mt=info]');
    if (!r || !r.def) {
      S.cur = null; $('.mtImg').removeAttribute('src'); $('.mtFoot').style.top = '-10px'; $('[data-mt=frames]').innerHTML = '';
      info.innerHTML = `<b>${esc(r ? r.label : '')}</b> — ${LABEL[r ? r.status : 'none']}${r && r.note ? '<br>' + esc(r.note) : ''}<br>再生できる素材はありません（実装済みとは扱いません）。`;
      refreshToggles(); return;
    }
    S.cur = r.def; S.curSlot = r.slot;
    S.loop = r.slot === 'idle';
    S.returnIdle = ['start', 'attack', 'skill', 'support', 'damage'].includes(r.slot);
    refreshToggles(); window.BattleFacing && BattleFacing.paint($('.mtImg'), cfg.characters.find(c => c.id === S.char).actor, r.state || 'idle');
    show(0); prepare(r.def); play(true);
  }
  async function prepare(def) {
    const seq = ++S.seq, ms = await Promise.all(def.urls.map(measure)); if (seq !== S.seq || S.cur !== def) return;
    const bad = ms.map((m, i) => m.ok ? null : def.urls[i].split('/').pop()).filter(Boolean);
    if (bad.length) S.warn = ['画像読み込み失敗: ' + bad.join(', ') + '（静止画へフォールバック）'];
    S.foot = ms; placeFoot(); renderInfo();
  }
  function stageFoot(def, i) {
    const m = S.foot && S.foot[i]; if (!m || !m.ok || m.foot == null) return null;
    const box = $('.mtStage').getBoundingClientRect(), sc = Math.min(box.width / m.w, box.height / m.h);
    return (box.height - m.h * sc) / 2 + (m.foot + 1) * sc;
  }
  function placeFoot() {
    if (!S.cur || !S.foot) return;
    const v = S.foot.map((_, i) => stageFoot(S.cur, i)).filter(x => x != null); if (!v.length) return;
    const y = v[0]; $('.mtFoot').style.top = y + 'px'; S.footSpread = Math.round((Math.max(...v) - Math.min(...v)) * 10) / 10;
    $('.mtFoot span').textContent = '足元ずれ最大 ' + S.footSpread + 'px'; renderInfo();
  }
  function renderInfo() {
    const d = S.cur, r = S.row; if (!d || !r) return;
    const n = d.urls.length, ms = d.ms.map(x => Math.round(x / S.speed));
    $('[data-mt=info]').innerHTML = `<b>${esc(r.label)}</b> — <span class="mtBadge ${r.status}">${LABEL[r.status]}</span> ${S.phase ? '／' + esc(S.phase) : ''}<br>コマ <b data-mt="cf">${S.idx + 1}</b> / <b data-mt="ct">${n}</b>　表示 <b data-mt="cms">${ms[S.idx]}</b>ms　合計 ${ms.reduce((a, b) => a + b, 0)}ms${d.hitFrame ? '　当たり:' + d.hitFrame + 'コマ' : ''}${d.hold === 'hide' ? '　（最終コマ後に消滅）' : ''}<br>${S.footSpread != null ? '足元の画面上ずれ(最大): ' + S.footSpread + 'px　' : ''}出典: ${esc(d.source)}`;
    $('[data-mt=frames]').innerHTML = d.urls.map((u, i) => `<span class="${i === S.idx ? 'cur' : ''}">${i + 1}:${ms[i]}ms</span>`).join('');
    $('[data-mt=warn]').textContent = S.warn.join(' / ');
  }

  // ---------- preview-only playback controller ----------
  function show(i) {
    const d = S.cur; if (!d) return; S.idx = i; const img = $('.mtImg'); img.classList.remove('mtGone'); $('.mtBadgeGone').classList.remove('on'); S.gone = false;
    img.dataset.frame = i + 1; img.dataset.url = d.urls[i]; img.src = d.urls[i]; renderInfo();
  }
  function onImgError() {
    const ch = cfg.characters.find(c => c.id === S.char), r = S.row; if (!ch || !r) return;
    const still = (r.state && BATTLE_ASSETS[ch.actor][r.state]) || BATTLE_ASSETS[ch.actor].idle, img = $('.mtImg');
    const failed = (img.dataset.url || '').split('/').pop();
    if (img.getAttribute('src') === still) return;
    S.warn = S.warn.filter(w => !w.includes(failed)).concat('画像読み込み失敗: ' + failed + '（静止画へフォールバック）'); img.dataset.fallback = '1'; img.src = still; renderInfo();
  }
  function clear() { clearTimeout(S.timer); S.timer = null; }
  function halt() { clear(); S.playing = false; if (root) refreshToggles(); }
  function schedule() {
    clear(); const d = S.cur; if (!d || !S.playing) return;
    const wait = d.ms[S.idx] / S.speed;
    S.timer = setTimeout(() => {
      if (!S.playing || S.cur !== d) return;
      if (S.idx < d.urls.length - 1) { show(S.idx + 1); schedule(); return; }
      if (S.loop && d.urls.length > 1) { show(0); schedule(); return; }
      if (d.hold === 'hide' && d.kind === 'frames') { $('.mtImg').classList.add('mtGone'); $('.mtBadgeGone').classList.add('on'); S.gone = true; S.phase = '消滅（非表示）で停止'; S.playing = false; refreshToggles(); renderInfo(); return; }
      const idle = S.returnIdle && S.curSlot !== 'idle' && S.row && S.row.state !== 'idle' ? returnToIdle() : null;
      if (idle) return;
      S.playing = false; S.phase = d.kind === 'still' ? '' : '最終コマ保持で停止'; refreshToggles(); renderInfo();
    }, wait);
  }
  function returnToIdle() {
    const ch = cfg.characters.find(c => c.id === S.char), idle = ch && resolve(ch.actor, 'idle');
    if (!idle) return null;
    S.cur = idle; S.curSlot = 'idle'; S.loop = true; S.phase = '待機へ復帰（ループ）'; S.foot = null; prepare(idle);
    window.BattleFacing && BattleFacing.paint($('.mtImg'), ch.actor, 'idle'); show(0); schedule(); refreshToggles(); return true;
  }
  function play(fromStart) {
    if (!S.cur) return;
    if (fromStart || (!S.playing && S.idx >= S.cur.urls.length - 1 && !S.loop)) { restoreRow(); show(0); }
    S.playing = true; S.phase = S.phase.startsWith('待機へ') ? '' : S.phase; refreshToggles(); renderInfo(); if (S.cur.urls.length > 1 || S.loop) schedule(); else S.playing = false, refreshToggles();
  }
  function restoreRow() {   // "restart" always returns to the selected motion (not the idle it fell back to)
    if (S.row && S.row.def && S.cur !== S.row.def) { S.cur = S.row.def; S.curSlot = S.row.slot; S.foot = null; prepare(S.cur); S.loop = S.row.slot === 'idle'; refreshToggles(); }
    S.phase = '';
  }
  function pause() { clear(); S.playing = false; S.phase = '一時停止'; refreshToggles(); renderInfo(); }
  function stop() { clear(); S.playing = false; restoreRow(); S.phase = '停止'; show(0); refreshToggles(); renderInfo(); }
  function step(dir) {
    if (!S.cur) return; clear(); S.playing = false; const n = S.cur.urls.length;
    S.idx = ((S.idx + dir) % n + n) % n; S.phase = 'コマ送り'; show(S.idx); refreshToggles(); renderInfo();
  }

  // ---------- open / close ----------
  function onKey(e) {
    if (!root || !root.classList.contains('open')) return;
    const k = e.key;
    if (k === 'Escape') { e.preventDefault(); close(); }
    else if (k === ' ') { e.preventDefault(); S.playing ? pause() : play(false); }
    else if (k === 'ArrowRight') { e.preventDefault(); step(1); }
    else if (k === 'ArrowLeft') { e.preventDefault(); step(-1); }
    if (k !== 'Tab') e.stopImmediatePropagation();   // keep the game under the overlay from reacting
  }
  async function load() {
    if (cfg) return cfg;
    loading = loading || fetch(new URL('../../data/dev/motion-test-config.json', SCRIPT || location.href).href).then(r => r.json());
    cfg = await loading; return cfg;
  }
  async function open(charId) {
    await load(); if (!root) build();
    root.classList.add('open'); document.body.classList.add('motionTestOpen');
    if (charId || !S.char) selectChar(charId || cfg.characters[0].id); else { renderChars(); renderRows(); refreshToggles(); }
    return true;
  }
  function close() { halt(); if (root) root.classList.remove('open'); document.body.classList.remove('motionTestOpen'); }
  window.MotionTest = Object.freeze({
    open, close, get isOpen() { return Boolean(root && root.classList.contains('open')); },
    select(charId, slot, state) { selectChar(charId); const r = S.rows.flatMap(g => g.rows).find(r => r.slot === slot && (state == null || r.state === state)); if (r) selectRow(r); return r ? {status: r.status, state: r.state} : null; },
    control: {play: () => play(false), pause, stop, restart: () => play(true), next: () => step(1), prev: () => step(-1), loop: v => { S.loop = v; refreshToggles(); }, speed: v => { S.speed = v; renderInfo(); }, returnIdle: v => { S.returnIdle = v; refreshToggles(); }},
    snapshot() { return {char: S.char, slot: S.row && S.row.slot, state: S.row && S.row.state, status: S.row && S.row.status, idx: S.idx, total: S.cur ? S.cur.urls.length : 0, playing: S.playing, loop: S.loop, speed: S.speed, phase: S.phase, gone: S.gone, footSpread: S.footSpread, warn: S.warn.slice(), kind: S.cur && S.cur.kind, curSlot: S.curSlot, curState: S.cur && S.cur.urls[0].split('/').pop(), hold: S.cur && S.cur.hold, ms: S.cur ? S.cur.ms.slice() : []}; },
    rows(charId) { const ch = cfg.characters.find(c => c.id === charId); return rowsFor(ch).flatMap(g => g.rows.map(r => ({slot: r.slot, state: r.state, label: r.label, status: r.status}))); },
    get config() { return cfg; }
  });
  addEventListener('keydown', onKey, true);   // registered at load (before the game's input handlers) so the overlay can claim its keys while open
  if (/[?&]motiontest=1/.test(location.search)) addEventListener('load', () => setTimeout(() => open(), 300));
})();
