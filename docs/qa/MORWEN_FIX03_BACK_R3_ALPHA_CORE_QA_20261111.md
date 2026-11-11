# MORWEN FIX-03 — R3 alpha-core correction (2026-11-11)

## Canonical design protection
Latest director-approved back robe V opening, visible legs/thigh-high stockings, right-leg-only garter and current decorations remain the **design canonical**. Historical back design is not the acceptance baseline.

## Pixel processing (local files, not registered in GitHub)
- Source: `morwen_back_fix03_r2_anchor_corrected_1200x1600.png` SHA-256 `93acafbc23b42509b4151e20264e51f6989d71d5b2a9682aaf945a65c760bad2`.
- Output: `morwen_back_fix03_r3_alpha_core_normalized_1200x1600.png` SHA-256 `a741b4c9d81f91c6b2db7e811f33902e5f4c6ef716ec428ed22ce38e784ffbec`.
- Operation: for alpha in **250..254**, set alpha to 255; alpha <=249 untouched. RGB unchanged. No image regeneration, movement, recoloring, redraw or scaling.
- Pixels with modified alpha: **558,021**.
- Alpha=255 pixels: **1,340 before**, **559,361 after**.
- Size 1200x1600 RGBA: PASS. RGB bitwise equal: PASS. Alpha <=249 preserved: PASS. Alpha=0 mask preserved: PASS.
- Ground anchor inherited from R2: y1540, not independently revalidated here.
- Visual QA, fringe color QA, cross-view skeletal QA and Android device QA: **NOT_RUN**.
- R3 remains a **technical candidate**. Original PNGs untouched; binary upload to GitHub **NOT_DONE**; no game integration or publication.

## Next task
Perform visual fringe/checkerboard inspection and compare only to current director-approved design. Do not resurrect historical robe/decorations or create repeated comparison sheets.
