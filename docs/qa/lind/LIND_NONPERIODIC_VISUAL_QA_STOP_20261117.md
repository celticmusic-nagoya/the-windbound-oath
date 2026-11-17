# LIND nonperiodic cliff candidate — visual QA / STOP (2026-11-17)

## Immutable evidence
- Draft PR #389: https://github.com/celticmusic-nagoya/the-windbound-oath/pull/389
- Successful Blender render run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44034184640
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44034184640/artifacts/14306388313
- Render PNG: `lind_macro_technical_clay.png`; SHA-256 `f6bee270b9e298901c665357aa0a46d2112a30322b83cfaff9c1cc37e97c226b`
- Topology: 5,670 vertices, 5,668 faces, one connected component, 0 boundary/nonmanifold edges, 0 orientation conflicts, 0 degenerate triangles, positive signed volume 4.260589266691341.
- Geometry is NONMETRIC, NONCANONICAL, reference-only.

## Independent image review
G2 **FAIL**. Upper surface remains implausibly smooth; diagonal crest-to-wall grooves appear as repeated strips; terminal sides are abruptly sliced; no rocky fractures, soil/turf interface or coherent local scan detail. Nonperiodic control points did not solve the underlying artificial procedural silhouette problem.

## Decision: STOP
Do **not** adjust notch amplitudes, control-point count, mesh resolution, random seeds, or shaders to repeat this method. Existing periodic macro also failed G2; do not reclassify either as production asset. Next method is source-scan-led *surface construction and authored terrain transitions*, not another pure profile loft.

## New method acceptance gate
1. Protect publisher scan SHA and original UVs, and distinguish source reference from authorized derivative.
2. First define the usable scan interior and artist-designed nonrectangular termination/transition. Do not repeat blind boundary erosion or global voxel remesh/decimation.
3. Render three real views of the proposed *scan-led* surface before any claim of integration; require independent G2 review.
4. Model separate terrain support and collider with connected oriented manifold QA; no unsupported world placement or scale.
5. Validate PBR, UVs, seams, turf/soil contact, performance and game-size visual quality before adoption.

G1 BLOCKED; G2 FAIL; G3 PASS for isolated topology/import/render only; G4 NOT_RUN.
No changes to official assets, main, or published content.
