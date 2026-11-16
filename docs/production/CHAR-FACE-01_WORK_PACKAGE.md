# CHAR-FACE-01 — Face / head parallel work package

Status: DRAFT / PREPRODUCTION / NO MODEL GENERATED. Base: PR #332. Contract source: docs/production/CHARACTER_INTERFACE_CONTRACT_V0.md on feature/char-interface-01 (not merged; review before modeling).

## Ownership
Head topology, eyes, mouth, ears, hair, expressions, four-view silhouettes. Preserve Morwen PR #327 eyelid/lash candidate and existing failed method history; no competing edits to its files.

## Required inputs — BLOCKED until verified
Approved face four-view image bytes and SHA, existing Layer 0 head mesh, rig facial bones, interface neck seam.

## Candidate package
Task ID CHAR-FACE-01; character_id morwen; candidate_id TBD; branch feature/char-face-01; outputs assets/candidates/char-face-01/<candidate_id>/; Blender scripts tools/character_blender/; QA docs/qa/. Record official and candidate SHA256 separately, Blender version, seed, source and license, camera, object transforms, mesh/material names, dependency commits, renders, and G1/G2/G3/G4.

## Independent QA
Four direction head-only views and full-head 48/96px, silhouette and facial expression comparison, normal/topology/UV/alpha; independent G2.

## Dependencies and execution
- Before any modeling, inspect latest main AGENTS.md, causal retry policy, exact accepted Layer 0 and reference binary; carry cumulative failed attempts across branches.
- Read shared interface contract; if neck seam, axes, units, rig or materials conflict, mark BLOCKED and request interface review, do not invent defaults.
- Build only finished-quality candidate modules, not primitive placeholders; render in pinned Blender Actions; preserve reproducible input hashes.
- Independent reviewer, not the producing agent, must certify G2. Game/Android QA is separate G4.
- No edits to canonical assets, no main merge, publication or PR auto-merge.

## Current gates
G1 BLOCKED (official image binary not verified); G2 NOT_RUN; G3 NOT_RUN; G4 NOT_RUN. Claude/Codex sessions are NOT STARTED by this document.
