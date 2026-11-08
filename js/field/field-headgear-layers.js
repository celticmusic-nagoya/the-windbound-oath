/* HEADGEAR-LAYER-01: pure candidate composition; no production game hooks. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.FieldHeadgearLayers = api;
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';
  const SLOTS = Object.freeze(['upper', 'middle', 'lower']);
  const DIRECTIONS = Object.freeze(['down', 'left', 'right', 'up']);
  const safeId = s => typeof s === 'string' && /^[a-z][a-z0-9_-]*$/.test(s);
  function validateItem(item) {
    if (!item || !safeId(item.id) || !SLOTS.includes(item.slot)) throw new TypeError('invalid headgear item');
    const occupies = item.occupies || [item.slot];
    if (!Array.isArray(occupies) || !occupies.length || !occupies.includes(item.slot) ||
        new Set(occupies).size !== occupies.length || occupies.some(s => !SLOTS.includes(s)))
      throw new TypeError('invalid occupied slots');
    if (!item.directions || DIRECTIONS.some(d => typeof item.directions[d] !== 'string' ||
        !new RegExp('^assets/candidates/headgear/[a-z0-9_-]+/' + d + '\\.png$').test(item.directions[d])))
      throw new TypeError('missing or unsafe directional sprite');
    return Object.freeze({id:item.id,slot:item.slot,occupies:Object.freeze([...occupies]),directions:Object.freeze({...item.directions})});
  }
  function equip(items, next) {
    const item=validateItem(next);
    const current=(items || []).map(validateItem);
    const kept=current.filter(old => !old.occupies.some(s => item.occupies.includes(s)));
    return Object.freeze([...kept,item].sort((a,b)=>SLOTS.indexOf(a.slot)-SLOTS.indexOf(b.slot)));
  }
  function compose(basePath, items, direction) {
    if (!DIRECTIONS.includes(direction)) throw new TypeError('invalid direction');
    if (typeof basePath !== 'string' || !/^assets\/candidates\/field-hd-pixel\/[a-z0-9_-]+\/(down|left|right|up)\.png$/.test(basePath))
      throw new TypeError('unsafe base path');
    const selected=(items || []).map(validateItem);
    const occupied=new Set();
    for(const item of selected)for(const s of item.occupies){if(occupied.has(s))throw new TypeError('headgear slot conflict');occupied.add(s);}
    return Object.freeze([{slot:'base',src:basePath},...selected.sort((a,b)=>SLOTS.indexOf(a.slot)-SLOTS.indexOf(b.slot)).map(i=>({slot:i.slot,id:i.id,src:i.directions[direction]}))]);
  }
  return Object.freeze({SLOTS,DIRECTIONS,validateItem,equip,compose});
});
