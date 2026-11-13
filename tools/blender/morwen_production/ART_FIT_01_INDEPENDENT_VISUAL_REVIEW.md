# MORWEN-HEAD-ART-FIT-01 — Independent visual review
Date: 2026-11-14
Status: QUALITATIVE G2 FAIL FOR UNMODIFIED VRoid HEAD; CALIBRATED LANDMARK QA NOT_RUN

## Evidence inspected
- Downloaded actual Actions artifact `morwen-head-structure-01`, ID `14056314894`, run #43463647869.
- Opened `HEAD_VS_CANONICAL_LAYER0_UNCALIBRATED.png` and `DIRECTOR_APPROVED_3D_TARGET.png` as images; inspected four directions and the target's face closeup.
- The reference row is Layer 0 canonical (purple layered bob, refined violet eyes); clay/original rows are an unrelated stock VRoid head (bare scalp / turquoise close-cropped texture hair). These are different *designs*, not a minor texture mismatch.
- In the clay front view, eyelids/eye plates project noticeably, with exaggerated exposed eye volumes compared with canonical face. Jaw and cheek silhouette, eye treatment and profile nose/chin differ visibly.
- In side views, scalp/hair geometry is missing the full-volume layered bob; the stock VRoid cap cannot reproduce canonical side and rear hair silhouettes.
- Director-approved target additionally requires hat asymmetry, gold glasses, ornate uniform, crest and accessories, none of which is provided by the unmodified VRoid head.
- These observations are **qualitative**, not measured errors. The comparison sheet is uncalibrated; head-size normalization and landmarks are NOT_RUN.

## Gate and decision
- G1: PASS source SHA from CI.
- G2: FAIL for **using the unmodified VRoid head as the final Morwen head**. Sculpt/reshape the base Face+Body head before further fit review; no approval of any replacement.
- G3: PASS prior render and artifact evidence.
- G4: NOT_RUN.
- Structure may be reused as a starting mesh. Rebuild hair volume and separate hat/glasses. Rework eyes, cheek, nose, chin with controlled sculpt and retopology as necessary; avoid treating a stock avatar as a completed asset.
- Next: produce actual calibrated four-view head-top/chin alignment and landmark overlays, then G2 rerun on reshaped candidate. Do not invent tolerance or mark PASS from technical metrics alone.

No original source, approved PNG, or main was modified.
