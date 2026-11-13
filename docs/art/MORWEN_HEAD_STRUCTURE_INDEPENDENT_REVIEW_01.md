# MORWEN-HEAD-STRUCTURE-01 | Independent evidence review
Date: 2026-11-14
Status: TECHNICAL EVIDENCE REVIEWED / ART ACCEPTANCE BLOCKED

## Inputs and provenance
- Claude Draft PR #302: https://github.com/celticmusic-nagoya/the-windbound-oath/pull/302 (branch `feature/morwen-head-structure-01`, HEAD `5cbb2473093e739972769f33ae0f2ce6c7c982c6` at review).
- `tools/blender/morwen_production/HEAD_STRUCTURE_01_AUDIT.md` and JSON reports under `_qa/head_structure_01/` in that branch.
- GitHub Actions run #43457599069 reported SUCCESS in the audit. The report claims 32 renders and consistent topology metrics.
- Director-approved high-quality PNG on `feature/morwen-reference-binary-01`: `assets/companions/morwen/reference/file_00000000301c8209af49625fd11d7670.png`, SHA-256 `7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957` verified by Actions #43459999519.
- Existing Layer 0 four-view canon is distinct from this full-costume production target. Canonical design priority remains `docs/design/MORWEN_V561_CANONICAL_20261108.md`.

## Technical evidence (reported by Claude, not an independent rerun)
- Legacy 588-vertex extract covers 78.81% of face skin polygons; do not use it as a complete-head reference.
- Face/Body interface has 38/38 coincident boundary vertices, indicating that the apparent missing head was an extraction artifact.
- Old dark renders resulted from a backlit single AREA light and lost custom split normals in `from_pydata` reconstruction; lighting A/B comparison reportedly clears darkness.
- Face topology, skinning and shape keys are candidates for structural REUSE; HairBack texture cap requires REBUILD for canonical layered bob.
- The comparison `HEAD_VS_CANONICAL_LAYER0_UNCALIBRATED.png` is explicitly **uncalibrated**. It cannot establish eye/nose/chin landmark fit.

## Independent gate decision
- G1: PNG file integrity PASS; canonical art-vs-model visual fit NOT_RUN.
- G2: BLOCKED. No calibrated side-by-side head landmark comparison, no approved final hair/hat/glasses/outfit, no visual art acceptance.
- G3: Technical report and CI evidence present; independent Blender rerun NOT_RUN in this review.
- G4: NOT_RUN (game-size / rig / Android).
- **Decision: PROVISIONAL STRUCTURAL REUSE ONLY; do not approve current VRoid head as final Morwen asset.**

## Next high-value non-destructive task
1. Generate orthographic four-view comparison from complete Face+Body head (not the 588-vertex fragment), with consistent camera, scale, and labeled head-top/eye-line/nose-tip/chin landmarks.
2. Compare against canonical Layer 0 head and director-approved PNG; distinguish calibrated and uncalibrated evidence.
3. Issue per-view G2 PASS/FAIL/BLOCKED with annotated proof. If face landmarks cannot fit without major topology deformation, switch to sculpt/retopology rather than repeated percentage tweaks.
4. Keep Claude PR #302 and PNG reference branch separate until independent review; no main merge, canon overwrite, or publication.

This file is a review of recorded evidence only, not a claim of direct visual inspection of binary render sheets.
