# BLENDER-20 canonical contour QA

Technical status: **PASS**. Actions runs 43246785841 (contour extraction), 43246786029 (BLENDER-19 baseline), 43246786013 (BLENDER-01 regression) all succeeded. Artifact: 13957027294.

All four SHA-locked 384x1024 RGBA canonical images were processed. Per-row left/right alpha boundaries at threshold 128 were generated as `canonical_alpha_contours.json`. The source files were read-only and unchanged.

**Important limits:** full-body alpha silhouettes contain hair, arms, sleeves, clothes and other outer layers. A per-row left/right extreme is not a torso contour. Do not use these full-image extremes to set chest, waist or pelvis radii. Before fitting the torso, trace or segment the garment-covered torso region and cross-check front and profile references. The current output is a measurement baseline, **not art approval**. No main merge or publication.
