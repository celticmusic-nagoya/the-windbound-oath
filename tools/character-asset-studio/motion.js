'use strict';
/* Character Asset Studio v0.4 — Motion Reference panel (UI). Pure logic: motion-core.js (window.MotionCore).
 * Reference videos stay on the device (object URL). Only timings/anchors/SHA-256 are exported, as UNAPPROVED_REFERENCE.
 * Nothing here writes to the studio's BASE_BODY_SPEC landmarks, sprite layers or any canonical asset.
 * Missing sprite frames are never generated: they are shown as 未登録, or (opt-in) as a labelled 仮表示 reuse. */
(function () {
  const M = window.MotionCore;
  const S = window.Studio;              // exposed by app.js (read-only use)
  const $ = id => document.getElementById(id);
  const video = $('mvVideo');
  const cv = $('mvCanvas'), cx = cv.getContext('2d', { willReadFrequently: true });
  const tl = $('mvTimeline'), tx = tl.getContext('2d');
  const JOINT_COLORS = { head: '#f5d76e', shoulder: '#ff9f43', elbow: '#ee5a24', wrist: '#ff6b81', hip: '#7bed9f', knee_L: '#70a1ff', knee_R: '#a29bfe', ankle_L: '#1e90ff', ankle_R: '#be2edd', toe_L: '#00d2d3', toe_R: '#e056fd' };
  const PHASE_COLORS = { contact: '#ff6b6b', down: '#feca57', passing: '#48dbfb', up: '#1dd1a1', push_off: '#c8d6e5' };
  const CAND_COLORS = { leg_spread_max: '#8da4c4', leg_spread_min: '#5b6f8c' };
  const CAND_LABELS = { leg_spread_max: '脚の開き幅 極大', leg_spread_min: '脚の開き幅 極小' };
  const VGROUND = '#4fd1e8', SGROUND = '#f08a4b';
  const m = { ref: M.createRef(), frame: 0, url: null, loaded: false, vbox: null, sbox: null, vGroundY: null, sGroundY: null, seekToken: 0, refCheck: null, pendingRef: null, cropKey: '', crop: null };
  const sprite = document.createElement('canvas'), sx = sprite.getContext('2d', { willReadFrequently: true });

  const fps = () => Math.max(1, Number($('mvFps').value) || 24);
  const total = () => m.ref.video.frameCount || 1;
  const regionOf = () => m.ref.region;
  const num = id => Number($(id).value);
  function status(t) { $('mvStatus').textContent = t; }
  function hex(buf) { return [...new Uint8Array(buf)].map(x => x.toString(16).padStart(2, '0')).join(''); }

  /* ---------- canvas layout: landscape on desktop, taller on narrow screens ---------- */
  function layoutCanvas() {
    const narrow = window.innerWidth <= 670;
    const [w, h] = narrow ? [720, 640] : [960, 540];
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
  }

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
  function play() { if (!m.loaded) return; video.playbackRate = num('mvRate'); video.play().then(playLoop); $('mvPlay').textContent = '❚❚ 一時停止'; }
  function pause() { video.pause(); $('mvPlay').textContent = '▶ 再生'; seek(M.timeToFrame(video.currentTime, fps())); }

  /* ---------- sprite (from the studio, guides off; viewing only) ---------- */
  function registeredFrames() {
    const st = S.state;
    return [...new Set(st.items.filter(it => it.view === st.view && it.visible).map(it => it.frame))].sort((a, b) => a - b);
  }
  function spriteFor(frame) {
    const st = S.state, keep = st.frame;
    sprite.width = S.W(); sprite.height = S.H();
    st.frame = frame;
    S.paint(sx, { guides: false, background: false, transparent: true });
    st.frame = keep;
    return sprite;
  }
  function alphaBox(c) {
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data, w = c.width, h = c.height;
    let x0 = w, y0 = h, x1 = -1, y1 = -1;
    for (let y = 0; y < h; y += 2) for (let x = 0; x < w; x += 2) if (d[(y * w + x) * 4 + 3] > 8) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    return x1 < 0 ? null : [x0, y0, x1 + 2, y1 + 2];
  }
  // Content crop shared by every frame of the current view (consistent scale), always including the ground line.
  function spriteCrop() {
    const st = S.state, reg = registeredFrames();
    const g = st.landmarks[st.view].ground.n, gy = Math.round(g[1] * S.H());
    const key = [st.view, S.W(), S.H(), gy, reg.join(','), st.items.length, st.items.filter(i => i.visible).length].join('|');
    if (key === m.cropKey) return m.crop;
    const u = M.unionBox(reg.map(f => alphaBox(spriteFor(f))), gy);
    let crop = [0, 0, S.W(), S.H()];
    if (u) {
      const pad = Math.round(0.04 * (u[3] - u[1]));
      crop = [Math.max(0, u[0] - pad), Math.max(0, u[1] - pad), Math.min(S.W(), u[2] + pad), Math.min(S.H(), u[3] + pad)];
    }
    m.cropKey = key; m.crop = { x: crop[0], y: crop[1], w: crop[2] - crop[0], h: crop[3] - crop[1], groundY: gy };
    return m.crop;
  }
  function syncedSpriteFrame() {
    if (!$('mvSync').checked) return S.state.frame;
    const c = M.cycles(m.ref).find(c => m.frame >= c.start && m.frame < c.end);
    if (!c) return S.state.frame;
    return Math.floor((m.frame - c.start) / c.length * S.frames()) % S.frames();
  }
  // Which image to show for a sprite frame: registered, reused (provisional) or missing. Never generated.
  function resolveSprite(frame) {
    // spriteSource(i, n, spriteFrames): with n === spriteFrames, sample i maps to sprite frame i.
    return M.spriteSource(frame, S.frames(), S.frames(), registeredFrames(), $('mvReuse').checked);
  }
  function drawSpriteInto(ctx, area, src, scale, offX, offY, alpha) {
    const crop = spriteCrop();
    const base = M.fitBox(crop.w, crop.h, area.x, area.y, area.w, area.h);
    const w = base.w * scale, h = base.h * scale;
    const box = { x: base.x + (base.w - w) / 2 + offX, y: base.y + base.h - h + offY, w, h };
    if (src.source != null) {
      const sp = spriteFor(src.source);
      ctx.save(); ctx.globalAlpha = alpha;
      ctx.drawImage(sp, crop.x, crop.y, crop.w, crop.h, box.x, box.y, box.w, box.h);
      ctx.restore();
    }
    const groundY = box.y + (crop.groundY - crop.y) / crop.h * box.h;
    stateLabel(ctx, area, src);
    return { box, groundY };
  }
  function stateLabel(ctx, area, src) {
    if (src.state === 'registered') return;
    const fs = Math.max(11, Math.round(area.w / 13));
    ctx.save(); ctx.textAlign = 'center'; ctx.font = `bold ${fs}px system-ui`;
    if (src.state === 'missing') {
      ctx.fillStyle = '#0a1018cc'; ctx.fillRect(area.x + area.w * 0.1, area.y + area.h / 2 - fs * 1.4, area.w * 0.8, fs * 2.6);
      ctx.fillStyle = '#c6d0df'; ctx.fillText('未登録', area.x + area.w / 2, area.y + area.h / 2);
      ctx.font = `${Math.round(fs * 0.62)}px system-ui`; ctx.fillStyle = '#8d9bb0';
      ctx.fillText(`sprite f${src.frame}`, area.x + area.w / 2, area.y + area.h / 2 + fs * 0.85);
    } else {
      ctx.fillStyle = '#e0a43a'; ctx.fillRect(area.x + 4, area.y + 4, area.w - 8, fs * 1.5);
      ctx.fillStyle = '#1b1406'; ctx.fillText(`仮表示 f${src.frame}←f${src.source}`, area.x + area.w / 2, area.y + 4 + fs * 1.1);
      ctx.strokeStyle = '#e0a43a'; ctx.setLineDash([8, 6]); ctx.lineWidth = 2; ctx.strokeRect(area.x + 2, area.y + 2, area.w - 4, area.h - 4); ctx.setLineDash([]);
    }
    ctx.restore();
  }

  /* ---------- drawing ---------- */
  function drawVideoRegion(ctx, box) {
    const [rx, ry, rw, rh] = regionOf();
    ctx.drawImage(video, rx * video.videoWidth, ry * video.videoHeight, rw * video.videoWidth, rh * video.videoHeight, box.x, box.y, box.w, box.h);
  }
  function videoAspect() { const [, , rw, rh] = regionOf(); return [rw * (video.videoWidth || 16), rh * (video.videoHeight || 9)]; }
  function videoBoxIn(area, scale, offY) {
    const [aw, ah] = videoAspect(), base = M.fitBox(aw, ah, area.x, area.y, area.w, area.h);
    const w = base.w * scale, h = base.h * scale;
    return { x: base.x + (base.w - w) / 2, y: base.y + base.h - h + offY, w, h };
  }
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
  function hline(ctx, y, x0, x1, color, dash) { ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.setLineDash(dash); ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke(); ctx.restore(); }
  function draw() {
    layoutCanvas();
    const Wc = cv.width, Hc = cv.height, mode = $('mvMode').value, half = mode === 'side';
    const vArea = { x: 0, y: 0, w: half ? Wc / 2 : Wc, h: Hc }, sArea = half ? { x: Wc / 2, y: 0, w: Wc / 2, h: Hc } : vArea;
    cx.fillStyle = '#0a1018'; cx.fillRect(0, 0, Wc, Hc);
    m.vbox = videoBoxIn(vArea, num('mvVScale') / 100, num('mvVOffY') / 100 * Hc);
    cx.save(); cx.beginPath(); cx.rect(vArea.x, vArea.y, vArea.w, vArea.h); cx.clip();
    if (m.loaded) drawVideoRegion(cx, m.vbox);
    else { cx.fillStyle = '#7d8ea5'; cx.font = `${Math.round(vArea.w / 20)}px system-ui`; cx.textAlign = 'center'; cx.fillText('参考動画（MP4）を読み込んでください', vArea.x + vArea.w / 2, Hc / 2); cx.textAlign = 'left'; }
    cx.restore();
    m.vGroundY = m.vbox.y + num('mvVGround') / 100 * m.vbox.h;
    const sf = syncedSpriteFrame(), src = resolveSprite(sf);
    cx.save(); cx.beginPath(); cx.rect(sArea.x, sArea.y, sArea.w, sArea.h); cx.clip();
    const r = drawSpriteInto(cx, sArea, src, num('mvScale') / 100, num('mvOffset') / 100 * sArea.w, num('mvSOffY') / 100 * Hc, half ? 1 : num('mvAlpha') / 100);
    cx.restore();
    m.sbox = r.box; m.sGroundY = r.groundY; m.spriteState = src;
    if (half) { cx.strokeStyle = '#394354'; cx.beginPath(); cx.moveTo(Wc / 2 + .5, 0); cx.lineTo(Wc / 2 + .5, Hc); cx.stroke(); }
    hline(cx, m.vGroundY, vArea.x, vArea.x + vArea.w, VGROUND, [10, 5]);
    hline(cx, m.sGroundY, sArea.x, sArea.x + sArea.w, SGROUND, [4, 4]);
    if (m.loaded) drawAnchors(cx, m.vbox, m.frame, $('mvTrails').checked);
    const ph = m.ref.phases.find(p => p.frame === m.frame);
    const cands = m.ref.candidates.filter(c => c.frame === m.frame);
    const fsz = Math.round(Wc / 55);
    let text = `F${m.frame} ${M.timecode(m.frame, fps())}`;
    if (ph) text += ` · ${ph.phase}(${ph.side})${ph.phase === 'contact' ? (M.isConfirmed(ph) ? ' 確定' : ' 候補') : ''}`;
    if (cands.length) text += ' · ' + cands.map(c => CAND_LABELS[c.kind]).join('/');
    cx.font = `${fsz}px system-ui`;
    cx.fillStyle = '#000b'; cx.fillRect(6, 6, Math.min(vArea.w - 12, cx.measureText(text).width + 16), fsz * 1.8);
    cx.fillStyle = '#fff'; cx.fillText(text, 14, 6 + fsz * 1.25);
    $('mvFrameLabel').textContent = `${m.frame} / ${Math.max(0, total() - 1)}`;
    $('mvSlider').value = m.frame;
    for (const [id, fmt] of [['mvAlpha', v => v + '%'], ['mvVScale', v => v + '%'], ['mvVOffY', v => v], ['mvVGround', v => v + '%'], ['mvScale', v => v + '%'], ['mvSOffY', v => Number(v).toFixed(1)], ['mvOffset', v => v]])
      $(id + 'Out').textContent = fmt($(id).value);
    drawTimeline();
  }
  function drawTimeline() {
    const Wt = tl.width, Ht = tl.height, n = Math.max(1, total() - 1);
    tx.fillStyle = '#0e1622'; tx.fillRect(0, 0, Wt, Ht);
    for (const c of M.cycles(m.ref)) { tx.fillStyle = c.side === 'B' || c.side === 'R' ? '#2f3e5a' : '#3a4b2f'; tx.fillRect(c.start / n * Wt, Ht - 6, c.length / n * Wt, 6); }
    for (const c of m.ref.candidates) { tx.fillStyle = CAND_COLORS[c.kind]; tx.fillRect(c.frame / n * Wt - 1, c.kind === 'leg_spread_max' ? 4 : Ht - 14, 2, 8); }
    for (const p of m.ref.phases) {
      const x = p.frame / n * Wt;
      if (p.phase === 'contact' && !M.isConfirmed(p)) { tx.strokeStyle = PHASE_COLORS.contact; tx.setLineDash([3, 2]); tx.lineWidth = 2; tx.beginPath(); tx.moveTo(x, 2); tx.lineTo(x, Ht - 8); tx.stroke(); tx.setLineDash([]); }
      else { tx.fillStyle = PHASE_COLORS[p.phase]; tx.fillRect(x - 1.5, p.phase === 'contact' ? 2 : 10, 3, p.phase === 'contact' ? Ht - 10 : Ht - 18); }
    }
    for (const f of Object.keys(m.ref.anchors)) { tx.fillStyle = '#fff'; tx.fillRect(Number(f) / n * Wt - .5, 0, 1, 4); }
    tx.fillStyle = '#e6b772'; tx.fillRect(m.frame / n * Wt - 1, 0, 2, Ht);
  }

  /* ---------- lists / stats ---------- */
  function badge(text, cls) { const b = document.createElement('span'); b.className = 'mvbadge ' + cls; b.textContent = text; return b; }
  function renderLists() {
    const list = $('mvPhaseList'); list.replaceChildren();
    const rows = [...m.ref.phases.map(p => ({ t: 'phase', frame: p.frame, p })), ...m.ref.candidates.map(c => ({ t: 'cand', frame: c.frame, c }))].sort((a, b) => a.frame - b.frame || (a.t === 'phase' ? -1 : 1));
    for (const r of rows) {
      const row = document.createElement('div'); row.className = 'layeritem'; row.dataset.kind = r.t;
      const go = document.createElement('button'); go.textContent = `F${r.frame}`; go.onclick = () => seek(r.frame);
      const sp = document.createElement('span');
      if (r.t === 'phase') {
        const p = r.p; sp.textContent = `${p.phase} · ${p.side} · ${p.confidence}`; sp.style.color = PHASE_COLORS[p.phase];
        if (p.phase === 'contact') sp.append(M.isConfirmed(p) ? badge('目視確定', 'ok') : badge('候補（未確定）', 'cand'));
      } else { sp.textContent = CAND_LABELS[r.c.kind]; sp.style.color = CAND_COLORS[r.c.kind]; sp.append(badge('解析マーカー', 'mark')); }
      const del = document.createElement('button'); del.textContent = '×'; del.setAttribute('aria-label', `F${r.frame}を削除`);
      del.onclick = () => { if (r.t === 'phase') M.removePhase(m.ref, r.frame); else M.removeCandidate(m.ref, r.frame, r.c.kind); renderLists(); draw(); };
      row.append(go, sp, del); list.append(row);
    }
    const cyc = M.cycles(m.ref), sel = $('mvCycle'), keep = sel.value; sel.replaceChildren();
    const conf = f => { const p = m.ref.phases.find(x => x.frame === f); return p && M.isConfirmed(p); };
    cyc.forEach((c, i) => sel.append(new Option(`#${i + 1} F${c.start}→F${c.end}（${c.length}コマ・${c.side}${c.sideAssumed ? '・交互仮定' : ''}${conf(c.start) && conf(c.end) ? '' : '・接地未確定'}）`, i)));
    if (keep && Number(keep) < cyc.length) sel.value = keep;
    const s = M.stats(m.ref), contacts = m.ref.phases.filter(p => p.phase === 'contact');
    $('mvStats').textContent = `未承認の参考値 · 接地 ${contacts.length}（目視確定 ${contacts.filter(M.isConfirmed).length}・候補 ${contacts.filter(p => !M.isConfirmed(p)).length}）· 解析マーカー ${m.ref.candidates.length} · 1歩 平均${s.meanStepFrames ?? '—'}コマ · 1周期 平均${s.meanCycleFrames ?? '—'}コマ（動画fps換算 ${s.meanCycleSecondsAtVideoFps ?? '—'}秒）· アンカー記録 ${Object.keys(m.ref.anchors).length}フレーム`;
  }

  /* ---------- cycle comparison (6 / 8 / 12) ---------- */
  async function buildCycle() {
    const cyc = M.cycles(m.ref)[num('mvCycle')];
    const grid = $('mvCycleGrid'); grid.replaceChildren(); delete grid.dataset.count;
    if (!cyc) { grid.textContent = '同じ側の接地（contact）を2つ以上登録すると周期が作れます。'; $('mvCycleInfo').textContent = ''; return; }
    const n = num('mvCount'), frames = M.sampleCycle(cyc.start, cyc.end, n), keep = m.frame, reg = registeredFrames(), reuse = $('mvReuse').checked;
    const counts = { registered: 0, reused: 0, missing: 0 };
    grid.style.setProperty('--n', n);
    for (let i = 0; i < n; i++) {
      const src = M.spriteSource(i, n, S.frames(), reg, reuse); counts[src.state]++;
      const cell = document.createElement('figure'); cell.className = 'mvcell';
      Object.assign(cell.dataset, { state: src.state, spriteFrame: src.frame, sourceFrame: src.source ?? '', videoFrame: frames[i] });
      const c = document.createElement('canvas'); c.width = 200; c.height = 400; const g = c.getContext('2d');
      g.fillStyle = '#0a1018'; g.fillRect(0, 0, 200, 400);
      const vArea = { x: 0, y: 0, w: 200, h: 200 }, sArea = { x: 0, y: 200, w: 200, h: 200 };
      if (m.loaded) {
        await seek(frames[i]);
        const vb = videoBoxIn(vArea, 1, 0);
        drawVideoRegion(g, vb); drawAnchors(g, vb, frames[i], false);
        hline(g, vb.y + num('mvVGround') / 100 * vb.h, 0, 200, VGROUND, [6, 4]);
      }
      g.fillStyle = '#121a26'; g.fillRect(0, 200, 200, 200);
      const r = drawSpriteInto(g, sArea, src, 1, 0, 0, 1);
      hline(g, r.groundY, 0, 200, SGROUND, [3, 3]);
      const cap = document.createElement('figcaption');
      cap.textContent = `${i + 1}/${n} · 動画F${frames[i]} · ` + (src.state === 'registered' ? `sprite f${src.frame}` : src.state === 'reused' ? `sprite f${src.frame}: 仮表示（f${src.source}を再利用・素材ではない）` : `sprite f${src.frame}: 未登録`);
      cell.append(c, cap); grid.append(cell);
    }
    $('mvCycleInfo').textContent = `比較枠 ${n} · 登録済みスプライト ${reg.length} / ${S.frames()} フレーム（${S.state.view}） · この比較で登録済み ${counts.registered} 枠 · 未登録 ${counts.missing} 枠 · 仮表示 ${counts.reused} 枠` +
      (counts.reused ? ' — 仮表示は既存フレームの再利用で、アニメーション素材ではありません' : '') + ' · 周期 F' + cyc.start + '→F' + cyc.end + (cyc.sideAssumed ? '（交互仮定）' : '');
    grid.dataset.registered = counts.registered; grid.dataset.missing = counts.missing; grid.dataset.reused = counts.reused;
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
    if (!m.loaded) { m.pendingRef = ref; m.ref = ref; $('mvFps').value = ref.video.fps; $('mvRegion').value = regionName(ref.region); status(`${label}: 読み込み済み（未承認の参考値・接地は候補）。対応する動画を読み込むとSHA-256を照合します。`); }
    else { ref.video.name = m.ref.video.name; m.ref = ref; $('mvFps').value = ref.video.fps; $('mvRegion').value = regionName(ref.region); status(`${label}: 適用（SHA-256一致・未承認の参考値・接地は候補）`); }
    $('mvSlider').max = total() - 1; renderLists(); draw();
    document.body.dataset.mvImported = String(Date.now());
  }
  function regionName(r) { for (const [k, v] of Object.entries(M.REGIONS)) if (v.every((x, i) => Math.abs(x - r[i]) < 1e-6)) return k; return 'full'; }

  /* ---------- input ---------- */
  function canvasPoint(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * cv.width, (e.clientY - r.top) / r.height * cv.height]; }
  cv.addEventListener('pointerdown', e => {
    if (!m.loaded || !$('mvRecord').checked) return;
    const [x, y] = canvasPoint(e), b = m.vbox, half = $('mvMode').value === 'side';
    if (x < b.x || x > b.x + b.w || y < b.y || y > b.y + b.h || (half && x > cv.width / 2)) return;
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
  for (const id of ['mvMode', 'mvAlpha', 'mvScale', 'mvOffset', 'mvSOffY', 'mvVScale', 'mvVOffY', 'mvVGround', 'mvTrails', 'mvGhost', 'mvSync', 'mvReuse', 'mvJoint']) $(id).addEventListener('input', draw);
  // Align: move only the sprite vertically so its ground line meets the video foot line (display only).
  $('mvAlignGround').onclick = () => {
    draw();
    const cur = num('mvSOffY'), deltaPct = (m.vGroundY - m.sGroundY) / cv.height * 100;
    $('mvSOffY').value = Math.max(-50, Math.min(50, Math.round((cur + deltaPct) * 10) / 10));
    draw();
  };
  $('mvResetView').onclick = () => {
    for (const [id, v] of [['mvVScale', 100], ['mvVOffY', 0], ['mvVGround', 95], ['mvScale', 100], ['mvSOffY', 0], ['mvOffset', 0], ['mvAlpha', 55]]) $(id).value = v;
    draw();
  };
  $('mvAddPhase').onclick = () => {
    const v = $('mvPhase').value;
    if (M.CANDIDATE_KINDS.includes(v)) M.setCandidate(m.ref, m.frame, v, 'manual_mark');
    else M.setPhase(m.ref, m.frame, v, $('mvSide').value, $('mvConf').value);
    renderLists(); draw();
  };
  $('mvConfirm').onclick = () => {
    const p = m.ref.phases.find(x => x.frame === m.frame && x.phase === 'contact');
    if (!p) { status(`F${m.frame} に接地（contact）が登録されていません。`); return; }
    M.confirmPhase(m.ref, m.frame, !M.isConfirmed(p));
    status(`F${m.frame} の接地を${M.isConfirmed(p) ? '目視確定にしました（全体は未承認の参考値のまま）' : '候補（未確定）に戻しました'}`);
    renderLists(); draw();
  };
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
  window.addEventListener('resize', () => { if (video.paused) draw(); });
  // Keep the comparison sprite in step with studio edits (view/frame/layers).
  if (S.onDraw) S.onDraw(() => { if (video.paused) draw(); });

  for (const p of M.PHASES) $('mvPhase').append(new Option(p === 'contact' ? 'contact（接地・候補として登録）' : p, p));
  const og = document.createElement('optgroup'); og.label = '解析マーカー（接地とは別）';
  for (const k of M.CANDIDATE_KINDS) og.append(new Option(CAND_LABELS[k], k));
  $('mvPhase').append(og);
  for (const s of M.SIDES) $('mvSide').append(new Option(s, s));
  for (const j of M.JOINTS) $('mvJoint').append(new Option(j, j));
  for (const n of M.SAMPLE_COUNTS) $('mvCount').append(new Option(`${n}コマ`, n));
  $('mvCount').value = 8;
  renderLists(); draw();
  window.MotionStudio = { get ref() { return m.ref; }, get frame() { return m.frame; }, get vbox() { return m.vbox; }, get sbox() { return m.sbox; },
    get vGroundY() { return m.vGroundY; }, get sGroundY() { return m.sGroundY; }, get spriteState() { return m.spriteState; }, seek, cv, registeredFrames };
})();
