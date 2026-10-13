/* WindDance: learn state + visibility gate for Fiona's 風の舞 (data: js/data/support-magic-data.js).
 * State lives in PartyManager.members.fiona.learned = {wind_dance:true}; members are saved wholesale, so the save format is unchanged
 * and old saves simply lack the key (sync(storyStage) restores it for saves past the altar event).
 * The battle command is gated by WINDBOUND_FEATURES.windDanceCommand (off until the numbers are approved; ?feature=windDanceCommand turns it on for testing). */
(function () {
  'use strict';
  const ID = 'wind_dance';
  const F = window.WINDBOUND_FEATURES = window.WINDBOUND_FEATURES || {windDanceCommand: false, boltMana: 'off'};
  if (!F.boltMana) F.boltMana = 'off';   // 'off' | 'hit' | 'action'  (provisional MP regain on Fiona's bolt; ?boltMana=hit|action turns it on for testing)
  try { if (/[?&]feature=windDanceCommand\b/.test(location.search)) F.windDanceCommand = true; } catch (e) {}
  try { const m = /[?&]boltMana=(hit|action)\b/.exec(location.search); if (m) F.boltMana = m[1]; } catch (e) {}
  const member = () => (typeof PartyManager !== 'undefined' ? PartyManager.members.fiona : null);
  const learned = () => { const m = member(); return !!(m && m.learned && m.learned[ID]); };
  function learn() {
    const m = member(); if (!m || learned()) return false;
    (m.learned = m.learned || {})[ID] = true;
    if (F.windDanceCommand && window.storyToast) storyToast('フィオナは「風の舞」を覚えた');
    return true;
  }
  // old saves / dev jumps: past the altar event the spell is known
  function sync(stage) { if (stage >= SupportMagicData[ID].learn.minStoryStage) learn(); }
  const commandVisible = () => learned() && F.windDanceCommand === true;
  // Battle-side helpers (used by js/prologue-combat.js): the spell's decided numbers, and the provisional bolt MP regain.
  const spell = () => SupportMagicData[ID];
  const boltMana = (timing) => (F.boltMana === timing ? SupportMagicData.fiona_bolt_mana.amount : 0);   // timing: 'hit' | 'action'
  window.WindDance = Object.freeze({id: ID, learned, learn, sync, commandVisible, data: spell, boltMana,
    mp: () => spell().mp, effect: () => spell().effect});
})();
