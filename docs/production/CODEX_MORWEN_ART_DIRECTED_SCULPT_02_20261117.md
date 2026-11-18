# CODEX HANDOFF — MORWEN ART-DIRECTED SCULPT 02
Status: READY_FOR_EXECUTION / NOT_DISPATCHED / NO_NEW_GEOMETRY
Source: Draft PR #399, HEAD ee8770de690db33fd1e1f0b66de063cf3075cbb8, Actions 44064066566, Artifact 14319881962.

## Before any edits
Read current main AGENTS.md, HANDOFF.md, Blender.md, the later approved canonical five-image manifest and the production reset / retry policy. Review docs/qa/morwen-head-sculpt-20261117/INDEPENDENT_VISUAL_REVIEW_20261117.md and ATTEMPT_LEDGER.md. Verify actual SHA-256 and licensed CC0 provenance; preserve original blend and QA evidence. Check current branch HEAD and existing PRs. Work only in a new isolated feature branch and Draft PR.

## Goal
A demonstrably different *sculpt-directed* candidate for Morwen's face and bob, grounded in the approved design-sheet JPEG and four Layer0 PNGs. The present procedural face-fit and evenly radial shell-bob family has failed twice and MUST NOT be rerun with parameter variations. The measured 7.749997 head ratio is a **technical measurement**, not artistic approval.

## Approach and feasibility gate
1. Check available software and tool capabilities first. Genuine interactive/manual sculpt may require a GUI Blender session, a sculpt artist, or a verified sculpt-capable AI 3D service. GitHub Actions alone runs Blender headlessly and does not provide a human artist or art judgment.
2. If an actual sculpt/retopo method is available, record its exact tool, model, version, editability, licensing, cost and reproducibility. If unavailable, mark **BLOCKED_SCULPT_CAPABILITY** and produce a concrete handoff for manual sculpt rather than pretending procedural remeshing equals art-directed sculpt.
3. Create a new editable .blend by copying (never overwriting) morwen_head_study_UNAPPROVED.blend. Retain CC0 anatomical base, canonical hashes, cameras and measured reference rulers; clearly separate rejected candidate geometry from any new sculpt layer.
4. Design first: align the approved reference art to the actual orthographic cameras, preserving pixel aspect and body/face scale. Document silhouette landmarks for crown, brow, eye corners, nose tip, lip line, chin, ear, hair part, bangs and bob perimeter. Do not invent coordinates from uncalibrated image empties.
5. Sculpt front and side facial planes and eye aperture with an art-directed method, then sculpt asymmetric overlapping broad hair masses and secondary locks. No procedural ellipsoid head, tubes, zipper/annulus eyelids, or evenly repeated wedge/shell hair. Ensure real 3D depth, back/side consistency and later retopo feasibility.
6. Keep glasses as a modular candidate, but check nose bridge/temple/ear support. Do not spend time on costume ornaments.
7. Render face front, side, 3/4 and hair front, back, side; neutral clay plus canonical-color review; also 64px/128px target display previews. Use fixed cameras and color management; verify clipping and transparent alpha.

## Deliverables / gates
- Editable sculpt source .blend + render PNGs + contact sheet; geometry inventory, SHA-256, licensed provenance, reproducible build and tool versions.
- Explicit geometry difference from PR #399 (topology/shape/silhouette) and visual comparison to canonical art; independent reviewer required for G2.
- G1 BLOCKED until source-to-sculpt alignment verified. G2 FAIL until visual review PASS. G3 only scoped technical checks. G4 NOT_RUN until game/Android QA.
- If capability blocked, deliver an exact Blender manual-sculpt brief with camera/view overlays and a non-destructive source file; **do not** generate another low-quality procedural face as a substitute.
- Same-family correction failures max two; record causal method switch.
- No main merge, canonical replacement, deletion or publication.

## Reporting
In Japanese: 1. actual changed files and geometry, 2. QA results and unverified items, 3. next concrete task. Provide PR and Artifact URLs only if actually created. Distinguish instructions from completed sculpt.
