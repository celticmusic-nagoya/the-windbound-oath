# LIND scan-led irregular surface — independent visual QA (2026-11-17)

## Verified execution and exact evidence
- Draft PR #391: https://github.com/celticmusic-nagoya/the-windbound-oath/pull/391
- Blender Actions success: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44036452900
- Artifact ID 14307148684: `scan_led_irregular_surface.blend`, `scan_led_irregular_surface.png`, `scan_led_manifest.json`, `blender.log`
- PNG SHA-256: `bc55bc215e7264aa97ef42a6e2cef8c6b41671d1c29c16eefd63bbc4081bf8c4` (locally rechecked)
- Original patch .blend SHA-256: `8c86b29c1d28c0aad0a5a07873ce40c5ff3b64b18c8d64819bd98151c5a7781a` (Actions checked)
- Scan-led surface: 16,676 original source faces of 86,764 source-patch faces, 21 other islands discarded, 462 open boundary edges, UVs retained. Explicitly open, not a collider.

## Independent image assessment
- **PASS as a rock-detail reference**: scanned fractures, undercuts, uneven strata and granular silhouette read materially more natural than periodic/nonperiodic loft candidates.
- **FAIL as complete cliff**: abrupt lower boundary, thin disconnected-looking hanging shards at termination, no continuous rock-to-earth/grass transition, no authored terrain silhouette or approved placement. Current Workbench gray render does not establish PBR or game-camera quality.
- The visible upper portion is detailed but reads as a cropped rock surface, not an integrated cliff/terrain structure.

## Next stage — stop unsafe shortcuts
1. Preserve original publisher mesh, texture UVs, and source hash. Do not use global voxel remesh, global decimation, or blind erosion (already failed).
2. Design *explicit local edge termination* with rock buttresses and transitional soil/turf mesh; do not pretend deleting triangles repairs topology. Avoid introducing false watertight claims.
3. Build separate stable support/collision mesh with verified oriented manifold and independent authored transition to scan dressing.
4. Produce front/oblique/top Blender views with scan PBR and independent G2; inspect the boundary at game display size.
5. Gate final adoption on official dimensions/placement, independent G1–G4 PASS and Android/WebGL QA.

## Gate results
- G1 **BLOCKED** (official scale, spatial placement, canonical scene not approved)
- G2 **FAIL** as production cliff; **PASS** only as rock-detail source reference
- G3 **PARTIAL PASS** for scan preservation, render, SHA; **FAIL/NOT_RUN** for production topology/collider/PBR/game integration
- G4 **NOT_RUN**
- No main merge, publication or official asset replacement.
