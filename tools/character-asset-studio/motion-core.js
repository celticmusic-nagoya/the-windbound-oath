/* Character Asset Studio v0.3 — Motion Reference core (pure logic, no DOM).
 * UMD: window.MotionCore in the browser, require('./motion-core.js') in Node.
 * Every value produced here is an UNAPPROVED REFERENCE measured on a reference video.
 * Nothing in this module writes to character skeleton/BASE_BODY_SPEC data (autoApply is always false).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.MotionCore = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const SCHEMA = 'motion-reference/1.0';
  const STATUS = 'UNAPPROVED_REFERENCE';
  // Walk phases (Williams-style naming). 'contact' anchors the cycle; others are optional markers.
  const PHASES = ['contact', 'down', 'passing', 'up', 'push_off'];
  // Side of the leading/supporting leg. 'A'/'B' = alternating but not identified as anatomical left/right.
  const SIDES = ['L', 'R', 'A', 'B', 'unknown'];
  const JOINTS = ['head', 'shoulder', 'elbow', 'wrist', 'hip', 'knee_L', 'knee_R', 'ankle_L', 'ankle_R', 'toe_L', 'toe_R'];
  const SAMPLE_COUNTS = [6, 8, 12];
  // Analysis markers are NOT phases: a leg-spread extremum is evidence, not a foot contact.
  const CANDIDATE_KINDS = ['leg_spread_max', 'leg_spread_min'];
  // Phase verification: absent = unverified candidate; 'visual_confirmed' = a person checked the frame by eye.
  // (Still UNAPPROVED_REFERENCE as a whole — confirmation is not adoption.)
  const VERIFIED = 'visual_confirmed';
  const REGIONS = { full: [0, 0, 1, 1], left_half: [0, 0, 0.5, 1], right_half: [0.5, 0, 0.5, 1] };

  const r6 = v => Math.round(v * 1e6) / 1e6;
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  function stableStringify(v) {
    const norm = x => {
      if (Array.isArray(x)) return x.map(norm);
      if (x && typeof x === 'object') { const o = {}; for (const k of Object.keys(x).sort()) if (x[k] !== undefined) o[k] = norm(x[k]); return o; }
      return x;
    };
    return JSON.stringify(norm(v), null, 2) + '\n';
  }

  // Frame <-> time. Seek to the middle of a frame so decoders land on the intended frame.
  function frameToTime(frame, fps) { return (frame + 0.5) / fps; }
  function timeToFrame(t, fps) { return Math.max(0, Math.floor(t * fps + 1e-6)); }
  function frameCountFor(duration, fps) { return Math.max(1, Math.round(duration * fps)); }
  function stepFrame(frame, delta, frameCount) { return clamp(frame + delta, 0, Math.max(0, frameCount - 1)); }
  function timecode(frame, fps) {
    const t = frame / fps, m = Math.floor(t / 60), s = Math.floor(t % 60), f = frame - Math.floor(Math.floor(t) * fps);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}+${String(Math.max(0, Math.round(f))).padStart(2, '0')}f`;
  }

  function createRef({ video = {}, region = 'full', note = '' } = {}) {
    return {
      schema: SCHEMA, status: STATUS, autoApply: false,
      policy: 'Measured on a third-party reference video. Unapproved reference values only; never applied automatically to character skeleton, BASE_BODY_SPEC or designs. Video pixels are not stored.',
      video: {
        name: video.name || null, sha256: video.sha256 || null,
        width: video.width || null, height: video.height || null,
        fps: video.fps || 24, frameCount: video.frameCount || null,
        fpsSource: video.fpsSource || 'user_entered'
      },
      region: Array.isArray(region) ? region.map(r6) : (REGIONS[region] || REGIONS.full).slice(),
      phases: [], candidates: [], anchors: {}, note
    };
  }

  function setPhase(ref, frame, phase, side = 'unknown', confidence = 'provisional') {
    if (!PHASES.includes(phase)) throw new Error('unknown phase: ' + phase);
    if (!SIDES.includes(side)) throw new Error('unknown side: ' + side);
    frame = Math.round(frame);
    ref.phases = ref.phases.filter(p => p.frame !== frame);
    ref.phases.push({ frame, phase, side, confidence });   // new phases always start unverified
    ref.phases.sort((a, b) => a.frame - b.frame);
    return ref;
  }
  function confirmPhase(ref, frame, confirmed = true) {
    const p = ref.phases.find(x => x.frame === Math.round(frame));
    if (!p) return false;
    if (confirmed) p.verification = VERIFIED; else delete p.verification;
    return true;
  }
  function isConfirmed(p) { return p.verification === VERIFIED; }
  function setCandidate(ref, frame, kind, source = 'manual_mark') {
    if (!CANDIDATE_KINDS.includes(kind)) throw new Error('unknown candidate kind: ' + kind);
    frame = Math.round(frame);
    ref.candidates = ref.candidates.filter(c => !(c.frame === frame && c.kind === kind));
    ref.candidates.push({ frame, kind, source });
    ref.candidates.sort((a, b) => a.frame - b.frame || a.kind.localeCompare(b.kind));
    return ref;
  }
  function removeCandidate(ref, frame, kind) { ref.candidates = ref.candidates.filter(c => !(c.frame === Math.round(frame) && (!kind || c.kind === kind))); return ref; }
  function removePhase(ref, frame) { ref.phases = ref.phases.filter(p => p.frame !== Math.round(frame)); return ref; }

  // Anchors are normalised to the selected region of the video frame (0..1).
  function setAnchor(ref, frame, joint, n, confidence = 'provisional') {
    if (!JOINTS.includes(joint)) throw new Error('unknown joint: ' + joint);
    const k = String(Math.round(frame));
    (ref.anchors[k] = ref.anchors[k] || {})[joint] = { n: [r6(clamp(n[0], 0, 1)), r6(clamp(n[1], 0, 1))], confidence };
    return ref;
  }
  function removeAnchor(ref, frame, joint) {
    const k = String(Math.round(frame));
    if (ref.anchors[k]) { delete ref.anchors[k][joint]; if (!Object.keys(ref.anchors[k]).length) delete ref.anchors[k]; }
    return ref;
  }
  function trajectory(ref, joint) {
    return Object.keys(ref.anchors).map(Number).sort((a, b) => a - b)
      .filter(f => ref.anchors[f][joint]).map(f => [f, ref.anchors[f][joint].n[0], ref.anchors[f][joint].n[1]]);
  }
  // Linear interpolation between recorded keys (null outside the recorded range).
  function anchorAt(ref, joint, frame) {
    const t = trajectory(ref, joint);
    if (!t.length || frame < t[0][0] || frame > t[t.length - 1][0]) return null;
    for (let i = 0; i < t.length; i++) {
      if (t[i][0] === frame) return [t[i][1], t[i][2]];
      if (t[i][0] > frame) { const a = t[i - 1], b = t[i], u = (frame - a[0]) / (b[0] - a[0]); return [r6(a[1] + (b[1] - a[1]) * u), r6(a[2] + (b[2] - a[2]) * u)]; }
    }
    return null;
  }

  // Full cycles = contact -> next contact of the same side. Without identified sides, alternation is assumed
  // (contact i -> contact i+2), which is flagged in the result.
  function cycles(ref) {
    const c = ref.phases.filter(p => p.phase === 'contact');
    const out = [];
    for (let i = 0; i < c.length; i++) {
      const known = c[i].side !== 'unknown';
      let j = -1;
      if (known) { for (let k = i + 1; k < c.length; k++) if (c[k].side === c[i].side) { j = k; break; } }
      else if (i + 2 < c.length) j = i + 2;
      if (j > i) out.push({ start: c[i].frame, end: c[j].frame, length: c[j].frame - c[i].frame, side: c[i].side, sideAssumed: !known });
    }
    return out;
  }
  // N evenly spaced frames over [start, end) — frame `end` is the next cycle's first frame.
  function sampleCycle(start, end, n) {
    if (!(end > start) || n < 1) throw new Error('invalid cycle');
    return Array.from({ length: n }, (_, i) => start + Math.round(i * (end - start) / n));
  }
  // Map sample i of N onto a sprite with `spriteFrames` frames (e.g. 12-frame master).
  function spriteFrameFor(i, n, spriteFrames) { return Math.round(i * spriteFrames / n) % spriteFrames; }

  function stats(ref) {
    const fps = ref.video.fps;
    const contacts = ref.phases.filter(p => p.phase === 'contact').map(p => p.frame);
    const steps = contacts.slice(1).map((f, i) => f - contacts[i]);
    const cyc = cycles(ref).map(c => c.length);
    const mean = a => a.length ? r6(a.reduce((s, v) => s + v, 0) / a.length) : null;
    const meanStep = mean(steps), meanCycle = mean(cyc);
    return {
      status: STATUS, contacts: contacts.length, stepFrames: steps, cycleFrames: cyc,
      meanStepFrames: meanStep, meanCycleFrames: meanCycle,
      meanCycleSecondsAtVideoFps: meanCycle == null ? null : r6(meanCycle / fps),
      cadenceStepsPerMinAtVideoFps: meanStep == null ? null : r6(60 * fps / meanStep)
    };
  }

  function serialize(ref) {
    const out = JSON.parse(JSON.stringify(ref));
    out.schema = SCHEMA; out.status = STATUS; out.autoApply = false;
    out.derived = stats(ref);
    out.derived.cycles = cycles(ref);
    if (!out.candidates || !out.candidates.length) delete out.candidates;   // keeps pre-v0.4 files byte-identical
    return stableStringify(out);
  }

  function parse(text) {
    const j = typeof text === 'string' ? JSON.parse(text) : text;
    if (!j || j.schema !== SCHEMA) throw new Error('not a ' + SCHEMA + ' file');
    const ref = createRef({ video: j.video || {}, region: j.region || 'full', note: j.note || '' });
    ref.video.fpsSource = (j.video && j.video.fpsSource) || ref.video.fpsSource;
    for (const p of j.phases || []) { setPhase(ref, p.frame, p.phase, p.side || 'unknown', p.confidence || 'provisional'); if (p.verification === VERIFIED) confirmPhase(ref, p.frame); }
    for (const c of j.candidates || []) setCandidate(ref, c.frame, c.kind, c.source || 'imported');
    for (const f of Object.keys(j.anchors || {})) for (const joint of Object.keys(j.anchors[f])) {
      const a = j.anchors[f][joint]; setAnchor(ref, Number(f), joint, a.n, a.confidence || 'provisional');
    }
    // Status cannot be upgraded by import: whatever the file says, it stays an unapproved reference.
    ref.status = STATUS; ref.autoApply = false;
    return ref;
  }

  // Sprite frame shown for comparison cell i of n. Missing frames are never generated: they are reported as
  // 'missing', or — only when reuse preview is on — filled by holding the previous registered frame ('reused', provisional).
  function spriteSource(i, n, spriteFrames, registered, reuse) {
    const frame = spriteFrameFor(i, n, spriteFrames);
    const reg = [...new Set(registered)].filter(f => f >= 0 && f < spriteFrames).sort((a, b) => a - b);
    if (reg.includes(frame)) return { frame, source: frame, state: 'registered' };
    if (!reuse || !reg.length) return { frame, source: null, state: 'missing' };
    const prev = reg.filter(f => f < frame);
    return { frame, source: prev.length ? prev[prev.length - 1] : reg[reg.length - 1], state: 'reused' };
  }
  // Union of pixel boxes [x0,y0,x1,y1] (inclusive-exclusive), optionally including a horizontal line y.
  function unionBox(boxes, lineY) {
    const b = boxes.filter(Boolean);
    if (!b.length) return null;
    const u = [Math.min(...b.map(x => x[0])), Math.min(...b.map(x => x[1])), Math.max(...b.map(x => x[2])), Math.max(...b.map(x => x[3]))];
    if (lineY != null) { u[1] = Math.min(u[1], lineY); u[3] = Math.max(u[3], lineY + 1); }
    return u;
  }
  // Map a normalised anchor (relative to region) to pixel coords inside a draw box {x,y,w,h}.
  function regionToBox(n, box) { return [box.x + n[0] * box.w, box.y + n[1] * box.h]; }
  function boxToRegion(px, box) { return [r6(clamp((px[0] - box.x) / box.w, 0, 1)), r6(clamp((px[1] - box.y) / box.h, 0, 1))]; }
  // Fit a source rect (region of a video) into a target, preserving aspect, bottom-aligned.
  function fitBox(srcW, srcH, dstX, dstY, dstW, dstH) {
    const s = Math.min(dstW / srcW, dstH / srcH), w = srcW * s, h = srcH * s;
    return { x: dstX + (dstW - w) / 2, y: dstY + (dstH - h), w, h, scale: s };
  }

  return {
    SCHEMA, STATUS, PHASES, SIDES, JOINTS, SAMPLE_COUNTS, REGIONS, CANDIDATE_KINDS, VERIFIED,
    confirmPhase, isConfirmed, setCandidate, removeCandidate, spriteSource, unionBox,
    stableStringify, frameToTime, timeToFrame, frameCountFor, stepFrame, timecode,
    createRef, setPhase, removePhase, setAnchor, removeAnchor, trajectory, anchorAt,
    cycles, sampleCycle, spriteFrameFor, stats, serialize, parse, regionToBox, boxToRegion, fitBox
  };
}));
