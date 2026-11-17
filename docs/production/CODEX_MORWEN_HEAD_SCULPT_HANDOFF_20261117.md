# CODEX TASK — MORWEN HEAD SCULPT / RENDER 01 (2026-11-17)

**Status:** READY_FOR_CODEX; NOT DISPATCHED; NOT IMPLEMENTED. This is an execution handoff, not evidence of sculpt completion.
**Repository:** celticmusic-nagoya/the-windbound-oath
**Work isolation:** Start from latest main + inspect Draft PR #339 / feature/morwen-fable-eval-01; use a dedicated feature branch and Draft PR. Never overwrite canonical files, existing Blender artifacts, or main.

## Mandatory read / baseline
1. Read latest main AGENTS.md, HANDOFF.md (if present), Blender.md (if present), and compare with working branch.
2. Read docs/production/MORWEN_PRODUCTION_METHOD_RESET_20261116.md, docs/production/MORWEN_LEGACY_FACE_WORK_AUDIT_20261116.md, docs/production/MORWEN_775_TURNAROUND_CONSTRUCTION_SPEC_20261117.md, docs/production/MORWEN_CANONICAL_VS_GENERATED_TURNAROUND_QA_20261117.md, and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md.
3. Inspect recent PRs, commits, failure ledger, and artifacts. In particular: Actions 44013725254, artifact 14298561244; reference-embedded Blender stage morwen_head_landmark_review_UNAPPROVED.blend. Do not infer model quality from Actions success.
4. Verify assets/canonical/morwen/2026-11-16/MANIFEST.json SHA-256 for all five immutable images. If actual source or latest canon cannot be read, mark G1 BLOCKED, do not guess.

## Director-approved scope
Build a **genuinely editable 3D anatomical head/face/hair candidate**, integrated with the verified body basemesh, suitable for later sculpt/retopo/rigging. Prioritize stable Blender rendering and visible 3D structure over tiny costume details. Design target is adult Morwen, 7.5–8 anatomical heads, nominal 7.75; official short purple bob, recognizable facial silhouette and glasses. Preserve asymmetry and do not silently substitute other character art.

## Execution stages
A. Inventory actual existing head/face/hair meshes and source .blend files. Classify REUSE_VERIFIED / REFERENCE_ONLY / REJECTED / NOT_FOUND, with SHA, provenance, mesh topology and fit evidence. Do not repeat the rejected procedural ellipsoid face, tubular hair, or annulus/zipper eyelid approach.
B. Use a legally documented, sculpt-ready head with credible facial topology; modify and integrate to the body, using a structural sculpt/retopo approach. If licensed usable topology is absent, stop the head sculpt at BLOCKED and report a specific alternative, without fake geometry.
C. Determine anatomical crown, chin underside, and sole landmarks on actual geometry, with reviewer-verifiable evidence. Measure ratio H / head_height; never treat the existing chin placeholder as a measured chin. Proportion adjustments must preserve natural neck/shoulder transition and silhouette.
D. Model face planes and broad overlapping bob hair volumes as **real 3D meshes** (not images/flat planes/tubes). Glasses can be a separately editable modular part. Stage quality should be judged from front, back, left, right, plus 3/4 and face close-up. Small outfit ornaments may remain TODO.
E. Produce Blender .blend (editable original), at least four orthographic RGBA PNGs and one 3/4 PNG, source hash manifest, mesh stats, Blender version, rendering configuration, and repeatable build instructions. Store in GitHub Actions artifacts with an explicit retention period; no external paid API.
F. Technical QA: source unchanged, mesh nonempty, normals/topology checks, geometry in frame, alpha nonzero, overexposure/clipping checks, 4-direction camera consistency, saved .blend reopen test, measured ratio evidence. Independent visual QA separately records discrepancies against actual canonical artwork.
G. Do not approve, merge, publish, or replace originals. If art fails, preserve candidate and identify the causal defect. Two same-family failed corrections -> switch structurally different method, not parameter-only retries.

## Deliverable / acceptance
- Dedicated Draft PR with actual changed scripts, workflow, and QA docs.
- Action run URL and artifact link to actual .blend and rendered PNGs.
- SHA manifest and evidence of source integrity.
- Explicit G1/G2/G3/G4 statuses; G2 cannot PASS based on CI alone; G4 stays NOT_RUN without game/Android testing.
- Report in Japanese: (1) changed files/implementation, (2) QA/regressions, (3) next task.
- If no new 3D geometry is created, report BLOCKED or NOT_RUN, **not** implementation complete.

**Delegation status:** Document prepared for Codex; Codex has not been invoked by this document.
