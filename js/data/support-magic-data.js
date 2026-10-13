/* Support-magic master (pure data). 風の舞 = Fiona's first support spell: it is first cast by instinct in the Moss Forest altar scene
 * (a story stall of the Goblin Raider), after which it can be used in normal battles.
 * DECIDED by the author (2026-10-13, "standard" plan): caster Fiona, all allies, evasion +15 points (NOT damage reduction), 3 enemy phases
 * (the phase of the cast included), MP10, no stacking (recasting refreshes the duration). Learned at the altar event, unusable before.
 * The command stays behind WINDBOUND_FEATURES.windDanceCommand (off by default) until the balance pass is approved.
 * fiona_bolt_mana = PROVISIONAL (amount 3 / hit-vs-action timing under comparison); default mode 'off'. Modes: 'hit' (MP on a landed bolt) | 'action' (MP when the attack is executed). */
window.SupportMagicData = Object.freeze({
  wind_dance: Object.freeze({
    id: 'wind_dance', name: '風の舞', caster: 'fiona', kind: 'support',
    effect: Object.freeze({type: 'evasion_up', target: 'all_allies', amount: 0.15, phases: 3, stacking: 'refresh'}),
    mp: 10,
    learn: Object.freeze({event: 'moss_altar_first_cast', minStoryStage: 13})
  }),
  fiona_bolt_mana: Object.freeze({amount: 3, provisional: true, defaultMode: 'off'})
});
