# MORWEN FIX-03 — R2 landmark-guide QA

Source candidate: `morwen_back_fix03_r2_anchor_corrected_1200x1600.png`
SHA-256: `93acafbc23b42509b4151e20264e51f6989d71d5b2a9682aaf945a65c760bad2`

Reference: `assets/candidates/morwen/real-canon-final-04/fix03/BASE_BODY_SPEC.json` (R2.1).

## Technical observations
- RGBA 1200x1600: PASS.
- Alpha >32 bounding box (inclusive): x=244..946, y=19..1540.
- Alpha >32 on ground row y=1540: 12 pixels. Ground line PASS.
- Nonzero-alpha pixels: 608593; alpha=255 pixels: 1340; alpha=254 pixels: 59741. Widespread partial alpha remains; do not blindly set to 255.
- R2.1 guide rows: neck=395, shoulder=430, elbow=600, wrist=786, knee=1100, sole=1540.
- R2.1 target guide points: shoulders (487,430)/(713,430); elbows (399,600)/(801,600); wrists (356,786)/(844,786).
- These are **reference guide positions, not measured joint coordinates**. Clothes obscure anatomical landmarks; match remains NOT_VERIFIED.
- Source front/right/left/back pixel comparison: BLOCKED until source PNG binaries are available in the image processing environment.
- Independent art QA: NOT_RUN. Director design approval for R2: NOT_RUN.

## Progress and next task
A local visual overlay and machine-readable measurement JSON were produced. These files and the R2 binary are not uploaded to GitHub. No original assets changed, no production integration or publication.

Next: acquire the 4 original PNG binaries in the same processing runtime and verify relative shoulder/hair/arm geometry, palette, and stockings. Avoid new overview-sheet generation.
