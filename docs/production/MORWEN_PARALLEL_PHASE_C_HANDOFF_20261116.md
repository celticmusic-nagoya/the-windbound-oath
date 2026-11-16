# MORWEN parallel production — Phase C handoff (2026-11-16)

Status: DESIGN READY / GEOMETRY NOT_RUN / ART QA NOT_RUN / PROMOTION BLOCKED.

## Verified baseline
- Parallel workflow: `.github/workflows/morwen-parallel-production-gates.yml` at eb15672.
- Design lane currently checks reference inputs only; `geometry_created=false`.
- Art-review lane checks evidence readiness only; it does not assess image quality.
- Existing candidate is not approved final Morwen geometry. Do not call technical framing success an art PASS.
- Five immutable references: `assets/canonical/morwen/2026-11-16/MANIFEST.json` (SHA-256 must be checked before production).

## Phase C — real geometry deliverable
1. Create a new isolated candidate directory under `assets/candidates/`; do not overwrite existing .blend or canonical PNGs.
2. Produce native Blender geometry as independently named modules: head/face, front/back/side hair, torso/garment, arms/sleeves, lower garment, legs, knee-high socks, shoes, accessories. Preserve asymmetry explicitly; never mirror asymmetric attachments by default.
3. Before any modeling, compare all four canonical views and the approved design sheet. Record conflicts, especially the anatomical-right-leg garter and 7.5–8-head target versus source illustration proportions. If canon cannot resolve, mark G1 BLOCKED rather than inventing a final design.
4. Freeze Blender version, generator source, parameters, random seed, reference hashes and candidate hash in machine-readable manifest.
5. Render four orthographic views plus face/detail closeups, with consistent camera, lighting, resolution and transparent PNG output. Produce a contact sheet and JSON report.
6. Automated technical QA: nonempty meshes, no missing texture paths, alpha, dimensions, pose orientation, camera framing, 7.5–8-head ratio and unchanged canonical hashes. Fail closed on missing artifacts.
7. Independent visual review compares each render against corresponding official reference. Human/vision-model assessment must explicitly inspect face, hair, costume, asymmetry, proportions and final display size; automated pixel metrics alone do not qualify.
8. Only after independent art PASS: rig/deformation QA, game-scale render and Android device QA. No main merge or publication without explicit approval.

## Lane contracts
- A canonical: immutable hashes and design precedence; BLOCKED on conflict.
- B design: outputs geometry and candidate manifest; `PASS_REFERENCE_INPUTS_ONLY` must never be treated as production PASS.
- C Blender: actual .blend, four rendered PNGs, deterministic build metadata, technical report.
- D art-review: independent review of actual rendered PNGs, with image evidence and PASS/FAIL/BLOCKED.
- E integration: verifies all lane artifacts originate from the same candidate hash and run; promotion stays BLOCKED unless G1–G4 PASS.

## Execution safeguards
- Do not loop rendering against the same root cause more than two substantive attempts. Preserve attempts and failure causes.
- Distinguish NOT_RUN from PASS and record every missing artifact.
- GitHub Actions jobs may run in parallel for independent QA, but geometry must complete before render and render before art review. Use `needs` and artifacts, not five unrelated matrix jobs for production dependencies.
- Preserve prior candidate work and use a Draft PR. No merge, deletion or publication.

## Current observations
GitHub connector returned no jobs and no artifacts for workflow run 43852160333; this is NOT evidence of success or failure. Recheck in GitHub UI/API.
