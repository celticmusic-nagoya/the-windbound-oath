# MORWEN FIX-03 — R3 background display QA (2026-11-11)

## Candidate and test
- Candidate: `morwen_back_fix03_r3_alpha_core_normalized_1200x1600.png`
- SHA-256: `a741b4c9d81f91c6b2db7e811f33902e5f4c6ef716ec428ed22ce38e784ffbec`
- Created local 3-panel preview on dark (#24252b), light (#f4f2ec), and 64px checkerboard (#dddddd/#999999), composited with PIL at native resolution then reduced to 480x640 per panel.
- Preview: `morwen_fix03_r3_background_display_qa.png` (local file, not uploaded to GitHub).

## Measured technical QA
- 1200x1600 RGBA: PASS.
- Alpha=255: 559361 pixels; alpha=1..249: 49232 pixels; alpha=0: 1311407 pixels.
- Nonzero alpha bbox: x=102..1097, y=16..1545 (exclusive max 1098,1546).
- Semi-transparent bright pixels with mean RGB >230: 2108; semi-transparent dark pixels with mean RGB <30: 11623. These metrics alone do not prove halo presence.
- At 480x640 preview scale on the three backgrounds, no prominent white halo or background contamination was observed in manual inspection: VISUAL_PASS_AT_PREVIEW_SCALE.
- Fine 1:1 edge inspection: NOT_RUN; independent art QA: NOT_RUN; four-view skeletal match: NOT_RUN; Android QA: NOT_RUN.
- Latest director-approved V-open back robe, visible thigh-high stockings, one right-leg garter and current ornament placement are **LOCKED**; do not use historical artwork to reject these revisions.

## Next deliverable
Perform targeted native-resolution fringe inspection, then compare R3 against current four-view canonical body dimensions once reference binaries are available. No redundant comparison-sheet regeneration. R3 binary remains local; no original overwrite or production merge.
