# TWO | AI-resilient blueprint-to-render production pipeline (proposal)

Status: PROPOSED / NOT MERGED / NOT PRODUCTION-VALIDATED. Workstream: shared character and map infrastructure. This proposal is not canon or G1-G4 approval.

## Source of truth and startup
Read current main AGENTS.md, docs/production/SESSION_CONTINUITY_INDEX.md, latest policies, private handoff canonical references, existing owning PR, branch HEAD, related runs and artifacts. Canon and adoption cannot be inferred from conversation memory. Preserve hashes, licenses, source provenance and separate candidate status.

## Durable state contract
One machine-readable checkpoint per asset/stage, written alongside the owning PR's artifacts (not a competing canonical source). Required fields: schema_version, asset_id, stage, owner, owning_pr, branch, head_sha, input_artifact_ids, input_sha256, blueprint_sha256, tool_versions, method_family, retry_count, attempt_ledger_ref, output_artifact_ids, output_sha256, G1, G2, G3, G4, error_category, blocker, next_action, next_action_preconditions, last_verified_at. Never fabricate PASS or source hashes. Explicit states: READY, PREFLIGHT_FAILED, RENDERING, RENDER_FAILED, TECH_QA_FAILED, WAITING_FOR_ART_QA, BLOCKED, NEXT_STAGE_READY. Writes must be idempotent and conditional on exact HEAD and input fingerprint.

## Pipeline
1. Blueprint: measurable multi-view geometry/material/lighting contract, source classification and assumptions; QA of reference compatibility before modeling.
2. Preflight: actionlint YAML, shellcheck/bas h -n where appropriate, Python compile, license/provenance, input SHA, LFS pointer and artifact availability, version pinning, disk/memory/time budget. Fail closed on missing canon.
3. Blender smoke: checksum-verified Blender install, --python-exit-code 1, minimal real scene build, .blend save and reopen. A smoke cube is NOT asset evidence.
4. Render: only when blueprint/preflight/smoke gates pass and input+script+settings fingerprint is not already covered by a valid artifact. Render actual asset in pinned cameras and lighting.
5. Technical QA: reopen actual .blend, topology/UV/rig/material checks, image existence/dimensions, SHA manifest, glTF as applicable. Preserve logs even on failure.
6. Independent artistic QA: source/blueprint comparison, silhouettes, proportions, material and final display size; no automatic G2 PASS from structural QA.
7. Integration: WebGL/Android G4 only after actual integration and device checks; no main merge or formal adoption without separate approval.

## Availability and delegation
GitHub Actions is the execution and persistence engine; AI chat subscriptions are NOT callable APIs. Claude and Codex can review/implement when available; ChatGPT can inspect GitHub state and continue authorized non-destructive tasks through available tools. No claim of background AI work without a configured automation/runner. On rate limit or session interruption, checkpoint status and next_action are sufficient to resume. If independent QA reviewer unavailable, mark WAITING_FOR_ART_QA rather than self-approve.

## Cost, deduplication, concurrency
No paid API or external account connection without explicit approval. One owning PR per asset-stage. Deduplicate by canonical input SHA + blueprint SHA + script SHA + Blender version + render config + stage. Concurrency by asset-stage and fingerprint, never cancel unrelated in-progress renders. Cache verified Blender dependencies and immutable evidence where valid; cache hit must verify manifest. No workflow-only change should automatically trigger full production render. Separate cheap validation from expensive render.

## Failures and circuit breaker
Classify CONFIG/YAML, DEPENDENCY, INPUT_SHA, LICENSE, BLENDER_RUNTIME, SCRIPT, RENDER, ART_TECHNICAL, ART_VISUAL, INTEGRATION, UNKNOWN. Preserve evidence. Two failures per same root cause and method family trigger STOP_METHOD, root-cause analysis and a materially different method, not a renamed retry. Do not stop independent workstreams.

## Rollout and acceptance
Phase A: audit existing PR #427 Morwen and PR #421 cliff workflows; verify current run status and no duplicate launches. Phase B: validate preflight and smoke on a bounded workflow run without rerendering unchanged assets. Phase C: add deterministic checkpoint writer/reader with schema and unit tests; integrate into existing owning PRs. Phase D: actual blueprint -> render -> QA -> checkpoint -> resume demonstration on one candidate per workstream. Acceptance: proven stop on syntax/input failure; no duplicate render for identical fingerprint; durable restart from checkpoint; actual .blend + PNG + hashes; accurate G1-G4; no user interaction except gated approvals. No new PR, main merge, canon adoption or publication is authorized by this proposal.
