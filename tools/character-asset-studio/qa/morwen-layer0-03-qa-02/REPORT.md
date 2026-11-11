# MORWEN-LAYER0-03-QA-02 — Codex execution report

Scope: `tools/character-asset-studio/qa/` only. Independent Codex automated QA; no asset adoption.

## Provenance and concurrent-edit isolation

- Initial supplied checkout: `d5c79f4e8dc9a8e20f1d427b7fff595f64de66a6` (`work`), clean; handoff absent there and on fetched main.
- Read AGENTS.md and handoff on source branch `feature/character-asset-studio`, pinned HEAD `fb85be65b48e640dc7d4555d70f90bb4b1a59957` (PR #224).
- Separate worktree and task branch: `feature/morwen-layer0-03-qa-02`. No edits in the supplied checkout or shared source branch. No concurrent agents were launched. Direct Claude coordination unavailable; isolation prevents shared-file writes.
- During execution upstream advanced to `b6026659426fa569925efe42fde1ecfbdf87663d`: only `.github/workflows/character-asset-studio-independent-qa.yml` added. No overlapping file edits. Tests below refer to the pinned source plus this QA-only patch; the additional workflow was not executed locally.

## Repair (1 attempt of maximum 2)

`audit_stance_contact.py` used rounded observation drift to decide overall status. A drift of 2.0000001 px at tolerance 2 px produced a FAIL observation but overall PASS. Added a regression test and observed its failure, then retained full precision in observation evidence and the overall gate. Exact tolerance still passes. `boundary-before.log` preserves the reproduced failure; final stance tests pass 7/7.

## Commands and observed results

Run from repository root. Exact initial/final stdout, stderr and exit codes for all four handoff commands: `COMMAND_RESULTS.json`.

```sh
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*morwen_v10_candidate.py' -v
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_audit_stance_contact.py' -v
python tools/character-asset-studio/qa/audit_layer0_rig.py tools/character-asset-studio/layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json
python tools/character-asset-studio/qa/audit_stance_contact.py tools/character-asset-studio/qa/stance_contact_fixture_v1.json --tolerance-px 2
python -m unittest discover -s tools/character-asset-studio/pipeline/tests -v
node --test tools/character-asset-studio/tests/*.cjs
node --test tests/*.cjs tests/field/*.test.js
python tools/character-asset-studio/pipeline/cas.py protect-verify
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python tests/run_python.py tools/character-asset-studio/tests/e2e_studio.py /workspace/work/morwen-qa02/e2e-studio
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python tests/run_python.py tools/character-asset-studio/tests/e2e_motion.py /workspace/work/morwen-qa02/e2e-motion
```

| Check | Baseline | Final |
|---|---|---|
| Migration unit tests | PASS 3/3 | PASS 3/3 |
| Stance unit tests | PASS 5/5 | PASS 7/7 (two added) |
| Rig audit | PASS 8/8 | PASS 8/8 |
| Synthetic stance fixture | PASS 4 samples | PASS 4 samples; max 1 px; L=1, R=1 |
| Studio Node tests | PASS 19/19 | PASS 19/19 |
| Pipeline | FAIL 55 pass / 3 fail | FAIL same 3 IDs |
| Repository Node regression | FAIL 52 pass / 8 fail | FAIL same 8 IDs |
| Studio E2E | FAIL 42 pass / 2 fail | FAIL same viewport/check IDs |
| Motion E2E (synthetic video) | FAIL 95 pass / 2 fail | FAIL same viewport/check IDs |
| Protected canonical hashes | PASS 17/17 | PASS 17/17 |
| Real-motion contact audit | NOT_RUN | NOT_RUN; integration BLOCKED |
| Human visual review / Android hardware / real reference video E2E | NOT_RUN | NOT_RUN |

E2E used installed Chromium via the repository's existing `tests/run_python.py` adapter; no dependencies installed. Final rerun used an equivalent temporary launch adapter plus HTTP-server stdout/stderr logging, without changing assertions. Both viewports (390×844 and 1440×900) request `/favicon.ico`, returning 404; this alone fails their `no console/page errors or alert dialogs` checks in both suites. Motion checks total 97, not historical report's 102: optional real-video checks were not run. Do not equate emulation with Android hardware QA.

## Regression deltas and unresolved defects

Exact failing IDs before/after: `REGRESSION_DIFF.json`; complete suite logs are alongside this report. New failing IDs after this patch: none. The added subprecision regression changes FAIL → PASS after the repair.

Pipeline failures (present before patch):

- `test_pipeline.V07Layer0.test_committed_candidate_reproducible`
- `test_pipeline.V07Normalize.test_reproducible_and_sources_untouched`
- `test_pipeline.V08MasterBody.test_guides_contain_no_canon_pixels_and_are_reproducible`

All three fail regenerated-PNG SHA equality against archived outputs. Cause beyond that observed mismatch is unproven; originals were preserved rather than regenerated or hashes updated. These pipeline tests and generators are outside the handoff's QA-only edit scope.

Repository failures (same eight as historical v0.7 report): `tests/common_loading.test.cjs`, `tests/continue_restore.test.cjs`, `tests/early_rewards.test.cjs`, `tests/field/frame_clock.test.js`, `tests/s2_transition_recovery.test.cjs`, `tests/save_compatibility.test.cjs`, `tests/startup_race.test.cjs`, `tests/title_continue.test.cjs`. Logs identify existing fixture extraction and runtime-reference errors. Product/runtime, pipeline generators, original PNGs and out-of-scope test files were not modified. Favicon/E2E and these failures remain follow-up defects; overall regression is FAIL, not a clean gate.

## Real-motion evidence and blocker

`REAL_MOTION_EVIDENCE.json` records 12 source observations (6 frame IDs × near/far legs), authored phases, original data path/hash and local ankle positions from `assets/candidates/morwen-right-walk/72/build_meta.json`. This is an older generated candidate, not an export from the v1.0 rig. Near/far is not verified anatomical L/R. `footSide` and `worldPx` are explicitly null; no ground-marker substitution and no fabricated sole coordinates.

Other inspected sources: reference motion JSON has 17 phase markers but no anchors; v0.9 modular JSON has only frame 0 per view; left walk delivery is AWAITING_ART. Existing PNG sequences cannot establish world contact. Evidence uses a separate schema because incomplete contacts must not be accepted as runnable stance input. Per-foot real drift is unknown (L=null, R=null); resulting contact audit NOT_RUN.

Required next export: per-frame anatomical L/R mapping, authored stance/swing interval, consistent tracked heel/ball/toe point, root/actor transform and unit/scale, plus final worldPx and source provenance. Then emit `cas/stance-frames/1.0` and run `audit_stance_contact.py` on that export. Never treat local ankle coordinates or the fixed (600,1540) marker as planted world-space foot positions.

`ASSET_PRESERVATION.json` verifies canonical SHA values and empty diffs for original v0.8/v0.9/v1.0 sources and official assets. `adoptionReady=false`; no main merge, publication or production integration.
