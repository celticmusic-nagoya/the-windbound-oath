// DEV-only portrait lab. Uses the production registry, canvas and blink controller; never writes game/save state.
(() => {
  'use strict';
  if (!window.WINDBOUND_DEV) return;
  const R = PortraitRegistry, P = TalkPortrait, OWNER = '__devPortrait';
  let root, panel, status, faces, chars, timer = null, seq = 0, char, face = 'normal', side = 'left', mode = 'stop', pending = false;
  const q = s => root.querySelector(s);
  function button(parent, text, fn, id) {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = text;
    if (id) b.id = id; b.onclick = fn; parent.append(b); return b;
  }
  const active = () => Boolean(root?.open);
  function close() {
    seq++; clearInterval(timer); timer = null;
    if (P.owner === OWNER) P.close(OWNER);
    if (P.element && root?.contains(P.element)) document.body.append(P.element);
    if (root?.open) root.close();
    document.body.classList.remove('devPortraitOpen');
  }
  function update() {
    if (!active()) return;
    if (P.owner !== OWNER || document.body.classList.contains('battleMode') || window.FieldTalk?.active || window.FieldScene?.running) { close(); return; }
    const s = P.status; if (mode === 'manual' && !s.blink) mode = 'stop';
    const wait = s.blink?.nextAt ? Math.max(0, (s.blink.nextAt - Date.now()) / 1000).toFixed(1) + '秒' : '-';
    status.textContent = `${s.char || char} / ${s.face || face} / 素材: ${!R.blinkOf(char,face) ? '未実装・静止画' : s.blinkReady ? 'READY' : pending ? 'LOADING' : 'MISSING'}\n${s.blink?.timers ? 'RUNNING' : 'STOPPED'} / 目: ${s.eye} / 次回: ${wait}\nreduced-motion: ${s.reduced ? 'ON（再生停止）' : 'OFF'} / hidden: ${document.hidden} / ${mode}`;
    const errors = P.diagnostics;
    q('#devPortraitErrors').textContent = errors.map(e => `${e.url}: ${e.reason}`).join('\n');
  }
  async function show() {
    const mine = ++seq;
    mode = 'stop'; pending = true;
    await P.show(char, face, OWNER, side);
    if (mine !== seq || !active() || P.owner !== OWNER) return;
    pending = false;
    if (P.element) root.append(P.element); // native modal top layer: use the actual production canvas, not a copy
    P.devControl('stop');
    const still=!R.blinkOf(char,face);
    for (const id of ['devPortraitBlink','devPortraitAuto','devPortraitLoop']) q('#'+id).disabled=still;
    q('#devPortraitFrames').querySelectorAll('button').forEach((b,i)=>b.disabled=still&&i>0);
    root.dataset.side = side;
    P.layout(); update();
  }
  function select(id) {
    if (!R.has(id)) return;
    char = id; face = R.get(id).faces[0]; faces.textContent = '';
    for (const f of R.get(id).faces) button(faces, f, () => { face = f; void show(); });
    void show();
  }
  function control(next, state) { mode = P.devControl(next, state) ? next : 'stop'; update(); }
  function build() {
    root = document.createElement('dialog'); root.id = 'devPortraitStage'; root.setAttribute('aria-label', '立ち絵・モーションテスト');
    panel = document.createElement('section'); panel.id = 'devPortraitControls'; root.append(panel);
    const h = document.createElement('h3'); h.textContent = '立ち絵・モーションテスト'; panel.append(h);
    chars = document.createElement('div'); chars.id = 'devPortraitChars'; panel.append(chars);
    faces = document.createElement('div'); faces.id = 'devPortraitFaces'; panel.append(faces);
    const actions = document.createElement('div'); panel.append(actions);
    button(actions, '左表示', () => { side = 'left'; void show(); }, 'devPortraitLeft');
    button(actions, '右表示', () => { side = 'right'; void show(); }, 'devPortraitRight');
    button(actions, '今すぐ瞬き', () => control('manual'), 'devPortraitBlink');
    button(actions, '自動瞬き（3〜6秒）', () => control('auto'), 'devPortraitAuto');
    button(actions, '連続テスト', () => control('loop'), 'devPortraitLoop');
    button(actions, '停止・開眼', () => control('stop'), 'devPortraitStop');
    const frames = document.createElement('div'); frames.id = 'devPortraitFrames'; panel.append(frames);
    for (let i = 0; i <= 4; i++) button(frames, `フレーム ${i}`, () => control('frame', i));
    status = document.createElement('pre'); status.id = 'devPortraitStatus'; panel.insertBefore(status, chars);
    const errors = document.createElement('pre'); errors.id = 'devPortraitErrors'; panel.append(errors);
    const toggle = button(root, '操作パネル', () => { root.classList.toggle('folded'); toggle.setAttribute('aria-expanded', String(!root.classList.contains('folded'))); }, 'devPortraitToggle');
    toggle.setAttribute('aria-controls', panel.id);
    button(root, '閉じる', close, 'devPortraitClose');
    root.addEventListener('cancel', e => { e.preventDefault(); close(); });
    root.addEventListener('close', () => { if (!root.open && document.body.classList.contains('devPortraitOpen')) close(); });
    document.body.append(root);
  }
  function open() {
    if (!window.WINDBOUND_DEV || P.owner && P.owner !== OWNER || window.FieldTalk?.active || window.FieldScene?.running || document.body.classList.contains('battleMode') || document.body.classList.contains('dialogueOpen') || window.LoadingInput?.busy) { hint.textContent = '会話・イベント・読み込みが終わってから開いてください。'; return false; }
    if (!root) build();
    chars.textContent = '';
    const ids = [...new Set([...R.ids(), 'aidan', 'fiona', 'lou', 'emma'])];
    const names = {aidan: 'エイダン', fiona: 'フィオナ', lou: 'ルー', emma: 'エマ'};
    for (const id of ids) {
      const b = button(chars, (R.get(id)?.name || names[id] || id) + (R.has(id) ? '' : '（未実装）'), () => select(id));
      b.disabled = !R.has(id); b.dataset.char = id;
    }
    document.getElementById('devPanel').style.display = 'none';
    window.dispatchEvent(new Event('loading-input-lock')); // cancel held walking/navigation without changing game state or input policy
    document.body.classList.add('devPortraitOpen');
    root.classList.toggle('folded', matchMedia('(orientation:landscape) and (max-height:600px)').matches);
    q('#devPortraitToggle').setAttribute('aria-expanded', String(!root.classList.contains('folded')));
    root.showModal(); P.open(OWNER); select(R.has(char) ? char : R.ids()[0]);
    clearInterval(timer); timer = setInterval(update, 100); return true;
  }
  // Installed before InputManager: modal keys cannot move the player or trigger game shortcuts.
  for (const type of ['keydown', 'keyup']) window.addEventListener(type, e => {
    if (!active()) return;
    if (e.key === 'Escape') { e.preventDefault(); close(); }
    e.stopImmediatePropagation();
  }, true);
  window.LoadCoordinator?.onInvalidate(close);
  window.addEventListener('field-talk', close);
  const entry = button(document.getElementById('devPanel'), '立ち絵・モーションテスト', open, 'devPortraitTest');
  const hint = document.createElement('p'); entry.after(hint);
  entry.className = 'dev-only-command';
  window.DevPortraitTest = Object.freeze({open, close, get active() { return active(); }, get timers() { return timer === null ? 0 : 1; }});
})();
