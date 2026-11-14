# Professional environment modeling workflow — Rilde / Aidan (candidate)

Status: PRODUCTION PROCESS PROPOSAL; not a replacement of canonical art, not G2 approval.

## Principle
**Control cage / construction skeleton first, then topology by silhouette and deformation/curvature need, then UV/PBR, then camera-distance QA.** Vertex count alone is not a quality metric. Add loops to curved or silhouette-critical masonry, slate chips and timber irregularity; use texture normal/roughness for subpixel cracks. Preserve consistent coordinate units, anchors, scale, seed and provenance.

## Modeling structure
1. **Reference and canon**: protect approved Rilde village CG, blue-gray slate roof, 25–30° game view; resolve proposed house dimensions/entrance as candidates.
2. **Structural skeleton**: foundation footprint and terrain contact; wall corners/height; load-bearing timbers and roof ridge/eaves, rafters, gables; openings and lintels; chimney, gutters and drainage; prop and collision anchors. Export named control vertices and dimensions as JSON. All derived meshes reference these controls, not independent hand-entered coordinates.
3. **Primary geometry**: continuous watertight wall/roof substrate, stone wall modules with nonuniform silhouette, correctly pitched slate courses and positive overlap, fascia, roof edge termination. Avoid coplanar faces and mesh intersections. Verify normals and manifold status for relevant closed pieces.
4. **Secondary detail**: stone edge relief, selective chipped slate silhouettes, carved wood, trim, windows and door frames, roof ridge. Use bevels with controlled widths and weighted normals on hard surfaces; apply subdivision only where curvature justifies it.
5. **Surface**: UV unwrap, real CC0 PBR material maps with recorded source/hash/license; correct texel density, tiling scale and roughness. No placeholder flat colors as finished material.
6. **Game output**: 27° orthographic plus 4 directions, final-size previews (290px and 384px), neutral clay render and PBR render, shadow/occlusion review, texture compression and runtime budget. Keep high-detail master and optimized game variant separate.

## Quality/geometry acceptance
- G1: skeleton and visible geometry conform to approved design and do not invent unapproved lore.
- G2: roof reads as layered slate at target size; no repetitive strip pattern, identical chimney stones or flat roof tiles; strong silhouette and appropriate weathering.
- G3: 5 PNGs + .blend + manifest with SHA-256, Blender version, seed, mesh/vertex/face counts; nonzero surface clearance; UV presence and no degenerate polygons. Compare source vs generated coordinates.
- G4: no runtime changes until G1–G3 pass; assess sprite readability, Android performance, collision, and SAVE separately.

## Lessons and references
- Blender manual, Bevel Modifier (non-destructive edge control): https://docs.blender.org/manual/en/4.0/modeling/modifiers/generate/bevel.html
- Blender manual, Weighted Normal Modifier: https://docs.staging.blender.org/manual/en/latest/modeling/modifiers/normals/weighted_normal.html
- Blender Studio modeling handoff checklist: https://projects.blender.org/zanqdo/blender-studio-tools/src/branch/main/docs/artist-guide/asset-creation/modeling.md
- Unreal Nanite technical documentation, shared mesh boundary precision and geometry trimming: https://dev.epicgames.com/documentation/unreal-engine/nanite-technical-details

**Do not transfer Nanite-specific assumptions to this browser RPG.** High-density source geometry is acceptable for offline baking, but game deliverables need measured budgets and final-resolution QA.

## Current state
- v1 geometry QA passed CI but G2 art QA failed (flat banding).
- v2 vertex-first source and renderer added; CI run #5 failed due to workflow mistakenly invoking v1 renderer. Workflow corrected on branch. New run and image inspection pending.
- All source work is on Draft PR #311. No main merge or production replacement.
