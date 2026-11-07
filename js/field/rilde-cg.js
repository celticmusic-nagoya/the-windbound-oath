/* Rilde CG approved registry. Asset selection only; no story/save mutations.
 * Reference composites are not inserted into gameplay until scene direction is approved.
 */
(function () {
  'use strict';
  const PREFIX = 'assets/approved/game/rilde_story/';
  const SCENES = Object.freeze({
    cliff_dialogue: PREFIX + 'cliff/stargazing_dialogue_background.png',
    road_reveal_reference: PREFIX + 'road/curve_reveal_APPROVED_user_reference.jpg',
    raid_background: PREFIX + 'raid/attack_background_only.png',
    raid_composite_reference: PREFIX + 'raid/attack_with_characters_APPROVED_user_reference.jpg',
    aftermath_background: PREFIX + 'aftermath/ruins_background_only.png',
    recovery_composite_reference: PREFIX + 'recovery/relief_with_characters_APPROVED_user_reference.jpg'
  });
  const REFERENCE_ONLY = Object.freeze([
    'road_reveal_reference', 'raid_composite_reference', 'recovery_composite_reference'
  ]);
  function pathFor(id) {
    return Object.prototype.hasOwnProperty.call(SCENES, id) ? SCENES[id] : null;
  }
  function gameplayPathFor(id) {
    return REFERENCE_ONLY.includes(id) ? null : pathFor(id);
  }
  window.RildeCG = Object.freeze({scenes: SCENES, referenceOnly: REFERENCE_ONLY, pathFor, gameplayPathFor});
})();
