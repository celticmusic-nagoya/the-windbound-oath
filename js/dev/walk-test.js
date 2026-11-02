/* DEV-only inspector; production PNGs and FieldWalkMotion own the animation. */
(() => {
  'use strict';
  if (!window.WINDBOUND_DEV) return;
  const W = window.FieldWalkMotion;
  const S = {group: 'ally', actor: 'aidan', direction: 'down', speed: 1, time: 0, index: 0, playing: false, raf: null, last: null, generation: 0, def: null, zoom: 1, width: 0, height: 0, ready: false};
  const images = new Map(), reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let root;
  const q = selector => root.querySelector(selector);
  const active = () => Boolean(root?.open);
  function pause() {
    if (S.raf != null) cancelAnimationFrame(S.raf);
    S.raf = null; S.playing = false; S.last = null;
    if (root) { q('[data-walk=play]').setAttribute('aria-pressed', 'false'); root.dataset.playing = 'false'; }
  }
  function info() {
    if (!root || !S.def) return;
    q('[data-walk=count]').textContent = `${S.index + 1} / ${S.def.frames.length}`;
    q('[data-walk=source]').textContent = `${S.def.note} / ${S.def.frames[S.index].url}`;
    q('[data-walk=policy]').textContent = (S.def.kind === 'distance' ? `周期 ${S.def.stride} world・基準速度 ${S.def.speed()} world/s` : `実ゲーム設定 ${S.def.fps} コマ/秒`) + (reduced.matches ? ' ／ 動きを減らす設定：コマ送りで確認' : '');
    q('[data-walk=play]').disabled = !S.ready || reduced.matches;
  }
  function render() {
    if (!S.def || !S.ready || !active()) return;
    const motion = W.frameAt(S.def, S.time), frame = S.def.frames[S.index], image = q('img');
    image.hidden = false;
    if (image.getAttribute('src') !== frame.url) image.src = frame.url;
    image.style.width = `${frame.width * frame.scale * S.zoom}px`;
    image.style.height = `${frame.height * frame.scale * S.zoom}px`;
    image.style.left = `${S.width / 2 - frame.anchor[0] * frame.scale * S.zoom}px`;
    image.style.top = `${S.height * .8 - frame.anchor[1] * frame.scale * S.zoom}px`;
    image.style.transformOrigin = `${frame.anchor[0] * frame.scale * S.zoom}px ${frame.anchor[1] * frame.scale * S.zoom}px`;
    image.style.transform = `translateY(${-motion.lift * S.zoom}px)` + (S.def.flip ? ' scaleX(-1)' : '');
    image.dataset.frame = String(S.index + 1);
    info();
  }
  function layout() {
    if (!active() || !S.def) return;
    const stage = q('.walkStage'); S.width = stage.clientWidth; S.height = stage.clientHeight;
    const widths = S.def.frames.map(f => f.width * f.scale);
    const above = S.def.frames.map(f => f.anchor[1] * f.scale + (S.def.art?.air || 0) + 5);
    const below = S.def.frames.map(f => (f.height - f.anchor[1]) * f.scale + 5);
    S.zoom = Math.min(3, (S.width - 20) / Math.max(...widths), S.height * .76 / Math.max(...above), S.height * .16 / Math.max(...below));
    render();
  }
  function tick(now) {
    S.raf = null;
    if (!active() || !S.playing || !S.ready) return;
    if (S.last != null) S.time += (now - S.last) / 1000 * S.speed;
    S.last = now; S.index = W.frameAt(S.def, S.time).index; render();
    S.raf = requestAnimationFrame(tick);
  }
  function play() {
    if (!active() || !S.ready || reduced.matches) return;
    pause(); S.playing = true; root.dataset.playing = 'true';
    q('[data-walk=play]').setAttribute('aria-pressed', 'true');
    S.raf = requestAnimationFrame(tick);
  }
  function step(delta) {
    if (!S.ready) return;
    pause(); S.index = (S.index + delta + S.def.frames.length) % S.def.frames.length;
    S.time = W.frameTime(S.def, S.index) + 1e-8; render();
  }
  function preload(url) {
    if (!images.has(url)) images.set(url, new Promise((resolve, reject) => {
      const image = new Image(); image.onload = () => resolve(image);
      image.onerror = () => reject(new Error(`読み込み失敗: ${url}`)); image.src = url;
    }));
    return images.get(url);
  }
  async function select() {
    pause(); S.ready = false; S.time = 0; S.index = 0;
    const generation = ++S.generation;
    S.def = W.resolve(S.group, S.actor, S.direction);
    q('img').hidden = true; q('[data-walk=error]').textContent = '';
    root.dataset.actor = S.actor; root.dataset.direction = S.direction;
    for (const b of root.querySelectorAll('[data-direction]')) b.setAttribute('aria-pressed', String(b.dataset.direction === S.direction));
    for (const b of root.querySelectorAll('[data-walk=prev],[data-walk=next]')) b.disabled = true;
    if (!S.def) { q('[data-walk=error]').textContent = '実ゲームの歩行設定がありません。'; return; }
    info();
    try {
      await Promise.all(S.def.frames.map(f => preload(f.url)));
      if (!active() || generation !== S.generation) return;
      S.ready = true;
      for (const b of root.querySelectorAll('[data-walk=prev],[data-walk=next]')) b.disabled = false;
      layout();
    } catch (error) {
      if (!active() || generation !== S.generation) return;
      q('[data-walk=error]').textContent = error.message; info();
    }
  }
  function characters() {
    const select = q('[data-walk=actor]'); select.textContent = '';
    for (const actor of W.catalog(S.group)) select.add(new Option(actor.label, actor.id));
    if (![...select.options].some(o => o.value === S.actor)) S.actor = select.options[0]?.value;
    select.value = S.actor;
  }
  function close() {
    pause(); ++S.generation; S.ready = false; images.clear();
    if (root) { q('img').hidden = true; q('img').removeAttribute('src'); if (root.open) root.close(); }
    document.body.classList.remove('devWalkOpen');
  }
  function build() {
    root = document.createElement('dialog'); root.id = 'walkMotionTest'; root.setAttribute('aria-label', '歩行モーションテスト');
    root.innerHTML = `<header><h3>歩行モーションテスト</h3><button type="button" data-walk="fold" aria-expanded="true">操作パネル</button><button type="button" data-walk="close">閉じる</button></header>
<div class="walkBody"><div class="walkStage checker" tabindex="0" aria-label="歩行プレビュー"><img alt="歩行フレーム" draggable="false" hidden><div class="walkGround" aria-hidden="true"></div><div class="walkCenter" aria-hidden="true"></div></div>
<section class="walkPanel"><label>敵・味方<select data-walk="group"><option value="ally">味方</option><option value="enemy">敵</option></select></label><label>キャラクター<select data-walk="actor"></select></label>
<div class="walkRow"><button type="button" data-direction="up">上</button><button type="button" data-direction="down">下</button><button type="button" data-direction="left">左</button><button type="button" data-direction="right">右</button></div>
<div class="walkRow"><button type="button" data-walk="play" aria-pressed="false">再生・ループ</button><button type="button" data-walk="pause">一時停止</button></div><div class="walkRow"><button type="button" data-walk="prev">◀ コマ戻し</button><button type="button" data-walk="next">コマ送り ▶</button></div>
<label>再生速度<select data-walk="speed"><option value="0.5">0.5倍</option><option value="1" selected>1倍</option><option value="2">2倍</option></select></label>
<output data-walk="count" aria-label="現在のコマ / 総コマ数"></output><div class="walkRow"><label><input type="checkbox" data-guide="checker" checked>チェッカーボード</label><label><input type="checkbox" data-guide="ground" checked>接地線</label><label><input type="checkbox" data-guide="center" checked>中心線</label></div>
<p data-walk="policy"></p><p data-walk="source"></p><p data-walk="error" role="status"></p></section></div>`;
    document.body.append(root);
    root.addEventListener('click', e => {
      const button = e.target.closest('button'); if (!button) return;
      if (button.dataset.direction) { S.direction = button.dataset.direction; void select(); return; }
      const action = button.dataset.walk;
      if (action === 'close') close();
      else if (action === 'play') play();
      else if (action === 'pause') pause();
      else if (action === 'next' || action === 'prev') step(action === 'next' ? 1 : -1);
      else if (action === 'fold') { root.classList.toggle('folded'); button.setAttribute('aria-expanded', String(!root.classList.contains('folded'))); layout(); }
    });
    root.addEventListener('change', e => {
      const control = e.target;
      if (control.dataset.walk === 'group') { S.group = control.value; characters(); void select(); }
      else if (control.dataset.walk === 'actor') { S.actor = control.value; void select(); }
      else if (control.dataset.walk === 'speed') { S.speed = Number(control.value); }
      else if (control.dataset.guide === 'checker') q('.walkStage').classList.toggle('checker', control.checked);
      else if (control.dataset.guide === 'ground') q('.walkGround').hidden = !control.checked;
      else if (control.dataset.guide === 'center') q('.walkCenter').hidden = !control.checked;
    });
    root.addEventListener('cancel', e => { e.preventDefault(); close(); });
    root.addEventListener('close', close);
    q('img').addEventListener('error', () => { if (active()) { pause(); S.ready = false; q('[data-walk=error]').textContent = 'フレーム画像を表示できません。'; info(); } });
    new ResizeObserver(layout).observe(q('.walkStage'));
  }
  function open() {
    if (window.LoadCoordinator?.phase !== 'READY' || window.LoadingInput?.busy || window.MossForest?.busy || window.FieldTalk?.active || window.FieldScene?.running || window.MotionTest?.isOpen || document.body.matches('.battleMode,.dialogueOpen,.devPortraitOpen')) {
      hint.textContent = '会話・イベント・読み込みが終わってから開いてください。'; return false;
    }
    if (!root) build();
    if (active()) return true;
    hint.textContent = ''; document.getElementById('devPanel').style.display = 'none';
    window.dispatchEvent(new Event('loading-input-lock'));
    document.body.classList.add('devWalkOpen'); root.showModal();
    root.classList.remove('folded'); q('[data-walk=fold]').setAttribute('aria-expanded', 'true');
    q('[data-walk=group]').value = S.group; characters(); void select(); return true;
  }
  for (const type of ['keydown', 'keyup']) window.addEventListener(type, e => {
    if (!active()) return;
    e.stopImmediatePropagation();
    if (type === 'keydown' && e.key === 'Escape') { e.preventDefault(); close(); }
    else if (type === 'keydown' && e.target === q('.walkStage')) {
      if (e.key === ' ') { e.preventDefault(); S.playing ? pause() : play(); }
      else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); step(e.key === 'ArrowRight' ? 1 : -1); }
    }
  }, true);
  window.LoadCoordinator?.onInvalidate(close);
  window.addEventListener('pagehide', close);
  window.addEventListener('field-talk', close);
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
  reduced.addEventListener('change', () => { pause(); info(); });
  new MutationObserver(() => { if (active() && document.body.matches('.battleMode,.actionCinematic,.devPortraitOpen,.motionTestOpen')) close(); }).observe(document.body, {attributes: true, attributeFilter: ['class']});
  const entry = document.createElement('button'); entry.id = 'devWalkMotionTest'; entry.type = 'button'; entry.className = 'dev-only-command'; entry.textContent = '歩行モーションテスト'; entry.onclick = open;
  const panel = document.getElementById('devPanel'); panel.querySelector('h3').after(entry);
  const hint = document.createElement('p'); entry.after(hint);
  window.DevWalkTest = Object.freeze({open, close, get active() { return active(); },
    snapshot() { return {group: S.group, actor: S.actor, direction: S.direction, index: S.index, total: S.def?.frames.length || 0, ready: S.ready, playing: S.playing, timer: S.raf != null, speed: S.speed, time: S.time}; }});
})();
