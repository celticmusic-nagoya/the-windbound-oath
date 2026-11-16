# CHAR-COSTUME-01 — Costume / accessories parallel work package

Status: DRAFT / PREPRODUCTION / NO MODEL GENERATED. Base: PR #332. Contract source: docs/production/CHARACTER_INTERFACE_CONTRACT_V0.md on feature/char-interface-01 (not merged; review before modeling).

## Ownership
Innerwear, outerwear, knee socks, shoes, belts, book, satchel, headgear and jewelry as separate collections. Exact official Morwen artwork governs asymmetry, palette, ornament placement. No guessed details.

## Required inputs — BLOCKED until verified
Actual approved design image bytes, equipment slot definitions, body/rig seam contract, clothing order and occlusion masks.

## Candidate package
Task ID CHAR-COSTUME-01; character_id morwen; candidate_id TBD; branch feature/char-costume-01; outputs assets/candidates/char-costume-01/<candidate_id>/; Blender scripts tools/character_blender/; QA docs/qa/. Record official and candidate SHA256 separately, Blender version, seed, source and license, camera, object transforms, mesh/material names, dependency commits, renders, and G1/G2/G3/G4.

## Independent QA
Four direction clothing overlays, clipping under deformation, UV/alpha/material slots, 48/96px readability, independent design comparison and license audit.

## Dependencies and execution
- Before any modeling, inspect latest main AGENTS.md, causal retry policy, exact accepted Layer 0 and reference binary; carry cumulative failed attempts across branches.
- Read shared interface contract; if neck seam, axes, units, rig or materials conflict, mark BLOCKED and request interface review, do not invent defaults.
- Build only finished-quality candidate modules, not primitive placeholders; render in pinned Blender Actions; preserve reproducible input hashes.
- Independent reviewer, not the producing agent, must certify G2. Game/Android QA is separate G4.
- No edits to canonical assets, no main merge, publication or PR auto-merge.

## Current gates
G1 BLOCKED (official image binary not verified); G2 NOT_RUN; G3 NOT_RUN; G4 NOT_RUN. Claude/Codex sessions are NOT STARTED by this document.

## Director-approved 3D visual target — 2026-11-16
- **New 3D characters: approximately 7.5–8 heads**, high-quality anime-style visual language comparable in production ambition to Genshin Impact and Neverness to Everness (NTE). Supersedes 2.8-head field-sprite proportions for this new 3D work package.
- Preserve approved official face, Layer 0, costume, colors and asymmetry. Do not replicate copyrighted third-party character meshes or artwork.
- Exact neck/rig/scale/axis measurements are still BLOCKED pending approved source inspection. Do not generate incompatible final geometry while interface is unlocked.
- Existing 2D sprites remain unchanged; 48px/96px previews are optional legacy diagnostics, not a new 3D head-ratio requirement. Final game-camera QA and Android performance must be independently tested.
