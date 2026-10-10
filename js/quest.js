/* Quest state (M6). Stored per quest: 'active' | 'reported'. Anything else is 'unaccepted'.
 * 'complete' (達成, not yet reported) is DERIVED: the quest is active and its `complete` condition (TalkConditions) holds,
 * so it never goes out of sync with the inventory / flags. Save payload: {id:'active'|'reported'} (root key `quests`).
 * Quest definitions live in js/field/quest-data.js. */
(function () {
  'use strict';
  const stored = {};
  const defs = () => (window.QuestData && QuestData.quests) || {};
  const def = id => defs()[id];
  function ctx() {   // same vocabulary as talk conditions; quest() avoids recursion by using stored state
    return {
      flag: n => Boolean(window.FieldTalk && FieldTalk.flag(n)),
      stage: () => (typeof storyStage === 'number' ? storyStage : 0),
      sealOpen: () => (window.PrologueProgress && PrologueProgress.count() >= 3) || (typeof storyStage === 'number' && storyStage >= 13),
      treasure: id => Boolean(window.Inventory && Inventory.serialize().claimed.includes(id)),
      item: id => (window.Inventory ? Inventory.count(id) : 0),
      talked: id => Boolean(window.FieldTalk && FieldTalk.seenEntry(id)),
      quest: id => (stored[id] === 'reported' ? 'reported' : stored[id] === 'active' ? 'active' : 'unaccepted')
    };
  }
  function state(id) {
    const d = def(id); if (!d) return null;
    const s = stored[id];
    if (s === 'reported') return 'reported';
    if (s === 'active') return TalkConditions.test(d.complete, ctx()) ? 'complete' : 'active';
    return 'unaccepted';
  }
  function accept(id) { if (!def(id) || stored[id]) return false; stored[id] = 'active'; return true; }
  // Report: allowed when complete (or when the quest is not yet accepted but already satisfied: found early).
  function report(id) {
    const d = def(id); if (!d || stored[id] === 'reported') return null;
    if (!TalkConditions.test(d.complete, ctx())) return null;
    stored[id] = 'reported';
    return d.reward ? Inventory.grant(d.reward) : [];
  }
  function objective(id) { const d = def(id), s = state(id); return d && d.objective ? (d.objective[s] || '') : ''; }
  function list() {
    return Object.keys(defs()).map(id => ({id, name: def(id).name, state: state(id), objective: objective(id)})).filter(q => q.state !== 'unaccepted');
  }
  function serialize() { return {...stored}; }
  function load(data) {
    for (const k of Object.keys(stored)) delete stored[k];
    if (!data || typeof data !== 'object') return;
    for (const [id, s] of Object.entries(data)) if (def(id) && (s === 'active' || s === 'reported')) stored[id] = s;
  }
  window.Quest = Object.freeze({state, accept, report, objective, list, serialize, load, reset: () => load(null)});
})();
