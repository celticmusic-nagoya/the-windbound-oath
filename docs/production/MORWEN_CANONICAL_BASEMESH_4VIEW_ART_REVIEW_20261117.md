# Morwen — canonical vs CC0 basemesh, four-view visual review (2026-11-17)

## Verified sources
- Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44035887651 — SUCCESS.
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44035887651/artifacts/14306278820
- Output: `canonical_vs_basemesh_4views.png` (4 rows x 3 columns) and `comparison_manifest.json`.
- Canonical source: `assets/canonical/morwen/2026-11-16/MANIFEST.json`; four Layer0 images SHA-256 verified. Neutral CC0 candidate renders reused from run 44032196306.
- **Important:** Each panel independently crops alpha and auto-fits the image. This is a *visual silhouette comparison*, not a calibrated physical scale or head-ratio measurement.

## Review
- **Preferred starting candidate: GEO-body_female_realistic**, for a new isolated Morwen-specific editable candidate. This is not a production approval.
- Stylized has visibly exaggerated head/ears and simplified limb/body proportions compared with the approved front/back/profile references.
- Realistic still differs in face/eyes/jaw, shoulders, waist, hips and leg silhouette. The pose/arm spread differs from the approved Layer0 references, preventing naive pixel silhouette scoring.
- Both candidate meshes lack canonical hair, costume, asymmetric details, textures and rig. The Layer0 reference set shows hair silhouette, decorative undergarments and thigh-high stockings, and a right-leg garter visible from behind; these must be designed as separate later layers. No reference design is to be copied from other games.
- No anatomical head/chin/sole landmarks have been reviewer-confirmed; **do not claim an actual 7.5–8 head match**.
- A head-to-toe morphological match requires a new editable 3D candidate, fixed view transforms, pose normalization, and independent artistic QA. The current comparison does not establish that.

## Gate
- G0 canonical four-image SHA: PASS.
- G1 Morwen-specific full-body silhouette: FAIL for both unmodified CC0 candidates; canonical integration BLOCKED.
- G2 finished character art: NOT_RUN.
- G3 existing neutral render and image comparison: PASS diagnostic only; Morwen model topology/rig NOT_RUN.
- G4 in-game/Android: NOT_RUN.

## Next production step and stop conditions
1. In an isolated branch/output, create **a genuinely editable Blender candidate** from the realistic CC0 source. Preserve source .blend and canonical images byte-for-byte; record both SHA-256 hashes.
2. Design geometry deformation against front/back/left/right canonical silhouette using a common orthographic projection, matched pose, and explicit 7.5–8 head target. No unreviewed chin coordinates as a gate bypass.
3. Save candidate .blend, four renders, parameter manifest, and compare with the canonical reference. Do not treat primitive proxies or neutral reference renders as finished Morwen geometry.
4. Stop after two ineffective attempts for the same failure cause; do not start hair/detail layers before G1/G2 body silhouette review.
5. No main merge, canonical overwrite, publication, or formal adoption without approval.
