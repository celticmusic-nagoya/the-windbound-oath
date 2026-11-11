# MORWEN-LAYER0-03 — Independent QA gate (ChatGPT)

Status: REVIEW SPEC / NOT_RUN for execution and visual checks. Source: v0.9 candidate at commit 1f7ce037cca3e8c549750c259fd2d935787d3844. This document is not an approval or an automated test result.

## Observations from source JSON

- The candidate specifies canvas 1200×1600 and contact (600,1540).
- `kinematicTree.ground = pelvis`: ground is attached to an animated joint. A world-space ground/contact anchor must be separate from pose-dependent joints.
- `ageCategory = minor` and `bodyGuidePolicy = minor_neutral_structure`: these fields do not match the director's newly requested age 18. Do not silently mutate archived candidate evidence; audit current canonical character metadata, policy and tests, then version the new candidate explicitly.
- The v0.9 QA report records independent visual review and final adoption as NOT_RUN. A numerical silhouette containment percentage is not a design approval.

## Proposed invariants and executable acceptance tests

1. **Ground independence:** worldGround is a world-space anchor, not a descendant of pelvis. Rotating/translating the pelvis may change foot positions, but must not move worldGround.
2. **Contact preservation:** for stance frames, heel/ball/toe contact selected by gait phase stays within a configurable tolerance of the planted world-space point. Compute per-foot displacement over frames and report maximum/median; never label a static T-pose check as a walk test.
3. **Joint hierarchy:** one root for the deforming rig, no cycles, all non-world joints have valid parents; verify left/right IDs and segment lengths in every pose.
4. **View projections:** project the same 3D pose to front/back/left/right. Compare common y landmarks and verify near/far limb visibility; do not infer hidden joint locations from costume boundaries.
5. **Versioned age migration:** update current character profile and candidate policy to age 18 only after verifying all dependent schema enumerations; retain immutable historical SHA evidence. Age does not imply identical body measurements across characters.
6. **Layer independence:** L0 and L1 independently toggle without modifying source pixels. Compare RGBA dimensions, ground anchor, manifest SHA and occlusion order.
7. **Regression:** re-run pipeline unit tests, studio unit tests, E2E and repository regression; compare names of eight previously failing tests, not merely the failure count.
8. **Visual gate:** independent review of all four structural views, L0+L1 composites, joint bending and reference silhouette. Keep adoptionReady=false until explicitly approved.

## Required evidence

- `AGE_MIGRATION_AUDIT.json` (paths, old/new values, dependency checks)
- `KINEMATIC_ROOT_QA.json` (before/after parent map, cycles, worldGround immutability)
- `STANCE_CONTACT_QA.json` (per-frame contact displacements and tolerances)
- `FOUR_VIEW_VISUAL_QA.md` (screenshots, findings, statuses)
- `REGRESSION_DIFF.json` (test identifiers, baseline vs current)

## Safety gates

Do not overwrite original canon, v0.8 or v0.9 candidate, or historical measurements. Keep PR #224 Draft; no merge, adoption, game integration or publication. The independent QA checks above are **specified, not executed**.
