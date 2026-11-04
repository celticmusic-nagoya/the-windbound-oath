# DEV-WALK-GROUND-01-QA — independent PR139 candidate image review

**Verdict: PASS for the candidate image's DEV comparison, not formal adoption or main merge.**

PR139 inspected exact head `d15aa83ab73e77e505895bea3c89485d3a9254bd`. Original06 SHA `b88fdf8e0b48bc303c065d0dcd179babbd2c6a55040f4ccca8a2c18ed8c55c00`; candidate SHA `d87b2ec56660568bd46eecb8559edfed1c3802fe1e2675a018f78f3c23f970df`. Input was extracted directly with `git show`, not accepted from Claude self-QA. All comparisons/metrics below were independently produced. This reviewer did not edit repository files, original/candidate assets or browser state and did not perform PR/main operations. Read AGENTS.md. The parent owns DEV implementation and serial browser QA; this report is not that exact-head implementation verdict.

## Independent image and edit-scope checks

Both files are actual2048×1280 RGBA PNG.16,651 pixels change; exact changed bounding rectangle is `[990,1062,1126,1237)` (right/bottom exclusive). No changed pixel outside supplied edit_mask, no change above row1062, no change atx≥1126. This independently confirms a local lower support-leg modification rather than a full-body translation.

Upper body/head/waist and the declared cloak comparison strips(y650..1050) are bit-identical. Native fullbody and enlarged leg plates show no apparent face/costume/equipment change. The lifted opposite boot's outer region is unchanged; the altered contour remains confined to the support-like shin/ankle/boot. The anatomical support label remains inferred from the painting, not measured force or heel load.

A lower-boot interior rectangle, candidate `[1000,1180,1110,1225)`, matches the original rectangle atY−7 **exactly,0 RGBA differences**. This supports preservation of boot/ankle decoration and toe shape by rigid translation, rather than claiming every edge pixel is byte-identical after interpolation. Near the blending/alpha border some edge pixels differ, as expected. The upper lower-shin band extends gradually; enlarged native inspection finds no obvious kink, detached ankle, broken gold trim, doubled edge or disproportionate shoe.

The cited6.4% is a band-average extension(7/110), not a promise of uniform local scale: smoothstep displacement varies locally. The result is subtle at gameplay scale, but extended shin proportions remain a director visual decision. No sign of a required further anatomy repair is evident in the viewed native/gameplay-equivalent plates.

Alpha topology counts with8-connectivity are unchanged: atalpha>0 both have68components(29of≥16pixels), atalpha>128 and>200 both have one connected component. No new disconnected opaque foot fragment appears. This is not a generic proof that every semitransparent pixel belongs to intended foreground.

Rawalpha bounds change from `[668,126,1524,1230)` to `[668,126,1524,1237)`.755 candidate pixels extend below anchorY1230, but their maximumalpha is30/255; none exceed128. On independently composited black/white backgrounds the fringe is faint, without an obvious baked rectangle/dark matte or new opaque ground protrusion. Do not describe candidate bounds as identical to original or claim all nonzero alpha ends at the ground line. Keep fullcanvas rendering and correct candidate-only bounds metadata; do not crop at the old1230bottom.

## Support-boot contour checks

Used independently declared support-boot ROIs and central columns from the previous source audit, not whole-canvas bottoms or broad screen halves. Metadata anchorY1230, scale.0625. Values are median gap from registered line to alpha-contour edge(lastcoveredrow+1), in native pixels:

|PNG|alpha>128|alpha>200|
|---|---:|---:|
|01|4|5|
|05|4|6|
|02|4|5|
|original06|11|12|
|candidate06|4|5|

The local candidate reduces06relative discrepancy7nativepx(.4375world atzoom1) at both thresholds. It does not make the contours literalzero-gap contacts, and alpha cannot establish physical ground/pressure.02's heel-contact interpretation is unchanged and remains a hypothesis.

At cycle90, bob25%, no06whole-frame offset, the bob wave is continuous. Its amplitude at02→06 is.375world and at06→01 is0. Alpha128 support-probe gap prediction:

- Original02→06: `.250+.375 = .625` → `.6875+.375 =1.0625world`.
- Candidate02→06: `.625` → `.625world`.
- Original06→01 wrap: `.6875` → `.250world`.
- Candidate06→01 wrap: `.250` → `.250world`.

This is a **relative contour-height improvement at the two relevant boundaries without a new whole-image offset step**. It does not erase the bob's continuous held-pose lift, change native02heel/06passing articulation, or prove a stationary world-space support foot through a stride. Inspect the entire gait, not only the4px reading.

## Whole gait, waist and cloak

Viewed own original/candidate four-pose plates,02→original06→candidate06→01 fullbody plate, and native boot black/white composites.01→05 and05→02 are entirely untouched. The candidate lengthens the support-like shin subtly and brings its boot down into the same contour-height band as01/05/02. The other limb's lifted pose remains the same. Across02→06→01 there is no new whole-body translation, upperbody size change, staff/sword/face change, ankle snap or obvious boot silhouette distortion attributable to the candidate. The slight source pose/cape differences and inferred transition phases remain visible, rather than being repaired by the7px adjustment.

Independently recomputed registered compositeRGB MAE(0..255; not perceptual flicker/animation scores) confirms waist/cape comparisons are exactly unchanged for **all four edges**:

|edge|left cloak,original=candidate|right cloak,original=candidate|waist,original=candidate|
|---|---:|---:|---:|
|01→05|36.70|35.21|31.79|
|05→02|50.92|39.46|49.04|
|02→06|44.48|42.42|40.01|
|06→01|33.01|31.66|43.59|

05→02 remains the largest left-cloak change; the local06candidate neither improves nor worsens that pre-existing issue. It must not be reported as a fully repaired cloak cycle. Identical upperbody comparisons do not by themselves prove temporal naturalness, but they exclude added upperbody differences from this asset replacement.

`own-cycle-native-game.png` includes1:1native boot crops and wholecanvas images resampled to production scale.0625 withDPR1 and2.625-equivalent physical pixel counts. These are **static resampling illustrations, not browser or actual-device captures**. At original small field scale the leg change is subtle; at enlarged native scale it remains coherent. The source proportions/design are preserved to the visual extent supported by these comparisons.

## Recommendation and residual limitations

Recommend prioritizing **candidate06 / cycle90 / bob25% / full-frame06offsetOFF** for director A/B viewing against the original06 under the identical settings. This addresses the support-contour discrepancy while avoiding the earlier±.5world whole-frame correction jumps. No image-level ADJUST request is necessary based on the independently viewed plates and measurements.

This is not a claim of complete biomechanical gait, physical ground contact, perfect cloak continuity or actual Android naturalness. Continuous bob lift remains,02heel contact is inferred,05→02cloth differences remain, and the supporting shin is locally extended. These are explicit residual review points rather than new candidate regressions. Actual1x rendered loops/controls/viewport behavior and exact feature-head isolation must come from the parent/final implementation QA. PhysicalAndroid isNOT_RUN here; director adoption remains pending. ProductionPNG/bank/SAVE/main must remain unchanged until separately approved.

Evidence: `analyze.py`, `independent-image-metrics.json`, `own-boot-diff.png`, `own-cycle-native-game.png`, `own-alpha-edges.png`, `own-wrap-fullbody.png`. Candidate/edit-mask copies in this evidence directory are byte-exact inputs extracted fromPR139, not newly modified outputs.

## Actual QA screenshot cross-check and reproduction

After producing independent native/resampled evidence, reviewed parent Chromium screenshots `portrait-candidate-06.png`, `portrait-candidate-06-sprite.png`, `portrait-official-06-sprite.png` and `landscape-candidate-06.png` from the real DEV A/B run. At cycle90/1x/bob25%/wholeframeoffsetOFF, candidate06 shows reduced visible support-boot gap with upperbody/cape registration visually matching original06. No new obvious shoe deformation appears in these actual paused render captures. These are parent-run browser screenshots, not this reviewer's own browser run; continuous1x temporal naturalness and actual Android are not established merely by paused screenshots. The .300-second loop remains brisk and05→02 still has the original cloak redraw; neither is repaired by localized06extension.

The analysis script is portable: run from a Git checkout using `python <path>/analyze.py --repo . --out /tmp/ground01-independent`. It reads PR139 exactcommit `d15aa83ab73e77e505895bea3c89485d3a9254bd`; fetch `refs/pull/139/head` first if that object is absent. It reads source original paths in the checkout and writes only to the requested output directory (default a fresh temp directory). No comparison input is rewritten in the repository.
