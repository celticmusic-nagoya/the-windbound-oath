# Morwen Blender 5.3 face-surface study — independent visual QA (2026-11-20)

## Provenance
- Workflow https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44627244607 — SUCCESS.
- Artifact 14579068540 (morwen-530-new-face-surface-study-unapproved), digest sha256:ccbae431478add49b75f9a264bab770eef1b9d05f22c53d82f63d5fcdad015bf.
- Blender 5.3.0, 5,525 vertices / 5,376 quads; source `tools/morwen_authored_sculpt/build_face_surface_530.py`.
- Editable `morwen_face_surface_530_candidate.blend`, actual `face_front.png`, `face_right.png`, `face_three_quarter.png`, `qa.json` verified from artifact.

## Visual findings
- Front: near-rectangular slab/oval mask with planar cut top and bottom, no cranium, ears, eyelids, eyeballs or neck. Eye areas are faint depressions, nose is an isolated sharp dark bump, mouth almost absent.
- Side: thin vertical slab with protruding nose and lip profile, not an anatomically continuous three-dimensional head. Three-quarter is likewise flat and expressionless.
- Cannot match approved Morwen Layer 0 four-view design or professional game-character sculpt standard. Image-plane face is not an acceptable substitute for complete head geometry.
- **G1 PARTIAL** (official refs present, actual silhouette mismatch); **G2 FAIL**; **G3 PARTIAL PASS** (real editable mesh, Blender 5.3 render and reopen; open back and no complete topology); **G4 NOT_RUN**.
- Stop this flat facial quad-grid method. Do not tweak minor displacement parameters or rerender it as a production candidate. Combined with prior ring and voxel failures, future method must be truly 3D art-directed sculpt / validated neutral anatomical sculpt base, not another parametric mask. HairHarpy remains independent hair-only tool; actual execution NOT_RUN.
- No formal adoption, main merge or source overwrite.
