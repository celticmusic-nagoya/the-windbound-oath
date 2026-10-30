# Fiona/Lou eyelid correction after Android feedback

Base main: `fac97543d19f85e85e8de38679162877e4577cf0`; user approved the natural curved-lid reference after asking to fix BOTH blink and expression images. Emma: user Android QA PASS, excluded from changes. PR [#91](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/91).

## Final technical result: PASS

Tested head: `ed76f33178b3f89d2aaa54da7e93cc31d3027f97`; final source/build commit: `3a06c73`. Later commits add only documentation and captured QA evidence. [All12 regression files, exact hashes/results](evidence/eyelid-correction/results.json).

- m48:28newPNG exactSHA/status;110existing PNGs unchanged (67formal normals/Aidan/CG +43previous20C candidates, including all15Emma candidates). Each12static revision retains every alpha byte and every RGBA pixel outside its explicit eye masks. Overlay coordinates/alpha verified.
- m47: all registered expressions, normal blink manual/auto/loop, frames0–4 and BOTH-eye actual pixels,6viewports, left/right/rotation, reduced-motion, DEV cleanup and save/story invariance.
- m46: actual Emma NPC, Fiona bench and Lou post-Raider conversations. THREE natural3–6second blinks per character, actual fullcanvas equals correct normal+overlay composite for every sampled frame; lifecycle/end/cancel/LOAD/CG takeover and existing story outcome PASS.
- m40–m45 and cliff/talk/save regressions: PASS. Node controller/registry unit tests:6PASS. Asset-registry build/check/audit:0errors.

Independent visual review caught two defects in the first branch-only candidate before landing: partial frames sampled the donor's future closed lash as a second contour, and Lou retained old long upper-lash tips above the new mask. The partial compositor now samples clear skin at least7px from the donor closed line; four narrowly bounded dark-tip cleanup islands preserve the retained brow arc. m48 includes exact point checks that fail on the earlier candidate. The interrupted earlier suite is not counted as the final successful12-file run.

## Actual production canvas eye frames

States0,1,2,3,4 captured from the actual shared canvas (3× enlargement only for inspection):

| Character | Left eye | Right eye |
|---|---|---|
| Fiona | [actual frames](evidence/eyelid-correction/20d_fiona_L_actual_strip.png) | [actual frames](evidence/eyelid-correction/20d_fiona_R_actual_strip.png) |
| Lou | [actual frames](evidence/eyelid-correction/20d_lou_L_actual_strip.png) | [actual frames](evidence/eyelid-correction/20d_lou_R_actual_strip.png) |

The reused test's filenames start20d, but these artifacts were captured on the20E tested head above, with the new28PNG versions.

## Scope/provenance and device follow-up

[New28PNG ledger and110protected SHA records](../portraits/PHASE4_EYELID_REVISION_20E.json), [build sources/masks/donor warning](../../tools/assets/eyelid-revision/README.md), [user feedback and shape approval](PHASE4_ANDROID_FEEDBACK_20261030.md).

Only eye-region art paths/coordinates and the registry cache key change at runtime. Same registry/renderer/blink controller; no new runtime rendering system, no dialogue/progression/flags/save/battle/title/CG changes. Old20C assets retained; approved normal PNGs are never build outputs. Source imagegen donors are NOT registered portraits; the generated body/face/background outside the eye masks never enters runtime.

New derived Fiona/Lou art remains **PROVISIONAL_ANDROID_QA**. Shape reference approved; final Android display recheck remains user pending. Emma remains user-declared physical QA PASS with its PNGs/coordinates/paths unchanged.

Check: published game→DEV→立ち絵・モーションテスト→Fiona/Lou→normal→frames1–4/manual/auto/loop; also smile/relieved/angry/determined as registered. Production routes remain Fiona summit bench, Lou post-Raider conversation. No new scene or story requirement.
