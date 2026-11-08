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
 *   {approach:{a,b,gap?,ms?,share?}}             two actors walk toward each other (walk -> idle), e.g. {a:'aidan',b:'fiona',gap:46,ms:1400}
 *   {move:{actor,x,y,ms?}} · {follow:'fiona'}   walk one actor to a point · give Fiona back to the follow behaviour
 *   {shake:{ms, amp}} · {wait:ms} · {set:{flag:true}} · {stage:n}  · {call:'hook'}
 * Stage flow: storyStage 3 (training done, road to the cliff open) -> this scene -> stage 4 -> returnScene -> 5 (village burning). */
window.FieldSceneData = Object.freeze({scenes: Object.freeze({
  // SCENARIO-PROLOGUE-02: played once by RildeVillage.afterTraining() right after the training dummy is beaten (stage 3).
  // The flag emma_snack_done (FieldTalk flags, saved with SAVE) keeps it from playing again. No stage change.
  emma_snack: {
    requireStage: 3,
    steps: [
      {lock: true},
      {talk: 'scene_emma_snack'},
      {set: {emma_snack_done: true}},
      {lock: false}
    ]
  },
  cliff_sunset_to_fire: {
    requireStage: 3,
    steps: [
      {lock: true},
      {move: {actor: 'aidan', x: 2384, y: 1022, ms: 650}},      // sit down on the bench: Aidan and Fiona settle in front of it
      {move: {actor: 'fiona', x: 2424, y: 1022, ms: 650}},
      {wait: 500},
      // Establishing sunset background, followed by the approved back-view two-character CG.
      {cg: {src: 'assets/approved/game/cliff/sunset_background.png', alt: '夕暮れの断崖と海', mode: 'dialogue'}},
      {wait: 900},
      {cg: {src: 'assets/approved/game/cliff/sunset_two_characters_back_view.png', alt: '夕暮れの断崖に佇むエイダンとフィオナ', mode: 'dialogue'}},
      {talk: 'scene_cliff_sunset'},
      {cg: {hide: true}},
      {fade: {to: 1, ms: 1200}},
      {tod: {set: 'night', instant: true}},
      {wait: 800},
      {fade: {to: 0, ms: 1600}},
      // Establishing starry-sky view; seated and standing approved compositions.
      {cg: {src: 'assets/approved/game/cliff/stargazing_seated.png', alt: '断崖で星空を見上げる二人', mode: 'dialogue'}},
      {wait: 900},
      {cg: {src: 'assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png', alt: '星空を見上げる断崖', mode: 'dialogue'}},
      {talk: 'scene_cliff_night'},
      {cg: {src: 'assets/approved/game/cliff/stargazing_standing_final.png', alt: '立ち上がり真上の星空を見上げる二人', mode: 'dialogue'}},
      {wait: 1100},
      {talk: 'scene_cliff_wind_stops'},
      {cg: {hide: true}},
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
