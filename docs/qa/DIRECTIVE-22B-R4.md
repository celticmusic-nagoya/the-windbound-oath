# DIRECTIVE-22B-R4 QA

Base main: c4c5d22047ba5c9cdeef84b49a9c742356295ce2. [Source revisions,29PNG SHA, Android steps](../portraits/PHASE4_FIONA_22BR4.md). All assets remain PROVISIONAL_ANDROID_QA; physical Android NOT_RUN.

## Asset and source inspection

R4static3/R3static2/R2blink24 match source SHA manifests byte-for-byte. All230formalPNG remain protected by unchanged21A and22A manifests. Formal120 adoption was already completed byPR94; no re-adoption or original replacement. Registry adds29provisional records; all old records unchanged. Runtime changes limited to5base/24overlay URLs and cache key. Shared renderer, crop, timing, scenario, save and battle code untouched.

Independent source reviewer checked exact source commits and all3 blink plates. R4 vsR3 angry276pixels, sad35, worried35, alpha exact; changed-region overlap with opaque R2 overlay pixels0 in all12states. Old protruding brow-head remnants removed, expression brow and fringe preserved; no extra upper crease or brow appears in source plate states0–4. Root also inspected actualcanvas plates and landscape phone screenshot. [Actual brow stages](evidence/directive-22br4/angry_actual_brow_states.png), [sad](evidence/directive-22br4/sad_actual_brow_states.png), [worried](evidence/directive-22br4/worried_actual_brow_states.png).

## Render and lifecycle

M52 uses real DEV UI and production FieldTalk API. All3 R4faces: fullcanvas state0–4 exactly equals independently loaded correctedstatic+R2overlays (browser getImageData), both eyes change pixels, stop restores exactbase. DEV manual/auto/loop,3–6second gaps,5faces candidate labels,static smile/relieved, left/right at390×844 and844×390, reduced-motion, conversation end/cancel/LOAD/battle/CG cleanup PASS. FieldTalk test-only tables do not alter committed story. M46 verifies real existing Fiona/Lou/Emma normal conversations and M44 real Aidan sunset conversation.

Test infrastructure history: initial restricted loopback bind exited125 before tests (NOT_RUN). Network-enabled serial rerun succeeded. Initial new m52 rawPillowRGBA-vs-canvas comparison reported15FAILs includingstate0, while independently decoded JSbase and eye-region checks passed; raw invisibleRGB/alpha rounding differ across decoders. Corrected verifier keeps strict fullpixel equality using browser decoding on both independently loadedexpected and actualcanvas; all15 fullcanvas checks PASS. No game renderer/assets were changed to make that comparison pass. Superseded results are not counted as successful tests.

## Final verification

Final machine result and independent exact-head review recorded with PR. Browser QA serial only. Physical Android final visual acceptance pending; no claim of physical-device execution.

Final technical QA: **11 unique regression files PASS** (10serial runner files +m48direct), **Node6/6PASS**, registryaudit0errors. No uncollected test countedPASS. Latestm52 with pinned29ledger set ran at9bcbf1e, runtime/assets same as earlier regression snapshot. [Machine results](evidence/directive-22br4/results.json).
