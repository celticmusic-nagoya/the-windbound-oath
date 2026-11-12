'use strict';
// MORWEN-LAYER-05: data-driven layer/canon viewer. Read-only: never writes, resizes or mirrors any image.
const ROOT = '../../../';
const TEMPLATE = 'morwen.layer-template.json';
const VIEWS = ['front', 'back', 'left', 'right'];
const VIEW_JA = { front: '正面', back: '背面', left: '左向き', right: '右向き' };
const $ = id => document.getElementById(id);
const st = { t: null, view: 'front', canon: {}, layers: {}, on: { L0: true, L1: true, L2: true, L3: true } };

async function sha256(buf) {
  const d = await crypto.subtle.digest('SHA-256', buf);
  return [...new Uint8Array(d)].map(x => x.toString(16).padStart(2, '0')).join('');
}
async function loadImage(path, expectSha) {
  try {
    const r = await fetch(ROOT + path, { cache: 'no-store' });
    if (!r.ok) return { status: 'BLOCKED', detail: `HTTP ${r.status}` };
    const buf = await r.arrayBuffer();
    const hash = await sha256(buf);
    if (expectSha && hash !== expectSha) return { status: 'FAIL', detail: 'SHA不一致', hash };
    const img = await createImageBitmap(new Blob([buf]));
    return { status: 'PASS', img, hash, w: img.width, h: img.height };
  } catch (e) { return { status: 'BLOCKED', detail: String(e) }; }
}
function alphaCheck(img) {
  const c = new OffscreenCanvas(img.width, img.height), x = c.getContext('2d');
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, img.width, img.height).data, W = img.width, H = img.height;
  let zero = 0, border = 0;
  for (let i = 3; i < d.length; i += 4) if (d[i] === 0) zero++;
  for (let px = 0; px < W; px++) border |= d[px * 4 + 3] | d[((H - 1) * W + px) * 4 + 3];
  for (let py = 0; py < H; py++) border |= d[(py * W) * 4 + 3] | d[(py * W + W - 1) * 4 + 3];
  return { zero, border: border !== 0 };
}
async function loadSlot(layer, view) {
  const slot = layer.views[view];
  if (!slot || !slot.image) return { status: 'BLOCKED', detail: slot && slot.reason || 'NOT_DELIVERED' };
  const r = await loadImage(slot.image.path, slot.image.sha256);
  if (r.status !== 'PASS') return r;
  const cv = st.t.canvas;
  if (r.w !== cv.width || r.h !== cv.height) return { ...r, status: 'FAIL', detail: `寸法 ${r.w}×${r.h}` };
  const a = alphaCheck(r.img);
  if (!a.zero) return { ...r, status: 'FAIL', detail: '透明画素なし' };
  if (a.border) return { ...r, status: 'FAIL', detail: '外周が透明でない' };
  return { ...r, detail: '寸法・透過・SHA一致' };
}
function badge(status, text) { return `<span class="b ${status}">${text || status}</span>`; }

function draw() {
  const t = st.t, v = st.view, cv = $('cv'), x = cv.getContext('2d');
  x.setTransform(1, 0, 0, 1, 0, 0); x.clearRect(0, 0, cv.width, cv.height);
  for (const L of t.layers) {
    const s = st.layers[L.id + ':' + v];
    if (st.on[L.id] && s && s.status === 'PASS') x.drawImage(s.img, 0, 0);
  }
  const c = st.canon[v];
  if ($('canonOn').checked && c && c.status === 'PASS') {
    const [a, b, cc, d, tx, ty] = t.views[v].canonToCanvas.matrix;
    x.save(); x.globalAlpha = $('canonAlpha').value / 100; x.setTransform(a, b, cc, d, tx, ty); x.drawImage(c.img, 0, 0); x.restore();
  }
  x.lineWidth = 2;
  if ($('gGround').checked) { x.strokeStyle = '#ff8c00'; x.beginPath(); x.moveTo(0, t.ground.y + .5); x.lineTo(cv.width, t.ground.y + .5); x.stroke(); }
  if ($('gCenter').checked) { x.strokeStyle = '#ff4fa3'; x.setLineDash([12, 8]); x.beginPath(); x.moveTo(t.ground.centerX + .5, 0); x.lineTo(t.ground.centerX + .5, cv.height); x.stroke(); x.setLineDash([]); }
  if ($('gAnchor').checked) {
    x.fillStyle = '#e63946'; x.beginPath(); x.arc(t.ground.centerX, t.ground.y, 7, 0, 7); x.fill();
    if (t.anchors.status === 'UNRESOLVED') { x.font = '28px sans-serif'; x.fillText('関節アンカー: UNRESOLVED', 24, 48); }
  }
}
function renderPanels() {
  const t = st.t, v = st.view, vw = t.views[v];
  $('views').innerHTML = VIEWS.map(k => `<button data-v="${k}" aria-pressed="${k === v}">${VIEW_JA[k]}</button>`).join('');
  $('layers').innerHTML = t.layers.map(L => {
    const s = st.layers[L.id + ':' + v] || { status: 'NOT_RUN' };
    return `<label><input type="checkbox" data-l="${L.id}" ${st.on[L.id] ? 'checked' : ''}> ${L.id} ${L.label} ${badge(s.status)} <small>${s.detail || ''}</small></label>`;
  }).join('');
  const c = st.canon[v] || { status: 'NOT_RUN' };
  $('canonBadge').className = 'b ' + c.status; $('canonBadge').textContent = c.status === 'PASS' ? 'SHA一致' : (c.detail || c.status);
  const dd = vw.dimensionDiff;
  const rows = [
    ['キャンバス', `${t.canvas.width}×${t.canvas.height}（${t.canvas.basis}）`],
    ['正本', `${vw.canonSource.path.split('/').pop()} ${dd.source.join('×')} ${vw.canonSource.mode} ${badge(c.status, c.status === 'PASS' ? 'SHA一致' : c.status)}`],
    ['寸法差', `倍率 ${dd.uniformScale}・${dd.exactFit ? '完全一致' : '非一致（拡大で配置）'}・α ${dd.sourceHasAlpha ? 'あり' : 'なし'}`],
    ['変換', `[${vw.canonToCanvas.matrix.join(', ')}] ${badge('NOT_RUN', vw.canonToCanvas.classification)}`],
    ['接地', `変換後 (${vw.canonToCanvas.contactAfterTransform.join(', ')}) → 基準 (${t.ground.centerX}, ${t.ground.y})`],
    ['方向ID', `${vw.directionId}（${vw.facing}）`],
    ...t.layers.map(L => { const s = st.layers[L.id + ':' + v] || {}; return [L.id, `${badge(s.status || 'NOT_RUN')} ${s.hash ? s.hash.slice(0, 12) + '…' : ''} ${s.detail || ''}`]; })
  ];
  $('info').innerHTML = rows.map(r => `<tr><td>${r[0]}</td><td>${r[1]}</td></tr>`).join('');
  const VJ = { MATCH: ['NOT_RUN', '一致（推定・要確認）'], MISMATCH: ['BLOCKED', '不一致・修正待ち'], NOT_VISIBLE_OCCLUSION_POSSIBLE: ['BLOCKED', '見えない・遮蔽の可能性'] };
  $('asym').innerHTML = t.asymmetry.map(a => {
    const e = a.views[v], [s, txt] = VJ[e.verdict] || ['FAIL', e.verdict];
    return `<tr><td>${a.label}<br>${badge(s, txt)}</td><td>想定: ${e.expected}<br>正本: ${e.observed}</td></tr>`;
  }).join('') + `<tr><td colspan="2"><small>観察はAIの目視（ESTIMATED）。見えない装備は反対側にあると推定しない。左右反転での流用は禁止。</small></td></tr>`;
}
function overall() {
  const all = [...Object.values(st.canon), ...Object.values(st.layers)].map(s => s.status);
  if (st.t.anchors.status === 'UNRESOLVED') all.push('BLOCKED');
  const o = all.includes('FAIL') ? 'FAIL' : all.includes('BLOCKED') ? 'BLOCKED' : all.includes('NOT_RUN') ? 'NOT_RUN' : 'PASS';
  $('overall').className = 'b ' + o; $('overall').textContent = o;
}
function refresh() { renderPanels(); draw(); overall(); }

async function init() {
  const r = await fetch(TEMPLATE, { cache: 'no-store' });
  st.t = await r.json();
  for (const v of VIEWS) {
    const cs = st.t.views[v].canonSource;
    st.canon[v] = await loadImage(cs.path, cs.sha256);
    for (const L of st.t.layers) st.layers[L.id + ':' + v] = await loadSlot(L, v);
  }
  $('views').onclick = e => { const b = e.target.closest('button[data-v]'); if (b) { st.view = b.dataset.v; refresh(); } };
  $('layers').onchange = e => { const c = e.target.closest('input[data-l]'); if (c) { st.on[c.dataset.l] = c.checked; draw(); } };
  for (const id of ['canonOn', 'gGround', 'gCenter', 'gAnchor']) $(id).onchange = draw;
  $('canonAlpha').oninput = () => { $('canonAlphaV').textContent = $('canonAlpha').value; draw(); };
  refresh();
  window.__layerTemplateState = { overall: $('overall').textContent, canon: Object.fromEntries(VIEWS.map(v => [v, st.canon[v].status])), layers: Object.fromEntries(Object.entries(st.layers).map(([k, s]) => [k, s.status])) };
}
init().catch(e => { $('overall').className = 'b FAIL'; $('overall').textContent = '読込失敗: ' + e; });
