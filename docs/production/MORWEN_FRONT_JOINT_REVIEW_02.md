# MORWEN FRONT JOINT REVIEW 02 — anatomical sanity check
Date: 2026-11-16
Status: TENTATIVE MARKERS REVIEWED / NOT APPROVED AS SKELETAL JOINTS / 3D FRONT ART NOT GENERATED

## Evidence
Reviewed the actual local `MORWEN_FRONT_JOINT_CANDIDATE_01.png` annotation image (950×1090) and its legend. It displays a source Layer 0 front silhouette with estimated source-coordinate y values. The cyan dots are manual guesses, not measured joints. This annotation PNG is not committed to this PR; no GitHub image-byte provenance is claimed.

## Review
- Hair crown y≈17, chin y≈178±4, floor y≈1003: approximate landmarks from prior audit. Source vertical extent ~986px; head height estimate ~161px, yielding ~6.12 heads, not 7.75.
- To represent 7.75 heads **at the same total pixel height**, target head height is ~986/7.75=127.23px. This is a **dimensioning constraint**, not permission to shrink only the head. Entire shoulder/torso/pelvis/leg proportions need coherent redesign.
- Shoulder markers y≈257, bust markers y≈330, elbow y≈419, wrist y≈537, hip y≈527, knee y≈766, ankle y≈964 are **unverified visual guesses**.
- The cyan 'bust' markers are located on visible garment/bust contours, **not** verified skeletal joint centers. Do not use them as rig bone joints.
- Wrist and hip points are not anatomical equivalents; the overlapping source y values do not prove correct arm/hip proportions.
- Knee dots on a stocking silhouette are insufficient to locate knee rotation centers; ankle dots likewise require skeletal/deformation review.
- The user-approved garter is on the character's anatomical right leg (front screen-left), and its rear continuation must be preserved in future orthographic views.

## Fail-closed decision
- The prior front-only spec `docs/production/MORWEN_FRONT_ONLY_01_SPEC.json` must retain `landmarks_reviewed_by_artist=false` until independent qualified anatomy/character-art review. Never flip it to bypass the preflight.
- The current evidence is sufficient to design a **measurement scaffold** and identify risks, but insufficient to certify precise joint coordinates or start production-quality front illustration as an accurate orthographic source.
- G1 new turnaround NOT_RUN; G2 new turnaround NOT_RUN; G3 image annotation PARTIAL; G4 NOT_RUN.
- Exhausted method `unconstrained-composite-image-generation` remains STOPPED (V1.0 and V1.1 same-root failures).

## Next controlled task
Create a separate, noncanonical **7.75-head proportional measurement scaffold** (one FRONT view only) with head-size ruler and proposed joint zones/ranges, not hardcoded joint centers. Require an anatomy artist to annotate/review shoulder, elbow, wrist, pelvis, knee and ankle centers. Use the 2026-11-16 five-source reference set for appearance, not the candidate annotation for exact anatomy. Only after review and passing front-only preflight may a new single-view illustration be produced.
