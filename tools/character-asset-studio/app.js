'use strict';
/* Character Asset Studio v0.3 — UI layer (v0.2 behaviour unchanged; v0.3 adds motion.js). Pure logic lives in studio-core.js (window.StudioCore). */
const C = window.StudioCore;
const VIEWS = C.VIEWS;
const LAYERS = ['body', 'underlayer', 'legs', 'bottom', 'top', 'outer', 'arms', 'head', 'props', 'reference'];
const CANON_DIR = '../../assets/candidates/morwen/final-visual-canon-20261111/';
// Fallback when profiles/*.json cannot be fetched (e.g. opened via file://).
const FALLBACK_PRESETS = [{ id: 'MORWEN_REAL_1200x1600', label: 'Morwen real-proportion master 1200×1600', canvas: [1200, 1600], ground: [0.5, 0.9625], frames: 12, pixelsPerUnit: null }];
const $ = id => document.getElementById(id);

const state = {
  presets: FALLBACK_PRESETS, preset: FALLBACK_PRESETS[0], view: 'front', frame: 0, items: [],
  landmarks: C.templateLandmarks(), selected: null, playing: false, qa: null,
  constraints: null, reviewed: {}, references: null
};
const canvas = $('canvas');
const ctx = canvas.getContext('2d', { willReadFrequently: true });
let timer = null, drag = null;
const drawListeners = [];

const W = () => state.preset.canvas[0];
const H = () => state.preset.canvas[1];
const frames = () => state.preset.frames;

function saveBlob(blob, name) {
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name;
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1500);
}
function saveText(text, name) { saveBlob(new Blob([text], { type: 'application/json' }), name); }
async function sha256(buf) { const d = await crypto.subtle.digest('SHA-256', buf); return [...new Uint8Array(d)].map(x => x.toString(16).padStart(2, '0')).join(''); }

function drawBackground(c, checker) {
  c.fillStyle = '#e9edf1'; c.fillRect(0, 0, W(), H());
  if (!checker) return;
  const s = Math.max(4, Math.round(W() / 30));
  c.fillStyle = '#d9e0e8';
  for (let y = 0; y < H(); y += s) for (let x = 0; x < W(); x += s) if (((x + y) / s) % 2 === 0) c.fillRect(x, y, s, s);
}
function selectedItems() {
  return state.items.filter(it => it.view === state.view && it.frame === state.frame && it.visible)
    .sort((a, b) => LAYERS.indexOf(a.layer) - LAYERS.indexOf(b.layer));
}
function drawItem(c, it) {
  const p = C.placement(it.width, it.height, { width: W(), height: H() });
  c.imageSmoothingEnabled = !p.exact; c.imageSmoothingQuality = 'high';
  c.drawImage(it.image, p.x, p.y, p.w, p.h);
}
function paint(c, { guides = true, background = true, mask = false, transparent = false, excludeCanon = false } = {}) {
  c.clearRect(0, 0, W(), H());
  if (background && !transparent) drawBackground(c, $('checker').checked);
  c.save(); c.globalAlpha = Number($('opacity').value) / 100;
  // Canonical originals are read-only references: never baked into exported composites/masks.
  for (const it of selectedItems()) if (!(excludeCanon && it.canonical)) drawItem(c, it);
  c.restore();
  if (mask) {
    const img = c.getImageData(0, 0, W(), H()), d = img.data;
    for (let i = 0; i < d.length; i += 4) { d[i] = 43; d[i + 1] = 58; d[i + 2] = 76; }
    c.putImageData(img, 0, 0);
  }
  if (!guides || mask) return;
  const unit = W() / 1200;
  if ($('grid').checked) {
    const step = Math.max(4, Math.round(50 * unit));
    c.save(); c.lineWidth = Math.max(1, unit);
    for (let x = 0; x <= W(); x += step) { c.strokeStyle = (x / step) % 4 === 0 ? '#70879e99' : '#91a3b255'; c.beginPath(); c.moveTo(x + .5, 0); c.lineTo(x + .5, H()); c.stroke(); }
    for (let y = 0; y <= H(); y += step) { c.strokeStyle = (y / step) % 4 === 0 ? '#70879e99' : '#91a3b255'; c.beginPath(); c.moveTo(0, y + .5); c.lineTo(W(), y + .5); c.stroke(); }
    c.restore();
  }
  if ($('landmarks').checked) {
    const lm = state.landmarks[state.view];
    c.save(); c.font = `${Math.max(8, Math.round(22 * unit))}px system-ui`; c.textBaseline = 'middle';
    for (const k of C.LANDMARK_KEYS) {
      const [x, y] = C.toPixel(lm[k].n, { width: W(), height: H() });
      c.strokeStyle = k === 'ground' ? '#df6b52' : '#1488b5'; c.lineWidth = Math.max(1, 2 * unit); c.setLineDash([10 * unit, 9 * unit]);
      c.beginPath(); c.moveTo(0, y); c.lineTo(W(), y); c.stroke(); c.setLineDash([]);
      c.fillStyle = k === state.selected ? '#ff5d2e' : '#eea246'; c.strokeStyle = '#fff'; c.lineWidth = Math.max(1, 3 * unit);
      c.beginPath(); c.arc(x, y, Math.max(3, 9 * unit), 0, Math.PI * 2); c.fill(); c.stroke();
      c.fillStyle = '#263849';
      const label = (k === state.selected || k === 'ground') ? `${k} (${x},${y}) ${lm[k].confidence}` : k;
      const side = /Left$/.test(k) ? -1 : 1;   // character-left labels to the left of the marker to avoid overlaps
      c.textAlign = side < 0 ? 'right' : 'left';
      c.fillText(label, Math.max(4, Math.min(x + side * 15 * unit, W() - 4)), Math.max(20 * unit, y - 18 * unit));
      c.textAlign = 'left';
    }
    c.restore();
  }
}
function draw() {
  paint(ctx, { guides: true, background: true, mask: $('silhouette').checked });
  const last = frames() - 1;
  $('frameLabel').textContent = `${state.frame} / ${last}`; $('frameSlider').value = state.frame;
  const k = state.selected;
  $('lmName').textContent = k || '—';
  if (k) {
    const p = state.landmarks[state.view][k];
    const px = C.toPixel(p.n, { width: W(), height: H() });
    $('lmCoord').textContent = `px ${px.join(',')} · n ${p.n.join(',')} · ${p.source}`;
    $('lmConfidence').value = p.confidence;
  } else $('lmCoord').textContent = '';
  for (const fn of drawListeners) fn();
}
function applyPreset(id) {
  const p = state.presets.find(x => x.id === id) || state.presets[0];
  state.preset = p;
  canvas.width = p.canvas[0]; canvas.height = p.canvas[1];
  const last = p.frames - 1;
  for (const id2 of ['frameInput', 'frameSlider']) $(id2).max = last;
  if (state.frame > last) state.frame = 0;
  $('canvasInfo').textContent = `${p.canvas[0]} × ${p.canvas[1]} px · ${p.frames}フレーム · 正本は非破壊`;
  $('preset').value = p.id;
  draw(); renderLayers();
}
function setFrame(n) { const f = frames(); state.frame = ((n % f) + f) % f; $('frameInput').value = state.frame; draw(); renderLayers(); }
function setView(v) { state.view = v; $('view').value = v; draw(); renderLayers(); renderConstraints(); }

function renderLayers() {
  const root = $('layers'); root.replaceChildren();
  const items = state.items.filter(x => x.view === state.view && x.frame === state.frame);
  if (!items.length) { const p = document.createElement('p'); p.className = 'hint'; p.textContent = 'この方向・フレームの画像は未登録です。'; root.append(p); return; }
  for (const it of items) {
    const row = document.createElement('div'); row.className = 'layeritem';
    const cb = document.createElement('input'); cb.type = 'checkbox'; cb.checked = it.visible;
    cb.addEventListener('change', () => { it.visible = cb.checked; draw(); });
    const span = document.createElement('span');
    span.textContent = `${it.layer}: ${it.name}${it.canonical ? ' [正本・読取専用]' : ' [候補]'}`; span.title = it.name;
    const del = document.createElement('button'); del.textContent = '削除';
    del.addEventListener('click', () => { state.items = state.items.filter(x => x !== it); renderLayers(); draw(); });
    row.append(cb, span, del); root.append(row);
  }
}
async function addImage(blob, name, view, layer, frame, extra = {}) {
  const buf = await blob.arrayBuffer();
  const image = await createImageBitmap(new Blob([buf], { type: 'image/png' }));
  const item = { name, view, layer, frame, image, width: image.width, height: image.height, hash: await sha256(buf), visible: true, canonical: false, ...extra };
  state.items.push(item); return item;
}
async function handleFiles(files) {
  for (const f of files) {
    if (f.type !== 'image/png') { alert(`${f.name}: PNGのみ対応`); continue; }
    try { await addImage(f, f.name, state.view, $('layer').value, state.frame); } catch (e) { alert(`読み込み失敗: ${f.name}\n${e.message}`); }
  }
  renderLayers(); draw();
}
async function loadDemo() {
  for (const v of VIEWS) {
    const name = `morwen_${v}_candidate.png`;
    if (state.items.some(it => it.name === name)) continue;
    try {
      const res = await fetch(`demo/${name}`); if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await addImage(await res.blob(), name, v, 'reference', 0, { origin: 'demo_candidate' });
    } catch (e) { alert('デモ画像が読み込めません。HTTPサーバーから開いてください。\n' + e.message); break; }
  }
  renderLayers(); draw();
}
// Read-only view of the director-approved four views. SHA-256 is checked against the repository MANIFEST.
async function loadCanon() {
  let man;
  try { const r = await fetch(CANON_DIR + 'MANIFEST.json'); if (!r.ok) throw new Error(`HTTP ${r.status}`); man = await r.json(); }
  catch (e) { alert('正本MANIFESTを読めません（リポジトリ直下からHTTPサーバーで開いてください）。\n' + e.message); return; }
  const results = [];
  for (const f of man.files) {
    const name = `canon_${f.direction}.png`;
    if (state.items.some(it => it.name === name)) continue;
    try {
      const r = await fetch(CANON_DIR + `${f.direction}.png`); if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const it = await addImage(await r.blob(), name, f.direction, 'reference', 0, { canonical: true, origin: 'final_visual_canon', expectedSha256: f.sha256 });
      results.push(`${f.direction}: ${it.hash === f.sha256 ? 'SHA一致' : 'SHA不一致!'}`);
    } catch (e) { results.push(`${f.direction}: 読込失敗 ${e.message}`); }
  }
  renderLayers(); draw();
  if (results.length) $('qa').replaceChildren(Object.assign(document.createElement('p'), { textContent: '正本照合: ' + results.join(' / ') }));
}
function imageDataFor(it) {
  const c = document.createElement('canvas'); c.width = it.width; c.height = it.height;
  const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(it.image, 0, 0);
  return x.getImageData(0, 0, it.width, it.height).data;
}
function runQA() {
  const result = {
    schemaVersion: '2.0', generatedAt: new Date().toISOString(), characterId: $('character').value,
    presetId: state.preset.id, canvas: state.preset.canvas, status: 'PARTIAL', files: [], checks: [],
    manualChecklist: (state.constraints ? state.constraints.constraints : []).map(c => ({ id: c.id, views: c.views, status: VIEWS.every(v => !c.views.includes(v) || state.reviewed[`${c.id}:${v}`]) ? 'REVIEWER_MARKED' : 'NOT_RUN' })),
    referenceBody: state.references ? state.references.references : null,
    limitations: ['骨格R2.1は最終正本4方向に対して未測定（BLOCKED）', 'デザイン・衣装の一致は目視QAが必要', '接地点は初期仮値を含み、解剖学的検証は未実施', '構造チェックリストは目視項目であり自動PASSにしない']
  };
  if (!state.items.length) { result.status = 'BLOCKED'; result.checks.push({ name: 'image_present', status: 'BLOCKED' }); }
  else {
    for (const it of state.items) {
      const s = C.alphaStats(imageDataFor(it), it.width, it.height);
      const pl = C.placement(it.width, it.height, { width: W(), height: H() });
      result.files.push({
        name: it.name, view: it.view, layer: it.layer, frame: it.frame, canonical: it.canonical, origin: it.origin || 'user_file',
        sha256: it.hash, expectedSha256: it.expectedSha256 || null, shaMatch: it.expectedSha256 ? it.hash === it.expectedSha256 : null,
        dimensions: [it.width, it.height], dimensionsMatch: pl.exact, previewScale: pl.scale,
        opaquePixels: s.opaque, semiTransparentPixels: s.semi, transparentPixels: s.transparent, borderAlphaPixels: s.border,
        hasTransparency: s.hasTransparency, alphaBBox: s.bbox
      });
    }
    const f = result.files;
    result.checks.push({ name: 'canvas_dimensions', status: f.every(x => x.dimensionsMatch) ? 'PASS' : 'FAIL' });
    result.checks.push({ name: 'real_transparency', status: f.every(x => x.hasTransparency) ? 'PASS' : 'FAIL' });
    result.checks.push({ name: 'transparent_canvas_border', status: f.every(x => x.borderAlphaPixels === 0 && x.hasTransparency) ? 'PASS' : 'FAIL' });
    result.checks.push({ name: 'canonical_sha256', status: f.some(x => x.shaMatch !== null) ? (f.every(x => x.shaMatch !== false) ? 'PASS' : 'FAIL') : 'NOT_RUN' });
    result.checks.push({ name: 'four_view_coverage_frame0', status: VIEWS.every(v => f.some(x => x.view === v && x.frame === 0)) ? 'PASS' : 'BLOCKED' });
    result.checks.push({ name: 'anatomy_and_design', status: 'NOT_RUN' });
    if (result.checks.some(x => x.status === 'FAIL')) result.status = 'FAIL';
  }
  state.qa = result;
  const root = $('qa'); root.replaceChildren();
  const p = document.createElement('p'); p.textContent = `総合: ${result.status} / ${result.files.length}ファイル`; root.append(p);
  for (const ch of result.checks) { const line = document.createElement('div'); line.className = ch.status.toLowerCase(); line.textContent = `${ch.status} · ${ch.name}`; root.append(line); }
  for (const f of result.files) {
    const line = document.createElement('p'); line.className = 'hint';
    line.textContent = `${f.view}/${f.layer} f${f.frame}${f.canonical ? ' [正本]' : ' [候補]'}: ${f.dimensions.join('×')} · 透過${f.hasTransparency ? 'あり' : 'なし'} · 外周α ${f.borderAlphaPixels}px${f.shaMatch === null ? '' : f.shaMatch ? ' · SHA一致' : ' · SHA不一致'}`;
    root.append(line);
  }
  return result;
}
function renderConstraints() {
  const root = $('constraints'); root.replaceChildren();
  if (!state.constraints) { root.append(Object.assign(document.createElement('p'), { className: 'hint', textContent: '制約定義（profiles/morwen_constraints.json）を読み込めません（HTTPで開いてください）。' })); return; }
  for (const c of state.constraints.constraints) {
    if (!c.views.includes(state.view)) continue;
    const key = `${c.id}:${state.view}`;
    const lab = document.createElement('label'); lab.className = 'check';
    const cb = document.createElement('input'); cb.type = 'checkbox'; cb.checked = !!state.reviewed[key]; cb.dataset.constraint = c.id;
    cb.addEventListener('change', () => { if (cb.checked) state.reviewed[key] = true; else delete state.reviewed[key]; });
    lab.append(cb, document.createTextNode(`${c.label}（${c.kind}）`)); root.append(lab);
  }
}
function currentSpec() {
  return C.buildSpec({
    characterId: $('character').value, preset: state.preset, landmarks: state.landmarks,
    assets: state.items.map(it => ({ name: it.name, view: it.view, layer: it.layer, frame: it.frame, sha256: it.hash, dimensions: [it.width, it.height], canonical: it.canonical })),
    referenceBody: state.references ? state.references.references.map(r => ({ id: r.id, status: r.status })) : null
  });
}
function exportCanvas(kind) {
  const c = document.createElement('canvas'); c.width = W(); c.height = H();
  const x = c.getContext('2d', { willReadFrequently: true });
  if (kind === 'guide') paint(x, { guides: true, background: true });
  else if (kind === 'mask') paint(x, { guides: false, background: false, mask: true, transparent: true, excludeCanon: true });
  else paint(x, { guides: false, background: false, transparent: true, excludeCanon: true });
  c.toBlob(b => saveBlob(b, `${$('character').value}_${state.preset.id}_${state.view}_f${state.frame}_${kind}.png`), 'image/png');
}
function pointerCoords(e) { const r = canvas.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * W(), (e.clientY - r.top) / r.height * H()]; }
canvas.addEventListener('pointerdown', e => {
  if (!$('landmarks').checked) return;
  const [x, y] = pointerCoords(e); let best = null, dist = Infinity;
  for (const k of C.LANDMARK_KEYS) {
    const [px, py] = C.toPixel(state.landmarks[state.view][k].n, { width: W(), height: H() });
    const d = Math.hypot(px - x, py - y); if (d < dist) { dist = d; best = k; }
  }
  if (dist < 40 * W() / 1200 + 10) { drag = best; state.selected = best; canvas.setPointerCapture(e.pointerId); draw(); }
});
canvas.addEventListener('pointermove', e => {
  if (!drag) return;
  const [x, y] = pointerCoords(e);
  const p = state.landmarks[state.view][drag];
  p.n = C.toNorm([Math.max(0, Math.min(W() - 1, Math.round(x))), Math.max(0, Math.min(H() - 1, Math.round(y)))], { width: W(), height: H() });
  p.source = 'manual_edit';
  draw();
});
canvas.addEventListener('pointerup', () => { drag = null; });
canvas.addEventListener('pointercancel', () => { drag = null; });
$('lmConfidence').addEventListener('change', e => { if (state.selected) { state.landmarks[state.view][state.selected].confidence = e.target.value; draw(); } });
$('file').addEventListener('change', e => { handleFiles([...e.target.files]); e.target.value = ''; });
$('view').addEventListener('change', e => setView(e.target.value));
$('preset').addEventListener('change', e => applyPreset(e.target.value));
$('frameInput').addEventListener('change', e => setFrame(Number(e.target.value)));
$('frameSlider').addEventListener('input', e => setFrame(Number(e.target.value)));
for (const id of ['grid', 'landmarks', 'silhouette', 'checker', 'opacity']) $(id).addEventListener('input', () => { $('opacityLabel').textContent = $('opacity').value + '%'; draw(); });
$('loadDemo').onclick = loadDemo;
$('loadCanon').onclick = loadCanon;
$('clear').onclick = () => { state.items = []; state.qa = null; renderLayers(); draw(); };
$('prev').onclick = () => setFrame(state.frame - 1);
$('next').onclick = () => setFrame(state.frame + 1);
$('play').onclick = () => {
  state.playing = !state.playing; $('play').textContent = state.playing ? '■ 停止' : '▶ 再生'; clearInterval(timer);
  if (state.playing) timer = setInterval(() => setFrame(state.frame + 1), 1000 / Math.max(1, Math.min(24, Number($('fps').value) || 7)));
};
$('runQA').onclick = runQA;
$('exportQA').onclick = () => saveText(JSON.stringify(state.qa || runQA(), null, 2), `${$('character').value}_QA.json`);
$('exportSpec').onclick = () => saveText(C.stableStringify(currentSpec()), `${$('character').value}_BASE_BODY_SPEC_v2.json`);
$('importSpec').addEventListener('change', async e => {
  const f = e.target.files[0]; if (!f) return;
  try {
    const j = JSON.parse(await f.text());
    const { landmarks, warnings } = C.parseSpec(j, state.preset);
    state.landmarks = landmarks;
    $('character').value = j.characterId || 'candidate';
    if (j.presetId && state.presets.some(p => p.id === j.presetId)) applyPreset(j.presetId);
    draw();
    $('qa').replaceChildren(Object.assign(document.createElement('p'), { textContent: '素体仕様を読み込みました（画像データは含まれません）。' + warnings.join(' ') }));
  } catch (err) { alert('仕様読込エラー: ' + err.message); }
  e.target.value = '';
});
$('guide').onclick = () => exportCanvas('guide');
$('exportComposite').onclick = () => exportCanvas('composite');
$('exportMask').onclick = () => exportCanvas('mask');
$('fit').onclick = () => { $('canvaswrap').scrollTop = 0; $('canvaswrap').scrollLeft = 0; };

async function init() {
  try { const r = await fetch('profiles/presets.json'); if (r.ok) state.presets = (await r.json()).presets; } catch (e) { /* file:// fallback */ }
  try { const r = await fetch('profiles/morwen_constraints.json'); if (r.ok) state.constraints = await r.json(); } catch (e) { /* optional */ }
  try { const r = await fetch('profiles/reference_bodies.json'); if (r.ok) state.references = await r.json(); } catch (e) { /* optional */ }
  const sel = $('preset'); sel.replaceChildren();
  for (const p of state.presets) sel.append(new Option(`${p.id} (${p.canvas.join('×')})`, p.id));
  applyPreset(state.presets[0].id);
  renderConstraints();
  document.body.dataset.ready = '1';
}
// Read-only bridge for the v0.3 Motion Reference panel (motion.js). Motion data never writes into state.landmarks.
window.Studio = { state, paint, W, H, frames, onDraw: fn => drawListeners.push(fn) };
init();
