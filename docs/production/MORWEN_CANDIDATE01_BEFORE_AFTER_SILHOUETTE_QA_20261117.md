# Morwen Candidate 01 — quantitative before/after silhouette QA (2026-11-17)

## Source evidence
- Original realistic neutral renders: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44032196306/artifacts/14305024028
- Candidate 01 renders and editable .blend: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44036495955/artifacts/14307014394
- All source images are 512×768 orthographic PNGs with identical camera scale and object center. Compare alpha>=128 binary silhouettes. Pixel count and IoU calculated from the actual downloaded PNGs. No alpha crop/recenter.
- Formula: intersection-over-union = pixels where both silhouettes are opaque / pixels where either is opaque.

| View | Original opaque px | Candidate opaque px | IoU | XOR pixels |
|---|---:|---:|---:|---:|
| Front | 63,355 | 61,835 | 0.94419 | 3,594 |
| Back | 63,357 | 61,832 | 0.94408 | 3,601 |
| Left | 35,909 | 35,622 | 0.99062 | 337 |
| Right | 35,911 | 35,629 | 0.99087 | 328 |

## Interpretation and stop decision
- The shape has **actually changed**, predominantly in front/back widths. The side silhouette is nearly unchanged (>99% IoU), so the regional X-width taper is not a substantive solution for overall four-direction Morwen morphology.
- IoU measures candidate-vs-original only. It **does not** measure candidate-vs-canonical Morwen and cannot establish an artistic improvement.
- Candidate remains generic neutral body with no approved Morwen face, hairstyle, clothing, garter, or rig.
- **Stop same-family micro-parameter iterations**; do not generate Candidate 02 by merely changing the taper coefficients. Next method must be source-aligned 3D silhouette constraints and independently verifiable front/side body proportions. Avoid inventing chin/head-top landmarks.

## Gate
- G3 diagnostic mesh generation, source integrity, four-view render, reproducible silhouette arithmetic: PASS.
- G1 Morwen canonical silhouette: BLOCKED; G2 art: FAIL for Candidate 01 as a finished character (incomplete/generic); G4: NOT_RUN.
- No canonical overwrite, main merge or publication.
