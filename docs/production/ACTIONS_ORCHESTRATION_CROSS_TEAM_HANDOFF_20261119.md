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
