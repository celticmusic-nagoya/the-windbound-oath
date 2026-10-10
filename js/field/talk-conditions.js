/* Talk condition evaluator (M6). Pure: no DOM, no globals. Works in the browser (window.TalkConditions) and node (module.exports).
 * A condition is an object; all keys in it must hold (AND). Keys:
 *   all:[c..]  any:[c..]  not:c
 *   flag:'name'                 ctx.flag(name) is truthy
 *   stage:[min,max] | {min,max} ctx.stage within range (either bound optional)
 *   sealOpen:true|false         ctx.sealOpen() equals value
 *   treasure:'id'               ctx.treasure(id) - that chest was opened
 *   item:'id' (+ min:n)         ctx.item(id) >= min (default 1)
 *   talked:'entryId'            ctx.talked(entryId) - that entry was already played
 *   quest:{id,state}            ctx.quest(id) === state
 * An empty / missing condition is true. Unknown keys make the condition FALSE (and validate() reports them). */
(function (root) {
  'use strict';
  const KEYS = ['all', 'any', 'not', 'flag', 'stage', 'sealOpen', 'treasure', 'item', 'min', 'talked', 'quest'];
  function test(c, ctx) {
    if (c == null) return true;
    if (typeof c !== 'object' || Array.isArray(c)) return false;
    for (const k of Object.keys(c)) {
      const v = c[k];
      switch (k) {
        case 'all': if (!Array.isArray(v) || !v.every(x => test(x, ctx))) return false; break;
        case 'any': if (!Array.isArray(v) || !(v.length ? v.some(x => test(x, ctx)) : true)) return false; break;
        case 'not': if (test(v, ctx)) return false; break;
        case 'flag': if (!ctx.flag(v)) return false; break;
        case 'stage': {
          const lo = Array.isArray(v) ? v[0] : v && v.min, hi = Array.isArray(v) ? v[1] : v && v.max, s = ctx.stage();
          if (lo != null && s < lo) return false; if (hi != null && s > hi) return false; break;
        }
        case 'sealOpen': if (Boolean(ctx.sealOpen()) !== Boolean(v)) return false; break;
        case 'treasure': if (!ctx.treasure(v)) return false; break;
        case 'item': if (ctx.item(v) < (c.min == null ? 1 : c.min)) return false; break;
        case 'min': break;   // modifier of 'item'
        case 'talked': if (!ctx.talked(v)) return false; break;
        case 'quest': if (!v || ctx.quest(v.id) !== v.state) return false; break;
        default: return false;
      }
    }
    return true;
  }
  function validate(c, path = 'when') {
    const bad = [];
    if (c == null) return bad;
    if (typeof c !== 'object' || Array.isArray(c)) return [path + ': must be an object'];
    for (const k of Object.keys(c)) {
      if (!KEYS.includes(k)) bad.push(path + ': unknown condition "' + k + '"');
      else if (k === 'all' || k === 'any') { if (!Array.isArray(c[k])) bad.push(path + '.' + k + ': must be an array'); else c[k].forEach((x, i) => bad.push(...validate(x, path + '.' + k + '[' + i + ']'))); }
      else if (k === 'not') bad.push(...validate(c[k], path + '.not'));
    }
    return bad;
  }
  const api = {test, validate, KEYS};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.TalkConditions = api;
})(typeof window !== 'undefined' ? window : globalThis);
