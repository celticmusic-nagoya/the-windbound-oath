# Independent visual review — MORWEN SCULPT02 (2026-11-17)

## Evidence actually reviewed
- PR #407, GitHub Actions run 44076487693, review artifact 14324029891 (retrieved).
- Render `color_contact_sheet.png` (six viewpoints, 1152×832).
- Approved source `MORWEN_DESIGN_SHEET_APPROVED_SOURCE.jpg` (1536×1024) included in the same review artifact.
- PR #407 description, including Blender GUI brush operation and technical QA claims.
This is an **independent image-level art review**, not a Blender geometry or rig inspection.

## Independent art findings (G2: FAIL)
1. **Facial identity / style — critical**: Face remains realistic and mature, with small eyes, long nose bridge and strongly anatomical jaw/cheek. Approved Morwen is a softer stylized anime face, relatively larger purple eyes and much smaller delicate nose and mouth. A minor vertex displacement cannot bridge this design mismatch.
2. **Hair mass — critical**: Despite asymmetry, the side/back silhouette is a thick continuous smooth helmet/bowl shell. Approved hair is a layered purple bob with directional strands, light breaks, a visible part/fringe and soft tapered ends. The huge unbroken side plane and blunt bottom edge are inconsistent with the official close-up.
3. **Hair roots and transitions — critical**: Forehead bangs look like thick solid petals stuck beneath a raised top plate. Distinct scalp origin, layered root-to-tip flow and side-lock attachment are not convincingly modelled. The crown cap reads as a separate broad band.
4. **Glasses and eyes — moderate**: Round gold glasses and purple iris color are directionally correct, but the eye-to-glasses ratio, eye aperture, facial expression and temple fit do not match the reference.
5. **Silhouette — moderate**: The bob has some left/right difference and six-view continuity; however volume at sides and back is disproportionately heavy and makes the head look helmeted.
6. **Positive verified image-level changes**: Six real camera views show a continuous editable candidate with visible purple hair masses and glasses; it is not a mere 2D billboard. This is meaningful technical progress but not final art acceptance.

## Required method change — not a third numerical tweak
- **Face**: establish a reference-registered anime face sculpt target; redesign orbital aperture, eyelids, midface and jaw as an interconnected local retopology. Preserve neck/body scale but do not rely on small Grab adjustments to a realistic anatomical face.
- **Hair**: remove/rebuild the broad cap and continuous bowl shell in a separate candidate; create rooted directional clumps with controlled thickness and distinct front/side/back layering, visible negative spaces, tapered edges and silhouette breakups. Avoid equal radial panels, thick petal bangs and purely painted lines.
- **QA**: review front, side, 3/4 and back at fixed matching framing against official source, plus 64/128px previews. Independently inspect actual editable topology and hair/scalp intersections before any G3 complete claim.
- Keep all rejected candidates and original files unchanged. The current GUI brush study already logged two failed art attempts; stop the same family and move to a structural redesign.

## Gates
- G1 BLOCKED: official source present but accurate landmark/face alignment not demonstrated.
- G2 **FAIL**: independent visual review.
- G3 PASS_TECHNICAL_SCREEN as reported by CI; full topology, UV, rig, intersections and deformations NOT_RUN in this independent review.
- G4 NOT_RUN.
- No formal adoption, main merge, source overwrite, deletion or publication.
