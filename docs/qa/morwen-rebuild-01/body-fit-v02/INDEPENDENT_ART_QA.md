# Independent art QA — MORWEN full-body fit v02

Reviewer: `/root/body_art_qa`, separate AI reviewer, not the mesh author. Date: 2026-11-17 UTC. This is an independent AI art review, not a human artist or Android device review.

**G2: FAIL. Actual geometry-edit milestone: verified.** The files contain a changed full-body mesh and visibly changed proportions. They do not yet establish accepted Morwen anatomy or commercial final quality.

## Evidence actually inspected

- Existing before renders: `assets/candidates/morwen-rebuild-01/base-source-intake/front.png` and source context inherited in the source scene.
- v01 front, back and right PNGs; v02 front, back, right and left PNGs.
- The four existing official Layer 0 PNGs: 7809 front, 7810 back, 7807 right, 7808 left. No images were reacquired and no reference SHA checks were rerun.
- Author's `body-fit-v01/mesh-edit.json`, `body-fit-v02/mesh-edit.json`, `measured-residuals.json`, `reopen-technical-qa.json`, and the four-view comparison sheet.
- Independently reopened the existing body workspace and v02 candidate in Blender 4.3.2 with scripts disabled. Compared actual world-space coordinates and face index lists; no mesh was edited and no renderer was rerun by this reviewer.

| Independent geometry check | Result |
|---|---|
| Source and v02 control counts | 12,502 vertices / 12,500 faces each |
| Face index lists identical | Yes |
| Finite world-space coordinates | Yes, both files |
| Vertices changed by more than 1e-7 normalized units | 12,502 |
| Maximum source-to-v02 displacement | 0.0781701523 normalized units |
| Mean source-to-v02 displacement | 0.0403485886 normalized units |
| Candidate reopened successfully | Yes |

These are limited technical observations. They do not certify intersections, manifoldness, deformation quality, UVs, rigging or final G3.

## Visible improvements

1. Relative head size is clearly reduced from the original generic stylized base. The torso and legs occupy more of the fixed full-body frame. This is a visible mesh change, not a renamed file or camera-only change.
2. Pelvis, knee and upper-body vertical relationships changed, and the waist is narrower. The result is closer to the intended elongated adult character proportions than the original base.
3. Arms are brought closer to the torso, and the hands occupy a lower, more reference-like relation to the hips and thighs than the widely spread source pose.
4. v02 reduces v01's conspicuous narrow upper-arm / wide-forearm transition. In front and rear views the arm outer contour is more continuous than v01.
5. Side depth and the torso/hip contour have visibly changed. The output is a genuine full-body fitting trial rather than the earlier unchanged source intake.

## Remaining G2 failures

1. **Shoulder and arm attachment:** Both v02 front and rear views retain pointed shoulder ends and abrupt planes around the deltoid/axilla connection. The back view has a broken, jagged transition beside the upper back. The reference has a rounded, continuous shoulder-to-arm surface. Reducing a classification blend width has improved one pinch but has not restored anatomical surface flow.
2. **Upper-arm surface and elbow:** Side views still show a hard, nearly cylindrical upper-arm region and a sharp transition towards the elbow/forearm. The reference's arm taper is gentler. Source faceting and deformation ridges are both visible; a smoother render alone would not establish that the new contour is correct.
3. **Knee and lower leg:** The lateral views retain an abrupt knee-to-shin directional change, and the front/rear calf and knee masses read as segmented blocks. The reference has softer transitions and a different visible standing-leg curvature. Because the drawings are not calibrated orthographic scans, this is a visual mismatch finding rather than a claimed exact joint-angle error.
4. **Hip/gluteal and torso transitions:** The posterior pelvis and the upper-thigh junction retain broad planar bands. The side hip, abdomen and thorax are not yet a coherent recreation of the reference's softer contour. The upper torso still reads as the generic base reshaped by height/width stations.
5. **Feet and stance:** Front/rear foot shapes and the spacing/opening of the stance remain visibly different from the closely placed, relaxed illustrated stance. Profile foot length and front-view foot placement need separate review; matching one profile extent does not establish four-view agreement.
6. **Identity and finish:** The source face remains generic and the body has no final surface finish. Face, hair, garments and equipment are outside this edit's scope, so their absence is not used to reject the narrow vertex-edit milestone. It does prevent any claim that the full Morwen character is accepted or complete.

## Measurement interpretation

- The reported 7.5079 head count uses an inferred skull crown hidden under hair. It is a design estimate, not a directly verified official head-height measurement. The approximately ±20 px crown uncertainty must remain visible in reporting.
- The cage stations map their chosen source values exactly to target values. An `after_cage_error_px` of zero measures the interpolator at its own constraints; it is not an independent contour, joint or identity accuracy score.
- Clothing covers some reference landmarks. Skeletal joint centers and the underlying skin contour are inferred separately from directly visible chin, foot and body outlines.
- The reference illustrations are not calibrated scans, and the stance differs across views. I did not certify an exact orthographic silhouette IoU or pixel-accurate anatomy match from them.

## Gate decision and handoff

- G1 body reference: previously established PASS; not rerun in this review. Final outfit/face design authority remains a separate scope.
- **G2 body fit v02: FAIL.** The proportion direction has improved, but the shoulder/arm, knee, hip and foot findings prevent anatomical/silhouette acceptance.
- G3: NOT_RUN as a complete character gate. My limited reopen, finite-coordinate and topology-preservation observations pass, but the author's separate local screen is FAIL: 38 source-to-candidate face-normal changes exceed 90 degrees. That finding warrants local surface inspection and must not be hidden by the successful reopen. A first-triangle normal change alone is not proof of a self-intersection or inverted manifold.
- G4: NOT_RUN.

The user's required **actual changed-mesh and four-view evidence milestone is met**. Formal adoption is not met. Do not advance to detailed face, hair, costume or rigging on the assumption that the body has passed.

This is the second full-body cage trial, following v01's shoulder/arm pinch failure. Do not perform a third near-identical classification-width/threshold adjustment and rename it as a new technique. Preserve both trials. The next body edit should use a causally different anatomical surface method: authored local quad-flow / sculpted shoulder–arm and knee–shin transitions with continuous anatomical controls, retaining the useful global proportion work. No new source download or reference-scene setup is needed.

## Supplemental numeric residuals reviewed

The author's tracked source-band measurements report the following absolute width errors in registered reference-pixel units. I read these results and checked their direction against the actual comparison sheet; I did not independently reproduce the band-selection algorithm. They are not silhouette IoU or calibration-free measurements.

| Measurement | Before absolute error | After absolute error | Interpretation |
|---|---:|---:|---|
| Waist width | 23.81 px | 4.04 px | Improvement, within the stated ±6 px target uncertainty |
| Pelvis width | 24.88 px | 10.78 px | Improvement; residual exceeds stated ±8 px uncertainty |
| Chest width | 43.37 px | 9.47 px | Improvement; near stated ±10 px uncertainty |
| Knee outer width | 13.23 px | 26.94 px | Regression; agrees with the remaining knee/calf concern |
| Foot-pair width | 29.97 px | 26.76 px | Small improvement; substantial stance/foot residual remains |

The wrist band centroid moves from 194.95 to 125.13 px against a 143 px target: the hand position is closer overall, but it overshoots toward the body by about 17.87 px. This is a region-centroid measure, not an exact anatomical joint. These mixed results support a recorded improvement checkpoint with **G2 FAIL**, not a blanket claim that all body measurements improved.
