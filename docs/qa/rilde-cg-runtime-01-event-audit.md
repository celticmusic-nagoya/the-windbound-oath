# RILDE-CG-RUNTIME-01 — event-trigger audit (2026-11-07)

## Verified in current source

| Narrative scene | Actual runtime trigger | Approved image | Implementation status |
|---|---|---|---|
| Sunset promise | `FieldTalk` bench choice -> `FieldScene.play('cliff_sunset_to_fire')` -> `scene_cliff_sunset` | `assets/approved/game/cliff/sunset_two_characters_back_view.png` | CG cue in Draft PR |
| Starry-sky conversation | Same FieldScene, after TOD changes to night -> `scene_cliff_night` | `assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png` | CG cue in Draft PR |
| Fire sighting | `village_fire` vista -> camera focus -> `scene_cliff_fire` | No separate approved background cue for the distant-view beat | Preserve existing vista; no image substitution |
| Return road | `cliffRunHome` -> `startReturnScene()` -> `returnScene` click pages | `road/curve_reveal_APPROVED_user_reference.jpg` | Reference-only composite; not injected into game |
| Burning village / attack | `returnScene` ends -> `enterBurningVillage()`, stage 5, `atk_enter` and combat | `raid/attack_background_only.png` | Asset permitted in renderer, but not yet attached to attack HUD/event; require scene-layer review |
| Attack with characters | Same stage 5 | `raid/attack_with_characters_APPROVED_user_reference.jpg` | Reference-only composite; no gameplay injection |
| Ruins | Current village resolver: stage >= 5 -> `rilde_village_01_ruin` | `aftermath/ruins_background_only.png` | Asset permitted in renderer; no verified standalone story cue |
| Relief / recovery | Attack stage 5–8, `startEscapeScene()` -> `enterMossForest()` | `recovery/relief_with_characters_APPROVED_user_reference.jpg` | Reference-only composite; exact beat requires director-approved trigger |

## Guards and follow-up

- Do not change dialogue, `storyStage`, `FieldTalk` flags, save compatibility, combat or scene timing just to show a CG.
- No composite reference CGs should be displayed over live actor sprites until the director approves the intended visual treatment.
- Existing `returnScene` and `escapeScene` are legacy click-driven overlays, not `FieldScene` scenes; extending them requires a separate presentation adapter with cleanup on click/skip/load.
- Keep the burning village's `MossForest` and DOM-village compatibility paths distinct.
- Verify that CG layering is behind dialogue and above the correct field, including portrait and mobile orientations, before merging.
- Current PR is a staging implementation; CI and Android device QA are required before main merge.
