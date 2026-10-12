/* EquipmentManager: who wears what. Equipment definitions: js/data/equipment-data.js. Owned-but-unworn pieces live in Inventory
 * (count(id) = bag only); equipping moves one piece bag -> slot, unequipping moves it back, swapping returns the old piece.
 * State: party_equipment_state = { <characterId>: { weapon, head, body, accessory1, accessory2 } }  (+ an 'unlocked' flag: the EQUIP menu opens after the prologue)  (only filled slots are stored).
 * Save payload (additive, optional in the save file):  { v:1, state:{aidan:{weapon:'wooden_sword'}} }  - ids only, never numbers,
 * so rebalancing a bonus later never invalidates a save. load() drops unknown ids / wrong slot / not-allowed wearer.
 * Final stats:  apply(id, baseStats) = base + sum(mods)   (charStats() calls it; nobody equipped = unchanged = old balance).
 * Weapons carry motionVariant -> BattleMotion.setVariant(characterId, variant) so 'aidan:wooden' attack frames play automatically
 * (no frames delivered for that variant -> base motion / still, see js/battle-motion.js). Emits 'equipment-change' {id,slot,item,prev}. */
(function () {
  'use strict';
  const E = window.EquipmentData, I = () => window.Inventory, state = {};
  const def = id => E.items[id] || null;
  const worn = c => (state[c] || (state[c] = {}));
  const fits = (slot, d) => slot === d.slot || (d.slot === 'accessory' && /^accessory[12]?$/.test(slot));
  const sockets = s => s === 'accessory' ? ['accessory1', 'accessory2'] : [s];
  let unlocked = false;
  const lockedAt = (c, s) => { const d = def(worn(c)[s]); return !!(d && d.locked); };
  function why(c, id, slot) {
    const d = def(id); if (!d) return 'unknown_item';
    if (slot && !fits(slot, d)) return 'wrong_slot';
    if (d.equipBy && !d.equipBy.includes(c)) return 'not_allowed';
    return null;
  }
  function syncVariant(c) {
    if (!window.BattleMotion) return;
    const w = def(worn(c).weapon); BattleMotion.setVariant(c, w && w.motionVariant ? w.motionVariant : null);
  }
  const emit = d => window.dispatchEvent(new CustomEvent('equipment-change', {detail: d}));
  function equip(c, id, slot) {
    const d = def(id), r = why(c, id, slot); if (r) return {ok: false, reason: r};
    if (I().count(id) < 1) return {ok: false, reason: 'not_in_bag'};
    const w = worn(c);
    const s = d.slot === 'accessory' ? (slot && /^accessory[12]$/.test(slot) ? slot : (sockets('accessory').find(k => !w[k]) || 'accessory1')) : d.slot;
    if (lockedAt(c, s)) return {ok: false, reason: 'locked'};
    const prev = w[s] || null;
    I().take(id, 1); if (prev) I().add(prev, 1);
    w[s] = id; if (s === 'weapon') syncVariant(c);
    emit({id: c, slot: s, item: id, prev}); return {ok: true, slot: s, prev};
  }
  function unequip(c, slot) {
    const w = worn(c), prev = w[slot]; if (!prev) return {ok: false, reason: 'empty'};
    if (lockedAt(c, slot)) return {ok: false, reason: 'locked'};
    delete w[slot]; I().add(prev, 1); if (slot === 'weapon') syncVariant(c);
    emit({id: c, slot, item: null, prev}); return {ok: true, prev};
  }
  // how many of `id` the party owns: bag + every wearer (shops use it to avoid duplicate purchases)
  const owned = id => I().count(id) + Object.values(state).reduce((n, w) => n + Object.values(w).filter(x => x === id).length, 0);
  const get = c => ({...worn(c)});
  function bonus(c) {
    const b = {};
    for (const id of Object.values(worn(c))) for (const [k, v] of Object.entries((def(id) || {}).mods || {})) b[k] = (b[k] || 0) + v;
    return b;
  }
  // stat change if `slot` held `id` (null = empty) instead of what it holds now: {atk:+4, def:-1 ...} (only changed keys)
  function delta(c, id, slot) {
    const sum = w => { const b = {}; for (const i of Object.values(w)) for (const [k, v] of Object.entries((def(i) || {}).mods || {})) b[k] = (b[k] || 0) + v; return b; };
    const cur = sum(worn(c)), nw = {...worn(c)}; if (id) nw[slot] = id; else delete nw[slot];
    const nx = sum(nw), d = {};
    for (const k of new Set([...Object.keys(cur), ...Object.keys(nx)])) { const v = (nx[k] || 0) - (cur[k] || 0); if (v) d[k] = v; }
    return d;
  }
  function apply(c, stats) {
    const b = bonus(c), o = {...stats};
    for (const [k, v] of Object.entries(b)) if (k in o) o[k] = o[k] + v;
    o.maxHp = Math.max(1, o.maxHp); return o;
  }
  function serialize() {
    const s = {}; for (const [c, w] of Object.entries(state)) if (Object.keys(w).length) s[c] = {...w};
    return unlocked ? {v: 1, state: s, unlocked: true} : {v: 1, state: s};
  }
  function load(data) {
    for (const c of Object.keys(state)) { delete state[c]; syncVariant(c); }
    unlocked = !!(data && data.unlocked);
    const s = data && data.state; if (!s || typeof s !== 'object') return;
    for (const [c, w] of Object.entries(s)) {
      if (!w || typeof w !== 'object') continue;
      for (const [slot0, id] of Object.entries(w)) {
        const slot = slot0 === 'accessory' ? 'accessory1' : slot0;   // saves from the one-socket era
        if (typeof id !== 'string' || !E.slots.includes(slot)) continue;
        const r = why(c, id, slot);
        if (!r) worn(c)[slot] = id;
        else if (r === 'not_allowed' && def(id)) I().add(id, 1);   // a piece the wearer may no longer use (Aidan's old iron/steel sword) goes back to the bag instead of vanishing
      }
      syncVariant(c);
    }
  }
  // Proposal only: convert legacy starter identity without modifying the source save or its schema.
  function migrateStarterSword(saved) {
    const out = JSON.parse(JSON.stringify(saved));
    const gear = out.inventory && out.inventory.gear;
    if (gear && typeof gear === 'object' && !Array.isArray(gear)) {
      const n = gear.wooden_sword;
      if (Number.isInteger(n) && n > 0 && n <= 99) {
        const existing = gear.father_sword === undefined ? 0 : gear.father_sword;
        if (!Number.isInteger(existing) || existing < 0 || existing + n > 99)
          throw new Error('Starter sword migration requires manual review: bag overflow/invalid count');
        gear.father_sword = existing + n;
        delete gear.wooden_sword;
      }
    }
    const aidan = out.equipment && out.equipment.state && out.equipment.state.aidan;
    if (aidan && aidan.weapon === 'wooden_sword') aidan.weapon = 'father_sword';
    return out;
  }
  // Story-driven weapon changes (the bag is not involved): the sword breaks / the oath sword is bound. Locked weapons are only set here.
  function setStoryWeapon(c, id) {
    const w = worn(c), prev = w.weapon || null; if (prev === id) return {ok: true, same: true};
    if (id && why(c, id, 'weapon')) return {ok: false, reason: why(c, id, 'weapon')};
    if (id) w.weapon = id; else delete w.weapon;
    syncVariant(c); emit({id: c, slot: 'weapon', item: id || null, prev}); return {ok: true, prev};
  }
  const isUnlocked = () => unlocked;
  function unlock() { if (unlocked) return false; unlocked = true; window.dispatchEvent(new CustomEvent('equipment-unlock')); return true; }
  const reset = () => load(null);
  window.EquipmentManager = Object.freeze({migrateStarterSword, setStoryWeapon, isUnlocked, unlock, equip, unequip, get, owned, bonus, delta, apply, serialize, load, reset, canEquip: (c, id, slot) => why(c, id, slot), def});
})();
