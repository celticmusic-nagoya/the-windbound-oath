/* DEV-only inspector; production PNGs and FieldWalkMotion own the animation. */
(() => {
  'use strict';
  if (!window.WINDBOUND_DEV) return;
  const W = window.FieldWalkMotion;
  const S = {group: 'ally', actor: 'aidan', direction: 'down', state: 'walk', loaded: false, speed: 1, sideStride: null, downSequence: 'six', downStride: 90, downFoot: false, downBob: true, time: 0, index: 0, playing: false, raf: null, last: null, generation: 0, def: null, zoom: 1, width: 0, height: 0, ready: false};
  const images = new Map(), reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let root;
  const q = selector => root.querySelector(selector);
  const active = () => Boolean(root?.open);
  const aidan = () => S.group === 'ally' && S.actor === 'aidan';
  const sideWalk = () => aidan() && S.state === 'walk' && ['left', 'right'].includes(S.direction);
  const downWalk = () => aidan() && S.state === 'walk' && S.direction === 'down';
  const downTrial = () => downWalk() && S.downSequence === 'four';
  function downInfo() {
    q('[data-walk=down-controls]').hidden = !downWalk();
    q('[data-walk=down-foot]').checked = downTrial() && S.downFoot;
    q('[data-walk=down-bob]').checked = !downTrial() || S.downBob;
    q('[data-walk=down-stride]').value = String(downTrial() ? S.downStride : 90);
    for (const key of ['down-stride', 'down-foot', 'down-bob']) q(`[data-walk=${key}]`).disabled = !downTrial();
    q('[data-walk=down-help]').textContent = downTrial()
      ? `DEV検証のみ：01 → 05 → 02 → 06 ／ 周期${S.downStride} ／ 1倍で${(S.downStride / S.def.speed()).toFixed(3)}秒/周。足元補正は06全体を+8画像px（0.5 world）移動。接地位相は画像からの推定です。`
      : '現行本編の6コマ・周期90・上下動をそのまま比較。変更時は停止して先頭へ戻ります。';
  }
  function strideInfo() {
    q('[data-walk=stride-controls]').hidden = !aidan();
    if (!aidan()) return;
    q('[data-walk=stride]').value = String(S.sideStride);
    q('[data-walk=stride-value]').textContent = String(S.sideStride);
    for (const b of root.querySelectorAll('[data-stride]')) b.setAttribute('aria-pressed', String(Number(b.dataset.stride) === S.sideStride));
    const source = W.resolve('ally', 'aidan', 'left');
    q('[data-walk=stride-help]').textContent = `横歩き1周 ${(S.sideStride / source.speed() / S.speed).toFixed(3)} 秒（周期 ÷ 基準速度 ${source.speed()} ÷ 再生倍率 ${S.speed}）。大きい周期ほどゆっくり。本編設定 ${source.stride} は変更しません。`;
  }
  function setStride(value) {
    if (!Number.isFinite(value)) return;
    const next = Math.max(40, Math.min(300, value));
    if (sideWalk() && S.def) {
      // Preserve fractional cycle and bob; leave the single running RAF alive.
      if (S.playing && S.last != null) { const now = performance.now(); S.time += (now - S.last) / 1000 * S.speed; S.last = now; }
      S.time *= next / S.def.stride;
      S.def = {...S.def, stride: next};
      S.index = W.frameAt(S.def, S.time).index;
    }
    S.sideStride = next;
    strideInfo(); render();
  }
  function pause() {
    if (S.raf != null) cancelAnimationFrame(S.raf);
    S.raf = null; S.playing = false; S.last = null;
    if (root) { q('[data-walk=play]').setAttribute('aria-pressed', 'false'); root.dataset.playing = 'false'; }
  }
  function info() {
    if (!root || !S.def) return;
    strideInfo();
    q('[data-walk=count]').textContent = `${S.index + 1} / ${S.def.frames.length}`;
    q('[data-walk=source]').textContent = `${S.def.note} / ${S.def.frames[S.index].url}`;
    q('[data-walk=policy]').textContent = (S.def.kind === 'distance' ? `周期 ${S.def.stride} world・基準速度 ${S.def.speed()} world/s` : `実ゲーム設定 ${S.def.fps} コマ/秒`) + (sideWalk() || downTrial() ? ' ／ DEV一時設定' : '') + (reduced.matches ? ' ／ 動きを減らす設定：コマ送りで確認' : '');
    q('[data-walk=play]').disabled = !S.ready || S.def.frames.length < 2 || reduced.matches;
  }
  function render() {
    if (!S.def || !S.ready || !active()) return;
    const motion = W.frameAt(S.def, S.time), frame = S.def.frames[S.index], image = q('img');
    image.hidden = false;
    if (image.getAttribute('src') !== frame.url) image.src = frame.url;
    image.style.width = `${frame.width * frame.scale * S.zoom}px`;
    image.style.height = `${frame.height * frame.scale * S.zoom}px`;
    image.style.left = `${S.width / 2 - frame.anchor[0] * frame.scale * S.zoom}px`;
    image.style.top = `${S.height * .8 - frame.anchor[1] * frame.scale * S.zoom + (downTrial() && S.downFoot && frame.key === 'aidan_walk_down_06' ? 8 * frame.scale * S.zoom : 0)}px`;
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
    if (!active() || !S.ready || S.def.frames.length < 2 || reduced.matches) return;
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
    pause(); S.ready = false; S.loaded = false; S.time = 0; S.index = 0;
    const generation = ++S.generation;
    S.def = W.resolve(S.group, S.actor, S.direction, S.state);
    // Clone the descriptor only; never mutate production settings or registries.
    if (sideWalk() && S.def) S.def = {...S.def, stride: S.sideStride};
    if (downTrial() && S.def) {
      const bank = S.def.frames;
      S.def = {...S.def, frames: Object.freeze([1, 5, 2, 6].map(n => bank.find(f => f.key === `aidan_walk_down_${String(n).padStart(2, '0')}`))), stride: S.downStride, bob: S.downBob, note: 'DEV未採用4コマ（正式PNG参照）'};
    }
    downInfo(); strideInfo();
    q('img').hidden = true; q('img').removeAttribute('src'); q('[data-walk=play]').disabled = true; q('[data-walk=error]').textContent = '';
    root.dataset.actor = S.actor; root.dataset.direction = S.direction; root.dataset.state = S.state;
    for (const b of root.querySelectorAll('[data-direction]')) {
      b.setAttribute('aria-pressed', String(S.state === 'walk' && b.dataset.direction === S.direction));
      b.textContent = ({up:'上',down:'下',left:'左',right:'右'})[b.dataset.direction] + (W.resolve(S.group,S.actor,b.dataset.direction,'walk') ? '' : '：未実装');
    }
    q('[data-walk=idle]').setAttribute('aria-pressed', String(S.state === 'idle'));
    for (const b of root.querySelectorAll('[data-walk=prev],[data-walk=next]')) b.disabled = true;
    if (!S.def) { S.loaded = true; q('[data-walk=count]').textContent = '0 / 0'; q('[data-walk=source]').textContent = ''; q('[data-walk=policy]').textContent = ''; q('[data-walk=error]').textContent = '未実装：この方向・状態の素材はありません。'; return; }
    info();
    try {
      await Promise.all(S.def.frames.map(f => preload(f.url)));
      if (!active() || generation !== S.generation) return;
      S.ready = true; S.loaded = true;
      for (const b of root.querySelectorAll('[data-walk=prev],[data-walk=next]')) b.disabled = false;
      layout();
    } catch (error) {
      if (!active() || generation !== S.generation) return;
      S.loaded = true; q('[data-walk=error]').textContent = error.message; info();
    }
  }
  function characters() {
    const select = q('[data-walk=actor]'); select.textContent = '';
    for (const actor of W.catalog(S.group)) select.add(new Option(actor.label, actor.id));
    if (![...select.options].some(o => o.value === S.actor)) S.actor = select.options[0]?.value;
    select.value = S.actor;
  }
  function background(value) {
    const stage = q('.walkStage'); stage.classList.toggle('checker', value === 'checker');
    stage.style.backgroundColor = ({light:'#fff',green:'#276f48',dark:'#101812',checker:'#243329'})[value];
    q('[data-guide=checker]').checked = value === 'checker'; q('[data-walk=background]').value = value;
  }
  function close() {
    pause(); ++S.generation; S.ready = false; S.loaded = false; images.clear();
    if (root) { q('img').hidden = true; q('img').removeAttribute('src'); if (root.open) root.close(); }
    document.body.classList.remove('devWalkOpen');
  }
  function build() {
    root = document.createElement('dialog'); root.id = 'walkMotionTest'; root.setAttribute('aria-label', '歩行モーションテスト');
    root.innerHTML = `<header><h3>歩行モーションテスト</h3><button type="button" data-walk="fold" aria-expanded="true">操作パネル</button><button type="button" data-walk="close">閉じる</button></header>
<div class="walkBody"><div class="walkStage checker" tabindex="0" aria-label="歩行プレビュー"><img alt="歩行フレーム" draggable="false" hidden><div class="walkGround" aria-hidden="true"></div><div class="walkCenter" aria-hidden="true"></div></div>
<section class="walkPanel"><label>分類<select data-walk="group"><option value="ally">味方</option><option value="enemy">敵</option><option value="npc">NPC</option></select></label><label>キャラクター<select data-walk="actor"></select></label>
<div class="walkRow"><button type="button" data-walk="idle">待機</button><button type="button" data-direction="up">上</button><button type="button" data-direction="down">下</button><button type="button" data-direction="left">左</button><button type="button" data-direction="right">右</button></div>
<div class="walkRow"><button type="button" data-walk="play" aria-pressed="false">再生・ループ</button><button type="button" data-walk="pause">一時停止</button></div><div class="walkRow"><button type="button" data-walk="prev">◀ コマ戻し</button><button type="button" data-walk="next">コマ送り ▶</button></div>
<fieldset data-walk="down-controls" hidden><legend>エイダン下方向4コマ比較（DEV・本番未採用）</legend>
<label>構成<select data-walk="down-sequence"><option value="six">現行6コマ：01〜06／周期90</option><option value="four">検証4コマ：01→05→02→06</option></select></label>
<label>検証周期<select data-walk="down-stride"><option value="60">60</option><option value="75">75</option><option value="90" selected>90</option></select></label>
<div class="walkRow"><label><input type="checkbox" data-walk="down-foot">06の足元補正 +8画像px</label><label><input type="checkbox" data-walk="down-bob" checked>本編の上下動</label></div><p data-walk="down-help"></p></fieldset>
<label>再生倍率<select data-walk="speed"><option value="0.5">0.5倍</option><option value="1" selected>1倍</option><option value="2">2倍</option></select></label>
<fieldset data-walk="stride-controls" hidden><legend>エイダン横歩き周期（DEV）</legend><label for="walkSideStride">横歩き周期 <output data-walk="stride-value" for="walkSideStride">72</output></label>
<input id="walkSideStride" data-walk="stride" type="range" min="40" max="300" step="any" value="72" aria-describedby="walkStrideHelp">
<div class="walkRow"><button type="button" data-stride="72">72</button><button type="button" data-stride="120">120</button><button type="button" data-stride="180">180</button><button type="button" data-stride="240">240</button></div>
<p id="walkStrideHelp" data-walk="stride-help"></p><p>40〜300・10刻み（採用値72はプリセット）。左右プレビューだけに適用。上下・待機・SAVEは変更しません。このページ内だけの一時設定です。</p></fieldset>
<label>背景<select data-walk="background"><option value="checker">チェッカーボード</option><option value="dark">暗色</option><option value="light">白</option><option value="green">緑</option></select></label>
<output data-walk="count" aria-label="現在のコマ / 総コマ数"></output><div class="walkRow"><label><input type="checkbox" data-guide="checker" checked>チェッカーボード</label><label><input type="checkbox" data-guide="ground" checked>接地線</label><label><input type="checkbox" data-guide="center" checked>中心線</label></div>
<p data-walk="policy"></p><p data-walk="source"></p><p data-walk="error" role="status"></p></section></div>`;
    document.body.append(root);
    root.addEventListener('click', e => {
      const button = e.target.closest('button'); if (!button) return;
      if (button.dataset.stride) { setStride(Number(button.dataset.stride)); return; }
      if (button.dataset.direction) { S.direction = button.dataset.direction; S.state = 'walk'; void select(); return; }
      const action = button.dataset.walk;
      if (action === 'idle') { S.state = 'idle'; void select(); }
      else if (action === 'close') close();
      else if (action === 'play') play();
      else if (action === 'pause') pause();
      else if (action === 'next' || action === 'prev') step(action === 'next' ? 1 : -1);
      else if (action === 'fold') { root.classList.toggle('folded'); button.setAttribute('aria-expanded', String(!root.classList.contains('folded'))); layout(); }
    });
    // Native step=any admits the off-grid adopted value 72; drag values snap to 10.
    root.addEventListener('input', e => { if (e.target.dataset.walk === 'stride') setStride(Math.round(Number(e.target.value) / 10) * 10); });
    root.addEventListener('change', e => {
      const control = e.target;
      if (control.dataset.walk === 'down-sequence') { S.downSequence = control.value; void select(); }
      else if (control.dataset.walk === 'down-stride') { S.downStride = Number(control.value); void select(); }
      else if (control.dataset.walk === 'down-foot') { S.downFoot = control.checked; render(); }
      else if (control.dataset.walk === 'down-bob') { S.downBob = control.checked; void select(); }
      else if (control.dataset.walk === 'group') { S.group = control.value; characters(); void select(); }
      else if (control.dataset.walk === 'actor') { S.actor = control.value; void select(); }
      else if (control.dataset.walk === 'speed') { S.speed = Number(control.value); info(); }
      else if (control.dataset.walk === 'background') background(control.value);
      else if (control.dataset.guide === 'checker') background(control.checked ? 'checker' : 'dark');
      else if (control.dataset.guide === 'ground') q('.walkGround').hidden = !control.checked;
      else if (control.dataset.guide === 'center') q('.walkCenter').hidden = !control.checked;
    });
    root.addEventListener('cancel', e => { e.preventDefault(); close(); });
    root.addEventListener('close', () => { if (!root.open) close(); });
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
    if (S.sideStride == null) S.sideStride = Math.max(40, Math.min(300, W.resolve('ally', 'aidan', 'left').stride));
    window.dispatchEvent(new Event('loading-input-lock'));
    document.body.classList.add('devWalkOpen'); root.showModal();
    root.classList.remove('folded'); q('[data-walk=fold]').setAttribute('aria-expanded', 'true');
    q('[data-walk=group]').value = S.group; characters(); void select(); return true;
  }
  for (const type of ['keydown', 'keyup']) window.addEventListener(type, e => {
    if (!active()) return;
    e.stopImmediatePropagation();
    if (type === 'keydown' && e.target === q('[data-walk=stride]')) {
      const key = e.key, up = ['ArrowRight', 'ArrowUp'].includes(key), down = ['ArrowLeft', 'ArrowDown'].includes(key);
      if (up || down || key === 'Home' || key === 'End' || key === 'PageUp' || key === 'PageDown') {
        e.preventDefault();
        setStride(key === 'Home' ? 40 : key === 'End' ? 300 : up ? (Math.floor(S.sideStride / 10) + 1) * 10 : down ? (Math.ceil(S.sideStride / 10) - 1) * 10 : (key === 'PageUp' ? Math.floor(S.sideStride / 10) + 5 : Math.ceil(S.sideStride / 10) - 5) * 10);
        return;
      }
    }
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
    snapshot() { return {group: S.group, actor: S.actor, direction: S.direction, state: S.state, loaded: S.loaded, index: S.index, total: S.def?.frames.length || 0, ready: S.ready, playing: S.playing, timer: S.raf != null, speed: S.speed, downSequence: S.downSequence, downStride: S.downStride, downFoot: S.downFoot, downBob: S.downBob, sideStride: S.sideStride, effectiveStride: S.def?.stride ?? null, time: S.time}; }});
})();
