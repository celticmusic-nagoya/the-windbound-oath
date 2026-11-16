# AIDAN-MASONRY — hybrid production gate / stop repeating failed renders (2026-11-16)

## Evidence / baseline
- Earlier Boolean-chip / rectangular stone approach: G2 FAIL (silhouette remains boxlike; chips/bevels too small).
- Broad-plane horizontal-ring v1: run 43781482098, Blender PASS, art G2 FAIL; horizontal belts, repeated courses, exposed rectangular backing. SHA 4890eb7e0b1674be192e3c8615543c3bceea2071f80343befc3a537562b619cd.
- Facet v2: new geometry experiment only, NOT art-approved. Do not repeat v2 with merely new seeds, material tint, small bevel, or microdisplacement if G2 fails. Await run and inspect actual PNG first.
- Environment issue libEGL.so.1: fixed by installing libegl1 and graphics runtime; subsequent Blender run succeeded. Do not conflate environment PASS with G2.

## Hybrid method — binding implementation decision
1. **Primary silhouette:** reference-guided, manually art-directed stone meshes OR independently verified licensed CC0 photogrammetry/stone meshes. Preserve uneven large break planes, course variation and credible corners. Do NOT rely on procedurally perturbing a cube/ring to reach final quality.
2. **Construction grammar:** author a small corner module with individually editable stones and plausible joints; verify adjacent stones, hidden backing, windows/door interfaces, and non-identical courses before mass instancing. Geometry Nodes for distribution/assembly only, not for manufacturing the sculpt quality. Use per-segment modules to preserve corner control.
3. **Surface:** add verified CC0 stone/plaster PBR (basecolor, normal, roughness, displacement) with recorded source URL/license/hash; render 2.5D final-size preview. Shader/normal alone cannot fix silhouette. Avoid copying Pinterest photos or X posts as unlicensed texture assets.
4. **Detail:** decals/floater for localized weathering, moss, chips only after large-form art PASS; use Blender-compatible non-destructive method in headless CI. Keep each candidate distinct from canonical source.
5. **Art gate before expansion:** compare silhouette (flat material), lit shaded view, game-size crop against the same reference/camera. Stop if stone edges still read as stacked blocks, repetitive strips, visible fixture, or obvious floating/gaps. Require independent G2 PASS before generating a full house.
6. **Technical gates:** watertightness, normals, object intersections/clearance, geometry validity, reproducibility (seed/Blender version), asset licenses, SHA, render size, Android performance separately.
7. **Fail stop:** max two effective fixes per same root cause. Prior Boolean-chip and horizontal-ring families have already failed visually; do not return to them. Facet v2 gets one independent evaluation; if FAIL, switch to curated CC0 scan or manually sculpted master stone rather than generate v3 random faceted cubes.

## External technical references (research, not incorporated assets)
- Poly Haven photogrammetry workflow: https://polyhaven.com/learn/photogrammetry (capture -> cleanup -> retopo -> bake -> game-ready; CC0 course files).
- Poly Haven stone/plaster PBR example: https://polyhaven.com/a/plaster_stone_wall_02 (CC0; not yet acquired).
- Parametric Rhine castle masonry: https://www.mdpi.com/2571-9408/8/1/31 (Geometry Nodes, per-segment stones, corner limitation of naive curve-deform method).
- Blender Studio bake workflow: https://studio.blender.org/training/realistic-human-research/baking/ (baking technique; not a ready-to-use stone asset).
- Decal technique: https://extensions.blender.org/add-ons/bam-decalit/ (optional; not installed, no license/compatibility approval assumed).
- User-provided https://x.com/ymt3d (reference to assess per technique; no unverified claims about its content or license).

## Current QA
G1 BLOCKED; G2 FAIL for previous approaches, v2 NOT_RUN pending actual render; G3 prior ring PARTIAL_PASS, v2 NOT_RUN; G4 NOT_RUN.
No main merge, no canon replacement, no publication.
