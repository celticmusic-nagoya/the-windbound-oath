# CHAR-BODY-01 — Body / rig parallel work package

Status: DRAFT / PREPRODUCTION / NO MODEL GENERATED. Base: PR #332. Contract source: docs/production/CHARACTER_INTERFACE_CONTRACT_V0.md on feature/char-interface-01 (not merged; review before modeling).

## Ownership
Torso, arms, legs, hands, feet, body weights and bind pose. Do not edit face or costume collections. Reuse existing approved rig only after exact bone inventory.

## Required inputs — BLOCKED until verified
Layer 0 body blend, approved neutral pose, rig names, unit scale, neck/shoulder/waist seams and coordinate transform.

## Candidate package
Task ID CHAR-BODY-01; character_id morwen; candidate_id TBD; branch feature/char-body-01; outputs assets/candidates/char-body-01/<candidate_id>/; Blender scripts tools/character_blender/; QA docs/qa/. Record official and candidate SHA256 separately, Blender version, seed, source and license, camera, object transforms, mesh/material names, dependency commits, renders, and G1/G2/G3/G4.

## Independent QA
Neutral pose and deformation views, bone-name match, skin weight sums, non-manifold check, neck/shoulder seam alignment, full-character game-size QA.

## Dependencies and execution
- Before any modeling, inspect latest main AGENTS.md, causal retry policy, exact accepted Layer 0 and reference binary; carry cumulative failed attempts across branches.
- Read shared interface contract; if neck seam, axes, units, rig or materials conflict, mark BLOCKED and request interface review, do not invent defaults.
- Build only finished-quality candidate modules, not primitive placeholders; render in pinned Blender Actions; preserve reproducible input hashes.
- Independent reviewer, not the producing agent, must certify G2. Game/Android QA is separate G4.
- No edits to canonical assets, no main merge, publication or PR auto-merge.

## Current gates
G1 BLOCKED (official image binary not verified); G2 NOT_RUN; G3 NOT_RUN; G4 NOT_RUN. Claude/Codex sessions are NOT STARTED by this document.
