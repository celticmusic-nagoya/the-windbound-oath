/* TalkPortrait — conversation portraits with expressions and blinking, for every character in PortraitRegistry.
 * Ported from feature/asset-emma-01 @ f4456a82 (talk-portrait.js: registry-free display + ownership/generation lifecycle of Issue #16 P2,
 * fix/fiona-lou-portrait-lifecycle-p2 @ 5d915ed9), extended for the common system (Phase 3):
 *   - characters, image paths, framing, side and blink overlays come only from PortraitRegistry (js/field/portrait-registry.js)
 *   - the portrait is a <canvas> at source resolution (crop size): open eyes = the adopted image drawn 1:1, a blink state = the same image +
 *     that state's eye overlays at their source coordinates; the canvas is scaled once by CSS, so image and overlays can never drift apart
 *   - blinking: PortraitBlink (js/field/portrait-blink.js), one timer per portrait, stopped on every face / character change, hide, close, revoke
 *
 * Conversation data (FieldTalk) selects portraits explicitly:
 *     conversation or page:  {char:'aidan', face:'smile', side:'left'}   (page values override the conversation's defaults)
 *     page without `char`  -> the portrait already on screen stays (a `face`-only page just changes its expression)
 *     `char:null`          -> hide the portrait for that page
 *     unknown/missing face -> `normal`; image that fails to load -> `normal`; if that fails too -> no portrait (the dialogue goes on)
 *     side: page/conversation `side` -> the registry default -> 'right'
 * Ownership / requests (unchanged from P2): a conversation OWNS the portrait (open/close by owner id); every request carries a generation number,
 * so anything that finishes after its page is gone changes nothing; a conversation-owned portrait is revoked whenever the dialogue box closes,
 * is replaced (say()), a battle starts, FieldTalk.load() runs, or a story/event-CG scene takes the screen. */
(function () {
  'use strict';
  const R = window.PortraitRegistry, PB = window.PortraitBlink;
  const DIRECT = '__direct', BAD_MS = 15000;
  // story scenes that own the whole screen (event CGs are drawn inside them): a portrait never stays over them
  const SCENE_IDS = ['louIntroScene', 'altarScene'];
  const imgs = new Map(), bad = new Map(), errors = new Map();
  const DEV_OWNER = '__devPortrait'; let devMode = 'auto';
  let box = null, cv = null, owner = null, gen = 0, want = null, cur = null, obs = null;
  const reduced = typeof matchMedia === 'function' ? matchMedia('(prefers-reduced-motion: reduce)') : {matches: false, addEventListener() {}};

  function load(u) {
    if (!u || typeof Image === 'undefined') return Promise.resolve(null);
    const t = bad.get(u); if (t && Date.now() - t < BAD_MS) return Promise.resolve(null);
    if (imgs.has(u)) return imgs.get(u);
    const p = new Promise(res => {
      const im = new Image(); im.decoding = 'async';
      im.onload = () => (im.decode ? im.decode().then(() => res(im), () => res(im)) : res(im));
      im.onerror = () => { errors.set(u, '画像取得または復号に失敗'); res(null); }; im.src = u;
    }).then(im => { if (!im) { imgs.delete(u); bad.set(u, Date.now()); } return im; });
    imgs.set(u, p); return p;
  }
  function preload(c, f) { if (R.has(c)) void load(R.imageUrl(c, f)); }
  async function resolve(c, face) {
    let im = await load(R.imageUrl(c, face)); if (im) return {face, im};
    if (face !== 'normal') { console.warn('[TalkPortrait] missing', c, face, '-> normal'); im = await load(R.imageUrl(c, 'normal')); if (im) return {face: 'normal', im}; }
    console.warn('[TalkPortrait] no image for', c); return null;
  }
  // all overlays of a blinking face, or null (any failure -> that face is shown still)
  async function loadBlink(c, face) {
    const b = R.blinkOf(c, face); if (!b) return null;
    const eyes = {};
    for (const [eye, e] of Object.entries(b.eyes)) { const ims = await Promise.all(e.urls.map(load)); if (ims.some(x => !x)) { console.warn('[TalkPortrait] blink overlay missing', c, face, eye); return null; } eyes[eye] = {box: e.box, ims}; }
    return {seq: b.seq, gap: b.gap, eyes};
  }

  function ensure() {
    if (box || typeof document === 'undefined' || !document.body) return box;
    box = document.createElement('div'); box.id = 'talkPortrait'; box.setAttribute('aria-hidden', 'true'); box.hidden = true;
    cv = document.createElement('canvas'); box.append(cv); document.body.append(box); return box;
  }
  // draw the current portrait at source resolution: crop of the adopted image, plus the eye overlays of `state` (0 = none = the image itself)
  function draw(state) {
    if (!cur || !cv) return;
    const k = R.get(cur.char).crop, ctx = cv.getContext('2d');
    if (cv.width !== k.w || cv.height !== k.h) { cv.width = k.w; cv.height = k.h; }
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.imageSmoothingEnabled = false; ctx.clearRect(0, 0, k.w, k.h);
    ctx.drawImage(cur.im, k.x, k.y, k.w, k.h, 0, 0, k.w, k.h);
    if (state > 0 && cur.blink) for (const e of Object.values(cur.blink.eyes)) ctx.drawImage(e.ims[state - 1], e.box[0] - k.x, e.box[1] - k.y);
    cur.state = state; box.dataset.eye = String(state);
  }
  function stopBlink() { if (cur && cur.ctl) { cur.ctl.stop(); cur.ctl = null; } }
  function canBlink() { return (owner !== DEV_OWNER || devMode !== 'stop' && devMode !== 'frame') && cur && cur.blink && !reduced.matches && !(typeof document !== 'undefined' && document.hidden) && box && !box.hidden; }
  function startBlink() {
    if (!canBlink() || cur.ctl) return;
    const me = cur;
    me.ctl = PB.create({seq: me.blink.seq, gap: owner === DEV_OWNER && devMode === 'loop' ? [400, 400] : me.blink.gap, onState: s => { if (cur === me) { draw(s); if (owner === DEV_OWNER && devMode === 'manual' && s === 0) queueMicrotask(() => { if (cur === me && devMode === 'manual') stopBlink(); }); } }});
    me.ctl.start();
  }
  function hideVisual() { stopBlink(); cur = null; if (box) { box.hidden = true; box.removeAttribute('data-char'); box.removeAttribute('data-face'); box.removeAttribute('data-eye'); } }
  function layout() {
    if (!box || box.hidden) return;
    const m = document.getElementById('msg'), top = m && m.style.display !== 'none' ? m.getBoundingClientRect().top : innerHeight * 0.9;
    box.style.setProperty('--tpBottom', Math.max(0, innerHeight - top + 4) + 'px');
    box.style.setProperty('--tpAvail', Math.max(80, top - 8) + 'px');
  }

  // ---------- ownership ----------
  function revoke() { devMode = 'auto'; owner = null; want = null; gen++; hideVisual(); }
  function open(o) { if (!o) return; owner = o; devMode = o === DEV_OWNER ? 'stop' : 'auto'; want = null; gen++; hideVisual(); watch(); }
  function close(o) { if (o && o === owner) revoke(); }
  const mine = o => (o === undefined ? (owner === null ? (owner = DIRECT) : owner) : o) === owner;

  // ---------- display ----------
  function present(c, f, side) {
    const my = ++gen;
    if (!c || !R.has(c) || !ensure()) { hideVisual(); return Promise.resolve(false); }
    want = c;
    stopBlink();                                         // a blink of the previous face never continues (or finishes) on the new one
    if (cur && cur.char !== c) hideVisual();             // another character: the old one goes first, the new one appears when it is ready
    else if (cur && cur.state) draw(0);                  // same character mid-blink: open eyes until the new face is ready
    const face = R.faceOf(f, c);
    return Promise.all([resolve(c, face), loadBlink(c, face)]).then(([r, bl]) => {
      if (my !== gen) return false;                      // superseded / ended / revoked while loading: change nothing
      if (!r) { hideVisual(); return false; }
      const k = R.get(c).crop;
      cur = {char: c, face: r.face, im: r.im, blink: r.face === face ? bl : null, state: 0, ctl: null};
      box.dataset.char = c; box.dataset.face = r.face; box.dataset.side = R.sideOf(c, side);
      box.style.setProperty('--tpAspect', k.w + '/' + k.h); box.style.setProperty('--tpRatio', String(k.w / k.h));
      draw(0); box.hidden = false; layout(); startBlink(); return true;
    });
  }
  function show(c, f, o, side) { if (!mine(o)) return Promise.resolve(false); return present(c, f, side); }
  function page(p, o) {
    if (!p || !mine(o)) return;
    if (p.char === null) { gen++; want = null; hideVisual(); return; }
    if (p.char === undefined) { if (want && (p.face !== undefined || p.side !== undefined)) void present(want, p.face !== undefined ? p.face : (cur ? cur.face : 'normal'), p.side); return; }
    void present(p.char, p.face, p.side);
  }

  // ---------- conversation-owned portraits end when their dialogue ends, however it ends ----------
  const sceneOpen = () => SCENE_IDS.some(id => { const e = document.getElementById(id); return e && getComputedStyle(e).display !== 'none'; }) || Boolean(window.EventCG && window.EventCG.active);
  function valid() {
    if (owner === null || owner === DIRECT) return;
    if (owner === DEV_OWNER && window.WINDBOUND_DEV && document.body.classList.contains('devPortraitOpen')) {
      if (document.body.classList.contains('battleMode') || window.FieldTalk?.active || sceneOpen()) revoke();
      return;
    }
    const m = document.getElementById('msg'), b = document.body;
    const ok = b.classList.contains('dialogueOpen') && !b.classList.contains('battleMode') && m && getComputedStyle(m).display !== 'none' && m.querySelector('.talkText') && !sceneOpen();
    if (!ok) revoke();
  }
  function watch() {
    if (obs || typeof MutationObserver === 'undefined' || typeof document === 'undefined' || !document.body) return;
    obs = new MutationObserver(valid);
    obs.observe(document.body, {attributes: true, attributeFilter: ['class']});
    const m = document.getElementById('msg'); if (m) obs.observe(m, {childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['style', 'class']});
    for (const id of ['battle', 'attackBattle', ...SCENE_IDS]) { const e = document.getElementById(id); if (e) obs.observe(e, {attributes: true, attributeFilter: ['style', 'class']}); }
  }
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', () => { layout(); valid(); }); window.addEventListener('orientationchange', layout);
    document.addEventListener('visibilitychange', () => { if (document.hidden) { stopBlink(); if (cur && cur.state) draw(0); } else startBlink(); });
    const onMotion = () => { if (reduced.matches) { stopBlink(); if (cur && cur.state) draw(0); } else startBlink(); };
    if (reduced.addEventListener) reduced.addEventListener('change', onMotion); else if (reduced.addListener) reduced.addListener(onMotion);
  }
  window.TalkPortrait = Object.freeze({
    FACES: R.FACES, chars: R.ids, has: R.has, faceOf: R.faceOf, url: R.imageUrl, preload, show, hide: revoke, page, layout, open, close, revoke,
    get current() { return cur ? {char: cur.char, face: cur.face, side: box && box.dataset.side} : null; },
    get owner() { return owner; }, get element() { return box; },
    // QA / dev (read-only w.r.t. the game): blink state, and a blink on demand
    get status() { return {char: cur && cur.char, face: cur && cur.face, side: box && box.dataset.side || null, visible: Boolean(box && !box.hidden), eye: cur ? cur.state : 0, blinkReady: Boolean(cur && cur.blink), blink: cur && cur.ctl ? cur.ctl.status : null, gen, reduced: reduced.matches}; },
    blinkNow() { if (canBlink()) { startBlink(); cur.ctl.blinkNow(); return true; } return false; },
    // DEV controls affect only the dedicated DEV owner; production conversations cannot use them.
    devControl(mode, state = 0) {
      if (!window.WINDBOUND_DEV || owner !== DEV_OWNER || !cur || !['auto','manual','loop','stop','frame'].includes(mode)) return false;
      stopBlink(); devMode = mode; draw(mode === 'frame' ? Math.max(0, Math.min(4, Number(state) || 0)) : 0);
      if (mode !== 'frame' && mode !== 'stop') { startBlink(); if (mode === 'manual') return this.blinkNow(); }
      return true;
    },
    get diagnostics() { return [...errors].map(([url, reason]) => ({url, reason})); },
    // QA: a read-only copy of what the renderer draws for eye state `s` (0 = open) for the portrait on screen (same code path as draw())
    frame(s) {
      if (!cur || !cv) return null; const keep = cur.state, c = document.createElement('canvas'); draw(s); c.width = cv.width; c.height = cv.height; c.getContext('2d').drawImage(cv, 0, 0); draw(keep); return c;
    }
  });
})();
