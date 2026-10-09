/* DEV-only temporary in-game art placement. Never serializes review coordinates.
 * Reuses the existing field camera/movement; restores position/room on exit. */
(function () {
  'use strict';
  if (!window.WINDBOUND_DEV || !window.LindFieldAssets) return;
  const assets = window.LindFieldAssets;
  let active = false, snapshot = null, depthFrame = null;
  const originalBlocked = window.blockedWorld;
  const originalSave = window.saveGrowthData;
  const layer = document.createElement('div');
  layer.id = 'lindReviewLayer';
  layer.hidden = true;
  layer.dataset.wind = window.LindFieldEnvironment?.wind ? 'on' : 'off';
  world.prepend(layer);
  const terrain = (name, x, y, width, height, tile = 64) => {
    const el = document.createElement('div');
    el.className = 'lind-review-ground';
    if (name === 'water') el.classList.add('lind-water-flow');
    Object.assign(el.style, {left:x+'px', top:y+'px', width:width+'px', height:height+'px',
      backgroundImage:`url("${assets.terrain[name]}")`, backgroundSize:tile+'px '+tile+'px'});
    layer.append(el);
  };
  terrain('grass', 0, 0, 2200, 1550, 256);
  terrain('dirt', 80, 560, 1350, 100, 128);
  terrain('dirt', 680, 100, 100, 1250, 128);
  terrain('edge', 80, 496, 1350, 64);
  terrain('stone', 570, 430, 350, 300);
  terrain('water', 1450, 0, 180, 1550, 128);
  terrain('riverbank', 1400, 0, 64, 1550, 128);
  // Same central bridge leads onto the east-bank dirt approach, not a new crossing.
  terrain('dirt', 1630, 565, 170, 60, 128);
  terrain('dirt', 1730, 600, 95, 170, 128);
  assets.objects.forEach(obj => {
    if(obj.actor === 'windStone') return;
    const image = document.createElement('img');
    image.loading = 'lazy';
    image.decoding = 'async';
    image.src = obj.path;
    image.alt = obj.label;
    image.className = 'lind-review-object';
    if (obj.motion === 'wind') image.classList.add('lind-wind-driven');
    image.dataset.assetId = obj.id;
    const draw = obj.draw || {x:obj.x, y:obj.y, width:obj.width, height:obj.height};
    Object.assign(image.style, {left:draw.x+'px', top:draw.y+'px', width:draw.width+'px',
      height:draw.height+'px', zIndex:obj.layer === 'groundDecoration' ? '1' : String(Math.round(obj.y+obj.height))});
    layer.append(image);
  });
  window.LindFieldAnimals?.mount(layer);
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
  window.LindFieldAnimals?.actors.forEach(actor => {
    const option = document.createElement('option');
    option.value = actor.id; option.textContent = actor.label;
    jump.append(option);
  });
  window.LindFieldNPCs?.definitions.forEach(npc=>{const option=document.createElement('option');option.value=npc.id;option.textContent=npc.label;jump.append(option);});
  if(window.LindFieldBirds){const option=document.createElement('option');option.value='lind_ground_birds';option.textContent='小鳥';jump.append(option);}
  function focus(id) {
    if (!active) return false;
    if(window.LindFieldNPCs?.focus(id))return true;
    if(id==='lind_ground_birds')return window.LindFieldBirds?.focus()||false;
    const obj = assets.objects.find(item => item.id === id) || window.LindFieldAnimals?.actors.find(item => item.id === id);
    if (!obj) return false;
    target = null; px = obj.x+obj.width/2-17; py = obj.y+obj.height+20;
    // Side approach keeps the full tall monument below DEV controls on landscape screens.
    if (obj.id === 'lind_wind_stone') { px=obj.x-65; py=obj.y+obj.height-75; }
    if (obj.id === 'lind_bridge') { px = 1390; py = 560; }
    if (['lind_fishing_pier','lind_fishing_rod'].includes(obj.id)) {
      const stand = window.LindFieldRiver.standingAreas.find(s=>s.id==='player');
      px = stand.x; py = stand.y;
    }
    camera(); return true;
  }
  jump.onchange = () => focus(jump.value);
  const wind = document.createElement('button');
  wind.id = 'lindWindToggle';
  wind.textContent = '風ON';
  wind.onclick = () => {
    const value = window.LindFieldEnvironment.setWind(!window.LindFieldEnvironment.wind);
    wind.textContent = value ? '風ON' : '風OFF';
  };
  controls.append(caption, jump, wind, close);
  document.body.append(controls);
  window.LindFieldTraining?.mount(layer, controls);
  window.LindFieldWindStone?.mount(layer, controls);
  window.LindFieldNPCs?.mount(layer, controls);
  window.LindFieldBirds?.mount(layer);
  window.AidanFieldActor?.mount(pl, controls);
  window.FieldCamera?.mount(controls);
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
    window.FieldCamera?.setReviewActive(active);
    window.LindFieldTraining?.clear();
    window.LindFieldWindStone?.clear();
    window.LindFieldNPCs?.setActive(active);
    window.LindFieldBirds?.setActive(active);
    window.AidanFieldActor?.setActive(active);
    if (active) window.LindFieldAnimals?.start(); else window.LindFieldAnimals?.stop();
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
    if (active && window.LindFieldRiver) {
      if (window.LindFieldRiver.blocked(x, y)) return true;
    } else if (originalBlocked(x, y)) return true;
    if (!active) return false;
    if (window.LindFieldAnimals?.blocked(x, y) || window.LindFieldNPCs?.blocked(x,y)) return true;
    // Foot box, not full roof image; entrances remain approachable from below.
    // Navigation sweeps call this frequently. Preserve the exact rectangles
    // without allocating nested arrays/functions for every sample.
    for(const obj of assets.objects) {
      if(obj.collisions){for(const c of obj.collisions)if(footOverlaps(obj,c,x,y))return true;}
      else if(obj.collision&&footOverlaps(obj,obj.collision,x,y))return true;
    }
    return false;
  }
  function footOverlaps(obj,c,x,y){return x+28>obj.x+c[0]&&x+6<obj.x+c[0]+c[2]&&
    y+42>obj.y+c[1]&&y+32<obj.y+c[1]+c[3];}
  window.blockedWorld = blocked;
  window.saveGrowthData = function (...args) {
    if (active) {
      toast('素材仮配置の座標は保存しません。戻ってからセーブしてください。');
      return false;
    }
    return originalSave.apply(this, args);
  };
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
    if (e.target.closest('#lindReviewControls')) {
      e.stopImmediatePropagation();
      return;
    }
    if (e.key === 'Enter' || e.key === 'e') {
      if(!window.LindFieldNPCs?.nearby()&&!window.LindFieldWindStone?.nearby()) window.LindFieldTraining?.nearby();
      e.preventDefault(); e.stopImmediatePropagation(); return;
    }
    if (!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','w','a','s','d'].includes(e.key)) {
      e.preventDefault(); e.stopImmediatePropagation();
    }
  }, true);
  window.LindFieldReview = Object.freeze({open:()=>setActive(true), close:()=>setActive(false), focus,
    get active(){return active;}, blocked});
})();
