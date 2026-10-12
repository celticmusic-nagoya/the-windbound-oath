/* Support-magic master (pure data). 風の舞 = Fiona's first support spell: it is first cast by instinct in the Moss Forest altar scene
 * (a story stall of the Goblin Raider), after which it can be used in normal battles.
 * CONFIRMED: name, caster (fiona), kind (support), effect type (ally evasion up), duration is "some turns", learned at the altar event.
 * UNDECIDED (null on purpose; do not fill without approval): evasion amount, turns, MP cost, single/all allies, stacking.
 * The battle engine has no evasion stat yet, so the command stays behind the feature flag WINDBOUND_FEATURES.windDanceCommand (off).
 * `proposal` holds the recommended values from the battle-system survey; it is documentation, never read by the game. */
window.SupportMagicData = Object.freeze({
  wind_dance: Object.freeze({
    id: 'wind_dance', name: '風の舞', caster: 'fiona', kind: 'support',
    effect: Object.freeze({type: 'evasion_up', target: null, amount: null, turns: null, stacking: null}),
    mp: null,
    learn: Object.freeze({event: 'moss_altar_first_cast', minStoryStage: 13}),
    proposal: Object.freeze({amount: '+20% evasion (flat)', turns: 3, mp: 10, target: 'all allies', stacking: 'refresh duration, no stacking'})
  })
});
