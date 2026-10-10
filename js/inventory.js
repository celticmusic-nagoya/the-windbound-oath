/* Inventory (M6). Consumables keep living in the existing battleItems/gold globals (battle code untouched);
 * key items ("大事なもの") are stored here. Save payload: {key:{id:n}, claimed:[treasureId...]}.
 * claimed = chests whose reward has been fully granted; it makes the legacy補正 idempotent. */
(function () {
  'use strict';
  const D = window.ItemData, E = window.EquipmentData || {items: {}}, key = {}, gear = {}, claimed = new Set();
  const def = id => D.items[id] || (E.items[id] && {...E.items[id], kind: 'equip'});
  const isGear = id => Boolean(E.items[id]);
  const isKey = id => def(id) && def(id).kind === 'key';
  const consumables = () => (typeof battleItems !== 'undefined' ? battleItems : {});
  function count(id) { return isGear(id) ? (gear[id] || 0) : isKey(id) ? (key[id] || 0) : (consumables()[id] || 0); }
  function add(id, n = 1) {
    if (!def(id) || !(n > 0)) return false;
    if (isGear(id)) gear[id] = Math.min(99, (gear[id] || 0) + n);
    else if (isKey(id)) key[id] = (key[id] || 0) + n;
    else consumables()[id] = (consumables()[id] || 0) + n;
    return true;
  }
  // hand items over (quest turn-in). Returns true when the full amount was removed.
  function take(id, n = 1) {
    if (!def(id) || !(n > 0) || count(id) < n) return false;
    if (isGear(id)) { gear[id] -= n; if (gear[id] <= 0) delete gear[id]; }
    else if (isKey(id)) { key[id] -= n; if (key[id] <= 0) delete key[id]; } else consumables()[id] -= n;
    return true;
  }
  // rewards: {potion:2, gold:30, charm_windward:1} -> list of {id,name,n,kind} actually granted
  function grant(rewards) {
    const got = [];
    for (const [id, n] of Object.entries(rewards || {})) {
      if (id === 'gold') { if (n > 0 && typeof gold !== 'undefined') { gold += n; got.push({id, name: 'G', n, kind: 'gold'}); } continue; }
      if (add(id, n)) got.push({id, name: def(id).name, n, kind: def(id).kind});
    }
    return got;
  }
  const describe = got => got.map(g => g.kind === 'gold' ? g.n + 'G' : g.name + ' ×' + g.n).join('、');
  function list(kind) { return Object.keys({...D.items, ...E.items}).filter(id => def(id).kind === kind && count(id) > 0).map(id => ({id, ...def(id), count: count(id)})); }
  function claim(treasureId) { claimed.add(treasureId); }
  // Treasure opened in-game: grant everything once. Returns granted list ([] when already claimed / unknown).
  function openTreasure(treasureId) {
    const r = D.treasure[treasureId];
    if (!r || claimed.has(treasureId)) return [];
    claimed.add(treasureId); return grant(r);
  }
  // Saves made before key items existed: chests already opened get only their key items, once.
  function reconcile(openedIds) {
    const added = [];
    for (const id of openedIds || []) {
      if (claimed.has(id) || !D.treasure[id]) continue;
      claimed.add(id);
      const keys = Object.fromEntries(Object.entries(D.treasure[id]).filter(([k]) => isKey(k)));
      added.push(...grant(keys));
    }
    return added;
  }
  function serialize() { return {key: {...key}, gear: {...gear}, claimed: [...claimed]}; }
  function load(data) {
    for (const k of Object.keys(key)) delete key[k]; for (const k of Object.keys(gear)) delete gear[k]; claimed.clear();
    if (!data || typeof data !== 'object') return;
    for (const [id, n] of Object.entries(data.key || {})) if (isKey(id) && Number.isFinite(n) && n > 0) key[id] = Math.min(99, Math.floor(n));
    for (const [id, n] of Object.entries(data.gear || {})) if (isGear(id) && Number.isFinite(n) && n > 0) gear[id] = Math.min(99, Math.floor(n));
    for (const id of Array.isArray(data.claimed) ? data.claimed : []) if (typeof id === 'string' && D.treasure[id]) claimed.add(id);
  }
  function reset() { load(null); }
  window.Inventory = Object.freeze({count, add, take, grant, describe, list, openTreasure, claim, reconcile, serialize, load, reset, def});
})();
