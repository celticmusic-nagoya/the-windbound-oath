# MORWEN FIX-03 — Director decisions and rebuild specification

Status: APPROVED DIRECTION / ARTWORK NOT YET PRODUCED
Source: FIX-02 report commit a204fe679d07bd454c0e24f9aa6705f0f313b974, Draft PR #221.

## Decisions
1. Rebuild the back-view upper body against the front-view anatomical landmarks; do not use simple translation, stretching or warping. Preserve approved design and untouched originals.
2. Resolve the back arm/robe occlusion anatomically: robe edges overlap sleeves naturally; visible hands and cuffs must remain coherent. Do not invent hidden side slits solely to explain the current mismatch.
3. Align hat vertical position and overall stature to the front reference. Differences of 14–20px are targets for correction, not accepted tolerances.
4. Accept FIX-01 boot-length correction as the approved candidate baseline, subject to final visual regression of the rebuilt asset. This does not promote the entire back-view artwork to official status.
5. Keep HD pixel-art production BLOCKED until four-view independent QA and director approval.

## Required workflow (base-body-first policy)
- Extract and document anatomical construction landmarks from front; reconstruct matching back shoulder, pelvis, elbows, wrists, legs and ground contact before clothing.
- Compare front/back/left/right on the 1200x1600 aligned canvas; ground anchor (600,1540). Use one coordinate convention, document pose differences and uncertainties.
- Rebuild back hair ending approximately 45–55px higher, shoulder/cape approximately 48px higher, upper arms anatomically longer, preserving cuffs and bag strap. These are reported diagnostic deltas, NOT instructions for literal pixel stretching; derive final placement from locked base body.
- Align hat and ornament height, retain green flower leaves, gold laurel trim, approved purple bob and glasses, academy emblem, crossbody bag, rear robe central slit, plain-base skirt with asymmetric character-right check detail, visible rear garter ornaments, dramatic side robe tails near heel level.
- Maintain separate source, edit masks, candidate, measurements, preview, QA report, SHA-256 manifest and machine/independent visual QA. Revalidate revised masks; previous revision NOT_RUN.
- Check transparent background alpha=0 outside subject, color match (including back skin), hair, shoulder, arm/cape overlap, skirt, boots and grounding. Do not assert visual PASS without actual inspection.
- New assets must be added to work branch and Draft PR #221; preserve existing originals, no main merge or publication.

## Acceptance gates
BASE-BODY QA PASS -> COSTUME/STRUCTURE QA PASS -> INDEPENDENT VISUAL QA PASS -> DIRECTOR APPROVAL. Until then status BLOCKED; Android NOT_RUN unless actually tested.
