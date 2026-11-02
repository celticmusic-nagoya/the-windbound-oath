/* Shared production frame policy. DEV reads these same registries and selectors. */
(() => {
  'use strict';
  const STRIDE = 90;
  const phaseDistance = (distance, count, stride = STRIDE) => Math.floor((distance || 0) / (stride / count)) % count;
  const phaseTime = (seconds, count, fps) => Math.floor(seconds * fps) % count;
  const bob = (distance, stride = STRIDE) => -Math.abs(Math.sin((distance || 0) / (stride / 2) * Math.PI)) * 1.5;
  const air = (art, clock) => art.air ? art.air + Math.sin(clock * 3) * 4 : 0;
  const cache = new WeakMap();
  const labels = {aidan: 'エイダン', fiona: 'フィオナ'};
  function ally(id, dir, profile = true) {
    const source = id === 'aidan' ? window.AidanFieldAssets : id === 'fiona' ? window.FionaFieldAssets : null;
    if (!source) return null;
    let banks = cache.get(source); if (!banks) { banks = new Map(); cache.set(source, banks); }
    const tag = dir + ':' + profile;
    if (banks.has(tag)) return banks.get(tag);
    const side = id === 'fiona' && profile && source.frames['fiona_side_' + dir + '_01'];
    const prefix = id + (side ? '_side_' : '_walk_') + dir + '_';
    const frames = Object.freeze(Object.entries(source.frames).filter(([k]) => k.startsWith(prefix) && /^\d+$/.test(k.slice(prefix.length))).sort(([a], [b]) => Number(a.slice(prefix.length)) - Number(b.slice(prefix.length))).map(([key, a]) =>
      Object.freeze({key, url: a.path, width: a.width, height: a.height, scale: a.scale, anchor: Object.freeze([...a.anchor])})));
    const def = frames.length ? Object.freeze({id, label: labels[id], group: 'ally', frames, kind: 'distance', stride: STRIDE,
      speed: () => (window.FieldMovement?.settings.pointerStep || 5) * 60, bob: id === 'aidan', flip: false, note: '専用方向'}) : null;
    banks.set(tag, def); return def;
  }
  function enemy(id, dir) {
    const type = window.FieldMonsters?.MONSTER_TYPES[id], art = type?.art;
    if (!art) return null;
    const bank = art.directions ? art.directions[dir] : art.walk || Array.from({length: art.frames}, (_, i) => i);
    if (!bank?.length) return null;
    const urls = Array.from({length: art.frames}, (_, i) => art.dir + (art.files ? art.files[i] : art.file.replace('{n}', String(i + 1).padStart(2, '0'))));
    return {id, label: type.name, group: 'enemy', art, frames: bank.map(i => ({url: urls[i], width: art.w, height: art.h, scale: art.scale, anchor: [art.w / 2, art.h - (art.feet || 0)]})),
      kind: art.directions ? 'distance' : 'time', stride: art.stride, speed: () => type.wanderSpeed,
      fps: art.fps * (art.always ? 2 : 1), clockRate: art.always ? 2 : 1,
      flip: !art.directions && art.faces * (dir === 'left' ? -1 : 1) < 0,
      note: art.directions ? '専用方向' : art.air ? '飛行・共通画像（専用方向なし）' : '共通画像（専用方向なし）'};
  }
  function resolve(group, id, dir) { return group === 'ally' ? ally(id, dir) : enemy(id, dir); }
  function catalog(group) {
    const ids = group === 'ally' ? Object.keys(labels) : Object.keys(window.FieldMonsters?.MONSTER_TYPES || {});
    return ids.map(id => resolve(group, id, 'down')).filter(Boolean).map(d => ({id: d.id, label: d.label}));
  }
  function frameAt(def, seconds) {
    const distance = seconds * (def.speed?.() || 0);
    const index = def.kind === 'distance' ? phaseDistance(distance, def.frames.length, def.stride) : phaseTime(seconds, def.frames.length, def.fps);
    return {index, frame: def.frames[index], lift: (def.bob ? -bob(distance, def.stride) : 0) + (def.art ? air(def.art, seconds * def.clockRate) : 0)};
  }
  function frameTime(def, index) {
    return def.kind === 'distance' ? index * def.stride / (def.frames.length * def.speed()) : index / def.fps;
  }
  window.FieldWalkMotion = Object.freeze({STRIDE, phaseDistance, phaseTime, bob, air, ally, resolve, catalog, frameAt, frameTime});
})();
