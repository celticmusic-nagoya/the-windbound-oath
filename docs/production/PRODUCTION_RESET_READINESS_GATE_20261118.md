# TWO production reset — readiness gate (2026-11-18)
Status: PREPARATION / NO-GO for new Morwen and map modeling. This is an operational proposal on an existing Draft PR branch, not adopted canon and not permission to merge or delete.

## Objective
One finished, independently QA-passed Morwen 3D character first. Resume high-end map modeling only when shared production controls and relevant source evidence are verified. Do not equate plans, CI green, renders, or PR counts with completed assets.

## Team and accountable ownership
- Director (user): approves canon changes, asset adoption, destructive cleanup, main merge and publication.
- Production lead (ChatGPT): source-of-truth, cross-PR coordination, research synthesis, readiness audit; independent QA where not author.
- Character artist / implementation (Codex or explicitly available agent): sculpt, retopo, UV, PBR, rig, animations, actual editable .blend and renders.
- Environment artist / implementation (separate assigned agent): art-directed hybrid terrain, cliffs, architecture, navigation, vegetation and water; no character-file edits.
- Art reviewer (Claude if connected/available, else separate review session): silhouette, likeness, anatomy, material, render composition; not author of reviewed change when possible.
- GitHub Actions: bounded reproducible builds, Blender renders, technical tests, SHA manifests and retained artifacts. CI is not an artist.
No AI team member is considered running until its actual task invocation and output are verified. If only one agent is available, sequence production and independent review rather than claiming concurrency.

## Branch/PR control
1. Inventory ALL open PRs and branches, with branch HEAD, base, owner, task, artifact location, status, latest QA, source SHA, and supersession relation.
2. One active implementation branch/PR per asset-and-stage owner. Reuse existing appropriate branch. No new branch merely to retry or rename a method.
3. Existing unmerged branches are evidence, not canon. Never mass-merge, mass-close, delete or overwrite.
4. Before creating any branch, search for an active matching PR and document why reuse is impossible.
5. Mark stale/superseded candidates only after inspecting their actual assets and dependencies; propose archival separately for director approval.
6. Put a minimal session entrypoint in main only after review/approval, with links to canonical registries. GitHub connectivity alone does not imply agents read it.

## Evidence and research gate
- Verify canonical lore/design, four-angle Layer 0 references, actual original SHA or approved visual-equivalence exception, landmarks and perspective limits.
- Recover and inspect VRoid, MPFB, official CC0 and prior Morwen sculpt meshes: editable topology, silhouette suitability, deformation, license, source provenance.
- Research documented professional character pipeline (anatomy/proportion, stylized sculpt, face/eyes/hair, garment construction, retopo, UV/PBR, rig, performance), with primary sources and specific reproducible methods.
- Research environment art-directed hybrid workflow: sculpted cliffs and overhangs, terrain, building construction, material authoring, scatter, route traversability, LOD and Android/WebGL budgets.
- Define target renders and actual game-display quality before sculpt. Do not begin details until base-body anatomy and clothed full silhouette are validated.
- Diagnose failed attempts by missing input, wrong base, inadequate skill/tool, implementation, render conditions, or method defect. The two-failure circuit breaker applies only to repeated ineffective same-cause/same-family attempts; it is not a substitute for preparation.

## Systems gate
- Verify branch/PR index, immutable source SHA manifests, license ledger, artifact retention/downloadability, cross-session read/write handoff, job concurrency and cancellation, retry budgets, independent QA assignment.
- GitHub Actions: pinned Blender version with reliable acquisition/cache; actual render and .blend reopen tests; run IDs and artifacts retained. Avoid duplicate downloads and meaningless reruns.
- Separate editable Blender master from optimized WebGL/Android exports.
- Verify real ChatGPT, Codex and Claude new-session retrieval independently; inability to access a connector is BLOCKED, not PASS.

## Resume decision
NO-GO until ALL of:
A. Canonical refs and actual previous candidate files recovered and compared (G1 evidence).
B. Single selected production base and method with license and independent artistic rationale.
C. Team ownership and one active branch/PR per workstream verified.
D. CI produces and reopens a real .blend and four-view renders, with downloadable artifacts.
E. Independent art QA criteria and Android/WebGL budgets defined; no claim of G2/G4 PASS before actual testing.
F. Cross-session handoff tested with at least the available agents; unavailable agents marked BLOCKED, not simulated.
G. Director approves resumption after evidence-backed readiness report.
Until then: audit, research, tooling tests and non-destructive consolidation only; no new Morwen/map geometry and no main merge.

## Evidence snapshot
- main/AGENTS.md and main/docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md inspected on 2026-11-18.
- Morwen branch search returned 78 matching names, not a complete audit of all repository branches or open PRs.
- Cross-branch attempt ledger auto-sync is explicitly NOT_IMPLEMENTED in the existing policy.
- Continuity entrypoint is on feature/morwen-rebuild-01, absent from main at check time.
- Actual multi-agent fresh-session and completed character verification: NOT_RUN.
