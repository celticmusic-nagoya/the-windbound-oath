'use strict';
/* Character Asset Studio v0.3 — Motion Reference panel (UI). Pure logic: motion-core.js (window.MotionCore).
 * Reference videos stay on the device (object URL). Only timings/anchors/SHA-256 are exported, as UNAPPROVED_REFERENCE.
 * Nothing here writes to the studio's BASE_BODY_SPEC landmarks or to any canonical asset. */
(function () {
  const M = window.MotionCore;
  const S = window.Studio;              // exposed by app.js
  const $ = id => document.getElementById(id);
  const video = $('mvVideo');
  const cv = $('mvCanvas'), cx = cv.getContext('2d', { willReadFrequently: true });
  const tl = $('mvTimeline'), tx = tl.getContext('2d');
  const JOINT_COLORS = { head: '#f5d76e', shoulder: '#ff9f43', elbow: '#ee5a24', wrist: '#ff6b81', hip: '#7bed9f', knee_L: '#70a1ff', knee_R: '#a29bfe', ankle_L: '#1e90ff', ankle_R: '#be2edd', toe_L: '#00d2d3', toe_R: '#e056fd' };
  const PHASE_COLORS = { contact: '#ff6b6b', down: '#feca57', passing: '#48dbfb', up: '#1dd1a1', push_off: '#c8d6e5' };
  const m = { ref: M.createRef(), frame: 0, url: null, loaded: false, vbox: null, sbox: null, seekToken: 0, refCheck: null };
  const sprite = document.createElement('canvas'), sx = sprite.getContext('2d');

  const fps = () => Math.max(1, Number($('mvFps').value) || 24);
  const total = () => m.ref.video.frameCount || 1;
  const regionOf = () => m.ref.region;
  function status(t) { $('mvStatus').textContent = t; }
  function hex(buf) { return [...new Uint8Array(buf)].map(x => x.toString(16).padStart(2, '0')).join(''); }

  /* ---------- video loading / transport ---------- */
  async function loadVideo(file) {
    if (m.url) URL.revokeObjectURL(m.url);
    m.loaded = false; status('読み込み中…');
    const buf = await file.arrayBuffer();
    const sha = hex(await crypto.subtle.digest('SHA-256', buf));
    m.url = URL.createObjectURL(file);
    video.src = m.url;
    await new Promise((res, rej) => { video.onloadedmetadata = res; video.onerror = () => rej(new Error('この形式はこのブラウザで再生できません')); });
    const keep = m.ref.video.sha256 === sha ? m.ref : null;   // re-attaching the same video keeps registered data
    const ref = keep || M.createRef({ region: $('mvRegion').value });
    ref.video = Object.assign(ref.video, { name: file.name, sha256: sha, width: video.videoWidth, height: video.videoHeight, fps: fps(), frameCount: M.frameCountFor(video.duration, fps()), fpsSource: ref.video.fpsSource || 'user_entered' });
    m.ref = ref; m.loaded = true;
    m.refCheck = m.pendingRef && m.pendingRef.video.sha256 ? (m.pendingRef.video.sha256 === sha ? 'match' : 'mismatch') : null;
    if (m.pendingRef && m.refCheck === 'match') { m.ref = m.pendingRef; m.ref.video.name = file.name; }
    m.pendingRef = null;
    $('mvSlider').max = total() - 1;
    await seek(0);
    renderLists();
    status(`${file.name} · ${video.videoWidth}×${video.videoHeight} · ${video.duration.toFixed(2)}s · ${fps()}fps → ${total()}コマ · SHA-256 ${sha.slice(0, 12)}…` +
      (m.refCheck === 'match' ? ' · 参照JSONと一致' : m.refCheck === 'mismatch' ? ' · 参照JSONと不一致（登録内容は適用しません）' : ''));
    document.body.dataset.mvReady = '1';
  }
  function seek(frame) {
    m.frame = M.stepFrame(Math.round(frame), 0, total());
    const token = ++m.seekToken;
    return new Promise(res => {
      if (!m.loaded) { draw(); return res(); }
      const t = M.frameToTime(m.frame, fps());
      const done = () => { if (token === m.seekToken) draw(); res(); };
      if (Math.abs(video.currentTime - t) < 1e-4 && video.readyState >= 2) return done();
      video.addEventListener('seeked', done, { once: true });
      video.currentTime = t;
    });
  }
  function playLoop() {
    if (video.paused) return;
    m.frame = M.timeToFrame(video.currentTime, fps());
    draw();
    if (video.requestVideoFrameCallback) video.requestVideoFrameCallback(playLoop); else requestAnimationFrame(playLoop);
  }
  function play() { if (!m.loaded) return; video.playbackRate = Number($('mvRate').value); video.play().then(playLoop); $('mvPlay').textContent = '❚❚ 一時停止'; }
  function pause() { video.pause(); $('mvPlay').textContent = '▶ 再生'; seek(M.timeToFrame(video.currentTime, fps())); }

  /* ---------- sprite (from the studio, guides off, canonical layers allowed for viewing only) ---------- */
  function spriteFor(frame) {
    const st = S.state, keep = st.frame;
    sprite.width = S.W(); sprite.height = S.H();
    st.frame = frame;
    S.paint(sx, { guides: false, background: false, transparent: true });
    st.frame = keep;
    return sprite;
  }
  function hasSprite(frame) { return S.state.items.some(it => it.view === S.state.view && it.frame === frame && it.visible); }
  function emptyNote(ctx, box, frame) {
    if (hasSprite(frame)) return;
    ctx.fillStyle = '#7d8ea5'; ctx.font = `${Math.max(10, Math.round(box.w / 14))}px system-ui`; ctx.textAlign = 'center';
    ctx.fillText(`sprite f${frame}: 未登録`, box.x + box.w / 2, box.y + box.h / 2); ctx.textAlign = 'left';
  }
  function syncedSpriteFrame() {
    if (!$('mvSync').checked) return S.state.frame;
    const c = M.cycles(m.ref).find(c => m.frame >= c.start && m.frame < c.end);
    if (!c) return S.state.frame;
    return Math.floor((m.frame - c.start) / c.length * S.frames()) % S.frames();
  }

  /* ---------- drawing ---------- */
  function drawVideoRegion(ctx, box) {
    const [rx, ry, rw, rh] = regionOf();
    ctx.drawImage(video, rx * video.videoWidth, ry * video.videoHeight, rw * video.videoWidth, rh * video.videoHeight, box.x, box.y, box.w, box.h);
  }
  function videoAspect() { const [, , rw, rh] = regionOf(); return [rw * (video.videoWidth || 16), rh * (video.videoHeight || 9)]; }
  function drawAnchors(ctx, box, frame, withTrails) {
    const lw = Math.max(1.5, box.w / 200);
    if (withTrails) for (const j of M.JOINTS) {
      const t = M.trajectory(m.ref, j); if (t.length < 2) continue;
      ctx.strokeStyle = JOINT_COLORS[j] + 'cc'; ctx.lineWidth = lw; ctx.beginPath();
      t.forEach(([, x, y], i) => { const [px, py] = M.regionToBox([x, y], box); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
      ctx.stroke();
      for (const [, x, y] of t) { const [px, py] = M.regionToBox([x, y], box); ctx.fillStyle = JOINT_COLORS[j] + '99'; ctx.fillRect(px - lw, py - lw, lw * 2, lw * 2); }
    }
    for (const j of M.JOINTS) {
      const rec = m.ref.anchors[String(frame)] && m.ref.anchors[String(frame)][j];
      const n = rec ? rec.n : ($('mvGhost').checked ? M.anchorAt(m.ref, j, frame) : null);
      if (!n) continue;
      const [px, py] = M.regionToBox(n, box);
      ctx.beginPath(); ctx.arc(px, py, Math.max(4, box.w / 70), 0, Math.PI * 2);
      ctx.fillStyle = rec ? JOINT_COLORS[j] : 'transparent'; ctx.strokeStyle = rec ? '#fff' : JOINT_COLORS[j];
      ctx.lineWidth = rec ? 2 : 2.5; ctx.setLineDash(rec ? [] : [4, 3]); ctx.fill(); ctx.stroke(); ctx.setLineDash([]);
      if (j === $('mvJoint').value) { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.strokeRect(px - 10, py - 10, 20, 20); }
    }
  }
  function draw() {
    const Wc = cv.width, Hc = cv.height, mode = $('mvMode').value;
    cx.fillStyle = '#0a1018'; cx.fillRect(0, 0, Wc, Hc);
    const [aw, ah] = videoAspect();
    const half = mode === 'side';
    m.vbox = M.fitBox(aw, ah, 0, 0, half ? Wc / 2 : Wc, Hc);
    if (m.loaded) drawVideoRegion(cx, m.vbox);
    else { cx.fillStyle = '#7d8ea5'; cx.font = '22px system-ui'; cx.textAlign = 'center'; cx.fillText('参考動画（MP4）を読み込んでください', half ? Wc / 4 : Wc / 2, Hc / 2); cx.textAlign = 'left'; }
    const sf = syncedSpriteFrame(), sp = spriteFor(sf);
    const scale = Number($('mvScale').value) / 100, offX = Number($('mvOffset').value) / 100;
    const base = half ? M.fitBox(sp.width, sp.height, Wc / 2, 0, Wc / 2, Hc) : M.fitBox(sp.width, sp.height, 0, 0, Wc, Hc);
    const w = base.w * scale, h = base.h * scale;
    m.sbox = { x: base.x + (base.w - w) / 2 + offX * (half ? Wc / 2 : Wc), y: base.y + base.h - h, w, h };
    cx.save();
    if (!half) cx.globalAlpha = Number($('mvAlpha').value) / 100;
    cx.drawImage(sp, m.sbox.x, m.sbox.y, m.sbox.w, m.sbox.h);
    cx.restore();
    emptyNote(cx, half ? { x: Wc / 2, y: 0, w: Wc / 2, h: Hc } : { x: 0, y: Hc * 0.8, w: Wc, h: Hc * 0.2 }, sf);
    if (half) { cx.strokeStyle = '#394354'; cx.beginPath(); cx.moveTo(Wc / 2 + .5, 0); cx.lineTo(Wc / 2 + .5, Hc); cx.stroke(); }
    // ground line of the sprite (studio landmark) for visual alignment
    const g = S.state.landmarks[S.state.view].ground.n;
    const gy = m.sbox.y + g[1] * m.sbox.h;
    cx.strokeStyle = '#df6b52aa'; cx.setLineDash([8, 6]); cx.beginPath(); cx.moveTo(0, gy); cx.lineTo(Wc, gy); cx.stroke(); cx.setLineDash([]);
    if (m.loaded) drawAnchors(cx, m.vbox, m.frame, $('mvTrails').checked);
    const ph = m.ref.phases.find(p => p.frame === m.frame);
    cx.fillStyle = '#000a'; cx.fillRect(8, 8, 330, 30);
    cx.fillStyle = '#fff'; cx.font = '16px system-ui';
    cx.fillText(`F${m.frame} ${M.timecode(m.frame, fps())}${ph ? ' · ' + ph.phase + '(' + ph.side + ')' : ''} · sprite f${sf}`, 16, 29);
    $('mvFrameLabel').textContent = `${m.frame} / ${Math.max(0, total() - 1)}`;
    $('mvSlider').value = m.frame;
    drawTimeline();
  }
  function drawTimeline() {
    const Wt = tl.width, Ht = tl.height, n = Math.max(1, total() - 1);
    tx.fillStyle = '#0e1622'; tx.fillRect(0, 0, Wt, Ht);
    for (const c of M.cycles(m.ref)) { tx.fillStyle = c.side === 'B' || c.side === 'R' ? '#2f3e5a' : '#3a4b2f'; tx.fillRect(c.start / n * Wt, Ht - 6, c.length / n * Wt, 6); }
    for (const p of m.ref.phases) { tx.fillStyle = PHASE_COLORS[p.phase]; tx.fillRect(p.frame / n * Wt - 1.5, p.phase === 'contact' ? 2 : 10, 3, p.phase === 'contact' ? Ht - 10 : Ht - 18); }
    for (const f of Object.keys(m.ref.anchors)) { tx.fillStyle = '#fff'; tx.fillRect(Number(f) / n * Wt - .5, 0, 1, 4); }
    tx.fillStyle = '#e6b772'; tx.fillRect(m.frame / n * Wt - 1, 0, 2, Ht);
  }

  /* ---------- lists / stats ---------- */
  function renderLists() {
    const list = $('mvPhaseList'); list.replaceChildren();
    for (const p of m.ref.phases) {
      const row = document.createElement('div'); row.className = 'layeritem';
      const go = document.createElement('button'); go.textContent = `F${p.frame}`; go.onclick = () => seek(p.frame);
      const sp = document.createElement('span'); sp.textContent = `${p.phase} · ${p.side} · ${p.confidence}`; sp.style.color = PHASE_COLORS[p.phase];
      const del = document.createElement('button'); del.textContent = '×'; del.setAttribute('aria-label', `F${p.frame}のフェーズを削除`);
      del.onclick = () => { M.removePhase(m.ref, p.frame); renderLists(); draw(); };
      row.append(go, sp, del); list.append(row);
    }
    const cyc = M.cycles(m.ref), sel = $('mvCycle'), keep = sel.value; sel.replaceChildren();
    cyc.forEach((c, i) => sel.append(new Option(`#${i + 1} F${c.start}→F${c.end}（${c.length}コマ・${c.side}${c.sideAssumed ? '・交互仮定' : ''}）`, i)));
    if (keep && Number(keep) < cyc.length) sel.value = keep;
    const s = M.stats(m.ref);
    $('mvStats').textContent = `未承認の参考値 · 接地${s.contacts} · 1歩 平均${s.meanStepFrames ?? '—'}コマ · 1周期 平均${s.meanCycleFrames ?? '—'}コマ（動画fps換算 ${s.meanCycleSecondsAtVideoFps ?? '—'}秒）· アンカー記録 ${Object.keys(m.ref.anchors).length}フレーム`;
  }

  /* ---------- cycle comparison (6 / 8 / 12) ---------- */
  async function buildCycle() {
    const cyc = M.cycles(m.ref)[Number($('mvCycle').value)];
    const grid = $('mvCycleGrid'); grid.replaceChildren();
    if (!cyc) { grid.textContent = '同じ側の接地（contact）を2つ以上登録すると周期が作れます。'; return; }
    const n = Number($('mvCount').value), frames = M.sampleCycle(cyc.start, cyc.end, n), keep = m.frame;
    grid.style.setProperty('--n', n);
    for (let i = 0; i < n; i++) {
      const cell = document.createElement('figure'); cell.className = 'mvcell';
      const c = document.createElement('canvas'); c.width = 160; c.height = 260; const g = c.getContext('2d');
      g.fillStyle = '#0a1018'; g.fillRect(0, 0, 160, 260);
      if (m.loaded) {
        await seek(frames[i]);
        const [aw, ah] = videoAspect(), box = M.fitBox(aw, ah, 0, 0, 160, 130);
        drawVideoRegion(g, box); drawAnchors(g, box, frames[i], false);
      }
      const sf = M.spriteFrameFor(i, n, S.frames()), sp = spriteFor(sf), sb = M.fitBox(sp.width, sp.height, 0, 130, 160, 130);
      g.drawImage(sp, sb.x, sb.y, sb.w, sb.h); emptyNote(g, { x: 0, y: 130, w: 160, h: 130 }, sf);
      const cap = document.createElement('figcaption'); cap.textContent = `${i + 1}/${n} · 動画F${frames[i]} · sprite f${sf}`;
      cell.append(c, cap); grid.append(cell);
    }
    grid.dataset.count = n;
    await seek(keep);
  }

  /* ---------- JSON ---------- */
  function exportJSON() {
    m.ref.video.fps = fps();
    const text = M.serialize(m.ref);
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'application/json' }));
    a.download = `motion_reference_${(m.ref.video.name || 'video').replace(/\.[^.]+$/, '')}.json`;
    document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1500);
  }
  function applyImported(ref, label) {
    if (m.loaded && ref.video.sha256 && ref.video.sha256 !== m.ref.video.sha256) {
      status(`${label}: 動画のSHA-256が一致しません（${ref.video.sha256.slice(0, 12)}… ≠ ${m.ref.video.sha256.slice(0, 12)}…）。適用していません。`); return;
    }
    if (!m.loaded) { m.pendingRef = ref; m.ref = ref; $('mvFps').value = ref.video.fps; $('mvRegion').value = regionName(ref.region); status(`${label}: 読み込み済み（未承認の参考値）。対応する動画を読み込むとSHA-256を照合します。`); }
    else { ref.video.name = m.ref.video.name; m.ref = ref; $('mvFps').value = ref.video.fps; $('mvRegion').value = regionName(ref.region); status(`${label}: 適用（SHA-256一致・未承認の参考値）`); }
    $('mvSlider').max = total() - 1; renderLists(); draw();
    document.body.dataset.mvImported = String(Date.now());
  }
  function regionName(r) { for (const [k, v] of Object.entries(M.REGIONS)) if (v.every((x, i) => Math.abs(x - r[i]) < 1e-6)) return k; return 'full'; }

  /* ---------- input ---------- */
  function canvasPoint(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * cv.width, (e.clientY - r.top) / r.height * cv.height]; }
  cv.addEventListener('pointerdown', e => {
    if (!m.loaded || !$('mvRecord').checked) return;
    const [x, y] = canvasPoint(e), b = m.vbox;
    if (x < b.x || x > b.x + b.w || y < b.y || y > b.y + b.h) return;
    e.preventDefault();
    M.setAnchor(m.ref, m.frame, $('mvJoint').value, M.boxToRegion([x, y], b), $('mvConf').value);
    renderLists(); draw();
    if ($('mvAutoAdvance').checked) seek(m.frame + Number($('mvAdvanceBy').value || 1));
  });
  $('mvFile').addEventListener('change', e => { const f = e.target.files[0]; if (f) loadVideo(f).catch(err => status('エラー: ' + err.message)); e.target.value = ''; });
  $('mvPlay').onclick = () => (video.paused ? play() : pause());
  $('mvPrev').onclick = () => { if (!video.paused) pause(); seek(m.frame - 1); };
  $('mvNext').onclick = () => { if (!video.paused) pause(); seek(m.frame + 1); };
  $('mvPrev10').onclick = () => { if (!video.paused) pause(); seek(m.frame - 10); };
  $('mvNext10').onclick = () => { if (!video.paused) pause(); seek(m.frame + 10); };
  $('mvSlider').addEventListener('input', e => { if (!video.paused) pause(); seek(Number(e.target.value)); });
  $('mvFps').addEventListener('change', () => { if (m.loaded) { m.ref.video.fps = fps(); m.ref.video.frameCount = M.frameCountFor(video.duration, fps()); m.ref.video.fpsSource = 'user_entered'; $('mvSlider').max = total() - 1; seek(m.frame); renderLists(); } });
  $('mvRegion').addEventListener('change', e => { m.ref.region = M.REGIONS[e.target.value].slice(); draw(); });
  $('mvRate').addEventListener('change', e => { video.playbackRate = Number(e.target.value); });
  for (const id of ['mvMode', 'mvAlpha', 'mvScale', 'mvOffset', 'mvTrails', 'mvGhost', 'mvSync', 'mvJoint']) $(id).addEventListener('input', draw);
  $('mvAddPhase').onclick = () => { M.setPhase(m.ref, m.frame, $('mvPhase').value, $('mvSide').value, $('mvConf').value); renderLists(); draw(); };
  $('mvDelAnchor').onclick = () => { M.removeAnchor(m.ref, m.frame, $('mvJoint').value); renderLists(); draw(); };
  $('mvBuildCycle').onclick = () => buildCycle();
  $('mvExport').onclick = exportJSON;
  $('mvImport').addEventListener('change', async e => {
    const f = e.target.files[0]; e.target.value = ''; if (!f) return;
    try { applyImported(M.parse(await f.text()), f.name); } catch (err) { status('JSONエラー: ' + err.message); }
  });
  $('mvLoadRepoRef').onclick = async () => {
    try { const r = await fetch('motion/grid_overlay_walk.reference.json'); applyImported(M.parse(await r.text()), 'Grid Overlay参照JSON'); }
    catch (err) { status('参照JSONを取得できません（HTTPサーバー経由で開いてください）: ' + err.message); }
  };
  $('mvTimeline').addEventListener('pointerdown', e => { const r = tl.getBoundingClientRect(); if (!video.paused) pause(); seek((e.clientX - r.left) / r.width * (total() - 1)); });
  document.addEventListener('keydown', e => {
    if (!m.loaded || /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)) return;
    if (e.key === ',') { e.preventDefault(); seek(m.frame - 1); } else if (e.key === '.') { e.preventDefault(); seek(m.frame + 1); }
  });
  // Keep the comparison sprite in step with studio edits (view/frame/layers).
  if (S.onDraw) S.onDraw(() => { if (video.paused) draw(); });

  for (const p of M.PHASES) $('mvPhase').append(new Option(p, p));
  for (const s of M.SIDES) $('mvSide').append(new Option(s, s));
  for (const j of M.JOINTS) $('mvJoint').append(new Option(j, j));
  for (const n of M.SAMPLE_COUNTS) $('mvCount').append(new Option(`${n}コマ`, n));
  $('mvCount').value = 8;
  renderLists(); draw();
  window.MotionStudio = { get ref() { return m.ref; }, get frame() { return m.frame; }, seek, cv };
})();
