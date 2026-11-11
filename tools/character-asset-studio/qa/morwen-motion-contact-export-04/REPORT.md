# MORWEN-MOTION-CONTACT-EXPORT-04

Status: **BLOCKED — no actual animated v1.0 rig pipeline or actor/root pose stream found.** No exporter or export hook was implemented: there is no authentic transform-calculation point at which to attach one. No real coordinates, pose sequence, anatomical mapping or source transforms were fabricated. Repair attempts: 0 (maximum 2).

## Branch and provenance

- Supplied checkout: `work`, HEAD `d5c79f4e8dc9a8e20f1d427b7fff595f64de66a6`, clean; packet is absent there and on fetched main.
- Latest source branch `feature/character-asset-studio`: `962e5af15f1bb2c261e235edff28d253bee7838c`, verified before checkout and again after tests.
- Isolated worktree `/workspace/morwen-motion-contact-export-04`; branch `feature/morwen-motion-contact-export-04`; base is the source HEAD above. Read that branch's AGENTS.md and the Export-04 packet. No shared branch edits or other agents launched; PR #225 worktree/files untouched.
- Final task HEAD is the commit containing this report (reported in the Draft PR/chat).

## Source investigation

Tracked-code/content searches (recorded in `SOURCE_DISCOVERY.log`) found:

1. `qa/build_morwen_v10_candidate.py:10` deep-copies a static v0.9 spec, changes metadata and detaches the fixed ground marker. It does not evaluate frames, poses or actor transforms.
2. `layer0/morwen-master-v1.0/` contains only `MASTER_BODY_SPEC.v1.0.candidate.json`. It has static 3D joints and four view projections, with no animated frame records or gait/actor stream.
3. `pipeline/caslib/articulated.py:217` defines `fk_rotate`; its only generator use at line 335 is a v0.9 QA probe rotating one selected axis by a designed range endpoint. Results test pivot and length invariants; these are not authored frames and have no actor world transform or gait provenance. `run` at line 238 consumes v0.8 plus static canon normalization transforms, writes v0.9 artifacts, and sets `frameCount: 1` at line 419. Those normalization transforms are not animated root transforms.
4. `pipeline/cas.py:208` exposes that static v0.9 generator, not a v1.0 animation generator. The other `fk_rotate` call is a unit test.
5. Historical `assets/candidates/morwen-right-walk/72/build_meta.json` contains near/far sprite-local ankles and phases; it is not v1.0 and has no verified L/R correspondence or per-frame root-to-world transform. Reference-video anchors are empty; left-walk delivery is AWAITING_ART. None is an authentic v1.0 animated pose source.

Exact inspected paths and their SHA-256 values: `BLOCKED_EVIDENCE.json`.

## Commands and observed results

Run from the isolated repository root. Full commands, exit codes, stdout/stderr before and after the new contract tests: `COMMAND_RESULTS.json`. The validator and converter were exercised in order on the actual static rig:

```sh
python tools/character-asset-studio/qa/validate_real_motion_export.py tools/character-asset-studio/layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json
python tools/character-asset-studio/qa/convert_real_motion_export.py tools/character-asset-studio/layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json /workspace/work/morwen-export04/real-stance.json
```

Both exit 2 / BLOCKED, including missing schema/source/frames. The converter creates no output. **Real drift auditor: NOT_RUN**, because no valid converted real frame stream exists. L/R real maximum drift: unknown/null.

Tool-only validator → converter → auditor CLI smoke used the existing unit-test fixture `test_validate_real_motion_export.valid()` saved as `/workspace/work/morwen-export04/synthetic-unit-export.json`:

```sh
python tools/character-asset-studio/qa/validate_real_motion_export.py /workspace/work/morwen-export04/synthetic-unit-export.json
python tools/character-asset-studio/qa/convert_real_motion_export.py /workspace/work/morwen-export04/synthetic-unit-export.json /workspace/work/morwen-export04/synthetic-stance.json
python tools/character-asset-studio/qa/audit_stance_contact.py /workspace/work/morwen-export04/synthetic-stance.json --tolerance-px 2
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*.py' -v
node --test tools/character-asset-studio/tests/*.cjs
node --test tests/*.cjs tests/field/*.test.js
python -m unittest discover -s tools/character-asset-studio/pipeline/tests -v
python tools/character-asset-studio/pipeline/cas.py protect-verify
```

| Check | Observed result |
|---|---|
| Actual static v1.0 validator/converter | BLOCKED, output absent |
| Real animated export/drift | BLOCKED / NOT_RUN, L=null, R=null |
| Synthetic CLI validator/converter/auditor | PASS, exit 0 each; one stance sample, not motion evidence |
| QA tests | PASS baseline 19/19 → final 25/25 |
| Studio tests | PASS 19/19 before and after |
| Repository regression | FAIL 52 pass / 8 fail before and after; exact IDs unchanged |
| Pipeline regression | FAIL 55 pass / 3 fail; same three IDs as prior QA-02; generators unchanged |
| Canonical protected SHA | PASS 17/17 |
| Real-device/browser E2E/human review | NOT_RUN; no runtime/UI changes |

`test_motion_contact_export_04.py` adds six checks: reject static rig as export, reject missing actor transform, reject missing selected contact point, document structural L/R authenticity gap, propagate a **synthetic** 5 px drift to FAIL, and reject a stanceId change without swing. Existing tests also exercise replanting after swing. No real drift was measured.

## Remaining blockers and limits

- Need an actual generator using the v1.0 rig, authored per-frame joint poses, IDs/timestamps, L/R gait phase + stanceId, selected heel/ball/toe points, actual actor/root local-to-world transforms, projection and units/scale, with source path/hash evidence. Once available, attach the narrow opt-in exporter where those real transforms are calculated and emit `cas/real-motion-contact-export/1.0`.
- Existing structural validator checks nonempty provenance but does not authenticate the source/hash or reject swapped L/R provenance. The new diagnostic test deliberately demonstrates this limitation; its PASS means the limitation was reproduced, not that anatomical inversion was rejected. No production validation change or claimed evidence-backed mapping was made without a real source.
- Existing repository failures: `common_loading`, `continue_restore`, `early_rewards`, `field/frame_clock`, `s2_transition_recovery`, `save_compatibility`, `startup_race`, `title_continue`. No new failing IDs. See `REGRESSION_DIFF.json` for complete paths.
- Pipeline failures are `V07Layer0.test_committed_candidate_reproducible`, `V07Normalize.test_reproducible_and_sources_untouched`, `V08MasterBody.test_guides_contain_no_canon_pixels_and_are_reproducible`: regenerated PNG SHA mismatches, same observed IDs as prior QA-02. Pipeline was run once in this task; full log is retained. Original assets/hashes were not regenerated or changed to suppress failures.
- PR #225's precision repair is not present on the shared source base. The prior auditor remains untouched as requested; this task's synthetic 5 px test does not exercise that subprecision defect.

## Changed files and protection

Only new `qa/test_motion_contact_export_04.py` plus this task's evidence directory (`REPORT.md`, `COMMAND_RESULTS.json`, `BLOCKED_EVIDENCE.json`, `REGRESSION_DIFF.json`, `SHA_CHECKS.json`, `SOURCE_DISCOVERY.log`, `pipeline.log`). No existing source/test/PR #225 files edited. `SHA_CHECKS.json` records unchanged v0.8/v0.9/v1.0 specs, official assets and canonical references, including all 17 expected manifest SHA values.

Draft PR only. No main merge, adoption, game integration or publication. This is a blocked investigation and contract-test deliverable, not a completed real-motion exporter.
