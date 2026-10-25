# S2 map transition recovery — DIRECTIVE-20B-RETRY

Base: `eb49dec67d5ff4217ad8cbf3bb27cc87d84e7efd`. Design reference: PR #48.
Verdict: PASS under the user-approved v1.3 environment fallback. Actual browser rendering is not verified.

## Behavior

Preparation leaves committed flags/treasure/slain state intact. Failed entry rejects its Promise; it never resolves `false` as apparent success. After destructive initialization, rollback rebuilds the previous world and restores positions, height, flags, treasure/event sets and copied Map-of-Sets slain data. A newer request owns the world; stale success/failure cannot mount, roll back or unlock it. External input locks remain explicit. If rollback or a post-commit hook fails, saving/deleting stays protected until a successful entry/LOAD. An explicit retry control remains available. Forest-arrival stage/objectives advance only after entry succeeds. The internal arrival flag preserves prologue monster availability while stage advancement is deferred; save format is unchanged.

## Retry failure diagnosis

The earlier integration test failed before map fetch: its VM did not define `battleBusy`/`guarding`, although `index.html` defines them and `TrainingCheckpoint.cancel()` assigns them. Initial LOAD and retry both raised `ReferenceError`, which the real coordinator correctly converted to failure. Classification: test fixture initialization defect, not a demonstrated product retry bug.

The fixture now defines both globals. Expectations were not relaxed. The retry test additionally requires one failed map request and a second successful request, FAILED→READY, active/not-busy/not-entering, exact restored map/position and byte-identical original storage. Diagnostic logs from the failed fixture are retained outside the checkout.

## Executed checks

- `S2_TEST_FILTER='real LOAD/coordinator' node tests/s2_transition_recovery.test.cjs`: PASS.
- `node tests/s2_transition_recovery.test.cjs`: all 19 scenarios PASS, including the prior 18 and LOAD→failure→retry.
- Real runtime scenarios cover normal entry, fetch/prepare/mount/render failure, deep rollback, first-entry retry, external locks, stale responses, hide/reset cancellation, post-commit errors, competing fade-in requests and success-only forest event progression.
- Real `PrologueProgress`, story and checkpoint modules cover KI-004 stage 0/15, v2 training recovery and v1 refusal. Real growth LOAD/coordinator and SAVE/DELETE guards check source-data protection.
- Existing `issue54_coordinator.test.cjs` and `issue51_command_lock.test.cjs`: PASS.
- `tests/battle/battle_opening.py --self-test`: existing asset checks and classifier checks PASS; these are not browser measurements.
- Field m0, frame clock, house02 spawn and Moss scatter Node suites: PASS.
- Changed JavaScript and all inline script syntax; `git diff --check`: PASS.

## Environment and remaining verification

Loopback socket creation raises `PermissionError: Operation not permitted`. Browser failure-injection R1–R15, actual retry-button hit testing, fade/height visuals, normal/raider browser regression and Android physical-device checks are `NOT_RUN / ENV_BLOCKED` (physical device: NOT_RUN). Their PASS is not inferred from simulated adapters. Tests execute actual product modules but mock networking, DOM and rendering boundaries. No permanent product fault-injection hook was added. No save-schema, battle-number or difficulty change.

Fallback approval: DIRECTIVE-20B-RESUME §1/§4 and DIRECTIVE-20B-RETRY §4/§5. The prior failed fixture is not reported as an environment permission failure. Updated executable alternate tests are all PASS.
