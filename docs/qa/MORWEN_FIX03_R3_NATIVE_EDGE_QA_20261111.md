# MORWEN FIX-03 — R3 native-resolution edge QA

Date: 2026-11-11. Source R3 local candidate: `morwen_back_fix03_r3_alpha_core_normalized_1200x1600.png`; SHA256 `a741b4c9d81f91c6b2db7e811f33902e5f4c6ef716ec428ed22ce38e784ffbec`.

## Procedure and results
- Composited three 1:1 pixel regions on both dark (#181820) and light (#f6f4ed) backgrounds; no resampling in crops. Local preview `morwen_fix03_r3_native_edge_qa_20261111.png`.
- Regions: hat/hair x300..950 y0..510; robe opening x350..850 y640..1250; stockings/boots x350..850 y1060..1560.
- Visual inspection: **PASS at inspected regions**; no prominent white halo or background-colored fringe seen.
- Semi-transparent alpha 1..249 pixels: 49,232. 22,105 are within 3 px of an opaque pixel; not an automatic defect.
- RGB-bright semi-transparent edge pixels near opaque core: 1,241; dark: 2,284. Color counts alone do not establish a halo.
- Director-approved latest back robe V opening, thigh-high stockings, right-leg-only garter and ornament presence/absence are preserved. Historical artwork is not the design acceptance baseline.
- Full four-direction skeletal QA: **BLOCKED** pending latest source binaries. Independent art QA: **NOT_RUN**. Android device: **NOT_RUN**.
- Local R3 binary not uploaded to GitHub. No production integration, no original overwrite.

## Decision
Do **not** further normalize alpha without a localized visible defect. Next step is a current-canon cross-view dimensional audit, followed by asset registration only after binary source and approval gates. Do not repeat reference-sheet generation.
