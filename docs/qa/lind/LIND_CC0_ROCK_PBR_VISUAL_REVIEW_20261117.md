# LIND CC0 rock candidates — independent PBR visual review (2026-11-17)

## Evidence and scope
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44100054813 — SUCCESS.
- Artifact: `lind-cc0-rock-pbr-lit-previews`, ID `14335167900`.
- Source candidate status: Poly Haven CC0, DOWNLOADED_UNREVIEWED; **not** a production-approved LIND cliff.
- Visual evidence reviewed: `rock_face_01_PBR_lit_preview.png` SHA-256 `fe053c1942149525c726f4f43d91796d8aee9e7e5037c298955ab8c2416f83a0`; `boulder_01_PBR_lit_preview.png` SHA-256 `f3132d25f3736e25db02d3fee5aef1aaedb369636129e32c6c40e1e491e339cd`.
- Both rendered with Cycles, 1100x760, 24 samples, no OpenImageDenoiser (unavailable in pinned Ubuntu Blender build). PBR diffuse/normal/ARM images 1024x1024 SHA-verified in `candidate_pbr_report.json`.
- Reviewed **actual PNGs**, not a source-library thumbnail. This is a candidate-level visual inspection only. The official LIND source CG was **not overlaid or directly compared in this review**.

## Independent visual findings
| Candidate | Positive evidence | Limitation | Decision |
| --- | --- | --- | --- |
| rock_face_01 | Visible stratification, overhang, fractured surface, localized moss and material color variation | Thin, slab-like outline; straight-ish exposed borders; no terrain join, rear volume or repeated-tile seam validation | KEEP_AS_CLIFF_FACE_INSERT_CANDIDATE; **not** a complete cliff |
| boulder_01 | Fractured silhouette, layered relief and rough PBR response | No ground contact, occlusion or mobile polygon budget verified; rock alone does not establish geographic structure | KEEP_AS_BOULDER_CANDIDATE; **not** approved game geometry |

## Causal next method (not the failed primitive stacking)
- **WORLD owns** the contiguous terrain/cliff mass and navigable top surface; do not fabricate approved coordinates, elevations, footprints or camera from the illustrative CG.
- Evaluate a continuous, sculpted/heightfield-supported **host terrain** with irregular cutaway, and place the verified `rock_face_01` scan only as localized exposed bedrock; avoid repeating slabs, box masonry, radial skirts or voxel blocks.
- For physical integration, independently verify front/back volume, silhouette at multiple viewpoints, watertight/overlap seams, material blending and slope/ground contacts. Reserve `boulder_01` for isolated outcrops where mobile LOD/normal-bake budget is feasible.
- Require authorized LIND source CG SHA `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620` and **approved metric/camera contract** before any official placement.
- Produce a separate editable `.blend`, wide/close/final-display renders, mesh statistics, UV/normal/seam checks and SHA manifest for any future candidate assembly. No main integration before G1–G4 PASS.

## Quality gates
- **G1 BLOCKED:** approved source reference SHA known; physical metric, location, camera and full CG composition not validated.
- **G2 FAIL for production adoption of either as a finished cliff**; candidate surface visual inspection completed, LIND art-direction match NOT_RUN.
- **G3 PASS limited to standalone PBR image loading and real Cycles render**; integrated mesh, mobile LOD, UV seam and collision QA NOT_RUN.
- **G4 NOT_RUN:** no game/Android integration, runtime or regression checks.
- This review changes **documentation only**. No model, source, runtime, character, official asset, or main changes.
