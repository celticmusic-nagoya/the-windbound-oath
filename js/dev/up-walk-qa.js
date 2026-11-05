/* PR147 comparison only: explicit URL gate, in-memory rendering policy, no asset-bank writes. */
(() => {
  'use strict';
  if (!window.WINDBOUND_DEV || new URLSearchParams(location.search).get('upWalkQA') !== '1') return;
  const base = window.FieldWalkMotion, cache = new WeakMap();
  const conditions = Object.freeze({A: Object.freeze({order: null, bob: 1}), B: Object.freeze({order: Object.freeze([3,4,1,6]), bob: 1}), C: Object.freeze({order: Object.freeze([3,4,1,6]), bob: .25}), D: Object.freeze({order: null, bob: .25})});
  let selected = 'A';
  const badge = document.createElement('span'); badge.id = 'upWalkQaStatus'; badge.style.cssText = 'position:fixed;top:5px;right:5px;z-index:9999;background:#10201cdd;color:white;padding:4px;pointer-events:none;font:12px system-ui'; document.body.append(badge);
  const show = () => { const c = conditions[selected]; badge.textContent = `DEV上${selected} / ${c.order ? '03→04→01→06' : '現行6'} / 周期90 / bob${c.bob*100}% / SAVE不変`; }; show();
  function ally(id, dir, profile = true, state = 'walk') {
    const original = base.ally(id, dir, profile, state);
    if (!original || id !== 'aidan' || dir !== 'up' || state !== 'walk' || selected === 'A') return original;
    let variants = cache.get(original); if (!variants) { variants = new Map(); cache.set(original, variants); }
    if (!variants.has(selected)) {
      const c = conditions[selected], frames = c.order ? Object.freeze(c.order.map(n => original.frames.find(f => f.key === `aidan_walk_up_${String(n).padStart(2,'0')}`))) : original.frames;
      variants.set(selected, Object.freeze({...original, frames, bobScale: c.bob, note: `DEV上方向${selected}（本番未採用）`}));
    }
    return variants.get(selected);
  }
  window.FieldWalkMotion = Object.freeze({...base, ally, resolve(group, id, dir, state = 'walk') { return group === 'ally' ? ally(id, dir, true, state) : base.resolve(group, id, dir, state); }});
  const reset = () => { selected = 'A'; show(); };
  window.DevUpWalkQA = Object.freeze({get condition() { return selected; }, conditions, setCondition(id) { if (!Object.hasOwn(conditions,id)) return false; selected = id; show(); return true; }, reset});
  window.LoadCoordinator?.onInvalidate(reset);
  window.addEventListener('pagehide', reset);
})();
