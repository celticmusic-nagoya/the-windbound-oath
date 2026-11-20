# MAP-VEG-01 — vegetation master production brief
Status: CANDIDATE WORK ORDER / G1 BLOCKED pending comparison with latest private canonical references and existing map assets. No accepted designs replaced.

## Goal
Create a reusable, high-quality, modular vegetation pack for the village, grassland and forest. First asset family: temperate meadow grass clumps; next fern, low broadleaf and wildflower only after master material/scale/display validation. Do not infer plant species as canonical.

## Art direction
Natural irregular silhouette, believable leaf/stem thickness and bend, distinct height/width variations, clustered growth (not radial clone repetition), subtle green/ochre variation and physically coherent root contact. Realistic organic topology; no box/flat-green placeholder accepted as finished art. Compare to approved map perspective, ground palette and V11 cottage mood where relevant. VFX optional only after geometry/material quality is approved.

## Deliverable contract
- Blender 4.2.3 pinned; script, seed, source and license hashes; .blend, .glb where appropriate.
- Neutral and warm lighting render, front/side/top/isometric views, 48px and 96px previews on representative game ground.
- Alpha correctness and silhouette inspection, UV/material consistency, object bounds, triangle counts, missing textures and transparency/overdraw risk.
- Explicit G1/G2/G3/G4 statuses, independent G2 reviewer, Android G4 NOT_RUN until actual device QA.
- Geometry Nodes/modular mesh recommended for repeatable variation; image/texture generation is a candidate source only, not proof of suitable 3D geometry.
- No commercial/restricted reference assets without documented license.
- Save all outputs under assets/candidates/map-veg-01/; no edits to accepted map assets.

## First production package
A. Reference audit: identify official map style, game camera, sprite display size, accepted ground texture, and existing flora to avoid duplicates. Mark missing facts BLOCKED.
B. One finished-quality meadow grass family: 3 distinct clumps from shared validated generator, not 3 low-quality prototypes.
C. G3: geometry, UV, alpha, transparent crop, deterministic generation and SHA256.
D. Independent G2 review of actual renders at native 48/96px and full size. FAIL means stop adoption, record cause and structural correction.
E. Only after PASS, scale to fern/flower/rocks in separate packages.

## Parallel boundaries
ART-02 masonry PR #331 remains independent. No edits to character files. Codex independent QA should inspect artifacts rather than trust producer's manifest. Claude/other AI session requires explicit connection/launch; this brief alone does not launch it.

## Gate definitions
G1 BLOCKED until latest canon and map camera/ground references verified.
G2 NOT_RUN until renders are produced and independently reviewed.
G3 NOT_RUN until Blender generation and checks run.
G4 NOT_RUN until integrated game/device test.
