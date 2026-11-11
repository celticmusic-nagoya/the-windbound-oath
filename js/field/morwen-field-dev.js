/* MORWEN-PRODUCTION-73: DEV-only Morwen field follower (right walk = MORWEN-PIXEL-72, left = provisional mirror).
 * Opt-in only: requires window.WINDBOUND_DEV === true AND the URL flag ?morwenField=1. Otherwise this file returns
 * immediately: no globals, no DOM, no timers, no reads/writes of saves, party, story flags or other actors.
 * Art is read in place from assets/candidates/morwen-right-walk/72/ (approved candidate; never copied or modified here).
 * Not implemented on purpose (no official art yet): up/down walk, idle. Up/down travel keeps the last side facing;
 * standing still holds walk F00 (labelled provisional). Join timing is not decided: nothing here touches PartyManager.
 * Optional DEV URL params: morwenSize=48|96 (default 48, 1:1 pixels), morwenFoot=<row> (default 63 = (24,63) contract),
 * morwenFps=<n> (default 8, sets the distance stride for the nominal 300 px/s pointer speed), morwenStride=<px> (overrides). */
(function () {
  'use strict';
  const q = typeof location !== 'undefined' ? location.search : '';
  if (window.WINDBOUND_DEV !== true || !/[?&]morwenField=1(?:&|$)/.test(q)) return;
  const num = (k, d) => { const m = new RegExp('[?&]' + k + '=([\\d.]+)').exec(q); const v = m ? Number(m[1]) : NaN; return Number.isFinite(v) && v > 0 ? v : d; };
  const SIZE = num('morwenSize', 48) === 96 ? 96 : 48;
  const SCALE = SIZE === 96 ? 0.5 : 1;                       // both render at 48x64 world px
  const FOOT_ROW = num('morwenFoot', 63);                    // 48x64 coordinates
  const FRAMES = 6, FPS = num('morwenFps', 8), NOMINAL_SPEED = 300;   // FieldMovement pointerStep 5 px/frame @ 60 Hz
  const STRIDE = num('morwenStride', NOMINAL_SPEED * FRAMES / FPS);  // world px per 6-frame cycle (default 225 => 8 fps at 300 px/s)
  const ART_STRIDE_48 = 18;                                  // planted foot travels 3 px/frame at 48x64 (6 px at 96x128) -> 18 px per cycle
  const BASE = 'assets/candidates/morwen-right-walk/72/';
  const frames = Object.freeze(Array.from({length: FRAMES}, (_, i) => Object.freeze({
    key: 'morwen_walk_right_' + String(i + 1).padStart(2, '0'),
    path: BASE + 'morwen_right_walk_' + String(i).padStart(2, '0') + '_' + (SIZE === 96 ? '96x128' : '48x64') + '.png',
    width: SIZE, height: SIZE === 96 ? 128 : 64, scale: SCALE,
    anchor: Object.freeze([SIZE / 2, SIZE === 96 ? FOOT_ROW * 2 : FOOT_ROW])})));
  const phase = (dist) => Math.floor((dist || 0) / (STRIDE / FRAMES)) % FRAMES;
  const mirrorLeft = true;   // provisional: the official left set (bag on the correct side) is MORWEN-ASSET-74

  const st = {el: null, imgs: [], x: 0, y: 0, dist: 0, face: 'right', frame: -1, ready: false, trail: [], raf: 0, map: null};
  function playerFeet() {
    const p = document.getElementById('forestPlayer');
    if (!p || !p.offsetParent) return null;
    const ax = window.FieldMovement?.settings?.anchorX ?? 17, ay = window.FieldMovement?.settings?.anchorY ?? 42;
    const x = parseFloat(p.style.left) + ax, y = parseFloat(p.style.top) + ay;
    return Number.isFinite(x) && Number.isFinite(y) ? {x, y} : null;   // before the map places the player
  }
  function mount() {
    const world = document.getElementById('forestWorld');
    if (st.el || !world) return Boolean(st.el);
    const d = document.createElement('div');
    d.id = 'forestMorwenDev'; d.setAttribute('aria-hidden', 'true'); d.dataset.devOnly = 'morwen';
    Object.assign(d.style, {position: 'absolute', left: '0px', top: '0px', width: '0px', height: '0px', pointerEvents: 'none'});
    for (const f of frames) {
      const im = new Image(); im.alt = ''; im.draggable = false; im.hidden = true; im.className = 'morwen-field-dev-frame';
      Object.assign(im.style, {position: 'absolute', width: f.width * f.scale + 'px', height: f.height * f.scale + 'px',
        left: -f.anchor[0] * f.scale + 'px', top: -f.anchor[1] * f.scale + 'px', imageRendering: 'pixelated', pointerEvents: 'none',
        transformOrigin: f.anchor[0] * f.scale + 'px 0px'});
      im.src = f.path; d.appendChild(im); st.imgs.push(im);
    }
    const tag = document.createElement('span'); tag.textContent = 'DEV モルウェン（右=正式72／左=暫定ミラー／上下・待機=未制作）';
    Object.assign(tag.style, {position: 'absolute', left: '-60px', top: '-84px', font: '9px/1 sans-serif', color: '#fff', background: 'rgba(0,0,0,.55)', padding: '1px 3px', whiteSpace: 'nowrap', pointerEvents: 'none'});
    d.appendChild(tag);
    world.appendChild(d); st.el = d;
    Promise.all(st.imgs.map(im => im.decode ? im.decode().catch(() => {}) : 0)).then(() => { st.ready = true; });
    return true;
  }
  function tick() {
    st.raf = requestAnimationFrame(tick);
    const feet = playerFeet();
    if (!feet || !mount()) { if (st.el) st.el.style.display = 'none'; return; }
    st.el.style.display = 'block';
    const last = st.trail[st.trail.length - 1];
    if (!last || Math.hypot(feet.x - last.x, feet.y - last.y) > 0.5) st.trail.push(feet);
    if (Math.hypot(feet.x - st.trail[st.trail.length - 1].x, feet.y - st.trail[st.trail.length - 1].y) > 160) st.trail = [feet];   // map change / teleport
    if (st.trail.length > 240) st.trail.shift();
    // follow 44 px of path behind the player (Fiona keeps about 48)
    let need = 44, target = st.trail[0];
    for (let i = st.trail.length - 1; i > 0; i--) {
      const a = st.trail[i], b = st.trail[i - 1], seg = Math.hypot(a.x - b.x, a.y - b.y);
      if (seg >= need) { const t = need / seg; target = {x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t}; break; }
      need -= seg; target = b;
    }
    if (st.map === null || !Number.isFinite(st.x) || Math.hypot(target.x - st.x, target.y - st.y) > 160) { st.x = target.x; st.y = target.y; st.map = 1; }
    const dx = target.x - st.x, dy = target.y - st.y, d = Math.hypot(dx, dy);
    st.x = target.x; st.y = target.y;
    if (d > 0.05) { st.dist += d; if (Math.abs(dx) > 0.05) st.face = dx > 0 ? 'right' : 'left'; }   // up/down travel keeps the side facing
    const moving = d > 0.05;
    const f = moving ? phase(st.dist) : 0;                                                          // standing: walk F00 (no idle art yet)
    if (f !== st.frame) { if (st.imgs[st.frame]) st.imgs[st.frame].hidden = true; st.frame = f; }
    const im = st.imgs[f]; im.hidden = !st.ready;
    im.style.transform = st.face === 'left' && mirrorLeft ? 'scaleX(-1)' : '';
    st.el.style.left = Math.round(st.x) + 'px'; st.el.style.top = Math.round(st.y) + 'px';
    st.el.style.zIndex = String(Math.round(st.y));
    st.el.dataset.frame = String(f); st.el.dataset.face = st.face; st.el.dataset.moving = String(moving);
  }
  window.MorwenFieldDev = Object.freeze({
    frames, size: SIZE, scale: SCALE, footRow: FOOT_ROW, fps: FPS, stride: STRIDE, artStride48: ART_STRIDE_48, nominalSpeed: NOMINAL_SPEED,
    phase, mirrorLeft,
    // ground covered per displayed frame minus the planted foot's drawn travel (world px; 48x64 art is 1:1 world px)
    footSlidePerFrame: () => STRIDE / FRAMES - ART_STRIDE_48 / FRAMES,
    state: () => ({x: st.x, y: st.y, dist: st.dist, face: st.face, frame: st.frame, ready: st.ready, mounted: Boolean(st.el)})});
  if (typeof requestAnimationFrame === 'function') st.raf = requestAnimationFrame(tick);
})();
