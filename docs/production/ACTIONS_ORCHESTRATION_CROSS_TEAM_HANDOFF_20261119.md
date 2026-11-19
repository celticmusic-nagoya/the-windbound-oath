# TWO | Cross-team Actions orchestration and recovery proposal (2026-11-19)

Status: PROPOSED / NOT ENABLED / NOT MERGED. Owner: shared CI coordination; map PR #421; character PRs #425 and #427. This document is not canonical lore and does not authorize GitHub Actions re-enablement, main merge, destructive deletion, or publication.

## Immediate operational state
- Director has temporarily disabled repository Actions in Settings. Admin setting and all active-run cancellations are NOT independently verified by this document. Do not dispatch runs or re-enable Actions until workflow inventory, ownership and safeguards are reviewed and the director explicitly approves re-enablement.
- main AGENTS.md and docs/production/SESSION_CONTINUITY_INDEX.md must be re-read on each session; compare private canon and current PR HEAD/Artifacts. Shared Blender installer: main:tools/production_qa/install_blender_524.sh (5.2.4, checksum verified).
- Map: Draft PR #421 feature/lind-cliff-rock-art-study-20261118; CC0 rock study is input only, not a completed cliff. Method B actual Blender sculpt render and G2/G3 still require verification.
- Character: Draft PR #425 feature/morwen-authored-sculpt-20261118; Draft PR #427 feature/morwen-artdirected-sculpt-20261119 is based on #425. Both are handoff/pre-production; do not claim finished sculpt or G2 PASS. Prior failures #407/#417/#419 preserved.

## Intended architecture (design, not yet implemented)
1. One small, centrally owned orchestration workflow, triggered by narrowly scoped push/pull_request paths, plus optional manual dispatch. All expensive Blender jobs must be reusable workflows (workflow_call) or controlled workers; no uncontrolled broad PR triggers. Do not create a new PR for this design if a safe existing CI ownership PR exists.
2. Preflight computes an idempotency key from asset ID, stage, source SHA-256, exact script/config/tool version, canonical reference identity, and output contract. Query existing successful run/manifest before launching. A matching SUCCESS artifact may be reused only if still accessible, SHA-verified, and satisfies the same output contract; expired/missing artifacts are not a cache hit.
3. Define ownership: character Morwen sculpt vs map cliff sculpt are separate concurrency groups. Use concurrency.cancel-in-progress only for superseded *identical disposable* validation runs, never for independent art work or unsaved artifacts. Limit parallel runners and avoid triggering every historical workflow on each PR edit.
4. Distinguish exact duplicate (SKIP/REUSE), probable semantic overlap (REVIEW_REQUIRED, no automatic cancellation), independent stages (RUN_PARALLEL if resources allow), prerequisite missing (BLOCKED), and stale/failed jobs (ESCALATE). Maintain a durable job ledger: owner PR, stage, branch, HEAD, inputs/hashes, run ID, artifact ID/expiry, QA gate, failure count, next action, timestamp.
5. A lightweight watchdog on a bounded schedule checks queued/in_progress age, completed-but-no-artifact, failed/timed-out/cancelled jobs and owner inactivity; report to existing owner PR/Issue, not new PR spam. It must not silently restart costly Blender work; bounded retries (max two same root-cause/method), structural switch after two failures, explicit escalation. If Actions are disabled, watchdog is also disabled; external manual/ChatGPT review is needed until re-enabled.
6. Guardrails: least-privilege GITHUB_TOKEN, no third-party paid APIs, pinned action versions as feasible, checksum-verified Blender, bounded timeouts, per-stage concurrency, artifact retention, no canonical overwrite or auto-merge, manual approval for changes to official design or destructive operations.
7. Rollout: (A) read-only inventory and duplicate trigger audit; (B) implement dry-run classifier and unit tests without dispatch; (C) enable only a pilot (one map and one character independent workflow) after director approval; (D) verify duplicate suppression, semantic-review gate, watchdog alert, Artifact provenance and cancellation safety; (E) expand selectively. G1–G4 remain independent quality gates.

## Cross-chat startup message
Read main AGENTS.md, main SESSION_CONTINUITY_INDEX.md, this PR #421 proposal and the latest character PR #425/#427. Actions are intentionally disabled. Before any CI or Blender run, check the shared job ledger, source SHA, stage, owner PR, existing runs and artifacts; do not recreate completed work. Character and map production are independent but share the same CI orchestration policy. Continue only approved non-destructive tasks; no Actions re-enable or main merge without director approval.

## Current implementation and QA (2026-11-19)
- Offline classifier: `tools/production_qa/classify_actions_jobs.py` (no network, dispatch, cancellation or side effects); deterministic input identity and fail-closed duplicate/overlap decisions.
- Unit test source: `tools/production_qa/test_classify_actions_jobs.py` (9 test cases covering verified reuse, semantic overlap, independent work, invalid inputs and prerequisites).
- Emergency bulk-cancel workflow `lind-one-shot-cancel-actions.yml` changed to manual dispatch with explicit confirmation input; no automatic push trigger.
- These changes are committed to Draft PR #421 only; GitHub Actions remain disabled. Runtime unit tests, orchestration dispatch integration, persistent ledger, watchdog and actual deduplication under concurrent runners are NOT_RUN. Do not claim end-to-end deduplication until verified.


## Offline watchdog increment (2026-11-19)
- `tools/production_qa/audit_actions_ledger.py`: pure read-only ledger audit; reports stale QUEUED/IN_PROGRESS, SUCCESS without verified accessible artifact/output contract, terminal failures, inactive owner PR, malformed records. Emits JSON only; does not poll GitHub, create comments, dispatch or cancel runs.
- `tools/production_qa/test_audit_actions_ledger.py`: 9 test cases committed. Existing classifier has 9 tests; total 18 test cases authored, execution NOT_RUN. Local container could not resolve raw.githubusercontent.com, so GitHub-hosted code was not fetched for local test execution.
- Durable ledger *storage and population*, live GitHub status polling, automated notification and controlled dispatch remain NOT_IMPLEMENTED. An offline report is not a functioning background watchdog.
- Before Actions re-enable: implement the ledger writer with atomic concurrency protection, reconcile live runs/artifacts, test dry-run routing, avoid unbounded pull_request triggers, and verify one-shot cancel workflow is manual-only.


## Read-only GitHub observation increment (2026-11-19)
- Added `tools/production_qa/collect_actions_snapshot.py` and `test_collect_actions_snapshot.py` (5 unit tests). The collector reads GitHub REST workflow-run pages with GH_TOKEN, bounded to 1–5 pages, de-duplicates run IDs, and emits JSON. It performs no GitHub writes, cancellation or dispatch. It has NOT been run against the live API, and test execution is NOT_RUN.
- Combined authored unit tests: classifier 9 + offline watchdog 9 + snapshot collector 5 = 23. Authored does not mean executed.
- Important: run snapshots alone do not prove identical work or artifact validity; a durable, atomic cross-run ledger/lock, verified artifact manifest, actual notification and narrowly scoped scheduler are still NOT_IMPLEMENTED. Do not turn on automatic production jobs based solely on these utilities.


## Explicit run identity reconciliation (2026-11-19)
- Added `tools/production_qa/reconcile_actions_snapshot.py`: read-only join of explicitly linked ledger run_id and GitHub snapshot, checking HEAD, branch, run status, and the existing artifact verification flags. Missing bounded-snapshot entries are REVIEW_REQUIRED, never assumed absent. Inconsistent or duplicate run IDs fail closed.
- Added `tools/production_qa/test_reconcile_actions_snapshot.py`: 10 authored test cases; total authored tests now 33. Execution NOT_RUN. The collector/reconciler do not themselves validate artifact bytes or acquire atomic locks.
- Next blocker: cross-run atomic reservation and durable ledger persistence with safe concurrency, plus artifact provenance checks, notification routing, scoped trigger audit and runtime tests. No automatic dispatch until these gates are verified and the director separately authorizes Actions re-enablement.


## Trigger reduction and offline QA workflow (2026-11-19)
- To prevent uncontrolled restart when Actions is eventually enabled, changed these previously automatic LIND workflows to manual-only: `lind-canon-reference-audit.yml`, `lind-cc0-editable-sources.yml`, `lind-authored-bedrock-a.yml`. In particular, the B sculpt production render will NOT auto-run until a scoped orchestrator is implemented and approved; it remains available for explicit dispatch later.
- Added `.github/workflows/two-actions-orchestration-offline-qa.yml`: manual-only, read-only token, 5-minute timeout, no cancel-in-progress, Python compile + offline unit test discovery. Does not dispatch Blender or invoke GitHub REST. It has NOT been executed while Actions is disabled.
- Existing narrowly path-filtered lightweight CI (such as `lind-agent-contract.yml` and `lind-ai-guard.yml`) was preserved. Other workflows may still have automatic triggers; the full repository-wide trigger audit and rollout approval are pending. No claim of zero fan-out is made.
- Atomic distributed locking is NOT implemented; a workflow-level concurrency group prevents overlap only for that one offline QA workflow, not for arbitrary character/map jobs. Do not re-enable Actions or production automation based on this change alone.


## Repository-wide trigger fan-out reduction (2026-11-19)
- Audited all 22 non-LIND workflow headers on PR #421. Ten lightweight game QA workflows had both `pull_request` and unrestricted `push` with overlapping path filters, meaning a feature-branch push could create duplicate runs for the same code change. Limited `push` to `branches: [main]` while preserving existing path-filtered PR checks: `approved-story-cg-sequence-qa`, `dev-cliff-summit-qa`, `dev-fresh-entry-qa`, `dev-menu-runtime-guard-qa`, `dev-summit-capture-qa`, `headgear-layer-qa`, `headgear-renderer-qa`, `portrait-all-blink-assets-qa`, `portrait-event-cg-qa`, `wind-stop-landscape-cg-qa`.
- Remaining LIND PR triggers inspected include small path-filtered contract/AI guard, source intake and topology tests. Retain useful lightweight QA until there is evidence of true duplicate execution. The LIND scan-cliff-C legacy 34-minute render still has a branch-specific push trigger; evaluate its ownership and whether its output remains needed before changing it.
- Trigger audit and edits are code-level only; no Actions execution or runtime fan-out measurement has occurred. Actions remains disabled. Changes are unmerged on Draft PR #421.


## Remaining LIND high-cost trigger review (2026-11-19)
- Inspected the actual YAML for `lind-scan-cliff-c.yml` (34-minute Blender 5.2.4 scan-first candidate with external packed-source artifact), `lind-cc0-rock-components.yml` (10-minute CC0 acquisition with downloads and Artifact), and `lind-parallel-independent-qa.yml` (three-way matrix, 8-minute each, fetching pinned historical Artifacts). All three are now **manual-only** pending a safe deduplicating dispatcher. No jobs were dispatched and no Artifacts deleted.
- Retained narrowly path-filtered lightweight `lind-agent-contract.yml` and `lind-ai-guard.yml` PR QA; indiscriminate disabling would weaken essential contract checks.
- A manual-only workflow can still be launched by an authorized person once Actions is enabled; manual-only does NOT imply idempotency, locking or verified reuse. Any manual production run must be preceded by explicit artifact/input review.
- Follow-up: audit remaining path-filtered LIND workflows for overlap, implement atomic reservation with optimistic concurrency and a durable store, validate test execution, then request explicit approval for staged re-enablement. The current 33 authored tests remain NOT_RUN.


## Manual high-cost workflow concurrency guard (2026-11-19)
- Inspected remaining path-filtered LIND lightweight tests and retained their PR triggers; no blanket disabling. Added workflow-level `concurrency` with group per workflow + ref and `cancel-in-progress: false` to five manual-only high-cost workflows: scan-cliff-C, CC0 rock components, parallel independent QA, CC0 editable sources, and authored bedrock B. This prevents simultaneous **running** copies of the same workflow/ref; it does NOT prevent duplicate requests or ensure artifact reuse.
- GitHub Actions concurrency permits at most one running and one pending run per group; a newer pending run can replace an older pending run even when `cancel-in-progress: false`. Do not use this as an authoritative lossless queue, durable ledger, or atomic idempotency key. Different workflow/ref groups can still run in parallel, as intended for independent map/character stages.
- All five workflows remain manual-only. No workflow was dispatched, no existing runs were cancelled by these code changes, and no runtime QA was performed while Actions is disabled. Explicit approval is still required before re-enabling Actions.


## Artifact byte-level verification increment (2026-11-19)
- Added `tools/production_qa/verify_actions_artifact.py` and 9 tests. It verifies a declared output contract and SHA-256 of each extracted local artifact file, rejecting absolute/parent paths and symlink files. It does not certify PNG/Blender semantics, canonical provenance, license, remote GitHub Artifact availability, or G1–G4.
- Extended the existing manual-only `two-actions-orchestration-offline-qa.yml` to compile and test the verifier. Authored tests now 42 (9 classifier + 9 watchdog + 5 snapshot + 10 reconciliation + 9 artifact verifier); execution still NOT_RUN while Actions is disabled.
- For safe cache reuse, a separate authenticated remote Artifact download, immutable run-to-manifest binding, byte-level verification and an atomic reservation store are still required. Never set `artifact_accessible` or production QA PASS from this offline verification alone.


## Explicit GitHub Artifact metadata inspection (2026-11-19)
- Added `tools/production_qa/inspect_actions_artifact_metadata.py` (read-only GitHub REST): requires explicit repository, run ID, artifact name and token. Verifies run repository/ID, successful completion, exact artifact-name uniqueness, unexpired nonzero size and artifact-to-run binding; bounded pagination (five pages). It never selects the latest success implicitly, dispatches, cancels or writes.
- Added ten mock-API tests `test_inspect_actions_artifact_metadata.py`, and extended the manual-only offline QA workflow compile step. **52 authored tests total; runtime NOT_RUN** while Actions disabled.
- Metadata accessibility is not ZIP download success, byte-level SHA verification, trusted manifest provenance, canonical adoption or safe cache reuse. The inspector intentionally returns `safe_to_reuse: false`. A separate authenticated download, content verification and cross-run atomic reservation remain blockers to automation.


## Explicit bounded ZIP acquisition candidate (2026-11-19)
- Added `tools/production_qa/download_actions_artifact.py`: explicit Artifact ID only, trusted caller-supplied ZIP SHA-256 required, HTTPS storage redirect allowlist, no bearer forwarding to storage, streaming size bound, no overwrite, failed-download cleanup, no extraction. Nine mock tests authored in `test_download_actions_artifact.py`; total 61 authored tests. Runtime NOT_RUN; real GitHub storage redirect compatibility NOT_VERIFIED.
- This is a candidate acquisition layer, NOT yet wired to auto-reuse. ZIP digest must originate from independently trusted evidence, not an unverified downloaded manifest. Extraction, path validation, extracted file SHA checks, run-to-artifact provenance and durable atomic lock remain separate gates. `safe_to_reuse` remains false.


## Offline QA execution feasibility and race fix (2026-11-19)
- Reviewed manual-only offline QA workflow: it compiles all seven orchestration modules and discovers `test_*actions*.py`, `test_audit_actions_ledger.py`, and `test_verify_actions_artifact.py`. GitHub Actions remains intentionally disabled; no run was dispatched. The execution environment could not reach raw.githubusercontent.com to retrieve the branch into the local test runner, so the **full 62 authored tests remain NOT_RUN**; do not report test PASS.
- Static review found a cleanup race in `download_actions_artifact.py`: a failed exclusive-create could previously unlink another process's file. Changed cleanup to unlink only after this invocation successfully created the output and added a concurrent-creation regression test. This is a code change with execution NOT_RUN, not proof of correctness.
- Next safe step: obtain an accessible repository checkout or explicit approval for a narrowly scoped Actions re-enable/manual offline QA run; until then do not re-enable Actions or assert test results. Do not build further automatic dispatch or claim atomic reservation is implemented.


## Isolated manual-only QA registration PR (2026-11-19)
- GitHub Actions UI reported workflow Not found because `two-actions-orchestration-offline-qa.yml` was present only on PR #421 branch and not registered on main. To avoid merging unfinished map and orchestration work, created isolated **Draft PR #428** (`ci/actions-offline-qa-isolated-20261119`) targeting main with only seven offline modules, seven test modules (62 authored cases), and one `workflow_dispatch`-only workflow. No main merge performed.
- Fixed isolated workflow's test discovery to invoke each seven test modules exactly once, avoiding duplicate execution from overlapping glob patterns in the original #421 workflow. PR #428 mergeability confirmed true; still Draft, runtime NOT_RUN.
- Next gate: explicit director approval to merge isolated PR #428, then enable ONLY this workflow and manually dispatch on main. Existing GitHub Actions global/other workflow disabled status must not be changed en masse. PR #421 remains owning implementation and continues independently.


## First actual Actions offline QA run / targeted fix (2026-11-19)
- Run [#44465028538](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44465028538), job 135360635934, on main SHA `9b04c06d598574a724c876c48c3c58dd9cb0892a`: workflow_dispatch; **completed FAILURE**. Checkout PASS; Python module py_compile PASS; classifier 9/9 PASS; watchdog 9/9 PASS; snapshot tests **4 PASS + 1 ERROR**. Remaining four modules **NOT_RUN** because shell `set -e` stopped at failure. This is not 62/62 PASS.
- Root cause: `collect_actions_snapshot.py` allowed owner path component `..` in `../bad` under its permissive regex; rather than raising ValueError it constructed an API URL and performed an unauthorized HTTP call (401). The snapshot utility should be strictly read-only and reject malformed input before I/O.
- Patched this owning #421 branch to reject `.` and `..` repo path components; added explicit negative stub regression test. **63 authored cases total; new test NOT_RUN.** Created independent minimal **Draft PR #429** targeting main with only those two file changes; main merge approval and a single targeted manual rerun are pending. Do not use bulk re-enable, heavy jobs or retries without a changed commit.


## Verified real Actions QA completion (2026-11-19)
- [Run #44466283104](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44466283104), job [135364735704](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44466283104/job/135364735704), `workflow_dispatch` on main `61e60f34a1c6e16d36afa64fcdbeb38a8a5c2fb4`: **completed SUCCESS**, actual raw job log retrieved through GitHub connector. Checkout and Python compilation succeeded; test modules yielded **9+9+6+10+9+10+10 = 63 PASS, 0 FAIL, 0 ERROR**. All seven test modules ran exactly once.
- Earlier failure run #44465028538 was resolved by merged PR #429 (validation of dot-segment repository names), with the corresponding negative regression included in this successful run. Isolated manual-only QA was registered via merged PR #428; both PRs were narrowly scoped, while PR #421 remains Draft and unmerged.
- QA scope is deterministic offline/mock tests of orchestration utilities, not live Artifact ZIP download, end-to-end distributed atomic reservation, launch orchestration, Blender execution, or 3D G1–G4. These production gates remain NOT_RUN or NOT_IMPLEMENTED. Do not repeatedly rerun identical SHA/input tests or auto-enable heavy workflows.


## Create-only atomic reservation prototype (2026-11-19)
- Added `tools/production_qa/reserve_actions_job_ref.py` and ten unit tests. The prototype uses a GitHub Git-ref **create-only** operation keyed by the existing eight-field fingerprint (`refs/tags/two-job-reservation/v1/<sha256>`). A single create operation is the proposed atomic uniqueness primitive; there is no check-then-create race in this interface. It does not issue real API requests: a callback must be supplied, and no CLI/dispatch is enabled.
- Only a `RUN_ELIGIBLE` request may attempt reservation. Existing queued/verified-success jobs, missing prerequisites, and conflicting same-asset stages are fail-closed. HTTP 409/422 is `REVIEW_REQUIRED`, never assumed to be a valid existing reservation. Unknown API errors propagate. Successful reservation returns `RESERVED_ONLY`, explicitly `dispatch_authorized: false`.
- **Important limitations:** This is not a production distributed lock/queue or lifecycle ledger yet. Git refs would persist and could clutter the repository; refs require separately approved write permission, governance and cleanup policy. A Git ref pointing at a commit does not encode verified owner, status, expiry, Artifact provenance or safe recovery. No ref was created, no API writes were made, no workflow dispatched. Ten new tests authored but NOT_RUN; previous 63 tests PASS on main at run #44466283104, total authored on #421 now 73.
- Next: execute new tests in an isolated, approved QA context, evaluate the Git-ref namespace and permissions against production constraints, implement safe ownership/reconciliation and bounded stale-reservation recovery before any real create-ref or automatic dispatch. Keep Blender and mass Actions disabled.


## Fail-closed recovery review prototype (2026-11-19)
- Added `tools/production_qa/assess_actions_reservation_recovery.py` plus 12 offline unit tests on existing owning Draft PR #421; no new PR or Actions dispatch. It evaluates a reservation ref, matching ledger owner/run identity, and caller-supplied complete run snapshot. Stale age alone never permits retries or releases. In-progress remote runs KEEP_RESERVED; verified success REUSE_VERIFIED; failed/cancelled runs and unverified success REVIEW_REQUIRED; missing/ambiguous evidence BLOCKED. All results explicitly forbid dispatch, ref deletion and ownership transfer.
- **Caveat:** The snapshot completeness flag and artifact booleans are inputs from the caller, not independently authenticated by this module. Integrating actual GitHub run provenance and artifact SHA verification, identity checks, owner acknowledgement, governance of persistent refs, and real API behavior remains mandatory before operational use. Do not infer safe restart from this assessment.
- New test definitions 12 (cumulative authored 85); **new 22 tests NOT_RUN** (10 reservation + 12 recovery). Previously verified 63 tests PASS in main run #44466283104; no change to main or heavy workflow settings.


## Verified 85/85 offline QA on owning branch (2026-11-19)
- GitHub Actions [run #44468597428](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44468597428) / job [135372293151](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44468597428/job/135372293151), `workflow_dispatch` on `feature/lind-cliff-rock-art-study-20261118`, head commit `0bb103a93e93273c31eb29db68ff630f6ef93007`, **completed SUCCESS**.
- Actual job logs: nine unique offline modules were executed exactly once, counts `9+9+6+10+9+10+10+10+12 = 85 PASS`, **0 FAIL, 0 ERROR**. Python compile and checkout passed. The 10 reservation tests and 12 recovery tests were included; this supersedes prior NOT_RUN status for those tests at this precise commit. Avoid redundant reruns of identical code and parameters.
- Scope remains **mock/offline unit QA only**. No live Git-ref creation, durable owner lifecycle, real distributed lock contention, automated dispatch, live Artifact ZIP verification, Blender render, or game G1–G4 success was validated. PR #421 remains Draft and not merged; recorded QA status does not grant production authorization. GitHub checkout@v4 Node.js 20 deprecation warning is non-fatal and a future maintenance item.


## Exact-run snapshot bridge (2026-11-19)
- Added `review_actions_reservation_snapshot.py` and nine unit tests. The bridge accepts the existing read-only GitHub runs snapshot and requires exactly one matching run ID plus explicit matching HEAD SHA and branch before invoking the read-only recovery assessor. Missing/duplicate runs or identity mismatches BLOCKED; observed active runs KEEP_RESERVED; failed terminal runs REVIEW_REQUIRED. It never dispatches, deletes a ref, or transfers ownership.
- **Fail-closed artifact handling:** a success with caller-provided artifact flags is **not** promoted to reusable output by this bridge; external authenticated Artifact SHA/contract verification remains mandatory. A bounded snapshot is never evidence of absence of other competing runs. Snapshot authenticity is not established solely by JSON `read_only` marker; operational integration remains blocked.
- Workflow updated to compile ten utilities and run ten distinct test modules exactly once. Nine new tests authored; total 94 tests, but new nine **NOT_RUN**. Previously verified 85 PASS applies only to SHA `0bb103a93e93273c31eb29db68ff630f6ef93007` and earlier code, not this branch HEAD. No workflow dispatched, no main merge, no real Git refs created.


## Verified 94/94 offline QA on owning branch (2026-11-19)
- GitHub Actions [run #44469918354](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44469918354) / job [135376602180](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44469918354/job/135376602180), `workflow_dispatch` on `feature/lind-cliff-rock-art-study-20261118`, head commit `a4c86229e8744e36700f39381b92dce9b017e468`, **completed SUCCESS**.
- Actual logs confirm ten distinct offline test modules run once each, counts `9+9+6+10+9+10+10+10+12+9 = 94 PASS`, **0 FAIL / 0 ERROR**. Python compilation passed. The nine new `review_actions_reservation_snapshot` tests passed. Previous 85/85 success remains historical evidence, not a new run at this commit.
- Non-fatal warning: `actions/checkout@v4` Node.js 20 deprecation / forced Node.js 24. Keep as a targeted follow-up; do not treat as test failure.
- Scope: offline mock tests only. No live Git-ref reservation, authenticated snapshot-to-ledger end-to-end integration, verified Artifact ZIP reuse, actual contention experiment, dispatch, Blender, or 3D G1–G4. No authorization to merge this broad Draft PR #421 or activate heavy Actions. **No rerun needed at identical SHA.**


## Offline QA verification at 96 tests (2026-11-19)
- GitHub Actions run [#44471983698](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44471983698) / job [#135383424420](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44471983698/job/135383424420) was `completed/success`, `workflow_dispatch`, attempt 1 on branch `feature/lind-cliff-rock-art-study-20261118` and tested SHA `0a66c24a76cc10176f206e8bc3da1f87babfb537`. This matched PR #421 HEAD before this documentation commit.
- Log evidence: ten offline modules, `9+9+6+10+9+10+10+10+12+11 = 96 PASS`, `0 FAIL`, `0 ERROR`; compilation PASS. Both new nonhex/uppercase SHA rejection tests PASS. No repeat at the same input SHA needed.
- Non-fatal deprecation warning: `actions/checkout@v4` (Node.js 20 target forced to Node.js 24). Separate compatibility maintenance; do not conflate with test failure.
- Scope remains offline/mock unit tests, not a live atomic Git ref reservation, ledger ownership proof, artifact verification, crash recovery or controlled production orchestration. These live gates remain **NOT_RUN/BLOCKED**. No refs created, no Blender/3D job started, no main merge.
