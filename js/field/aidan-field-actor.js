/* A1 field-art review only. Observes actual field displacement; never changes
 * movement, navigation, collisions, story, saves, party or battle actor state. */
(function () {
  'use strict';
  if (!window.WINDBOUND_DEV || !window.AidanFieldAssets) return;
  const assets = window.AidanFieldAssets;
  const images = new Map();
  let active = false, enabled = true, player = null, button = null, raf = null;
  let previous = null, direction = 'down', state = 'IDLE', phase = 0;
  let walkingSince = 0, lastMoved = 0, visible = null, loaded = false, loading = null;
  function mount(root, controls) {
    player = root;
    for (const [name, asset] of Object.entries(assets.frames)) {
      const image = new Image();
      image.dataset.src = asset.path; image.alt = 'エイダン · 誓いの剣';
      image.className = 'aidan-field-frame'; image.hidden = true;
      image.dataset.frame = name;
      // Source PNGs remain unchanged. Explicit per-frame foot registration
      // removes canvas padding from placement, independently of collider size.
      const scale = asset.scale;
      Object.assign(image.style, {width:asset.width*scale+'px', height:asset.height*scale+'px',
        left:17-asset.anchor[0]*scale+'px', top:42-asset.anchor[1]*scale+'px'});
      player.append(image); images.set(name, image);
    }
    button = document.createElement('button'); button.type = 'button';
    button.id = 'aidanFieldToggle'; button.onclick = () => {enabled=!enabled;apply();};
    const display = document.createElement('label');
    display.className = 'aidan-field-display';
    display.append('プレイヤー表示 ', button);
    controls.insertBefore(display, document.getElementById('lindWindToggle')); apply();
  }
  function render() {
    const name = 'aidan_'+(state==='WALK'?'walk_'+direction+'_'+String(phase+1).padStart(2,'0'):'idle_'+direction);
    if (visible !== name) {
      if (visible) images.get(visible).hidden = true;
      images.get(name).hidden = !(active && enabled && loaded); visible = name;
    } else images.get(name).hidden = !(active && enabled && loaded);
    player.dataset.fieldState = state; player.dataset.fieldDirection = direction;
    player.dataset.fieldFrame = name;
  }
  function apply() {
    if (!player) return;
    player.classList.toggle('aidan-field-active', active && enabled && loaded);
    button.textContent = enabled ? (loaded ? 'Aidan A1（仮プレイヤーへ切替）' : 'Aidan A1 読込中') : '仮プレイヤー（Aidan A1へ切替）';
    button.setAttribute('aria-pressed', String(enabled)); render();
  }
  function update(now) {
    if (!active) return;
    const dx=px-previous.x, dy=py-previous.y, distance=Math.hypot(dx,dy);
    // Focus/review jumps are not movement animation. Only real small steps
    // choose facing; blocked movement naturally settles into matching IDLE.
    if (distance>.01 && distance<=23) {
      const next = Math.abs(dx)>=Math.abs(dy) ? (dx>0?'right':'left') : (dy>0?'down':'up');
      if (state!=='WALK' || direction!==next) {walkingSince=now;phase=0;}
      direction=next; state='WALK'; lastMoved=now;
    } else if (distance>23 || now-lastMoved>110) {state='IDLE';phase=0;}
    if (state==='WALK') phase=Math.floor((now-walkingSince)/100)%4;
    previous={x:px,y:py}; render(); raf=requestAnimationFrame(update);
  }
  function setActive(value) {
    active=value; cancelAnimationFrame(raf); raf=null;
    state='IDLE';phase=0;previous={x:px,y:py};lastMoved=0;
    if (active) {
      direction='down';raf=requestAnimationFrame(update);
      ready().then(apply).catch(()=>{enabled=false;apply();button.textContent='Aidan 読込失敗';});
    } apply();
  }
  function ready() {
    if (!loading) loading=Promise.all([...images.values()].map(image=>{
      image.src=image.dataset.src;return image.decode();
    })).then(()=>{loaded=true;});
    return loading;
  }
  window.AidanFieldActor=Object.freeze({mount,setActive,
    get active(){return active;}, get enabled(){return enabled;},
    get status(){return {direction,state,frame:visible,phase,anchor:{x:px+17,y:py+42}};},
    ready});
})();
