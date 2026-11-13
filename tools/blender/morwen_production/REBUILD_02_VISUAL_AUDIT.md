# MORWEN-REBUILD-02 — visual audit and topology decision gate

Status: **REVIEW / NOT PRODUCTION APPROVED**.

## Verified source
Canonical Layer 0 front/right/back/left: 7809.png, 7807.png, 7810.png, 7808.png. SHA-256 verified by MORWEN-REBUILD-01 workflow. Layer 0 shows the original character's **purple layered bob and purple eyes**, with purple-gold undergarments and thigh-high stockings. It is not the final outer costume, hat, or accessories.

## Art direction from actual reference
- Front: oval/tapered face, large violet eyes, short nose, small mouth, asymmetrically parted bangs, full layered bob. The **hair silhouette must not be used as the skull or jaw contour**.
- Profile: projecting nose, distinct chin and mouth silhouette, side locks in front of ears. Side-facing face landmarks must be independently reviewed.
- Back: hair volume and neck occlusion dominate; do not invent unseen back-of-skull landmarks.
- Symmetry: keep costume/accessory asymmetry and avoid reflecting left into right.

## Production decision
**STOP** arbitrary percentage-based jaw taper iterations. Existing VRoid skin-only shape key and 34-component diagnostic remain QA assets, not the adopted Morwen head. Existing face component IDs alone cannot establish anatomical fit.

**NEXT**: create *explicitly provisional* landmark overlays on the canonical front and profile images; independently review eyes/nose/mouth/chin and face outline. Use matched orthographic camera and scale to compare candidate 3D projections. Record pixel and normalized coordinates with visibility/occlusion flags. Once reviewed, decide which mesh regions can be reused and which need new topology. Do not approve any face shape before a visually grounded silhouette review.

## Gates
G1 canonical source hash: PASS. G2 geometry fidelity: NOT YET TESTED. G3 current pipeline: PASS as of run 43434828918. G4 NOT RUN. No main merge or production asset replacement.
