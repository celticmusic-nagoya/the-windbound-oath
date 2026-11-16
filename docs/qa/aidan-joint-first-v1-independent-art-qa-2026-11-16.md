# Joint-first corner v1 — independent rendered-image QA (2026-11-16)

Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43786940632
Artifact: `aidan-joint-first-corner-v1` id `14190817441`, with front/top/three-quarter PNGs and JSON.

## Verified
- CI SUCCESS: Python compile, Blender render, structural invariants and evidence upload.
- 3 meshes watertight per audit, design-plane z difference = 0.0. **These do not prove physical face contact**.
- Independently inspected all three actual rendered images.

## Art and physical integration verdict: FAIL
- At front view, dark triangular void between the lower stones and upper bond remains, despite identical nominal z planes.
- Upper stone appears to bridge two separate beveled blocks rather than rest continuously on prepared bearing faces.
- Exposed faceted and beveled planar faces read as manufactured polygonal blocks, not weathered hand-fitted masonry.
- Top view shows uneven footprint and an obvious overhang; shape does not read as an L-corner house quoin.
- Underlying cause: shared nominal plane and closed manifold mesh are insufficient. Per-stone ring scaling bevels the physical bearing face away from the z plane and does not enforce actual shared contact polygons. The joint graph does not provide a common surface with measurable support. `joint_x_difference=0` is a design constant, not measured clearance.
- **G1 BLOCKED** (canonical dimensions), **G2 FAIL**, **G3 PARTIAL_PASS / contact FAIL**, **G4 NOT_RUN**.

## Correct next approach
Do not iterate on bevel sizes, offsets, or names. This is a method-family failure for *planar joint-first + independent silhouette rings* in this application. Move to a **shared-surface construction**: generate exact mating face polygons once, share them between adjacent stone meshes, then sculpt/distort only exterior surfaces. Compute actual polygon overlap area for bearing and explicit signed-distance/triangle intersection; preserve a continuous architectural L footprint. Add true stone relief (licensed scan-derived height/normal displacement on exposed faces) only after contact QA passes. Maintain noncanonical isolated study; no main merge.
