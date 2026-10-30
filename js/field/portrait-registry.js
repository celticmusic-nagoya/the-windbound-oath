/* PortraitRegistry — the single place that knows every conversation-portrait character: where its images are, which expressions it has,
 * how it is framed, which side of the screen it prefers, and (optionally) its blink overlays. No code outside this file builds image paths.
 *
 *   define(id, def)   def = {
 *     name, src:{w,h}                     source PNG size; every coordinate below is in these pixels
 *     base                                folder of the adopted portraits: assets/images/characters/portraits/{id}/
 *     file(face) -> file name             expression image, relative to base
 *     crop:{x,y,w,h}                      bust framing (source px); the on-screen frame keeps this aspect ratio
 *     side: 'left'|'right'                default side (a page / conversation `side` wins; fallback 'right')
 *     faces:[ids]                         expressions this character really has (subset of the shared ids); others resolve to 'normal'
 *     blink?: { seq:[[state,ms]...], gap:[minMs,maxMs], faces:[ids that blink], file(face,eye,state) -> name (relative to base),
 *               eyes:{L:[x0,y0,x1,y1], R:[...]}  overlay boxes (source px), or per face: eyesByFace:{face:{L,R}} }
 *   }
 *   A character without `blink` (or a face not listed in blink.faces, e.g. a closed-eye smile) is shown as a still portrait.
 *
 * Shared expression ids (kept from the earlier TalkPortrait so existing data stays valid): normal smile angry sad surprised worried determined relieved
 * (also "01".."08"). Adding a character = one define() + its images; nothing else changes. */
(function () {
  'use strict';
  const FACES = Object.freeze(['normal', 'smile', 'angry', 'sad', 'surprised', 'worried', 'determined', 'relieved']);
  const SIDES = Object.freeze(['left', 'right']);
  const FALLBACK_SIDE = 'right';
  // the blink timing proven by Fiona battle idle v3 (open -> 30 -> 60 -> 85 -> 100 % -> ... -> open, 260 ms; every 3-6 s; both eyes together)
  const BLINK_V3 = Object.freeze({seq: Object.freeze([[1, 30], [2, 30], [3, 35], [4, 70], [3, 35], [2, 30], [1, 30]]), gap: Object.freeze([3000, 6000])});
  const chars = new Map();
  let ROOT = '';   // prefix for every asset URL; '' in the game (paths are relative to index.html). Pages in sub-folders (dev/) call setRoot('../').

  function define(id, def) {
    if (!/^[a-z][a-z0-9_]{0,31}$/.test(id)) throw new Error('PortraitRegistry: bad id ' + id);
    const faces = Object.freeze((def.faces || FACES).filter(f => FACES.includes(f)));
    const b = def.blink ? Object.freeze({
      seq: Object.freeze((def.blink.seq || BLINK_V3.seq).map(x => Object.freeze([x[0], x[1]]))),
      gap: Object.freeze([...(def.blink.gap || BLINK_V3.gap)]),
      faces: Object.freeze((def.blink.faces || faces).filter(f => faces.includes(f))),
      states: Math.max(...(def.blink.seq || BLINK_V3.seq).map(x => x[0])),
      file: def.blink.file, eyes: def.blink.eyes || null, eyesByFace: def.blink.eyesByFace || null
    }) : null;
    chars.set(id, Object.freeze({id, name: def.name || id, src: Object.freeze({...def.src}), base: def.base, file: def.file, crop: Object.freeze({...def.crop}),
      provisionalFaces: Object.freeze((def.provisionalFaces || []).filter(f => faces.includes(f))), provisionalBlink: Boolean(def.provisionalBlink),
      side: SIDES.includes(def.side) ? def.side : FALLBACK_SIDE, faces, blink: b}));
  }
  const get = id => chars.get(id) || null;
  // expression id -> one this character can show ('01'..'08' accepted; unknown -> normal)
  function faceOf(face, id) {
    const c = get(id), list = c ? c.faces : FACES;
    let f = /^0[1-8]$/.test(String(face)) ? FACES[+face - 1] : face;
    return list.includes(f) ? f : 'normal';
  }
  const imageUrl = (id, face) => { const c = get(id); return c ? ROOT + c.base + c.file(faceOf(face, id)) : null; };
  // {eye: {box:[x0,y0,x1,y1], urls:[state1..stateN]}} for a face that blinks, else null
  function blinkOf(id, face) {
    const c = get(id); if (!c || !c.blink) return null; const f = faceOf(face, id); if (!c.blink.faces.includes(f)) return null;
    const eyes = (c.blink.eyesByFace && c.blink.eyesByFace[f]) || c.blink.eyes; if (!eyes) return null;
    const out = {};
    for (const [eye, box] of Object.entries(eyes)) out[eye] = {box: box.slice(), urls: Array.from({length: c.blink.states}, (_, i) => ROOT + c.base + c.blink.file(f, eye, i + 1))};
    return {seq: c.blink.seq, gap: c.blink.gap, eyes: out};
  }
  // side precedence: explicit (page / conversation) -> registry default -> fallback
  const sideOf = (id, explicit) => SIDES.includes(explicit) ? explicit : (get(id) ? get(id).side : FALLBACK_SIDE);

  // ---------- adopted characters ----------
  // Aidan: adopted conversation portraits (expression set v2, 2026-10-27) + Phase 2 Rev2 blink overlays (adopted 2026-10-27).
  // Sources: handoff handoff/aidan-expressions-claude-20261027 reports/ASSETS/AIDAN-EXPR-20261027/v2/ and
  //          handoff/talk-portrait-blink-claude-20261027 reports/TALK-PORTRAIT-BLINK-20261027/phase2-aidan-rev2/ (bytes unchanged; SHA-256 in docs/ASSET_INVENTORY.md).
  define('aidan', {
    name: 'エイダン', src: {w: 1024, h: 1536}, base: 'assets/images/characters/portraits/aidan/', file: f => 'aidan_' + f + '.png',
    crop: {x: 190, y: 0, w: 800, h: 760}, side: 'left',
    faces: ['normal', 'smile', 'angry', 'worried', 'sad', 'surprised'],
    blink: {seq: BLINK_V3.seq, gap: BLINK_V3.gap, faces: ['normal', 'smile', 'angry', 'worried', 'sad', 'surprised'],
      file: (f, eye, s) => 'blink/' + f + '_' + eye + '_s' + s + '.png', eyes: {L: [570, 268, 654, 320], R: [672, 314, 716, 350]}}
  });
  // DIRECTIVE-19B normal PNGs remain formally adopted and unchanged.
  // DIRECTIVE-20D: revised20C expressions + normal blink are PROVISIONAL_ANDROID_QA only (2026-10-30).
  for (const [id, name, src, crop] of [
    ['fiona', 'フィオナ', {w:1024,h:1536}, {x:130,y:45,w:840,h:840}],
    ['lou', 'ルー', {w:1312,h:1199}, {x:0,y:0,w:1312,h:1199}],
    ['emma', 'エマ', {w:1024,h:1536}, {x:90,y:0,w:880,h:880}]
  ]) {
    const provisionalFaces = FACES.filter(f => f !== 'normal' && !(id === 'lou' && ['smile','relieved'].includes(f)));
    const eyes = {
      fiona: {L:[508,298,568,353], R:[582,252,660,312]},
      lou: {L:[678,354,769,436], R:[790,397,865,474]},
      emma: {L:[504,318,562,381], R:[629,267,683,325]}
    }[id];
    //20E: user-approved curved eyelids for Fiona/Lou; Emma20C passed physical QA and stays unchanged.
    const revision = id === 'emma' ? 'provisional-20c' : 'provisional-20e';
    define(id, {name, src, crop, base:'assets/images/characters/portraits/'+id+'/',
      file:f=>(f === 'normal' ? '' : revision+'/expressions/')+id+'_'+f+'.png', side:'right',
      faces:['normal', ...provisionalFaces], provisionalFaces, provisionalBlink:true,
      blink:{seq:BLINK_V3.seq,gap:BLINK_V3.gap,faces:['normal'],eyes,
        file:(f,eye,s)=>revision+'/blink/'+f+'_'+eye+'_s'+s+'.png'}});
  }

  window.PortraitRegistry = Object.freeze({FACES, SIDES, FALLBACK_SIDE, BLINK_V3, define, get, has: id => chars.has(id), ids: () => [...chars.keys()],
    faceOf, imageUrl, blinkOf, sideOf, setRoot: r => { ROOT = typeof r === 'string' ? r : ''; }, get root() { return ROOT; }});
})();
