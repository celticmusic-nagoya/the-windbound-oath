# DEV-WALK-CYCLE-A01 — independent source/visual evaluation

Scope: original Aidan down PNG01..06 at main `e63780543d7ba1719a39a2f68b9924dc6d5b3933`; PR135 `d209d72af8116262566433b9411fdf01d68ab661` plan is reference, not adoption evidence. User authorizes DEV-only4-frame01→05→02→06 at60/75/90, not production registration/main merge. Read AGENTS.md. No repository/PNG edits or browser runs during this inspection. This report is not the final exact-head implementation QA.

## Source phase evaluation

Viewed all six native boot crops and the equal-registration six-vs-four plate. Frontal-view anatomical-left is image-right; anatomical-right is image-left. Image01 shows image-right boot low/forward,05 keeps that support-like leg while the other boot rises/pass-like;02 puts the broad image-left sole low/forward,06 keeps that leg lower while the opposite boot rises. Thus4-frame order plausibly groups two left-support-like poses then two right-support-like poses, rather than current01→06 alternating to right02 and back to a run of left-emphasis03/04/05 before right06.

This is an improvement in **visible phase grouping**, not proof of actual force/contact.02 may plausibly represent heel strike: a low, large sole toward camera can be a raised toe with heel contact. A single painted image does not establish heel force, depth, exact ground plane or limb tracking across every transition. Keep the annotation explicitly inferred; do not label all physical-contact QA PASS solely from this ordering.01/05 and02/06 retain different body/cape shapes inherited from original drawings.

## Foot height and DEV correction

`measurements.json` records exact SHA, native alpha>200 baseline gaps per sampled x column and all matching/difference ROIs. Broad screen-half bottoms are intentionally labelled NOT_foot_specific because a forward boot can cross the half boundary. Sampled columns avoid that semantic error:

-01 support-like image-right boot x1100..1150: gap about5–6nativepx below reference y1229; opposite boot centralx1030..1060 gap59–64.
-05 corresponding support-like boot x1100..1170: gap5–6; opposite boot x1060..1080 gap71–74.
-02 support-like heel/sole x1050..1080: gap4–6; other boot x1100..1160 gap20–23.
-06 support-like boot x1040..1110: gap12–13; other boot x1130..1180 gap78–89.

At high-alpha threshold06 support-like edge is about7–8nativepx above the other support-like edges. At scale.0625 this is.44–.50world/CSSpx, consistent in scale with PR135's lower-alpha6–12px estimate. A DEV-only +8nativepx image shift is reasonable **comparison**, not an original-art correction or validated adoption. It moves the whole frame, including waist/head/cape. No anatomical-contact conclusion should be inferred from a lowest-alpha-row alignment.

The existing shared bob also lifts the complete4-frame drawing at quarter phases by0/1.5/0/1.5world. Consequently passing/support-like05/06 can float due to renderer bob even if the painted edge is level. A +8native correction(.5world) addresses relative06 edge placement only; it cannot cancel1.5world of bob or guarantee grounded supports. Compare bobON/OFF separately from correctionON/OFF. Keep original rendering available as the baseline; do not silently declare a corrected contact.

## Waist and cloak

Own broad torso/waist strip(850..1250,y600..880) translation matching against04 over integer offsets±30 gives01−2,05−4,02−14,06−11nativepx;03+1,04zero. PR135's separate phase-correlation estimate is similar in broad left-vs-right grouping but not identical. This is a broad appearance match, **not tracked pelvis coordinates or measured physical center of mass**. Chosen4-frame order retains a modest left→right weight-shift-like grouping. Full field-scale largest offset≈.875CSSpx; it is more conspicuous enlarged. Do not erase it with automatic horizontal centering without an anatomy judgment.

Registered fixed-ROI cape differences(composited RGB,0..255 MAE, no alignment) show:

|region|current6 mean/transition|trial4 mean/transition|current6 max|trial4 max|
|---|---:|---:|---:|---:|
|left cape|40.43|41.28|48.70|50.92(05→02)|
|right cape|37.86|37.19|48.16|42.42(02→06)|
|waist strip|43.71|41.11|53.08|49.04|

This supports similar average appearance differences, but **does not establish “flicker does not increase”**: left-cape average rises≈2.1% and its worst new transition rises≈4.5%; right average/max decline. Pixel differences are not psychophysical flicker scores, and the ROIs include surrounding garment areas. Original cloak details still redraw between poses. Temporal rate matters:4frames at90 reduces transitions/s relative to current6, while4at60 keeps the original20framechanges/s. Review05→02 at enlarged and native field scales.

## Loop boundary

Both banks end06 and start01. Their **native06→01 image pair is exactly the same**; all fixed-ROI boundary differences in measurements.json are identical. Reordering cannot repair a native wrap jump. At discrete phase sampling, bob exposure differs: last slot5/6 of6 has bob≈1.299world, last slot3/4 of4 has1.5world, then both return0. If optional06shift is enabled, the observed boundary changes again because the whole last image moves down. Inspect each variant's actual render rather than treating the unchanged native pair as proof of a clean dynamic seam.

## Period recommendation — proposal only

Reference speed300world/s, playback1x:

|bank / distance|cycle|per frame|framechanges/s|interpretation|
|---|---:|---:|---:|---|
|current6 /90|.300s|50ms|20|baseline|
|trial4 /60|.200s|50ms|20|same exposure as baseline but two-support cycle is1.5x faster|
|trial4 /75|.250s|62.5ms|16|middle control|
|trial4 /90|.300s|75ms|13.33|same complete-cycle duration as baseline, clearer pose exposure|

**Recommend90 as first director comparison**,75 as the faster alternative,60 as the brisk control.90 retains current full-cycle timing while reducing redraw frequency and giving the inferred contact/pass images more exposure; it does not claim mechanically perfect no-slip walking. Actual body travel speed remains a separate production setting and must not be changed to manufacture naturalness. This choice is a reasoned DEV recommendation, not a physical-Android subjective verdict or production adoption. Existing side180 remains untouched.

## Verdict boundary

- Source identity/order proposal and comparative static metrics: reviewed.
- Visible support-side grouping: improved/plausible, with02heel interpretation explicitly uncertain.
- Physical grounded-contact correctness / absolute naturalness: NOT_PROVEN from static art.
- Exact-head DEV code/browser isolation/PC+Android-equivalent controls: to be verified separately by final implementation QA.
- Actual Android: NOT_RUN.
- Production adoption/main merge: NOT_APPROVED. Director should compare90/75, bob and06correction at1x; approve exact implementation/material configuration only after that review.

Evidence: analyze.py, measurements.json, all-feet.png, six-vs-four-feet.png. Original PNGs were opened read-only; all generated graphics are analysis composites, not replacement character assets.
