# PLAYER-WALK-ARM-01 — independent PR142 art evaluation

**Visual/adoption recommendation: ADJUST / HOLD. DEV A/B comparison and technical image isolation: PASS.**

PR142 exact head inspected: `01511ee1a8f0b198ef185900b2c0ec010ac20262`, baseline main `74d0401`. Read AGENTS and candidate README but did not reuse the author's correlation or optical-flow result as independent evidence. Candidate01 SHA `7c09040f93b39462a97796505ee0dabe115f194adb8fdba16fa21ab1fc9b9764`; candidate02 SHA `1a6e2d3677b10b8e280c7bfc80293c5686b89ffa778d2242d1c4111c31c48e93`.

This reviewer generated own native/cycle/wrap/game-scale plates and exact-pixel metrics, then inspected parent-produced portrait DEV paused screenshots. No original/candidate PNG, sharedsource, repository file, browser or SAVE state was edited. Parent owns DEV implementation and serial browser QA; this is not the final feature-head code review. No main/Pages/adoption or PR137 operation is approved here.

## 1. Exact edit scope and protected areas

Both candidates are actual2048×1280 RGBA PNG. Independent differences:

|frame|changed pixels|changed bounds(exclusive right/bottom)|outside raw mask|outside documented3px feather|
|---|---:|---|---:|---:|
|01|32,374|[1198,576,1375,846)|2,000|0|
|02|33,816|[1209,572,1379,851)|2,139|0|

The supplied edit_mask files encode the transplant **core**, not its feather envelope. All additional changed pixels are within3px of the core; the author's build QA allows4px. There is no escaped far-region edit, but a report saying simply “outside edit_mask=0” would be inaccurate without the documented margin. Shoulder/arm-adjacent seams should therefore be reviewed in core+feather, not just the core.

For both candidates: y<560(head/face), y≥870(legs/shoes) andx<1150(protected opposite arm/central torso) have **zero RGBA differences** from their corresponding production PNGs. Fullalpha bounds are unchanged. There are1,921/2,256 alpha-channel changes within the permitted arm region; do not equate unchanged externalbounds with everyalpha pixel unchanged. Enclosed alpha200 hole counts match their own source(01:1,074;02:844); no newly detached limb/matte appears in viewed crops. All four production inputs01/05/02/grounded06 are independently byte-identical to main74d0401;05 and the existing down4repair06 remain untouched.

## 2. Native anatomy and seam inspection

Own `own-arm-native.png` compares original/candidate01 and02 at identical native registration with nearest-neighbor enlargement. Shoulder armor/sleeve, elbow/forearm, bracer and glove remain visually connected; no clear detached wrist, duplicated finger silhouette, abrupt cut line or lost equipment is evident in these inspected poses. This is a visual finding, not an anatomical motion proof.

01 lowers the visible screen-right(anatomical-left) glove using an existing donor pose.02 raises it. The candidate02 transplantation also brings the06 **inner cloak/white lining** around and below the fist. The bright curved lining patch/crescent and nearby fold/pattern placement visibly change; this is material-pose content, not just an arm position. The boundary is not an obvious rectangular matte, but the lining's transition is conspicuous enlarged and must be evaluated over05→02 and06→01. It should not be silently treated as unchanged costume merely because the patch comes from the same character.

Exact donor identity independently checked:
- Candidate01 glove rectangle[1270,750,1320,800) equals production02 at translated coordinates(+2,−5):0RGBA mismatches.
- Candidate02 glove rectangle[1274,730,1342,793) equals productiongrounded06 at(+7,+9):0RGBA mismatches.

These prove genuine copied donor glove content and shifts; they do not prove that the assembled shoulder/cloth motion is naturally phased.

## 3. Hand motion: what can and cannot be concluded

Own native10px grid plates (`own-fist-grid.png`, `own-right-fist-grid.png`) show productionleft01/05 in near-similar glove positions, a lower pose02, then raised06. Candidate01 is lowered; candidate02 is raised toward06. Thus the visible left-arm grouping becomes more opposed to the unchanged other-arm grouping. The candidate fixes the apparent near-hold in01→05, but02→06 remains a near-hold and the largest left-arm return is concentrated at06→01. At four75ms exposures(cycle90/1x), a larger boundary change can read as a snap even if the four sampled arm positions are negatively correlated.

No precise anatomical-hand trajectory is claimed from these coarse grids. Source pose, glove shape and chest movement make a fingertip/bottom/center a different measurement. A particularly important author-annotation consistency limit: the donor glove in candidate02 is exactly translated+9px inY from source06. The author's raw manual bottom annotations06=777,candidate02=780 differ only+3px. They cannot both be the exact same transported point under+9 unless the chosen landmark changes or manual error absorbs the discrepancy. The stated±3px uncertainty places this at its combinederror limit. This is not proof that the candidate is wrong, but it prevents treating the derived−0.79 correlation as independently validated phase/naturalness evidence. Four samples, different projection/landmark choices and a selected reference arm are insufficient to certify gait.

The inverse-phase trend is plausible; “naturally alternating arms” remains a visual question over the complete loop, not a correlation threshold PASS.

## 4. All four cycle edges and material continuity

Own fixed-coordinate compositeRGB MAE(0..255) was computed over declared ROIs, independently of the author's optical flow. These are **appearance-difference measures, not motion magnitude, psychophysical flicker scores or proof of naturalness**.

ROIs: left glove/nearby material[1240,710,1360,825); innercape/white lining[1300,740,1390,855); protected otherarm[840,560,1000,800); chest[760,300,1340,500). The gloveROI includes some nearbycloth; it must not be reported as anatomical hand displacement.

|edge|glove ROI prod→candidate|white-lining ROI prod→candidate|visible assessment|
|---|---|---|---|
|01→05|27.24→27.26|33.26→31.40|Left glove now changes position; overallROIappearance change remains similar.|
|05→02|35.59→59.02|30.79→50.72|Candidate02 changes gloveandlining strongly; watch the new bright innercape/fold switch.|
|02→06|52.67→34.88|49.81→39.01|Donor06-based candidate02 resembles next06more; near-hold remains.|
|06→01|50.54→56.62|40.38→47.00|Candidate01 produces larger glove/material return; loop needs actual1x acceptance.|

The protected opposite-arm and chestROI measures are **exactly unchanged on all four edges**. No new wholebodyoffset is introduced. Legs and grounded06 stay identical, so this change does not undo the foot correction.

White-lining difference rises≈64.7% on05→02 and≈16.4% on06→01, while02→06declines. This matches the visible transplant's redistribution of material poses and is a concrete reason to avoid declaring a universal motion-quality PASS. It is not sufficient by itself to call a rendering bug or require arbitrary texture flattening.

Own `own-cycle-arms.png` shows original/candidate01→05→02→06 at consistent crop/scale. `own-wrap-06-01-05.png` makes the raised06→loweredcandidate01 return reviewable in fullbody context. `own-game-scale.png` resamples wholecanvas at.0625 andDPR1/2.625-equivalent physicalpixel counts: these are static scale illustrations, not Android captures. The patch is subtle at smallfieldscale, more visible in enlargedDEV or highDPR inspection.

## 5. Parent actual browser screenshots and limits

Inspected parent `screens/portrait-candidate-02-sprite.png` and `portrait-production-02-sprite.png`: the lowered-to-raised glove/lining change is present in the realDEV render and does not create an obvious detached wrist or altered legs/bodyroot in the paused frames. These screenshots are from the parent's run, not this reviewer's browser. Parent reports actual decoded4-frame/cadence.300s/bob25/nooffset tests across3viewports. No paused image or timer success substitutes for perceived continuous naturalness. This reviewer has not claimed to watch an actualAndroid loop or independently performed runtime QA.

## Recommendation

**Keep this as a DEV comparison candidate, but ADJUST/HOLD the formal-adoption recommendation.** The arm-phase grouping is promising and technical isolation is sound; the visible02 innercape/white-lining transplant and increased05→02/06→01 material/hand transitions remain unresolved aesthetic tradeoffs. Before adoption, either refine the02 lining/transition without disturbing the improved arm pose, or obtain explicit director acceptance of the actual1x loop at the intended field/DEV scales. Do not approve merely because correlation becomesnegative.

No demand to repaint all art or alter legs/grounded06 is implied. No confirmed broken shoulder/elbow/wrist requires an emergency repair in the viewed stills. The requested focus is the localizedlining/materialtransition and loopreturn. Formal adoption, productionbank changes, mainmerge andPages remain outside this evaluation. ActualAndroid:NOT_RUN.

Evidence: portable `analyze.py --repo <checkout> --out <analysisdir>`, `independent-arm-metrics.json`, native/grid/cycle/wrap/game-scale plates. Script reads original/candidate files and writes only the selected analysisoutputdirectory(default fresh tempdir), never modifies sourceassets.
