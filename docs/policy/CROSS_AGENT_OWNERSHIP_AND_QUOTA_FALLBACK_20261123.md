# Cross-agent ownership, quota fallback and continuity — 2026-11-23

Status: director-approved operational assignment and safe handoff rules. This document supplements, and does not supersede, current main AGENTS.md, POLICY_REGISTRY.json, PRODUCTION_RULES.json, TWO_PRODUCTION_OS_V1.md and CONTINUITY_AND_PRODUCTION_READINESS_20261123.md. Later explicit approvals take precedence. Assignment is not proof of implementation or production readiness.

## Responsibility map (dated assignments; resolve live owner before work)

These are historical starting pointers to existing workstreams, not fixed AI restrictions or grants of writer authority. The current AGENTS and live owner/STOP_ACK/CAS/fence determine assignment. Any qualified AI may execute independent approved tasks, and a missing connector method must not erase an existing authorized route.

| Scope | Primary | Boundary |
| --- | --- | --- |
| Shared Blueprint Engine | Claude (common infrastructure) | Reuse #468 target/measurement/operation contracts; do not fork a competing schema. Engine implementation, adapters and verification only, not asset canon or owner artwork. |
| Long-run Production Engine | Codex, existing PR #468 | Factory, Session Controller, real edit guard, checkpoint, cross-run restore, queue, CAS/lease/fencing and Actions dispatch. |
| Character/Morwen actual blueprint and native 3D | Current character owner, PR #427 | Official CG/VRoid-first, face/hair/body/wardrobe, G1–G4; preserve native, SHA and approved scope. |
| World/area actual blueprints and native 3D | Current map/world owners, including #364 and #421 | Country/area drawing, rock/terrain/buildings, actual renders, G1–G4. |
| Production Studio | ChatGPT development coordinator | Read-only mobile-first artifact/blueprint/GLB/VRM views, provenance, PR/run/QA/lease visibility; public eligibility and secret boundaries enforced. |
| Cross-agent coordination and independent review | ChatGPT development coordinator | Synchronize evidence, review contracts, handle safe fallback, never assume writer ownership. |

A named AI is a default assignment, not an automatic exclusive lock or authority to edit an asset. Live owner acknowledgement, stage lease and fencing determine write authority. Existing specialist work is not displaced by this document. Avoid new duplicate PRs, duplicate CI, redundant rendering or replacing verified work.

## Required shared handoff record

Record each material stage change in the owning PR and existing Production OS queue, using a monotonically increasing revision. Required fields: task_id; asset_id and stage; owner and backup coordinator; PR/branch/HEAD; lease_id, fencing_token, expiry and last owner acknowledgement; read/write scope and protected paths; reference/source/dependency SHA-256; current native checkpoint path/SHA; output artifact IDs, run/event IDs, retention/expiry and verified restore route; blueprint target/measurement/operation contract SHA; exact tested software/runtime; G1–G4 and readiness status; completed stages and reusable outputs; failure/correction history; blocker, next executable operation, stop condition and timestamp. Missing values are explicitly UNKNOWN, not invented. Do not publish private handoffs, native masters, secrets or redistribution-restricted sources.

## Quota exhaustion / disconnection fallback

1. Detect quota exhaustion, disconnection or inactivity from owner-provided evidence; do not infer a stopped writer from silence or a chat limit alone. Do not claim automatic monitoring or failover until demonstrated.
2. Read current main policy and all owner PR comments, current stage, branch/HEAD, all-event Actions with pagination/error checks, lease/fencing, input/output SHA, checkpoint bytes, artifact expiry and QA. A prior chat summary or stale PR comment is insufficient.
3. Prefer owner voluntary stop and explicit STOP_ACK. Before any backup write, prove the old writer cannot continue, validate lease transition via existing atomic CAS and a new fencing token, verify exact-byte working copy and native checkpoint restore. Never forcibly reclaim a live lease on quota exhaustion alone.
4. If STOP_ACK, atomic handover or checkpoint authenticity cannot be established: mark SYNC_UNVERIFIED / BLOCKED for affected writes, dispatch, recovery and candidate QA. Continue independent read-only review, Studio improvements and unrelated qualified work. Escalate any force recovery for explicit director approval.
5. Once safe, the coordinator may resume only the unfinished approved non-destructive stage in the same owner PR and scope. Reuse matching successful checkpoints by input/dependency/tool/settings/QA hashes; do not repeat successful renders or reset failure counts. Respect edit-vs-read-only guard, measured change and protected fingerprints.
6. On original owner return, publish a new ordered handoff revision, stop backup writer and obtain STOP_ACK, verify fenced transition and exact current SHA/checkpoint, then return ownership. Never run two writers for one stage.

## Integration contracts and acceptance

- Claude Blueprint Engine emits source-grounded targets with coordinates, units, projection, target/measurement IDs, tolerances, uncertainty, qualified operations, protected scopes and dependency fingerprints. Inferred geometry and unknown values are labeled; no speculative canon. Codex #468 remains the shared execution/measurement contract owner; coordinate interface changes in its PR before adapter adoption.
- Codex Factory accepts only qualified contracts, records actual native SHA and measured deltas for required edits, prohibits edits for read-only stages, verifies reopen and independent cross-run restore. No automatic precision PASS from a JSON schema alone.
- Asset owners author actual blueprint and native work in their existing PRs; independent visual G2 and measured G1/G3/G4 remain owner-specific. No cross-owner writes without a verified handoff.
- Studio consumes only authenticated, provenance-checked, publication-eligible records; displays current/candidate/quarantine/adopted distinctly and unknown/expired evidence explicitly. Public site is read-only; publication is separately approved.
- Readiness vocabulary: POLICY_ONLY, IMPLEMENTED, ISOLATED_PASS, PRODUCTION_VERIFIED, BLOCKED, NOT_RUN. Require revision-specific evidence; a successful CI, isolated Blender test, same-run reopen or merged PR does not prove production-ready cross-run recovery, 60–360 minute runs, or G1–G4.
- Ordinary scoped reviewed main integration follows current AGENTS after QA; adoption, canon changes, protected asset changes, destructive deletion, new publication, added cost and forced recovery require separate explicit approval.

## Minimal handoff test matrix (NOT_RUN until independently evidenced)

- Quota interruption during actual edit; owner STOP_ACK; atomic lease/fencing transition; exact-byte restore in a different Actions run; measured native resume without duplicate edit.
- Stale writer and competing writer rejected; missing/expired artifact, changed dependency SHA, corrupted checkpoint and conflicting owner each fail closed.
- Read-only stage does not edit; required-edit stage changes native SHA and measured geometry; protected fingerprint and unrelated metrics unchanged.
- Original owner returns after backup STOP_ACK and receives verified current checkpoint; no lost updates.
- Studio renders current ownership, SHA, readiness, G1–G4 and blocker without leaking private material.

Log each case with actual run ID, HEAD, input/output hashes, timestamp, observed outcome and next action. Until tests pass, automatic cross-agent takeover remains NOT_RUN.
