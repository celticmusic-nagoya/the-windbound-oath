# Aidan masonry — G2 recovery design gate (candidate only)

Baseline: Draft PR #323, commit `5b6dbe2126be8db5be91e83c7d38ec77c2a1b25f`.
Status: DESIGN / NOT ART APPROVED. This document does not change the approved house or the current candidate generator.

## Evidence and failure classification
- GitHub Actions run 43732157438: Python syntax, Blender render and artifact upload succeeded.
- Artifact: `aidan-corner-bond-v2-candidate` (run 43732157438).
- Existing independent visual review: G2 FAIL — corner blocks still read as regular prisms; isolated chips, 1–4 mm plan wear, 7 mm bevel and 3 mm displacement do not resolve the silhouette mismatch.
- CI success is **not** proof of mesh manifoldness after evaluated Boolean modifiers, art quality, or in-game suitability.
- No further tuning of the same bevel/displacement/two-chip approach without a newly evidenced distinct cause.

## Next geometry architecture
1. Keep the existing six-course L-bond layout as a **dimensional reference**, not an approved production mesh.
2. Create a separate, non-destructive prototype file for a single corner stone with a coherent hand-dressed silhouette: asymmetrical large-scale chipped planes, irregular edge rhythm and broad face relief. Avoid uniform random noise as the primary silhouette.
3. Generate a stone-specific outer shell with controlled cut planes; retain the inner seating/bond faces and a bounded clearance envelope. Model the corner as one contiguous solid.
4. Define a shared material/shape language for regular infill stones and quoins; do not evaluate the corner stone alone.
5. Render three comparisons at matched camera, lighting, resolution and material: old corner, new corner, and new corner embedded in two courses. Include final game-scale crop.
6. Technical checks on the **evaluated** mesh: manifold edge count, connected components, positive volume, normals, self-intersections where measurable, clearances, stone overlap, missing geometry and deterministic SHA/seed.
7. G1 requires checking approved house references and dimensions; if unavailable, BLOCKED. G2 requires independent visual acceptance. G4 requires integration and target-device check.

## Stop criteria
- Two failed attempts at the same large-plane fracture method => stop and compare sculpt/manual retopology or licensed scanned limestone workflow, with evidence and licensing.
- Do not overwrite original renders or manifests. Keep new candidate output and manifest separately.
- No main merge, release, canonical replacement or destructive cleanup without approval.

## QA state at authoring
G1 BLOCKED; G2 FAIL for current baseline; G3 PASS for existing CI execution only, evaluated topology NOT_RUN; G4 NOT_RUN.
