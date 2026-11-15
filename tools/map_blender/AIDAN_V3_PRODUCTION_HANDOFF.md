# AIDAN-HOUSE-03 | Production handoff and independent QA

Status: DIAGNOSTIC ONLY. Not an approved asset. Never overwrite v1/v2, adopted reference images, or merge main without approval.

## Evidence
- Draft PR #323, branch feature/aidan-architecture-v3-01.
- Blender 4.0.2 CI run 43662689245: PASS for Python syntax, five PNG renders, manifest hashes, gable count, first-face slate normals, porch flag, 27-degree camera parameter.
- Artifact ID 14140478610; expires 2026-11-22. Retain evidence before expiration.
- G1: protected originals unchanged; G2: FAIL (visual finish); G3: PASS only for existing checks; G4: NOT_RUN.
- Previous failures: undefined Vector and unavailable OpenImageDenoiser. Both repaired; logs now preserved.

## Approved design decision
Porch option A: independent pitched entrance porch below main eaves, no intersecting roof valley. Keep design aligned with officially approved Aidan house images; do not assume a new canonical shape from this diagnostic.

## Independent review assignments (not yet executed)
**Claude — art and architecture QA (read-only):**
Inspect all five PNG views and the approved design references; distinguish verified observations from inferred geometry. Assess gable closure, slate course overlap, eaves/ridge/verge detailing, masonry and timber joinery, door/window fit, porch silhouette, chimney/ivy and lived-in props. Return P0/P1/P2 with exact view and evidence; do not edit or claim formal adoption.

**Codex — code and QA audit (read-only):**
Review architecture_v3.py, architecture_render_v3.py, and CI workflow. Specifically test all six faces for correct winding on both roof sides (not just polygon 0), world-space transforms, roof offsets and collision, corner and opening gaps, camera elevation measured from actual target, artifact existence and sha256, and false-positive CI cases. Propose minimal deterministic tests with runnable commands. Do not edit, merge, or publish.

## Production architecture
Do not polish v3's uniform boxes into 'final' art. Build separate production modules for (1) stone masonry courses and dressed corners, (2) timber framing and joinery, (3) slate roof with course overlap and verge/ridge caps, (4) door/window assemblies, (5) porch A, (6) optional approved details. Use a shared metric coordinate frame and parametric roof surface. Record seeds, material definitions, and Blender version. Keep canonical reference checks and 48px game-scale preview as quality gates.

## Next gates
G1: compare official references and geometry; G2: independent art QA of production modules; G3: manifold/normal/UV/PBR/render/export tests; G4: actual game camera, 48px view and Android device QA. A passing CI render is not G2/G4 approval.
