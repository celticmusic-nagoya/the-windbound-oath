# LIND-REF-01 — first verified source-to-scene matrix (read-only audit)
Status: PARTIAL; exact map-image geometry and CG scene frames still require visual inspection. No invented final coordinates.

## Provenance and authority
- Policy: main/AGENTS.md and main/docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md (read 2026-11-16).
- Canon: private the-windbound-oath-handoff/main reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md section 8, CANON_ADDENDUM.md and CANON_STATUS.md (directly read). Do not reproduce private script text in public.
- Village reference: main/docs/art/reference/lind/リルド村RPGアセット全体マップ.png, inventory SHA-256 83dd4ad1eb10103fdb7eb569e8b1b22cc92920d4c94d4eae85735125de87fe6c. Binary image has **not** yet been visually verified in this audit.
- Prototype implementation: main/docs/field/lind-production-step0.md and main/docs/field/lind-production-batch1.md, both directly read. These document implementation, not approved final village coordinates.

## Scene and spatial matrix
| Place or action | Verified narrative/spatial rule | Existing prototype connection | Source confidence / remaining evidence |
| --- | --- | --- | --- |
| Village core | Agricultural and livestock village; central square, wind rune stone and well; inn, shop, elder home, Aidan home, dwellings and barns | #world DOM field, CSS camera() | CANON text verified; map pixel placement BLOCKED |
| North | Wind hill direction | hillIndex===10 prototype windVeil behavior | CANON text verified; hill geometry and event CG BLOCKED |
| Northwest | Waterfall and elder home | existing elder door data-room=elder | CANON text verified; footprint/CG BLOCKED |
| South/southeast | Wheat, vegetables, flowers, apples, hay and livestock | first-batch farm candidates | CANON text verified; individual candidate QA and placement BLOCKED |
| East | River crossing and separate training ground | prototype river x1450..1630; bridge y540..625; training at x1540 y800, dummies x1630 y900 and x1760 y930, Fiona x1710 y845 | Relative relationship CANON; **numeric coordinates prototype only**, not final |
| Aidan house | Village home and opening-story staging | door data-room=home; first-batch house PNG candidate | Location/appearance/CG and entrance anchor BLOCKED |
| Other buildings | Inn/shop/elder entrances | door data-room=inn/shop/elder | Existing IDs verified in step0; final footprint BLOCKED |
| Wind-stop | Grass, trees, signs, laundry and leaves stop wind motion; water continues | hillIndex===10 stops only #windVeil | CANON verified; full village environmental controller NOT_IMPLEMENTED |
| Birds | Flying, grounded, proximity takeoff, altered activity during wind-stop | no validated integrated behavior in inspected docs | CANON verified; integration NOT_RUN |
| Escape and battle | Village attack and river-side retreat; event sequence must preserve approved prologue | existing event/story system and training stage1->2 described in step0 | Scene-specific CG, route geometry, runtime code and save regression NOT_AUDITED |
| Save and navigation | Preserve existing door and story hooks and save compatibility | windbound_oath_v028 version29 in step0, PrologueProgress.serialize/load, camera(), px/py and ipx/ipy | Documented prototype; current runtime source must be checked before modifying |

## Current render CI evidence
- GitHub Actions run 43824719424: LIND Blender technical integration **success**; setup, fixture generation, baseline/corrected render and evidence upload all success. Artifact ID 14205758180.
- This is a 96×96 **technical cube fixture**, not an artistic asset or village scene. No G2 or G4 approval implied.

## Next tasks by lane
- STORY/Codex: list actual village CG files, event scripts, IDs, scene sequence and event-to-place anchors, with source hashes; do not change game code.
- WORLD/Claude: inspect canonical map PNG pixels and terrain/water sheets, reconcile against the matrix and propose spatial JSON for review.
- HOME/Claude: inspect all official Aidan home CG and first-batch candidates, previous masonry QA and interior threshold; write evidence-based master-model interface.
- COORD: require each candidate PR to cite this matrix, the approved spatial contract revision and the input hashes.
- INTEGRATION/Codex: visually inspect actual render PNG artifact and validate render output before applying the workflow to any accepted building.

Gate: G1 PARTIAL/BLOCKED on map and CG; G2 NOT_RUN; G3 PASS **technical fixture only**; G4 NOT_RUN.

## Follow-up audit — scene CG and wind/birds implementation (2026-11-16)
Directly inspected main/docs/qa/rilde-cg-runtime-01-event-audit.md, main/js/field/lind-birds.js and main/js/event-cg.js. The 2026-11-07 CG audit is historical and does not establish current implementation completeness; recheck source and PR before G1/G4 PASS.

| Scene | Event-to-place relationship | Asset or source | Caveat |
| --- | --- | --- | --- |
| Sunset promise | bench choice -> FieldScene cliff_sunset_to_fire -> scene_cliff_sunset | assets/approved/game/cliff/sunset_two_characters_back_view.png | Historical audit calls cue Draft PR; no village footprint inferred |
| Night sky | same FieldScene, after TOD night -> scene_cliff_night | assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png | Camera viewpoint reference, not a terrain height measurement |
| Distant village fire | village_fire vista -> scene_cliff_fire | no separate approved distant-view background cue in audit | Do not invent CG |
| Return route | cliffRunHome -> startReturnScene -> returnScene | road/curve_reveal_APPROVED_user_reference.jpg | Reference-only composite; no runtime injection |
| Attack | enterBurningVillage stage 5, atk_enter | raid/attack_background_only.png | HUD integration unverified |
| Attack composite | same stage | raid/attack_with_characters_APPROVED_user_reference.jpg | Reference-only, not gameplay layer |
| Ruins | stage >= 5 -> rilde_village_01_ruin | aftermath/ruins_background_only.png | No independently verified standalone cue |
| Recovery | startEscapeScene -> enterMossForest | recovery/relief_with_characters_APPROVED_user_reference.jpg | Exact scene beat requires approval |

Wind/bird runtime: main/js/field/lind-birds.js is DEV-gated by WINDBOUND_DEV and listens to lind-wind-change. It uses wind state and two prototype perching positions (575,750) and (1320,1175), which are NOT canonical coordinates. It does not own water or livestock timelines. The separate main/js/event-cg.js focuses on Lou/altar scenes rather than establishing village CG spatial coordinates. Keep village CG event layer inventory separate from unrelated altar CG. Next step is image-binary review and full runtime event code inspection; G1 and G4 remain BLOCKED/NOT_RUN as appropriate.
