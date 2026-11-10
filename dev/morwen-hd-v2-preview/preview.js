/* DEV-only preview for MORWEN-HD-CANONICAL-V2. Reads data/morwen-hd-canonical-v2.json; no game state. */
(async function () {
  'use strict';
  const ROOT = '../../';
  const LABEL = { front: '正面', left: '左（新正本）', right: '右', back: '背面' };
  const grid = document.getElementById('grid');
  const status = document.getElementById('status');
  const els = ['style', 'height', 'bg', 'anchorFix', 'pixelated'].reduce((o, id) => (o[id] = document.getElementById(id), o), {});
  const params = new URLSearchParams(location.search);
  for (const [k, v] of params) {
    if (!els[k]) continue;
    if (els[k].type === 'checkbox') els[k].checked = v === '1';
    else els[k].value = v;
  }

  let reg;
  try {
    reg = await MorwenHDCanonical.load(ROOT + 'data/morwen-hd-canonical-v2.json');
  } catch (err) {
    status.textContent = '読み込み失敗: ' + err.message;
    status.classList.add('bad');
    return;
  }

  const results = (window.__morwenHdPreview = { ready: false, cells: {} });

  function render() {
    const style = els.style.value;
    const h = Number(els.height.value);
    const stageH = Math.max(140, Math.round(h * 1.08));
    grid.textContent = '';
    results.ready = false;
    results.cells = {};
    let pending = 0;
    const cells = [];
    for (const dir of reg.directions) {
      const cell = document.createElement('section');
      cell.className = 'cell';
      cell.dataset.direction = dir;
      const head = document.createElement('h2');
      head.innerHTML = '<span></span><span></span>';
      head.children[0].textContent = LABEL[dir];
      const stage = document.createElement('div');
      stage.className = 'stage bg-' + els.bg.value + (els.pixelated.checked ? ' pixelated' : '');
      stage.style.setProperty('--stage-h', stageH + 'px');
      const img = new Image();
      img.alt = 'モルウェン ' + LABEL[dir];
      img.decoding = 'async';
      const meta = document.createElement('div');
      meta.className = 'meta';
      cell.append(head, stage, meta);
      grid.append(cell);
      const footY = stageH - Math.round(h * 0.04) - 4;
      const ground = document.createElement('div');
      ground.className = 'guide-ground';
      ground.style.top = footY + 'px';
      stage.append(img, ground);
      cells.push({ dir, stage, img, head, meta, footY });
    }
    // Second pass: measure only after every cell is in the grid, so each stage has its final width.
    for (const c of cells) {
      const { dir, stage, img, head, meta, footY } = c;
      const cw = stage.clientWidth;
      let a;
      if (style === 'display') {
        const p = reg.placeDisplay(dir, { height: h, anchorCorrection: els.anchorFix.checked, footX: cw / 2, footY: footY });
        a = reg.asset('display.pixel.' + dir);
        Object.assign(img.style, { left: p.left + 'px', top: p.top + 'px', width: p.width + 'px', height: p.height + 'px' });
        const anchor = document.createElement('div');
        anchor.className = 'guide-anchor';
        anchor.style.left = cw / 2 + 'px';
        stage.append(anchor);
        head.children[1].textContent = 'dx ' + p.anchorDx;
        results.cells[dir] = { src: p.src, sha256: p.sha256, anchorDx: p.anchorDx, left: p.left, top: p.top, width: p.width, height: p.height, footX: cw / 2, footY, stageWidth: cw };
      } else {
        a = reg.original(style, dir);
        const s = h / a.size[1];
        const w = a.size[0] * s;
        Object.assign(img.style, { left: (cw - w) / 2 + 'px', top: footY - h + 'px', width: w + 'px', height: h + 'px' });
        head.children[1].textContent = a.size.join('×');
        results.cells[dir] = { src: a.path, sha256: a.sha256, stageWidth: cw };
      }
      meta.textContent = a.path.split('/').slice(-3).join('/') + '\nSHA-256 ' + a.sha256.slice(0, 16) + '…  ' + (a.role || '');
      pending++;
      img.onload = () => { results.cells[dir].natural = [img.naturalWidth, img.naturalHeight]; if (--pending === 0) done(); };
      img.onerror = () => { results.cells[dir].error = true; status.textContent = '画像の読み込みに失敗: ' + dir; status.classList.add('bad'); if (--pending === 0) done(); };
      img.src = ROOT + a.path;
    }
    function done() {
      results.ready = true;
      if (!status.classList.contains('bad')) status.textContent = '4方向を表示しました（' + els.style.selectedOptions[0].textContent + '）。';
    }
  }

  for (const el of Object.values(els)) el.addEventListener('change', () => { status.classList.remove('bad'); render(); });
  window.addEventListener('resize', () => { clearTimeout(render.t); render.t = setTimeout(render, 150); });
  render();
})();
