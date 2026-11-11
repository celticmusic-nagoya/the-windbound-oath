# MORWEN FIX-03 — Back R1 measured technical QA (2026-11-11)

Source (local candidate, **not yet registered as a PNG in GitHub**): `morwen_back_fix03_candidate_r1_1200x1600.png`
SHA-256: `de68bea7cdc4d2f56270a3b194f53b56d804518a9c1257c02e08680c3b13c33d`

## Measured
- Canvas: **1200x1600 RGBA — PASS**
- Alpha >32 bounding box: **x244..946, y13..1534**.
- Opaque alpha=255 pixels: **1,340 / 608,593 nonzero-alpha pixels**. Alpha=254: **59,741**; alpha 1..253: **547,512**. Transparency exists, but widespread partial alpha requires visual display QA.
- R2.1 ground reference: **(600,1540)**. At y1540, **0 pixels alpha >32**; at y1539, **0 pixels alpha >32**. **Exact contact-anchor PASS is not supported**. Ground/sole alignment needs correction or explicit anchor convention reconciliation.
- R2.1 back anatomical target landmarks: shoulder row y430, elbow y600, wrist y786. The joints are occluded by clothing; their true positions **cannot be verified from bounding-box analysis alone**.

## Status
- Technical canvas PASS; ground-anchor **FAIL / requires correction**; alpha rendering **PASS_WITH_CONCERNS**.
- Skeleton comparison **NOT_RUN**; original 4-direction PNG pixel comparison **BLOCKED (original files not available in the image-processing runtime)**; independent art QA **NOT_RUN**.
- Existing candidate PNG has **not been changed**. No original assets overwritten, no production merge or publish.

## Next action
Obtain the original back/front/right/left PNGs in the same processing environment, compare scale and landmarks, and apply only the verified fixes to a new back PNG candidate. Do not regenerate overview sheets or blindly normalize alpha.
