/* Shared production frame policy. DEV reads these same registries and selectors. */
(() => {
  'use strict';
  const STRIDE = 90;
  const WALKER_FPS = 7;
  const phaseDistance = (distance, count, stride = STRIDE) => Math.floor((distance || 0) / (stride / count)) % count;
  const phaseTime = (seconds, count, fps) => Math.floor(seconds * fps) % count;
  const bob = (distance, stride = STRIDE, scale = 1) => -Math.abs(Math.sin((distance || 0) / (stride / 2) * Math.PI)) * 1.5 * scale;
  const air = (art, clock) => art.air ? art.air + Math.sin(clock * 3) * 4 : 0;
  const cache = new WeakMap();
  const labels = {aidan: 'エイダン', fiona: 'フィオナ'};
  function ally(id, dir, profile = true, state = 'walk') {
    const source = id === 'aidan' ? window.AidanFieldAssets : id === 'fiona' ? window.FionaFieldAssets : null;
    if (!source) return null;
    let banks = cache.get(source); if (!banks) { banks = new Map(); cache.set(source, banks); }
    const tag = dir + ':' + profile + ':' + state;
    if (banks.has(tag)) return banks.get(tag);
    const side = id === 'fiona' && profile && source.frames['fiona_side_' + dir + '_01'];
    const prefix = id + (side ? '_side_' : '_walk_') + dir + '_';
    let entries = state === 'idle' ? Object.entries(source.frames).filter(([k]) => k === id + '_idle_down') : Object.entries(source.frames).filter(([k]) => k.startsWith(prefix) && /^\d+$/.test(k.slice(prefix.length))).sort(([a], [b]) => Number(a.slice(prefix.length)) - Number(b.slice(prefix.length)));
    if (state === 'walk' && source.walkBanks?.[dir]) entries = source.walkBanks[dir].map(key => [key, source.frames[key]]);
    const frames = Object.freeze(entries.map(([key, a]) =>
      Object.freeze({key, url: a.path, width: a.width, height: a.height, scale: a.scale, anchor: Object.freeze([...a.anchor])})));
    const def = frames.length ? Object.freeze({id, label: labels[id], group: 'ally', frames, kind: state === 'idle' ? 'time' : 'distance', fps: 1,
      get stride() { return window.MossForest?.walkStride?.(id, dir) ?? STRIDE; },
      speed: () => (window.FieldMovement?.settings.pointerStep || 5) * 60, bob: state === 'walk' && id === 'aidan', bobScale: source.bobScale?.[dir] ?? 1, flip: false, dedicated: true,
      note: state === 'idle' ? '待機（基準向き・静止画）' : '専用方向'}) : null;
    banks.set(tag, def); return def;
  }
  function enemy(id, dir, state = 'walk') {
    const type = window.FieldMonsters?.MONSTER_TYPES[id], art = type?.art;
    if (!art) return null;
    if (state === 'walk' && (art.always || !art.directions && (dir === 'up' || dir === 'down'))) return null;
    const bank = state === 'idle' ? art.idle || (art.always ? Array.from({length: art.frames}, (_, i) => i) : [0]) : art.directions ? art.directions[dir] : art.walk || Array.from({length: art.frames}, (_, i) => i);
    if (!bank?.length) return null;
    const urls = Array.from({length: art.frames}, (_, i) => art.dir + (art.files ? art.files[i] : art.file.replace('{n}', String(i + 1).padStart(2, '0'))));
    return {id, label: type.name, group: 'enemy', art, frames: bank.map(i => ({url: urls[i], width: art.w, height: art.h, scale: art.scale, anchor: [art.w / 2, art.h - (art.feet || 0)]})),
      kind: state === 'walk' && art.directions ? 'distance' : 'time', stride: art.stride, speed: () => type.wanderSpeed,
      fps: art.fps, clockRate: 1, dedicated: Boolean(art.directions),
      flip: state === 'walk' && !art.directions && art.faces * (dir === 'left' ? -1 : 1) < 0,
      note: state === 'idle' ? art.idle ? '待機アニメーション' : art.always ? '待機・飛行ループ（歩行素材は未実装）' : '本編は歩行1コマ目を共用（専用待機素材は未実装）' : art.directions ? '専用方向' : '本編の共通画像・左は反転（専用方向素材は未実装）'};
  }
  const npcNames = {soldier:'王国兵士',captain:'兵士隊長',merchant:'商人',townsman:'町人（男）',townswoman:'町人（女）',elder:'長老',child:'子ども',bard:'吟遊詩人',questgiver:'依頼人',liam:'リアム（NPC）',dwarf_drunk:'ドワーフ（NPC）',barkeep:'酒場の主人',guard:'衛兵'};
  function npcLabel(id) { return npcNames[id] || window.LindNpcRegistry?.get(id.replace(/^rv_/, ''))?.label || id; }
  function npc(id, dir, state) {
    if (state === 'walk' && (dir === 'up' || dir === 'down')) return null;
    const data = window.FieldWalkers?.describe(id); if (!data) return null;
    const urls = state === 'idle' ? data.frames.slice(0, 1) : data.frames.slice(1);
    if (!urls.length) return null;
    return {id, label: npcLabel(id), group:'npc', frames: urls.map(url => ({url, width:data.w, height:data.h, scale:1, anchor:[data.w / 2, data.h], native:false})),
      kind:'time', fps:state === 'idle' ? 1 : data.fps, dedicated:false, flip:state === 'walk' && dir === 'left',
      note:state === 'idle' ? '本編の待機画像（基準向き）' : '本編の横向き共通画像・左は反転（専用方向素材は未実装）'};
  }
  function resolve(group, id, dir, state = 'walk') { return group === 'ally' ? ally(id, dir, true, state) : group === 'npc' ? npc(id, dir, state) : enemy(id, dir, state); }
  function catalog(group) {
    const ids = group === 'ally' ? Object.keys(labels) : group === 'npc' ? window.FieldWalkers?.looks() || [] : Object.keys(window.FieldMonsters?.MONSTER_TYPES || {});
    return ids.map(id => resolve(group, id, 'down', 'idle')).filter(Boolean).map(d => ({id: d.id, label: d.label}));
  }
  function frameAt(def, seconds) {
    const distance = seconds * (def.speed?.() || 0);
    const index = def.kind === 'distance' ? phaseDistance(distance, def.frames.length, def.stride) : phaseTime(seconds, def.frames.length, def.fps);
    return {index, frame: def.frames[index], lift: (def.bob ? -bob(distance, def.stride, def.bobScale ?? 1) : 0) + (def.art ? air(def.art, seconds * def.clockRate) : 0)};
  }
  function frameTime(def, index) {
    return def.kind === 'distance' ? index * def.stride / (def.frames.length * def.speed()) : index / def.fps;
  }
  window.FieldWalkMotion = Object.freeze({STRIDE, WALKER_FPS, phaseDistance, phaseTime, bob, air, ally, resolve, catalog, frameAt, frameTime});
})();
