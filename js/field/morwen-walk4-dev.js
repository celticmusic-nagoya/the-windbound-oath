/* MORWEN-WALK-4DIR: DEV-only Morwen field walker, 12 frames per facing (left 74G / right 75 / up 76; down 77 BLOCKED).
 * Opt-in only: window.WINDBOUND_DEV === true AND the URL flag ?morwenWalk4=1. Otherwise the file returns at once:
 * no globals, no DOM, no timers, no save / party / story access. Production display and other actors are unchanged.
 * Art is read in place from assets/candidates/ (candidates; never copied or modified here).
 *
 * Frame clock (one float phase `ph` in frames, 12 per cycle, shared by every facing):
 *   field mode (default): distance-linked, ph += distance / (STRIDE / 12); STRIDE 180 world px (Aidan side convention,
 *                         20 frames/s at 300 px/s). Movement speed is NOT changed (FieldMovement untouched).
 *   event mode:           time-linked 840 ms cycle (70 ms/frame) while moving, for slow scripted walks.
 *   turn:  facing changes, ph does not -> the new facing continues at the same leg phase (no frame jump).
 *   stop:  after 100 ms without movement the clock runs on at the event rate to the next contact frame (F00 / F06)
 *          and holds there; resume continues from the held phase. The shown frame only ever advances by 0 or +1 per tick
 *          at <= 300 px/s and >= 30 Hz (max 10 px/tick < 15 px/frame).
 *   down:  no approved front art (MORWEN-WALK-DOWN-77 BLOCKED) -> down travel keeps the last side facing (provisional).
 * Optional DEV URL params: morwenStride=<px> (default 180), morwenMode=event, morwenSize=48|96, morwenFoot=<row 48x64>. */
(function () {
  'use strict';
  const q = typeof location !== 'undefined' ? location.search : '';
  if (window.WINDBOUND_DEV !== true || !/[?&]morwenWalk4=1(?:&|$)/.test(q)) return;
  const num = (k, d) => { const m = new RegExp('[?&]' + k + '=([\\d.]+)').exec(q); const v = m ? Number(m[1]) : NaN; return Number.isFinite(v) && v > 0 ? v : d; };
  const NF = 12, CYCLE_MS = 840, FRAME_MS = CYCLE_MS / NF, STOP_MS = 100;
  const SIZE = num('morwenSize', 48) === 96 ? 96 : 48;
  const SCALE = SIZE === 96 ? 0.5 : 1;
  const FOOT = num('morwenFoot', 62);                      // 48x64: feet on row 61 in every facing -> bottom edge 62
  const STRIDE = num('morwenStride', 180);
  const C = 'assets/candidates/';
  const BANKS = Object.freeze({
    left: {dir: C + 'morwen-left-walk/74G/', name: (i, s) => `morwen_left_walk_74G_12f_${i}_${s}.png`, task: 'MORWEN-ASSET-74G'},
    right: {dir: C + 'morwen-right-walk/75/', name: (i, s) => `morwen_right_walk_75_12f_${i}_${s}.png`, task: 'MORWEN-WALK-RIGHT-75'},
    up: {dir: C + 'morwen-up-walk/76/', name: (i, s) => `morwen_up_walk_76_12f_${i}_${s}.png`, task: 'MORWEN-WALK-UP-76'},
    down: null,
  });
  const sz = SIZE === 96 ? '96x128' : '48x64';
  const frames = Object.freeze(Object.fromEntries(Object.entries(BANKS).filter(([, b]) => b).map(([face, b]) =>
    [face, Object.freeze(Array.from({length: NF}, (_, i) => Object.freeze({
      path: b.dir + b.name(String(i).padStart(2, '0'), sz), width: SIZE, height: SIZE === 96 ? 128 : 64, scale: SCALE,
      anchor: Object.freeze([SIZE / 2, SIZE === 96 ? FOOT * 2 : FOOT])})))])));

  /* pure state machine (no DOM): step({dx, dy, dt}) -> {face, frame, moving} */
  function createState(opt = {}) {
    const s = {ph: 0, face: opt.face || 'right', side: opt.face === 'left' ? 'left' : 'right', mode: opt.mode || 'field',
      stride: opt.stride || STRIDE, idle: 0, settling: false};
    const per = () => s.stride / NF;
    function faceFor(dx, dy) {
      const ax = Math.abs(dx), ay = Math.abs(dy);
      if (ax < 0.01 && ay < 0.01) return s.face;
      if (ay > ax * 1.2) {
        if (dy < 0) return 'up';
        return s.side;                                   // down: BLOCKED -> keep the last side facing
      }
      if (ax > ay * 1.2 || s.face === 'up') { s.side = dx > 0 ? 'right' : 'left'; return ax > ay * 1.2 ? s.side : s.face; }
      return s.face;                                     // diagonal dead zone: keep facing (no flicker)
    }
    function step({dx = 0, dy = 0, dt = 1000 / 60}) {
      const d = Math.hypot(dx, dy), moving = d > 0.05;
      if (moving) {
        s.idle = 0; s.settling = false;
        s.face = faceFor(dx, dy);
        s.ph += s.mode === 'event' ? dt / FRAME_MS : d / per();
      } else {
        s.idle += dt;
        if (s.idle >= STOP_MS) {
          const fr = Math.floor(s.ph) % NF;
          if (fr % 6 !== 0 || s.settling) {             // run on to the next contact frame (F00 / F06) at the event rate
            s.settling = true;
            const next = Math.floor(s.ph / 6) * 6 + 6;
            s.ph = Math.min(next, s.ph + dt / FRAME_MS);
            if (s.ph >= next) s.settling = false;
          }
        }
      }
      s.ph %= NF * 1000;
      return {face: s.face, frame: Math.floor(s.ph) % NF, moving, settling: s.settling};
    }
    return Object.freeze({step, setMode: m => { s.mode = m === 'event' ? 'event' : 'field'; }, get: () => ({...s})});
  }

  const core = createState({mode: /[?&]morwenMode=event(?:&|$)/.test(q) ? 'event' : 'field'});
  const st = {el: null, imgs: {}, shown: null, x: NaN, y: NaN, trail: [], last: 0, ready: false};
  function playerFeet() {
    const p = document.getElementById('forestPlayer');
    if (!p || !p.offsetParent) return null;
    const ax = window.FieldMovement?.settings?.anchorX ?? 17, ay = window.FieldMovement?.settings?.anchorY ?? 42;
    const x = parseFloat(p.style.left) + ax, y = parseFloat(p.style.top) + ay;
    return Number.isFinite(x) && Number.isFinite(y) ? {x, y} : null;
  }
  function mount() {
    const world = document.getElementById('forestWorld');
    if (st.el || !world) return Boolean(st.el);
    const d = document.createElement('div');
    d.id = 'forestMorwenWalk4Dev'; d.setAttribute('aria-hidden', 'true'); d.dataset.devOnly = 'morwen-walk4';
    Object.assign(d.style, {position: 'absolute', left: '0px', top: '0px', width: '0px', height: '0px', pointerEvents: 'none'});
    const all = [];
    for (const [face, list] of Object.entries(frames)) {
      st.imgs[face] = list.map(f => {
        const im = new Image(); im.alt = ''; im.draggable = false; im.hidden = true;
        Object.assign(im.style, {position: 'absolute', width: f.width * f.scale + 'px', height: f.height * f.scale + 'px',
          left: -f.anchor[0] * f.scale + 'px', top: -f.anchor[1] * f.scale + 'px', imageRendering: 'pixelated', pointerEvents: 'none'});
        im.src = f.path; d.appendChild(im); all.push(im); return im;
      });
    }
    const tag = document.createElement('span'); tag.textContent = 'DEV モルウェン12コマ（左74G／右75／上76／下=未制作）';
    Object.assign(tag.style, {position: 'absolute', left: '-60px', top: '-84px', font: '9px/1 sans-serif', color: '#fff', background: 'rgba(0,0,0,.55)', padding: '1px 3px', whiteSpace: 'nowrap', pointerEvents: 'none'});
    d.appendChild(tag); world.appendChild(d); st.el = d;
    Promise.all(all.map(im => im.decode ? im.decode().catch(() => {}) : 0)).then(() => { st.ready = true; });
    return true;
  }
  function tick(now) {
    requestAnimationFrame(tick);
    const dt = st.last ? Math.min(100, now - st.last) : 1000 / 60; st.last = now;
    const feet = playerFeet();
    if (!feet || !mount()) { if (st.el) st.el.style.display = 'none'; return; }
    st.el.style.display = 'block';
    const lastT = st.trail[st.trail.length - 1];
    if (!lastT || Math.hypot(feet.x - lastT.x, feet.y - lastT.y) > 0.5) st.trail.push(feet);
    if (Math.hypot(feet.x - st.trail[st.trail.length - 1].x, feet.y - st.trail[st.trail.length - 1].y) > 160) st.trail = [feet];
    if (st.trail.length > 240) st.trail.shift();
    let need = 44, target = st.trail[0];
    for (let i = st.trail.length - 1; i > 0; i--) {
      const a = st.trail[i], b = st.trail[i - 1], seg = Math.hypot(a.x - b.x, a.y - b.y);
      if (seg >= need) { const t = need / seg; target = {x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t}; break; }
      need -= seg; target = b;
    }
    if (!Number.isFinite(st.x) || Math.hypot(target.x - st.x, target.y - st.y) > 160) { st.x = target.x; st.y = target.y; }
    const r = core.step({dx: target.x - st.x, dy: target.y - st.y, dt});
    st.x = target.x; st.y = target.y;
    const im = st.imgs[r.face][r.frame];
    if (st.shown !== im) { if (st.shown) st.shown.hidden = true; st.shown = im; }
    im.hidden = !st.ready;
    st.el.style.left = Math.round(st.x) + 'px'; st.el.style.top = Math.round(st.y) + 'px';
    st.el.style.zIndex = String(Math.round(st.y));
    st.el.dataset.face = r.face; st.el.dataset.frame = String(r.frame); st.el.dataset.moving = String(r.moving);
  }
  window.MorwenWalk4Dev = Object.freeze({
    frames, banks: BANKS, frameCount: NF, cycleMs: CYCLE_MS, stride: STRIDE, size: SIZE, footRow: FOOT, createState,
    setMode: m => core.setMode(m), state: () => core.get()});
  if (typeof requestAnimationFrame === 'function') requestAnimationFrame(tick);
})();
