# MORWEN-BLENDER-21 QA

Technical QA: **PASS**. Run 43248559535 and BLENDER-01 regression run 43248559909 both PASS. Artifact 13958102021 contains `torso_candidate_segments.json`.

The four canonical reference PNGs were SHA-checked and their central alpha spans were sampled at chest, waist, pelvis and intervening heights. This identifies **review-only alpha-connected segments**, not anatomical torso contours. Arm overlap, costume and hair can still influence the spans; the automated segmentation is not independent art approval.

Next: inspect per-view candidates against the actual canonical images, mark body/costume ambiguity, create a human-reviewable mask or tracing contract before altering mesh proportions. No main merge, official design modification, or publication.
