/* DEV-only temporary in-game art placement. Never serializes review coordinates.
 * Reuses the existing field camera/movement; restores position/room on exit. */
(function () {
  'use strict';
  if (!window.WINDBOUND_DEV || !window.LindFieldAssets) return;
  const assets = window.LindFieldAssets;
  let active = false, snapshot = null, depthFrame = null;
  const originalBlocked = window.blockedWorld;
  const layer = document.createElement('div');
  layer.id = 'lindReviewLayer';
  layer.hidden = true;
  world.prepend(layer);
  const terrain = (name, x, y, width, height, tile = 64) => {
    const el = document.createElement('div');
    el.className = 'lind-review-ground';
    Object.assign(el.style, {left:x+'px', top:y+'px', width:width+'px', height:height+'px',
      backgroundImage:`url("${assets.terrain[name]}")`, backgroundSize:tile+'px '+tile+'px'});
    layer.append(el);
  };
  terrain('grass', 0, 0, 2200, 1550, 256);
  terrain('dirt', 80, 560, 1350, 100, 128);
  terrain('dirt', 680, 100, 100, 1250, 128);
  terrain('edge', 80, 528, 1350, 32);
  terrain('stone', 570, 430, 350, 300);
  terrain('water', 1450, 0, 180, 1550, 128);
  terrain('riverbank', 1400, 0, 64, 1550, 128);
  assets.objects.forEach(obj => {
    const image = document.createElement('img');
    image.loading = 'lazy';
    image.decoding = 'async';
    image.src = obj.path;
    image.alt = obj.label;
    image.className = 'lind-review-object';
    image.dataset.assetId = obj.id;
    Object.assign(image.style, {left:obj.x+'px', top:obj.y+'px', width:obj.width+'px',
      height:obj.height+'px', zIndex:String(Math.round(obj.y+obj.height))});
    layer.append(image);
  });
  const controls = document.createElement('div');
  controls.id = 'lindReviewControls';
  controls.hidden = true;
  const caption = document.createElement('span');
  caption.textContent = 'DEV · リルド素材仮配置 · STEP 12統合前';
  const close = document.createElement('button');
  close.textContent = '戻る';
  close.onclick = () => setActive(false);
  const jump = document.createElement('select');
  jump.setAttribute('aria-label', '素材確認場所');
  const placeholder = document.createElement('option');
  placeholder.textContent = '素材へ移動'; placeholder.value = '';
  jump.append(placeholder);
  assets.objects.forEach(obj => {
    const option = document.createElement('option');
    option.value = obj.id; option.textContent = obj.label;
    jump.append(option);
  });
  function focus(id) {
    if (!active) return false;
    const obj = assets.objects.find(item => item.id === id);
    if (!obj) return false;
    target = null; px = obj.x+obj.width/2-17; py = obj.y+obj.height+20;
    camera(); return true;
  }
  jump.onchange = () => focus(jump.value);
  controls.append(caption, jump, close);
  document.body.append(controls);
  const launch = document.createElement('button');
  launch.textContent = 'リルド村 · 素材仮配置';
  launch.onclick = () => setActive(true);
  document.getElementById('devGrid').append(launch);

  function setActive(value) {
    if (value === active) return;
    if (value && (storyStage >= 5 || ['battle','attackBattle','raiderBattle','battleResult'].some(id => {
      const el = document.getElementById(id);
      return el && getComputedStyle(el).display !== 'none';
    }))) {
      toast('平和なリルド村へDEV Jumpしてから素材仮配置を開いてください。');
      return;
    }
    if (value) {
      // Only the field review is shown. No DEV Jump, story flags or save are changed.
      snapshot = {px, py, target, playerZ:pl.style.zIndex,
        roomDisplay:document.getElementById('inside').style.display};
      target = null;
      document.getElementById('inside').style.display = 'none';
      document.getElementById('devPanel').style.display = 'none';
      px = 620; py = 740;
    } else {
      px = snapshot.px; py = snapshot.py; target = snapshot.target;
      cancelAnimationFrame(depthFrame);
      pl.style.zIndex = snapshot.playerZ;
      document.getElementById('inside').style.display = snapshot.roomDisplay;
      snapshot = null;
    }
    active = value;
    document.body.classList.toggle('lindFieldReview', active);
    layer.hidden = !active;
    controls.hidden = !active;
    camera();
    if (active) {
      const updateDepth = () => {
        if (!active) return;
        pl.style.zIndex = String(Math.round(py+44));
        depthFrame = requestAnimationFrame(updateDepth);
      };
      updateDepth();
    }
  }
  function blocked(x, y) {
    if (originalBlocked(x, y)) return true;
    if (!active) return false;
    // Foot box, not full roof image; entrances remain approachable from below.
    return assets.objects.some(obj => obj.collision && (() => {
      const c = obj.collision;
      return x+28 > obj.x+c[0] && x+6 < obj.x+c[0]+c[2] &&
        y+42 > obj.y+c[1] && y+32 < obj.y+c[1]+c[3];
    })());
  }
  window.blockedWorld = blocked;
  // Prevent live story/quest/save controls while reviewing art. Field pointer
  // destinations and existing arrow/WASD handlers remain available.
  document.addEventListener('pointerdown', e => {
    if (active && !e.target.closest('#world,#lindReviewControls')) {
      e.preventDefault(); e.stopImmediatePropagation();
    }
  }, true);
  document.addEventListener('keydown', e => {
    if (!active) return;
    if (e.key === 'Escape') { setActive(false); e.stopImmediatePropagation(); return; }
    if (!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','w','a','s','d'].includes(e.key)) {
      e.preventDefault(); e.stopImmediatePropagation();
    }
  }, true);
  window.LindFieldReview = Object.freeze({open:()=>setActive(true), close:()=>setActive(false), focus,
    get active(){return active;}, blocked});
})();
