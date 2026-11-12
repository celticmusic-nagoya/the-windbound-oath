# MORWEN-BLENDER-06 — four-view silhouette assessment

Source: GitHub Actions run 43221473663, artifact 13944984095, reference_silhouette_diagnostics.json. Reviewed rendered front/right/back/left contact sheet.

| Facing | Raw silhouette IoU | Reference bbox width | Render bbox width | Ref foreground pixels | Render foreground pixels |
|---|---:|---:|---:|---:|---:|
| Front | 0.40388 | 319 | 347 | 155393 | 79578 |
| Right | 0.34343 | 221 | 112 | 101946 | 42702 |
| Back | 0.40254 | 317 | 347 | 157833 | 79576 |
| Left | 0.30436 | 218 | 112 | 103185 | 42703 |

## Visual observations
- Neutral candidate is composed of visibly disconnected ellipsoids. This is not a continuous humanoid surface.
- Side-view torso/limb thickness is narrow relative to full illustrated reference silhouettes.
- Front and back rendered bounding boxes touch/crop the image edge; comparison must be registered to a common center before artistic grading.
- Candidate renders have no official hair, costume, asymmetric accessories or skin design; cannot certify character likeness.
- Projection renders show neutral rig only. No facial/costume detail can be judged.

## Next implementation gates
1. Preserve reference PNG SHA and existing .blend; no overwrite.
2. Normalize camera framing, compare alpha bboxes after rigid translation and common scale, report registered IoU separately from raw IoU.
3. Build a candidate-only joined/smoothed torso and hip surface; maintain 17-bone contract and no production use.
4. Repeat independent rig deformation and four-direction render QA; conduct human artistic signoff before adoption.

Status: NUMERICAL_AND_RENDER_VISUAL_REVIEW_ONLY. ART_APPROVAL=FAIL_NOT_READY. PRODUCTION_USE=false.
