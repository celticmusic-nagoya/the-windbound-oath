# MORWEN-MOTION-SOURCE-05

**PARTIAL / BLOCKED.** Implemented a minimal data-driven frame-data supplier, verified input/coordinate binding and generated 12 explicit incomplete slots. Actual adopted left/right six-frame animation and the authored v1.0 pose/root stream are still absent. No real foot coordinates were invented. Completion criteria requiring adopted walking images and real motion remain unmet; **MORWEN-MOTION-CONTACT-EXPORT-06 NOT_STARTED**.

## Branch/base/protection

- Base: PR #226 HEAD `905dfb8a3a202cf2b7b66e2be726cd0858ca164d`, verified unchanged on remote. Isolated worktree `/workspace/morwen-motion-source-05`, task branch `feature/morwen-motion-source-05`.
- Shared studio branch observed at `1ac9402b5302c44c7c988ca161e0e8dd8df9c20f`; since the packet baseline it only adds a Layer1 attachment candidate, not a motion source. Deliberately based on the requested PR #226 HEAD.
- Read base AGENTS.md. No agents or shared-file edits. PR #225 HEAD `c9d04592f0669e884858779296d72137a74b45a5` and PR #226 HEAD unchanged. Only new task paths are added. Official PNGs, archived v0.8/v0.9, v1.0 rig, existing tests and prior QA reports untouched.
- Protected canonical manifest: **17/17 SHA-256 PASS** (`SHA_CHECKS.json`). No merge, publication, asset adoption or game integration.

## Investigation and source decision

`SOURCE_INVENTORY.json` pins inspected files and lists each expected left frame's existence/status. Findings:

- `qa/build_morwen_v10_candidate.py` migrates a static spec. `pipeline/caslib/articulated.py` renders v0.9 static images (`frameCount: 1`); `fk_rotate` evaluates isolated range endpoints for QA, not an authored time series. No v1.0 animated renderer or per-frame actor/root computation exists.
- Adopted general field policy specifies static direction sprites with runtime bounce; it does not establish twelve new walk PNGs. The separate HD DEV decision specifies six unique **left** frames at nominal 10fps and contact events F1/F4. These are planning constraints, not measurements, per-foot phases or actual frames.
- `data/sprite-rig/morwen_hd_left_walk6_delivery.json` is AWAITING_ART, all six frames NOT_DRAWN and absent. No adopted right six-frame sequence/definition was located. The six right IDs added here are task slots only.
- `data/morwen-hd-canonical-v2.json` registers static originals/display derivatives and marks prior 74I/75/76/77 chibi walk candidates SUPERSEDED. Older candidate72 near/far ankles are not a v1.0 pose source or measured heel/ball/toe world coordinates. They were not grafted into this task.
- Existing `js/field/morwen-hd-canonical.js:27` computes still-preview placement from scale/anchor correction, not animated sole contacts. Actual images and coordinates cannot be inferred from that placement or the fixed ground marker.

## Implemented changes

New `motion-source/generate_frame_data.py` consumes an explicit JSON plan plus optional actual SHA-pinned PNG, adoption receipt and frame measurement source. It verifies file hashes, PNG format, frame/direction/time/image binding, anatomical joint suffixes, selected sole points and explicitly supplied actor/root transform. It computes world coordinates only from supplied local contact measurements and transform; unknowns stay null with reasons. Output is new task-local JSON only; overwrite and out-of-scope output paths are refused. It never rewrites/re-encodes PNGs or starts a runtime timer.

This is a **frame-data input/evaluation layer**, not an implemented animated v1.0 raster/pose generator. Creating a walking pose sequence without adopted authored motion inputs would invent the requested evidence. The original requested full generator remains BLOCKED by those inputs; no frame synthesis is claimed.

New `motion-source/morwen_walk6.source-plan.json` preserves planned left frame IDs/paths/timing separately from actual image/time/measurement fields. Right-facing source mapping and timing remain unknown. `FRAME_DATA.json` deterministically emits six left + six right slots, all BLOCKED. **0/12 actual adopted frames verified; 0 measured contacts; 24 anatomical-foot records remain NOT_MEASURED**. Both L/R world coordinates and actor transforms are null for every slot. No static image was relabelled as a moving frame.

`motion-source/README.md` defines source receipt/measurement contracts and coordinates:

- local image pixels: top-left origin, x right/y down; anatomical L/R independent of facing;
- explicit per-frame positive scale, clockwise rotation in y-down space, translation in world pixels;
- `world = translationPx + scale * R(rotationDeg) * localPx`, pre-camera; CSS pixels and camera zoom excluded;
- no implicit identity/root translation, no 3D projection inferred, no ankle-to-sole substitution;
- source-recorded measurements are distinct from independently verified anatomy/approval; a matching receipt checks consistency, not human authority. Even complete input would remain REVIEW_REQUIRED, with `export06Allowed=false` until independent evidence review.

## Commands and results

Full before/after output and exit codes: `COMMAND_RESULTS.json`.

```sh
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*.py' -v
node --test tools/character-asset-studio/tests/*.cjs
node --test tests/*.cjs tests/field/*.test.js
python -m unittest discover -s tools/character-asset-studio/pipeline/tests -v
python /workspace/work/morwen-source05/pipeline_diagnostic.py
python tools/character-asset-studio/pipeline/cas.py protect-verify
python tools/character-asset-studio/motion-source/generate_frame_data.py tools/character-asset-studio/motion-source/morwen_walk6.source-plan.json tools/character-asset-studio/qa/morwen-motion-source-05/FRAME_DATA_REPLAY.json
```

| Test | Before | After |
|---|---|---|
| QA unit tests | PASS 25/25 | PASS 37/37 |
| Studio Node | PASS 19/19 | PASS 19/19 |
| Repository regression | FAIL 52 pass / 8 fail | FAIL identical IDs |
| Pipeline | FAIL 55 pass / 3 fail | FAIL identical IDs; decoded pixels examined |
| Protected SHA | — | PASS 17/17 |
| Source generator | — | expected BLOCKED / exit 2; 12 unknown slots |
| Generator replay | — | byte-identical JSON to committed FRAME_DATA.json |
| Actual motion/foot drift | NOT_RUN | NOT_RUN; no valid real source |
| Browser E2E / Android hardware / human visual approval | NOT_RUN | NOT_RUN; no runtime/UI or asset changes |

Twelve new tests cover unknown preservation, explicit translation/scale/rotation, missing transform, source mutation, unapproved frame, L/R inversion, identity mismatch, unknown contact, nonfinite transforms and duplicate IDs. All moving coordinate examples are temporary **synthetic** test fixtures, never real motion evidence. New tests passed on first execution; no failing repair loop.

The pipeline diagnostic runs all existing 58 tests without assertion changes and captures RGBA pixel comparisons on failure before cleanup. Its replayable source is saved alongside this report as `pipeline_diagnostic.py`; from repo root run `python tools/character-asset-studio/qa/morwen-motion-source-05/pipeline_diagnostic.py`. Replay writes a separate diagnostic JSON. Standard pipeline baseline and instrumented final share the same failing IDs.

## Causal analysis of 8 + 3 failures

`REGRESSION_CAUSALITY.json` compares exact before/after test IDs. **No new failing IDs.** All eleven failures reproduced on the specified PR #226 base before Source-05 edits. No runtime files, existing test fixtures, normalized PNGs or archived generators changed; the new supplier is not imported by those paths.

- `common_loading` and `s2_transition_recovery`: save fixture calls `saveGrowthData` without `rildeReturnActive` in its test environment.
- `continue_restore`, `early_rewards`, `save_compatibility`, `startup_race`, `title_continue`: shared fixture cannot find its product DEV-block end marker.
- `field/frame_clock`: isolated renderer fixture loads `field-walkers.js` without `FieldWalkMotion`; reading `WALKER_FPS` fails.
- Pipeline IDs: `V07Layer0.test_committed_candidate_reproducible`, `V07Normalize.test_reproducible_and_sources_untouched`, `V08MasterBody.test_guides_contain_no_canon_pixels_and_are_reproducible`. All **12/12** generated-versus-archived image comparisons have **identical decoded RGBA and zero differing pixels**. SHA mismatch is in PNG byte encoding rather than changed artwork (`PIPELINE_PIXEL_DIAGNOSTIC.json`, Pillow 12.3.0). The exact historical encoder/compression version responsible is unproven. Expected SHA values were not updated and the failing strict byte assertions were not weakened.

These are independent existing fixture/encoding defects, not evidence of a new motion regression. This task investigates them; it does not silently repair unrelated runtime/tests or alter canonical bytes.

## Remaining inputs / next gate

Need actual adopted unique left and right six-frame PNGs with frame-specific adoption evidence; authored v1.0 frame poses, anatomical gait/contact choice and timestamps; measured/producer-calculated sole positions; explicit actor/root transforms and projection evidence. Until those are supplied and independently bound to frame IDs and source SHA, completion conditions for real adopted frames remain **BLOCKED**, and Export-06 is not authorized by the task's conditional gate.
