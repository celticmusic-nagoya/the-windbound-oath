/* TalkPortrait — conversation portraits with expression variants (Fiona / Lou).
 *   Character registry: id -> {name, dir, prefix, crop:{x,y,w,h} (source px, bust framing), side}
 *   Expression IDs shared by all characters: normal smile angry sad surprised worried determined relieved (01..08)
 *   Conversation data (FieldTalk) selects portraits explicitly:
 *     conversation or page:  {char:'fiona', face:'smile'}   (page values override the conversation's defaults)
 *     page without `char`  -> the portrait already on screen stays (a `face`-only page just changes its expression)
 *     `char:null`          -> hide the portrait for that page
 *     unknown/missing face -> `normal`; image that fails to load -> `normal`; if that fails too -> no portrait (the dialogue goes on)
 *   Display: #talkPortrait (fixed, pointer-events:none, below #msg), only while body.dialogueOpen (css/style.css), sits just above #msg.
 *
 *   Ownership / requests (P2, Issue #16):
 *     - A conversation OWNS the portrait: FieldTalk calls open(owner) when a conversation starts and close(owner) when it ends; page(p, owner)
 *       is ignored unless `owner` is the current owner. revoke() (also hide()) takes the portrait away from whoever has it.
 *     - Every image request carries a generation number (`gen`). open / close / revoke / every new page bump it, so an image that finishes
 *       loading (or fails, or finishes its normal-fallback) after its page is gone changes nothing on screen.
 *     - Switching to another character hides the old portrait first and shows the new one only after it is decoded; a same-character face
 *       change keeps the old face until the new one is decoded, then swaps the decoded <img> in one step (no src rewrite -> no blank frame).
 *     - A conversation-owned portrait is revoked on its own whenever the dialogue box is closed, replaced (say()), hidden, a battle starts,
 *       or FieldTalk.load() runs (DOM observers below) — without ever calling FieldTalk.finish() / dispatching `field-talk-end`.
 *     - show()/page()/hide() without an owner are the direct (dev / test) API: they use the owner '__direct' and are not DOM-validated. */
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
  const DIRECT = '__direct', BAD_MS = 15000;
  const imgs = new Map();   // url -> Promise<HTMLImageElement|null> (a decoded <img>, shared: only one portrait is on screen at a time)
  const bad = new Map();    // url -> time of the last failure (not retried for BAD_MS: no request storm while someone taps through)
  let box = null, owner = null, gen = 0, want = null /* character the owner asked for last */, cur = null /* what is on screen */, obs = null;

  const faceOf = f => (FACES.includes(f) ? f : (/^0[1-8]$/.test(String(f)) ? FACES[+f - 1] : 'normal'));
  const url = (c, f) => BASE + CHARS[c].dir + '/' + CHARS[c].prefix + '_' + f + '.png';
  // resolves a decoded <img> or null — never rejects, never touches the display
  function load(u) {
    if (typeof Image === 'undefined') return Promise.resolve(null);
    const t = bad.get(u); if (t && Date.now() - t < BAD_MS) return Promise.resolve(null);
    if (imgs.has(u)) return imgs.get(u);
    const p = new Promise(res => {
      const im = new Image(); im.alt = ''; im.draggable = false;
      im.onload = () => (im.decode ? im.decode().then(() => res(im), () => res(im)) : res(im));
      im.onerror = () => res(null);
      im.src = u;
    }).then(im => { if (!im) { imgs.delete(u); bad.set(u, Date.now()); } return im; });
    imgs.set(u, p); return p;
  }
  function preload(c, f) { if (CHARS[c]) void load(url(c, faceOf(f))); }
  // face -> {face, im}; falls back to normal, then null. Pure with respect to the display: a stale caller just throws the result away.
  async function resolve(c, face) {
    let im = await load(url(c, face)); if (im) return {face, im};
    if (face !== 'normal') { console.warn('[TalkPortrait] missing', c, face, '-> normal'); im = await load(url(c, 'normal')); if (im) return {face: 'normal', im}; }
    console.warn('[TalkPortrait] no image for', c); return null;
  }
  function ensure() {
    if (box || typeof document === 'undefined' || !document.body) return box;
    box = document.createElement('div'); box.id = 'talkPortrait'; box.setAttribute('aria-hidden', 'true'); box.hidden = true;
    document.body.append(box); return box;
  }
  function hideVisual() { cur = null; if (box) { box.hidden = true; box.replaceChildren(); box.removeAttribute('data-char'); box.removeAttribute('data-face'); } }
  // place it right above the dialogue box, whatever its size on phone / tablet / PC
  function layout() {
    if (!box || box.hidden) return;
    const m = document.getElementById('msg'), top = m && m.style.display !== 'none' ? m.getBoundingClientRect().top : innerHeight * 0.9;
    box.style.setProperty('--tpBottom', Math.max(0, innerHeight - top + 4) + 'px');
    box.style.setProperty('--tpAvail', Math.max(80, top - 8) + 'px');
  }

  // ---------- ownership ----------
  function revoke() { owner = null; want = null; gen++; hideVisual(); }
  function open(o) { if (!o) return; owner = o; want = null; gen++; hideVisual(); watch(); }
  function close(o) { if (o && o === owner) revoke(); }
  const mine = o => (o === undefined ? (owner === null ? (owner = DIRECT) : owner) : o) === owner;

  // ---------- display ----------
  function present(c, f) {
    const my = ++gen;
    if (!c || !CHARS[c] || !ensure()) { hideVisual(); return Promise.resolve(false); }
    want = c;
    if (cur && cur.char !== c) hideVisual();   // another character: the old one goes first, the new one appears when it is ready
    const face = faceOf(f);
    return resolve(c, face).then(r => {
      if (my !== gen) return false;            // superseded / ended / revoked while loading: change nothing
      if (!r) { hideVisual(); return false; }
      const k = CHARS[c].crop, im = r.im;
      im.style.width = (100 * SRC[c].w / k.w) + '%'; im.style.left = (-100 * k.x / k.w) + '%'; im.style.top = (-100 * k.y / k.h) + '%';
      box.dataset.char = c; box.dataset.face = r.face; box.dataset.side = CHARS[c].side;
      box.style.setProperty('--tpAspect', k.w + '/' + k.h); box.style.setProperty('--tpRatio', String(k.w / k.h));
      box.replaceChildren(im); cur = {char: c, face: r.face};
      box.hidden = false; layout(); return true;
    });
  }
  function show(c, f, o) { if (!mine(o)) return Promise.resolve(false); return present(c, f); }
  // a page: {char, face}; undefined char keeps the owner's character
  function page(p, o) {
    if (!p || !mine(o)) return;
    if (p.char === null) { gen++; want = null; hideVisual(); return; }
    if (p.char === undefined) { if (want && p.face !== undefined) void present(want, p.face); return; }
    void present(p.char, p.face);
  }

  // ---------- conversation-owned portraits end when their dialogue ends, however it ends ----------
  function valid() {
    if (owner === null || owner === DIRECT) return;
    const m = document.getElementById('msg'), b = document.body;
    const ok = b.classList.contains('dialogueOpen') && !b.classList.contains('battleMode') && m && getComputedStyle(m).display !== 'none' && m.querySelector('.talkText');
    if (!ok) revoke();
  }
  function watch() {
    if (obs || typeof MutationObserver === 'undefined' || typeof document === 'undefined' || !document.body) return;
    obs = new MutationObserver(valid);
    obs.observe(document.body, {attributes: true, attributeFilter: ['class']});
    const m = document.getElementById('msg'); if (m) obs.observe(m, {childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['style', 'class']});
    for (const id of ['battle', 'attackBattle']) { const e = document.getElementById(id); if (e) obs.observe(e, {attributes: true, attributeFilter: ['style', 'class']}); }
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', () => { layout(); valid(); }); window.addEventListener('orientationchange', layout);
  }
  window.TalkPortrait = Object.freeze({FACES, FACE_IDS, chars: () => Object.keys(CHARS), has: c => Boolean(CHARS[c]), faceOf, url, preload, show, hide: revoke, page, layout, open, close, revoke,
    get current() { return cur ? {...cur} : null; }, get owner() { return owner; }, get element() { return box; }});
})();
