# PLAYER-WALK-UP-07 — director-authorized integration

Status: **READY_TO_MERGE_WITH_EXPLICIT_DIRECTOR_WAIVER**; no merge performed at this checkpoint.

## Approval superseding the earlier hold

On 2026-11-06 (director local date), the user instructed: 「エラーに関しては今後の全体監査などで一緒に調査するとして、致命的な進行不能バグなどでなければ一旦保留として、エイダンの歩行モーションに関しては本編へマージすることを許可します。」

This explicitly authorizes merging the scoped Aidan up-walk implementation while deferring nonfatal errors. It does not turn previous FAIL results into PASS, authorize gameplay/SAVE changes, or waive a severe progression/compatibility defect. The earlier reports remain historical records, not current integration authority.

## Fixed production input

PR #155 head `0494f6452548ea476b4cebbc69d9f41d878d540d`; main baseline `6e28466751f124fc5a483be3d89c65f35a320b5c`. Production order is new → 03 → 04 → 01 → 06, stride 90, up bob 25%, applied through the existing engine to straight/diagonal up. Anchor/scale, down ARM-02, sides 180, movement speed, collision, other actors and SAVE code remain unchanged.

Known deferred items:

- Original PR #155 PC/UR cadence failure: CASE D, failed UR numeric evidence unavailable; subsequent success cannot establish the original cause.
- Original REQA m67 exact floating feet equality: FAIL retained; existing integer SAVE quantization explains the observed 0.5530-world displacement. Snapshot STABLE/SAVE strings are exact matches. See [preserved REQA report](PLAYER-WALK-UP-07-REQA.md) / Draft PR #157.

## Additional independent verification

Remaining original regressions are running serially under the unchanged assertion logger. A separate supplemental m67 run may continue only past the precisely named known exact-feet failure, retaining its original false result and FAIL/checkpoint. To qualify the explicit waiver it must additionally prove exact restored serialized coordinates, the existing JS rounding rule, per-axis quantization at most 0.5 world, exact map/STABLE/SAVE strings. Every other original predicate is unchanged; any unqualified failure stops execution. Supplemental completion is never labelled original m67 PASS.

Results, independent integration verdict, rollback/readback, merge and deployed-byte verification will be appended after completion. Android physical QA is NOT_RUN.

## Completed verification

- Previous fixed-input Node originals:17/17 PASS.
- Newly executed unchanged regressions:6/6 PASS (m62 down, m58 sides, m55 ally/enemy/NPC DEV, SAVE/CONTINUE lifecycle, asset registry, m49 formal protection).
- Supplemental full m67:98 original checks,95 true /3 false retained as FAIL_DEFERRED /0 new failures. Three normal UI SAVE/document-cold CONTINUE routes meet all six exact qualification conditions. All three viewports and12 actual movement intervals (straight/UL/UR/continued-up) completed. This is not original m67 PASS.
- Independent recorded-pixel review:9 direction/viewport intervals, no obvious limb loss, gross loop breakdown or direction-frame contamination. Subtle gait judgment remains physical Android QA.
- Formal259 SHA and fixed existing PNG/old failure evidence unchanged, production and original measurement inputs protected; worktree clean after tests.
- No SAVE/gameplay/production repair or predicate/tolerance change. Only the named nonfatal known check's assertion-stop was deferred under user authority; original false/checkpoints retained.

[Independent integration recommendation](evidence/player-walk-up-07-authorized/MERGE-WAIVER-REVIEW.md) · [Independent visual review](evidence/player-walk-up-07-authorized/VISUAL-REVIEW.md) · [Original regressions](evidence/player-walk-up-07-authorized/regression-results.json) · [Supplemental authoritative result](evidence/player-walk-up-07-authorized/supplemental-results.json) · [Lossless raw evidence, complete native videos and SHA index](evidence/player-walk-up-07-authorized/README.md).

Merge only PR1550494. Do not merge PR156 diagnostics, Draft157 REQA or supplemental continuation code. Rollback ref was created and remotely read back at the unchanged current main. No configured required checks were found; GitHub's normal merge gate remains in force. Preserve existing failure histories for later comprehensive audit.
