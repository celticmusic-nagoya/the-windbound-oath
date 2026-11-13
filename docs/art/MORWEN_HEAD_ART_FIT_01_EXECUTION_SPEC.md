# MORWEN-HEAD-ART-FIT-01 | Calibrated comparison execution specification
Status: SPEC READY / RENDER NOT_RUN / INDEPENDENT VISUAL QA NOT_RUN
Date: 2026-11-14

## Immutable inputs
- Director-approved target PNG: `assets/companions/morwen/reference/file_00000000301c8209af49625fd11d7670.png`, SHA-256 `7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957`.
- Layer 0 views: `tools/blender/production_mesh_08/references/7809.png` front; `7807.png` right; `7810.png` back; `7808.png` left. Preserve manifest digests.
- Complete Face+Body head from Claude PR #302 (`feature/morwen-head-structure-01` @ `5cbb2473093e739972769f33ae0f2ce6c7c982c6`). Never use the 588-vertex fragment as a head.
- Canonical hierarchy: `docs/design/MORWEN_V561_CANONICAL_20261108.md` and `docs/lore/MORWEN_CANON_20261108.md`. The 3D target is not authorization to replace them.

## Required comparison pipeline
1. Record source commit, input hashes, Blender version, exact script, camera, orthographic scale, model/world orientation and reference crop bounds.
2. Extract each Layer 0 head region without stretching or altering source files; record top/eye-line/nose-tip/chin landmarks and crop coordinates in a JSON sidecar.
3. Render complete Face+Body head (front/right/back/left) with neutral clay material, calibrated orthographic camera, uniform illumination, and visible model anchors. Preserve model's custom split normals and skinning. Export RGBA PNG.
4. Align rendered and reference head-top/chin vertical distance; apply **uniform scaling only**. Record transform and pixel error; do not assume physical world-unit dimensions from stylized reference. Flag ambiguous landmarks as UNMEASURABLE rather than estimating.
5. Create four-view side-by-side + overlay sheets with head outline, eye centers, nose tip, chin and ear landmarks where visible. Report signed and absolute pixel offsets normalized by head height.
6. Compare separately with the director-approved target PNG and canon. Any mismatch in design, hairstyle, glasses, asymmetric ornaments must be reported; do not resolve by replacing canon.
7. Produce `ART_FIT_01_REPORT.json` (per-view measurements, evidence files, G1-G4 verdicts, failure classifications, reproduction metadata), `ART_FIT_01_CONTACT_SHEET.png` and 4 overlays.
8. QA: ensure no original input changed, source SHA unchanged, all views rendered, consistent orthographic scale and anchors, transparent output, no missing landmarks silently substituted. Reproduce on GitHub Actions and inspect actual image evidence before G2 decision.

## Decision thresholds
No arbitrary numeric face-match tolerance is approved. G2 remains BLOCKED until calibrated evidence exists and an independent visual review judges silhouette, face landmarks, expression, and material suitability. Technical REUSE from PR #302 is provisional, not visual acceptance. If face shape requires substantial deformation, favor sculpt/retopology over repeated local percentage edits. HairBack must be rebuilt as volume; eyes' alpha/material wiring needs rebuild.

## Execution boundary
This spec does not claim to have rendered or visually inspected GitHub PNG binaries. GitHub text connector cannot decode PNG, and current runtime cannot retrieve raw.githubusercontent.com. Preserve existing Claude PR #302 and avoid parallel edits to its scripts. Implement render/overlay on a dedicated branch once binary-capable environment is available. Do not merge to main, overwrite canonical sources, or publish.
