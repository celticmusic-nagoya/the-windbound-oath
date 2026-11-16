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
