/* Character Asset Studio — pure core logic (no DOM). Works in the browser (window.StudioCore) and in Node (require). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.StudioCore = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const SPEC_VERSION = '2.0';
  const VIEWS = ['front', 'back', 'left', 'right'];
  const LANDMARK_KEYS = ['headTop', 'neck', 'shoulderLeft', 'shoulderRight', 'pelvis', 'kneeLeft', 'kneeRight', 'footLeft', 'footRight', 'ground'];
  const CONFIDENCE = ['high', 'medium', 'low', 'provisional'];
  const SOURCES = ['template_default', 'manual_edit', 'imported_spec', 'measured_reference'];

  // Template landmarks in NORMALISED canvas space (0..1). Illustrative only — never official measurements.
  const TEMPLATE = {
    headTop: [0.5, 0.075], neck: [0.5, 0.19375], shoulderLeft: [0.4, 0.21875], shoulderRight: [0.6, 0.21875],
    pelvis: [0.5, 0.5125], kneeLeft: [0.44583, 0.725], kneeRight: [0.55417, 0.725],
    footLeft: [0.43333, 0.9625], footRight: [0.56667, 0.9625], ground: [0.5, 0.9625]
  };

  function round(n, d) { const f = Math.pow(10, d); return Math.round(n * f) / f; }

  function templateLandmarks() {
    const out = {};
    for (const v of VIEWS) {
      out[v] = {};
      for (const k of LANDMARK_KEYS) out[v][k] = { n: TEMPLATE[k].slice(), confidence: 'provisional', source: 'template_default' };
    }
    return out;
  }

  function toPixel(n, canvas) { return [Math.round(n[0] * canvas.width), Math.round(n[1] * canvas.height)]; }
  function toNorm(px, canvas) {
    return [round(Math.min(1, Math.max(0, px[0] / canvas.width)), 5), round(Math.min(1, Math.max(0, px[1] / canvas.height)), 5)];
  }

  // Place an image of any size onto the canvas: 1:1 when sizes match; otherwise uniform scale to fit,
  // bottom-centred (keeps the ground line). Never anisotropic.
  function placement(imgW, imgH, canvas) {
    if (imgW === canvas.width && imgH === canvas.height) return { scale: 1, x: 0, y: 0, w: imgW, h: imgH, exact: true };
    const s = Math.min(canvas.width / imgW, canvas.height / imgH);
    const w = imgW * s, h = imgH * s;
    return { scale: round(s, 6), x: round((canvas.width - w) / 2, 3), y: round(canvas.height - h, 3), w: round(w, 3), h: round(h, 3), exact: false };
  }

  function sortKeys(v) {
    if (Array.isArray(v)) return v.map(sortKeys);
    if (v && typeof v === 'object') return Object.keys(v).sort().reduce((o, k) => { o[k] = sortKeys(v[k]); return o; }, {});
    return v;
  }
  function stableStringify(obj) { return JSON.stringify(sortKeys(obj), null, 2) + '\n'; }

  function buildSpec({ characterId, preset, landmarks, assets, referenceBody }) {
    const canvas = { width: preset.canvas[0], height: preset.canvas[1] };
    const lm = {};
    for (const v of VIEWS) {
      lm[v] = {};
      for (const k of LANDMARK_KEYS) {
        const p = landmarks[v][k];
        lm[v][k] = { n: p.n.slice(), px: toPixel(p.n, canvas), confidence: p.confidence, source: p.source };
      }
    }
    return {
      schemaVersion: SPEC_VERSION,
      status: 'candidate_not_canonical',
      characterId: characterId || 'candidate',
      presetId: preset.id,
      canvas,
      groundNormalized: preset.ground.slice(),
      worldScale: { pixelsPerUnit: preset.pixelsPerUnit == null ? null : preset.pixelsPerUnit },
      coordinateSpace: 'normalized canvas (0..1, origin top-left, y down); px = n * canvas size',
      views: VIEWS.slice(),
      landmarks: lm,
      referenceBody: referenceBody || null,
      assets: (assets || []).map(a => ({ name: a.name, view: a.view, layer: a.layer, frame: a.frame, sha256: a.sha256, dimensions: a.dimensions, canonical: !!a.canonical }))
        .sort((a, b) => (a.view + a.layer + String(a.frame).padStart(3, '0') + a.name).localeCompare(b.view + b.layer + String(b.frame).padStart(3, '0') + b.name)),
      notes: 'Landmarks are provisional unless confidence/source say otherwise. No anatomy is inferred automatically.'
    };
  }

  // Validate and normalise an imported spec. Accepts v1.0 (pixel arrays) and v2.0. Returns {landmarks, warnings}.
  function parseSpec(j, preset) {
    if (!j || typeof j !== 'object') throw new Error('JSONではありません');
    const warnings = [];
    const lmIn = j.landmarks;
    if (!lmIn) throw new Error('landmarks がありません');
    const out = {};
    if (j.schemaVersion === '1.0') {
      const cw = j.canvas && j.canvas.width, ch = j.canvas && j.canvas.height;
      if (!(cw > 0 && ch > 0)) throw new Error('v1.0: canvas.width/height が不正です');
      for (const v of VIEWS) {
        out[v] = {};
        for (const k of LANDMARK_KEYS) {
          const p = lmIn[v] && lmIn[v][k];
          if (!Array.isArray(p) || p.length !== 2 || !p.every(Number.isFinite) || p[0] < 0 || p[1] < 0 || p[0] > cw || p[1] > ch) throw new Error(`${v}.${k} の座標が不正です`);
          out[v][k] = { n: toNorm(p, { width: cw, height: ch }), confidence: 'provisional', source: 'imported_spec' };
        }
      }
      warnings.push('v1.0（ピクセル座標）を正規化座標へ変換しました。信頼度は provisional として扱います。');
    } else if (j.schemaVersion === SPEC_VERSION) {
      for (const v of VIEWS) {
        out[v] = {};
        for (const k of LANDMARK_KEYS) {
          const p = lmIn[v] && lmIn[v][k];
          if (!p || !Array.isArray(p.n) || p.n.length !== 2 || !p.n.every(x => Number.isFinite(x) && x >= 0 && x <= 1)) throw new Error(`${v}.${k}.n が不正です（0〜1）`);
          if (!CONFIDENCE.includes(p.confidence)) throw new Error(`${v}.${k}.confidence が不正です`);
          if (!SOURCES.includes(p.source)) throw new Error(`${v}.${k}.source が不正です`);
          out[v][k] = { n: p.n.slice(), confidence: p.confidence, source: p.source };
        }
      }
      if (j.canvas && preset && (j.canvas.width !== preset.canvas[0] || j.canvas.height !== preset.canvas[1])) {
        warnings.push(`仕様のキャンバス ${j.canvas.width}×${j.canvas.height} を現在のプリセット ${preset.canvas[0]}×${preset.canvas[1]} へ正規化座標で換算しました。`);
      }
    } else {
      throw new Error(`未対応の schemaVersion: ${j.schemaVersion}`);
    }
    return { landmarks: out, warnings };
  }

  // Alpha statistics for an RGBA buffer.
  function alphaStats(data, w, h) {
    let opaque = 0, semi = 0, border = 0, minX = w, minY = h, maxX = -1, maxY = -1;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const a = data[(y * w + x) * 4 + 3];
      if (a === 255) opaque++; else if (a > 0) semi++;
      if (a > 0 && (x === 0 || y === 0 || x === w - 1 || y === h - 1)) border++;
      if (a >= 128) { if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; }
    }
    const total = w * h;
    return { opaque, semi, transparent: total - opaque - semi, border, bbox: maxX >= 0 ? [minX, minY, maxX, maxY] : null, hasTransparency: total - opaque > 0 };
  }

  return { SPEC_VERSION, VIEWS, LANDMARK_KEYS, CONFIDENCE, SOURCES, templateLandmarks, toPixel, toNorm, placement, stableStringify, buildSpec, parseSpec, alphaStats };
});
