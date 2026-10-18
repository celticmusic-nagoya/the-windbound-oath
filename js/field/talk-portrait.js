/* TalkPortrait — conversation portraits with expression variants (Fiona / Lou).
 *   Character registry: id -> {name, dir, prefix, crop:{x,y,w,h} (source px, bust framing), side}
 *   Expression IDs shared by all characters: normal smile angry sad surprised worried determined relieved (01..08)
 *   Conversation data (FieldTalk) selects portraits explicitly:
 *     conversation or page:  {char:'fiona', face:'smile'}   (page values override the conversation's defaults)
 *     page without `char`  -> the portrait already on screen stays (a `face`-only page just changes its expression)
 *     `char:null`          -> hide the portrait for that page
 *     unknown/missing face -> `normal`; image that fails to load -> `normal`; if that fails too -> no portrait (the dialogue goes on)
 *   Display: #talkPortrait (fixed, pointer-events:none, below #msg), only while body.dialogueOpen (css/style.css), sits just above #msg. */
(function () {
  'use strict';
  const BASE = 'img/portraits/';
  const FACES = ['normal', 'smile', 'angry', 'sad', 'surprised', 'worried', 'determined', 'relieved'];
  const FACE_IDS = {normal: '01', smile: '02', angry: '03', sad: '04', surprised: '05', worried: '06', determined: '07', relieved: '08'};
  const CHARS = {
    fiona: {name: 'フィオナ', dir: 'fiona', prefix: 'fiona', crop: {x: 130, y: 45, w: 840, h: 840}, side: 'right'},   // source 1024x1536
    lou: {name: 'ルー', dir: 'lou', prefix: 'lou', crop: {x: 0, y: 0, w: 1312, h: 1199}, side: 'right'}                // source 1312x1199
  };
  const SRC = {fiona: {w: 1024, h: 1536}, lou: {w: 1312, h: 1199}};   // source png sizes (crop is in these px)
  const cache = new Map();   // url -> 'ok' | 'bad' | Promise
  let box = null, img = null, cur = null, token = 0;

  const faceOf = f => (FACES.includes(f) ? f : (/^0[1-8]$/.test(String(f)) ? FACES[+f - 1] : 'normal'));
  const url = (c, f) => BASE + CHARS[c].dir + '/' + CHARS[c].prefix + '_' + f + '.png';
  function probe(u) {
    const hit = cache.get(u); if (hit === 'ok' || hit === 'bad') return Promise.resolve(hit === 'ok');
    if (hit) return hit;
    const p = new Promise(res => {
      const im = new Image();
      im.onload = () => { cache.set(u, 'ok'); res(true); };
      im.onerror = () => { cache.set(u, 'bad'); res(false); };
      im.src = u;
    });
    cache.set(u, p); return p;
  }
  function preload(c, f) { if (CHARS[c] && typeof Image !== 'undefined') void probe(url(c, faceOf(f))); }
  function ensure() {
    if (box || typeof document === 'undefined' || !document.body) return box;
    box = document.createElement('div'); box.id = 'talkPortrait'; box.setAttribute('aria-hidden', 'true'); box.hidden = true;
    img = document.createElement('img'); img.alt = ''; img.decoding = 'async'; img.draggable = false; box.append(img);
    document.body.append(box); return box;
  }
  // place it right above the dialogue box, whatever its size on phone / tablet / PC
  function layout() {
    if (!box || box.hidden) return;
    const m = document.getElementById('msg'), top = m && m.style.display !== 'none' ? m.getBoundingClientRect().top : innerHeight * 0.9;
    box.style.setProperty('--tpBottom', Math.max(0, innerHeight - top + 4) + 'px');
    box.style.setProperty('--tpAvail', Math.max(80, top - 8) + 'px');
  }
  function hide() { token++; cur = null; if (box) { box.hidden = true; box.removeAttribute('data-char'); box.removeAttribute('data-face'); } }
  async function show(c, f) {
    if (!c || !CHARS[c]) { hide(); return false; }
    if (!ensure()) return false;
    const face = faceOf(f), my = ++token;
    let use = face;
    if (!(await probe(url(c, face)))) {
      if (face !== 'normal' && (console.warn('[TalkPortrait] missing', c, face, '-> normal'), await probe(url(c, 'normal')))) use = 'normal';
      else { if (my === token) hide(); console.warn('[TalkPortrait] no image for', c); return false; }
    }
    if (my !== token) return false;   // a newer page took over while loading
    const k = CHARS[c].crop, st = box.style;
    box.dataset.char = c; box.dataset.face = use; box.dataset.side = CHARS[c].side;
    st.setProperty('--tpAspect', k.w + '/' + k.h);
    img.style.width = (100 * SRC[c].w / k.w) + '%';
    img.style.left = (-100 * k.x / k.w) + '%'; img.style.top = (-100 * k.y / k.h) + '%';
    img.onerror = () => { cache.set(img.src, 'bad'); if (use !== 'normal') void show(c, 'normal'); else hide(); };
    img.src = url(c, use); cur = {char: c, face: use};
    box.hidden = false; layout(); return true;
  }
    // a page: {char, face}; undefined char keeps the current portrait
  function page(p) {
    if (!p) return;
    if (p.char === null) { hide(); return; }
    if (p.char === undefined) { if (cur && p.face !== undefined) void show(cur.char, p.face); return; }
    void show(p.char, p.face);
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', layout); window.addEventListener('orientationchange', layout);
    window.addEventListener('field-talk-end', hide);
  }
  window.TalkPortrait = Object.freeze({FACES, FACE_IDS, chars: () => Object.keys(CHARS), has: c => Boolean(CHARS[c]), faceOf, url, preload, show, hide, page, layout,
    get current() { return cur ? {...cur} : null; }, get element() { return box; }});
})();
