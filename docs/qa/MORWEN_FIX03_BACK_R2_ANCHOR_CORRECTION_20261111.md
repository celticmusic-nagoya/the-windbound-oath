# MORWEN FIX-03 — back R2 anchor correction (2026-11-11)

## Candidate (local file, not yet uploaded as binary to GitHub)
- Input: `morwen_back_fix03_candidate_r1_1200x1600.png`
- Input SHA-256: `de68bea7cdc4d2f56270a3b194f53b56d804518a9c1257c02e08680c3b13c33d`
- Output: `morwen_back_fix03_r2_anchor_corrected_1200x1600.png`
- Output SHA-256: `93acafbc23b42509b4151e20264e51f6989d71d5b2a9682aaf945a65c760bad2`
- Pixel-preserving operation: translate whole RGBA image **down by 6 px**, no scaling, alpha normalization, repaint, or palette change.

## QA
- Canvas 1200x1600, RGBA: **PASS**.
- Alpha >32 bounding box: **x244..946, y19..1540**.
- Pixels with alpha >32 at ground row y1540: **12**. Ground row alignment: **PASS**.
- Nonzero-alpha pixel count preserved: **PASS**.
- Alpha-value histogram preserved: **PASS**.
- Original four-view image comparison: **BLOCKED** (original binaries unavailable in processing runtime).
- Anatomical landmark matching: **NOT_RUN**; independent art QA: **NOT_RUN**.
- Wide use of partial alpha is inherited and **not fixed**.

## Safety and next action
The R2 PNG exists as a local downloadable candidate, not a GitHub asset. Existing official assets were not modified. Do not adopt or integrate until pixel-level reference comparison, shoulder/arm/hair QA, and art approval. Do not regenerate comparison sheets.
