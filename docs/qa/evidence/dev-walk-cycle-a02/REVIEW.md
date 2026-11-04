# DEV-WALK-CYCLE-A02 — independent support-boot/render comparison

Read-only source/pixel/mathematical evaluation of original down01→05→02→06. Source PNGs remain at main `e63780543d7ba1719a39a2f68b9924dc6d5b3933`; base DEV PR136 does not change them. Read AGENTS. No production, candidate, original PNG, registry, shared source, browser or SAVE edits/runs were performed by this reviewer. Generated graphics are analysis plates/graphs only, not replacement assets. No final exact-head implementation verdict is implied.

## Foot probes and uncertainty

Declare each support-like boot explicitly, rather than split the canvas into halves. Frontal-view anatomical-left is viewer-right.01/05 use that boot as a visually inferred support;02/06 use viewer-left/anatomical-right.02 is heel-contact-like, but alpha and a visible sole do not prove actual heel force/contact or depth.

All coordinates are original2048×1280 PNG pixels. Metadata ground/anchorY1230, scale.0625. ROI is `[x0,y0,x1,y1]`, with exclusive right/bottom. The marker is an actual central-column contour edge chosen nearest the median bottom edge; `bottom_edge_y = last covered row +1`. The gap is `1230-bottom_edge_y`, not a physical pressure measurement. Central columns avoid the other boot/cape. Native alpha thresholds128 and200 are reported separately; low-opacity contour tails cannot silently establish grounding.

|PNG / inferred phase|support-boot ROI|central x|median gap alpha>128|median gap alpha>200|
|---|---|---|---:|---:|
|01 left contact-like|1080,1110,1175,1230|1100..1150|4px|5px|
|05 left support / right pass-like|1090,1110,1180,1230|1100..1170|4px|6px|
|02 right heel-contact-like|1015,1090,1100,1230|1040..1090|4px|5px|
|06 right support / left pass-like|1025,1100,1120,1230|1040..1100|11px|12px|

Thus06 central boot contour is about7nativepx above the comparable others(about.4375world), not a whole-canvas-margin problem. An +8native DEV offset(.5world downward) slightly overcompensates by≈1nativepx at this probe. It is a reasonable comparison, not a certified artifact repair or anatomical contact alignment.

`support-boot-rois.png` shows original boots on the shared ground line, declared ROIs and actual contour probes. `support-analysis.json` stores exact sourceSHA, every central-column measurement, both thresholds, marker coordinates, each edge/configuration and texture comparisons. A UI overlay should be labelled **“支持足候補・alpha輪郭プローブ”**, track original pixel coordinates through current image scale/zoom/bob/offset, and never be used as a contact-PASS indicator. Keep a separate fixed root marker at the metadata anchor; this is not automatically a measured pelvis.

## Continuous bob, not four fixed offsets

Let cyclephase `p=(time*300/stride)%1`. Source rendering lift is `A*abs(sin(2*pi*p))`, where A is0(OFF),.375world(25%) or1.5world(100%). The four held PNG intervals are01:[0,.25),05:[.25,.5),02:[.5,.75),06:[.75,1).

Within01 the whole image rises0→A, within05 fallsA→0, within02 rises0→A, within06 fallsA→0. Bob is continuous across all four switch edges. Sampling only frame starts0,A,0,A misses floating during held poses. A painted support-like foot stays part of the whole image; bob moves it too.

Optional06+8native gives a constant downward world offset C=.5 only during06. Rendered whole-frame Y transform is `C-bob`; selected contour gap above ground is `native_gap+bob-C`. This changes the head, waist and cloak together with the foot. It adds a **+.5world image step at02→06 and−.5world step at06→01**, regardless of bob amplitude or cycle period. A lower foot-gap mismatch can therefore trade against a new body/root/garment discontinuity. The offset is not a foot-only deformation or continuous root correction.

## All four switch edges

The following uses alpha>128 central-probe medians. “A” is the common continuous bob at the edge. Positive gap is above the registered line. Units areworld; atDEVzoom1 one world is one displayCSSpx, atotherpreviewzoom multiply by thatzoom.

|edge|bob at edge|gap before→after,offsetOFF|gap before→after,offsetON|whole-frame step added by06offset|
|---|---:|---|---|---:|
|01→05|A|.250+A→.250+A|same|0|
|05→02|0|.250→.250|same|0|
|02→06|A|.250+A→.6875+A|.250+A→.1875+A|+.500 downward|
|06→01|0|.6875→.250|.1875→.250|−.500 upward|

At alpha>200 the native gaps are.3125/.375/.3125/.750; with06offset the last is.250. The slight first-half differences(.0625world) remain; there is no claim that a chosen contour threshold equals the physical plane.

Examples at02→06 withoffsetON:
- bob100%:gap1.750→1.6875world, despite the native06gap correction.
- bob25%:gap.625→.5625world.
- bobOFF:gap.250→.1875world.

The fullcurve diagram `predicted-foot-gap.png` includes01→05,05→02,02→06 and the06→01 wrap endpoint for thresholds128/200 with bothoffsetstates. It predicts existing/render-option arithmetic, not observed force/3Dcontact. Sourcebody drawing and root translation can both affect perception; no generated curve alone proves naturalness.

## Pelvis/root and cloak cues

Earlier independent broad waist-strip matching(y600..880,x850..1250 againstPNG04) estimated sourceX translations01−2,05−4,02−14,06−11nativepx. These are appearance matches, not tracked anatomical pelvis or physical center-of-mass coordinates. The left-support-like half and right-support-like half have a small lateral grouping; no horizontal recentering is recommended merely to zero the metric. Root/anchor stays unchanged in original images.

Native source06→01 pair is unchanged from both previous4and6banks. The DEVoffset changes the rendered boundary, not the PNG. Own fixed-ROI compositeRGB MAE(0..255; appearance difference, **not flicker quality**) foroffsetOFF→ON:

|edge|left cloak|right cloak|waist|
|---|---|---|---|
|01→05|36.70→36.70|35.21→35.21|31.79→31.79|
|05→02|50.92→50.92|39.46→39.46|49.04→49.04|
|02→06|44.48→44.96|42.42→39.52|40.01→36.50|
|06→01|33.01→27.16|31.66→35.42|43.59→44.30|

The offset helps some registered texture comparisons and worsens others. No scalarmean should be read as universally less flicker or a clean seam.05→02 remains the largest left-cloak change and is unaffected by06correction. Bob at each switch is common onbothframes, so the newly added step comes from the06offset; during eachhold the bob still moves allsourcefeatures.

##90 versus75 and recommendation

At reference300world/s andplayback1x:

|cycle|fullperiod|4frame exposure|redraws/s|maxYvelocity bob100%|bob25%|
|---|---:|---:|---:|---:|---:|
|90|.300s|75ms|13.33|31.42world/s|7.85world/s|
|75|.250s|62.5ms|16|37.70world/s|9.42world/s|

75 changes phase20%faster than90; the sameperphase footgap andoffsetsteps occur20%moreoften. **90 remains the recommended first director comparison**: clearerpose exposure, lowerbobvelocity and lowergarmentredrawfrequency while retaining previous6/90fullcycle duration.75 is a useful briskercontrol, not automatically moregrounded.

For strict visible contour-height consistency, compare **bobOFF+06offsetON**: it numerically minimizes theseprobeheightdifferences, but has limited wholebodybounce and still introduces±.5world body/clothsteps. For a smallbody-sway compromise, **bob25%+06offsetON** is a reasonable DEV hypothesis: compared100% it cuts verticalmotion amplitude/velocity4×, while preserving a continuouswave. Neither is certified “natural” by these measurements; offsetON may be rejected if its02→06/06→01 wholebodyjumps are visible. Keep bobOFF/nooffset as a diagnosticcontrol and old100%/nooffset as the baseline. Do not change production PNG,bank,stride,worldspeed,collision,SAVE or otheractors from this evaluation.

Director decision still requires actual1x loop viewing, PC/Android-equivalent render checks and physicalAndroid, with specialattention to05→02cloak and02→06/06→01wholebodycontinuity.02heel-contact remains an inference. PhysicalAndroid:NOT_RUN. Productionadoption/mainmerge:NOT_APPROVED.
