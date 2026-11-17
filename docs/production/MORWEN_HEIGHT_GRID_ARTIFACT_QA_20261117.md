# Morwen height-grid artifact QA — 2026-11-17

## Actual CI evidence
- Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43985146164 — SUCCESS.
- Artifact ID: 14284998427, ZIP verified to contain 24 files.
- 8 Blender-generated orthographic PNGs (2 candidate meshes × front/back/left/right).
- 8 SVG height-grid overlays.
- `diagnostic_renders/height_overlay_manifest.json`: `PASS_GRID_ONLY`, 8 overlays, `reviewer_confirmed: false`.
- `landmark_vertex_evidence.json`: `PASS_GEOMETRY_EVIDENCE_ONLY`, `source_unchanged: true`, `reviewer_confirmed: false`.

## Independent visual inspection (not G2 approval)
A local composite of the 8 source PNGs with the same world-Z tick calculation was inspected. Both meshes are full-body, have distinguishable front/back/left/right views, and have visible head/torso/limb silhouettes. Stylized has relatively larger head and narrower body; realistic has a relatively smaller head and broader shoulder/torso silhouette. These are qualitative observations, not approved anatomical landmarks.

**Technical limitation**: Source is 8-bit PNG and orthographic clay render; the grid is a world-Z guide, not a skull/chin or joint annotation. The montage is a derived review image, not a canonical design source. No head-count or 7.75-head fit can be concluded.

## Gate state
- G3 diagnostic geometry/render and grid generation: PASS.
- G1 3D canonical conformity: BLOCKED (landmarks and full official turnaround not approved).
- G2 artistic conformity: NOT_RUN.
- G4 game/Android: NOT_RUN.
- No source replacement, model approval, merge or publication.

## Next effective action
Have a reviewer mark chin and head-top on both real renders (front and side cross-check), then verify exact mesh vertices/surface locations in Blender before entering coordinates into the evidence-gated calculator. Do not add an automatic anatomy inference based solely on image brightness or bounds.
