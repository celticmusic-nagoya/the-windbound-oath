# AIDAN-MATERIAL-VARIATION-01 — material art specification (candidate)

Status: PROPOSAL / NOT ART APPROVED. Does not alter canonical artwork or geometry.

## Objective
Handcrafted, lived-in Celtic-fantasy cottage. Avoid uniform blocks, random
noise for its own sake, excessive grime, or a glossy procedural look.

## Spatially conditioned variation
- Limestone: per-stone warm grey/ochre variation within a restrained palette.
  Distinct scales: coarse chipped geometry, medium mottling, fine grain.
- Moisture: darken bottom courses and sheltered wall/ground intersections,
  stronger on rain-facing surfaces; keep windows and doorway legible.
- Runoff: subtle vertical streaks beneath eaves, sills, and roof transitions;
  not every stone. Streaks must follow actual building orientation.
- Weathering: edge abrasion and occasional desaturation. Rare moss in
  damp joints, not an even green wash. Preserve the readable stone bond.
- Quoins: stronger, larger dressed stones with alternating bond; avoid
  apparent floating intersections and impossible overlaps.
- Timber: anisotropic grain along each beam's local long axis; growth rings,
  knots and end-grain on cut faces. Slightly different grain direction and
  wear per beam, not globally randomized texture rotation.
- Doors and frames: hand-contact abrasion near latch, sun fading on exposed
  faces, darker moisture at bottom edges.
- Slate: restrained per-tile color and roughness variation, subtle weathering
  according to roof pitch and water flow.

## Deterministic implementation
Use stable per-object IDs and seed 141127. Prefer shader parameters and
instances over unique large textures; keep geometry relief at the scale where
it survives the game camera. Separate weathering masks from base materials.
Do not use unlicensed external textures.

## Required validation
G1: Compare to official architectural references and protect original assets.
G2: Neutral-light material board, 3-view wall section with corner quoin,
    and game-size crop. Reject repetitive noise and visible tiling.
G3: Geometry/manifold, real door/window clearances, stable SHA, Blender 4.x
    render and resource usage. Validate deterministic per-stone variation.
G4: Check 2.5D game scale, mobile readability and frame cost.

## Implementation sequence
1. Isolated 2m x 2m wall section with corner and a timber beam.
2. Material masks driven by object ID and local orientation; compare clean
   versus aged variants under the same light.
3. Independent art QA before integration into v3 architecture.
4. No canonical overwrite, main merge or publication without approval.
