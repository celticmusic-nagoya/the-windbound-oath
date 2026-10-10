/* Scripted scenes (data only; executed by js/field/field-scene.js).
 *   scene = {requireStage?: n | [min,max], steps:[step...], done?: 'hookName'}
 * steps (run in order, each waits until finished):
 *   {lock:true|false}                         freeze / free the player
 *   {talk:'scene_id'}                          FieldTalk conversation (see talk-data-scenes.js); waits for its end
 *   {fade:{to:0..1, ms}}                       black screen (1 = fully black)
 *   {tod:{set:'dusk|night|day', ms?, instant?}} time of day (js/field/field-timeofday.js)
 *   {vista:{id, on, ms?}}                      reveal / hide a map vista (burning village etc.)
 *   {pan:{x, y, ms, hold}}                     camera glide to a world point and back
 *   {focus:{x, y, ms}} … {release:{ms}}        camera glides to a point and STAYS (talk during it) until released
 *   {shake:{ms, amp}} · {wait:ms} · {set:{flag:true}} · {stage:n}  · {call:'hook'}
 * Stage flow: storyStage 3 (training done, road to the cliff open) -> this scene -> stage 4 -> returnScene -> 5 (village burning). */
window.FieldSceneData = Object.freeze({scenes: Object.freeze({
  cliff_sunset_to_fire: {
    requireStage: 3,
    steps: [
      {lock: true},
      {talk: 'scene_cliff_sunset'},
      {fade: {to: 1, ms: 1200}},
      {tod: {set: 'night', instant: true}},
      {wait: 800},
      {fade: {to: 0, ms: 1600}},
      {talk: 'scene_cliff_night'},
      {vista: {id: 'village_fire', on: true, ms: 2000}},
      {focus: {x: 560, y: 2830, ms: 2200}},     // camera slides down to the far village and stays
      {wait: 900},
      {shake: {ms: 700, amp: 4}},
      {talk: 'scene_cliff_fire'},
      {wait: 600},
      {fade: {to: 1, ms: 1000}},
      {release: {ms: 10}},
      {stage: 4},
      {call: 'cliffRunHome'}
    ]
  }
})});
