# MAP-BLENDER-17 — composition-first redesign specification (DRAFT)

Status: DESIGN_ONLY / NOT_RENDERED / NOT_CANON

## Evidence
MAP-16 Actions #43245437729 succeeded, 9/9 sampled rays blocked.
Visual inspection of rilde_map16_preview.png: the oversized ridge dominates the village; rock patches are square polygon blocks; village buildings are evenly spaced; bridge and river are simple planar placeholders.

## Reference principles (no copying of third-party assets)
- Octopath Traveler II: atmospheric light, layered silhouettes, legible foreground/midground/background.
- Triangle Strategy: coherent isometric village composition and readable traversal routes.
- Dragon Quest XI: varied building silhouettes and contextual village props.

## Structural change before additional detail
1. Replace the monolithic ridge with 2–3 lower overlapping landforms; vary silhouette at multiple scales. No new decorative meshes until skyline and routes pass visual QA.
2. Preserve coastal Windwatch Cliff (west-northwest), separate SW fishing inlet, eastern river and bridge, north road to Dunvar, SE Moss Forest.
3. Establish an explicit player route graph (village square -> north road / eastern bridge / SW inlet / Windwatch path). Keep clear traversable corridors.
4. Introduce village districts: irregular central square, clustered homes, garden plots, waterfront access. Avoid a uniform building grid.
5. Replace polygon-index stone patches with slope/height-driven procedural material blending (noise in world coordinates, not per-face checkerboard).
6. Verify event sightlines using actual cliff and village coordinates and cinematic camera frusta; the 9 synthetic rays are regression checks only.
7. Keep runtime and original MAP08–16 blend assets untouched. Produce a new draft candidate and image comparison before acceptance.

## Acceptance gates
- Structural QA: routes connected; river crossing at bridge; sea cliff distinct from riverbank escape cliff.
- Occlusion: representative event camera views cannot see village fire until the final large return-road bend.
- Art QA: no giant single-colored berm, polygon checker patches, floating roads, or visibly rectangular terrain boundaries.
- Gameplay QA: 390px Android viewport keeps protagonist, collision obstacles, and interactable entrances distinguishable.
- Regression: SHA chain passes; MAP15/16 files unchanged.

No main merge, no publication, no canonical map replacement.
