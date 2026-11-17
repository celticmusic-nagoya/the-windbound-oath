# LIND CC0 Rock Candidates — Visual Review (2026-11-17)

## Verified input
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44068824053
- Actual Workbench PNGs: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44068824053/artifacts/14321452746
- Parallel independent automated evidence QA: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44069687005 (provenance, geometry, render all PASS).
- Geometry inspection: Rock Face 01 = 11,106 vertices / 20,174 faces; Boulder 01 = 67,042 vertices / 66,122 faces.
- These are isolated candidates, **not** integrated into the cliff.

## Human-style visual inspection of actual 1100x760 Workbench renders
### rock_face_01
- Distinct stratified surface and irregular chipped edges are visible.
- Overall shape resembles a thin, rectangular exposed slab/rock-face fragment rather than a complete landform.
- A prominent long diagonal fissure crosses the upper half. Its suitability for a particular location requires composition review.
- Likely role: isolated exposed cliff face insert after authored support/terrain transition, not a terrain/collider replacement.

### boulder_01
- Jagged, fractured rock mass with high-frequency broken surfaces and varied large forms.
- At the captured angle, the lower-left region shows planar, relatively flat facets and the silhouette is not uniformly rounded.
- Likely role: occasional foreground or cliff-foot accent, subject to scale and contact/occlusion review.
- Higher mesh cost requires target LOD/texture budget before production use.

## Gate assessment
- G1 BLOCKED: official placement, size, terrain continuity and camera relation not approved.
- G2 candidate geometry reference: reviewable; **production cliff FAIL / NOT ACCEPTED**. Workbench screenshots cannot verify PBR, seams, backfaces, or game camera.
- G3 automated evidence (source/geometry/png): PASS. Full topology, UV, PBR and runtime budgets: NOT_RUN.
- G4 NOT_RUN: no WebGL/Android integration or real device QA.

## Next work, bounded
1. Render material-lit views from actual imported PBR assets, check missing textures and normals; no procedural cliff shell generation.
2. Make two or three carefully chosen placement candidates in an isolated Blender scene with terrain support, preserving the original scanned rock geometry and source hashes.
3. Independently assess seam concealment, geological continuity, silhouette, ground contact, performance and camera composition.
4. Reject candidates that reintroduce ring extrusion, repetition, clipping or flat slab appearance. No main merge.
