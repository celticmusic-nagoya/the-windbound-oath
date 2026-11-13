# MORWEN-FACE-20 — Face art direction and acceptance criteria

Status: ART DESIGN / NOT PRODUCTION APPROVED

## Immutable source
Morwen Layer 0 official four-view PNGs in `tools/blender/production_mesh_08/references/`. Preserve original bytes and SHA-256. Current VRoid Base_Female is an isolated CC0 candidate, not Morwen.

## What the latest render proves
The Shape Key experiment and orthographic renders run in Blender CI. A 5.5% lower-face taper is **not** evidence of canonical fidelity. Do not repeatedly change taper percentages without annotated facial landmarks.

## Next production-oriented mesh steps
1. Separate and label source Face components by actual mesh indices and visual inspection (skin, sclera, irises, lids, brows, mouth). Material names are only hints.
2. Record canonical front/profile landmarks with manually reviewed coordinates and confidence; do not silently derive them from alpha bounds. Store annotations separately from canonical PNGs.
3. Establish face and jaw target silhouettes with reference-aligned orthographic views; check head-to-body scale and neck attachment.
4. Implement a controllable non-destructive facial adaptation rig/shape keys for jaw, cheeks, eyelids, eyes, nose and mouth. Do not modify detached eye/mouth islands with generic jaw transforms.
5. Model layered purple bob hair, fine gold spectacles and asymmetrical headwear as independent authored meshes only after face direction is approved.
6. Render at actual game-display size and evaluate front/right/left/three-quarter, expressions and deformation.

## QA gates
G1 canonical silhouette and anatomy landmarks signed off; G2 artistic quality from actual render review; G3 watertight/deformation topology where needed, transparent PNG, dimensions, performance; G4 in-game display and Android performance. Keep all experimental results labelled CANDIDATE. No main merge or production asset replacement.

## Third-party sourcing
A higher-quality legally usable base may replace the candidate if licensing, topology, rig and art compatibility reduce total work. Do not import recognizable Vocaloid/Vtuber character IP without rights to commercial derivative game use.
