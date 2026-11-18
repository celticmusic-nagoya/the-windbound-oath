# Independent art QA — Morwen local shoulder / axilla / knee / shin v01

Reviewer: `/root/body_art_qa`, separate AI reviewer, not the vertex-edit author. Date: 2026-11-17 UTC. This is an independent AI review, not human artist or device QA.

## Decision

- **Actual local mesh edit: PASS.** A different stored mesh exists, and its changes are visible in the new close-ups and four-view renders.
- **Reduction of the specified surface pinches / abrupt planes: PASS, narrowly scoped.** Shoulder/axilla transitions and the knee-to-shin surface are visibly more continuous than the v02 source.
- **Local canonical anatomical acceptance: FAIL.** Shoulder width/cap shape, the depth of the axillary groove and knee/standing-leg curvature still need work.
- **Whole-body G2: FAIL.** This local improvement does not override the previous whole-body failure or accept the final Morwen body.

The bounded improvement finding is not a final-art PASS. No face, hair, garment or rig acceptance is implied.

## Evidence inspected

I inspected all five before/after close-up pairs (shoulder front/back/right, knee front/right), all four after full-body views, and the shoulder and knee wire diagnostic PNGs. The existing official Layer 0 four-view images and the earlier v02 independent review supply the reference context; no reference source was downloaded or reverified.

I read `local-targets.json`, the local source and stored-coordinate delta archives, and both `sculpt_local_surface.py` and `render_local_surface.py`. I independently reopened the actual source `MORWEN_BODY_FIT_V02_UNAPPROVED.blend` and the saved `MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend` in Blender 4.3.2, with scripts disabled. I did not edit geometry or rerender it.

## Independent geometry and protection observations

| Check | Independent result |
|---|---|
| Source and local control counts | 12,502 vertices / 12,500 faces, both files |
| Face index lists preserved | Yes |
| Finite coordinates | Yes |
| Changed vertices above 1e-7 world-space delta | 3,422 |
| Fixed vertices | 9,080 |
| Fixed vertices' stored local coordinates | Exactly identical |
| Maximum world delta outside free patch | 0 |
| Maximum world delta within edited mesh | 0.0236747221 normalized units |
| Mean world delta in free patch | 0.0078312234 normalized units |
| Central chest mask | 346 vertices, exactly unchanged |
| Waist test band | 807 vertices, exactly unchanged |
| Pelvis test band | 1,731 vertices, exactly unchanged |
| Chest measurement-band bounding planes | Identical before and after on X, Y and Z |
| Saved candidate reopens | Yes |

**Protection caveat:** The chest measurement band contains 104 vertices; 34 of them move in the lateral upper-thorax/axilla editing area. The central protected chest surface and the measurement extrema are preserved, but the entire chest band is not coordinate-identical. Do not describe this result as “every chest vertex unchanged.” This is a scoped observation, not evidence of a new waist or pelvic change.

The diagnostic wire images show rendered triangulation as well as the underlying control surfaces. They are not evidence of new retopology. The actual face index lists remain unchanged.

## Visual assessment

### Shoulders and axillae

The v02 source has pointed superior shoulder corners, a triangular torn-looking shading transition beside the upper back, and a pronounced angular notch at the arm attachment. In the local v01 front and rear views, those small spikes and the sudden upper-arm transition are reduced. The side shoulder surface now joins the upper arm through a more continuous curved region. This is visible both close-up and at the whole-body scale; it is not merely a camera change.

Residuals remain. The shoulder tips now form a broad rounded cap with an extended sloping upper contour. This removes the pointed source corner but does not yet reproduce the reference's restrained, natural shoulder outline. The axillary/side-chest groove is still deep and has an abrupt transition into the protected chest planes. The back view also retains conspicuous planar shoulder-blade/axilla bands. Thus I accept a reduction in the original discontinuity, not anatomical or reference-fit acceptance.

### Knees and lower legs

The knee-front pair shows less block-like banding and a gentler connection between thigh, knee and calf. The right profile also has a smoother curvature transition rather than the source's short angular crease. The narrowing and repositioning of the local leg surface are visible, while the source foot and upper-thigh boundary stay fixed.

The standing-leg silhouette remains unresolved. In profile, the knee/shin centerline still changes direction strongly compared with the illustrated relaxed leg. The anterior knee reads as a relatively flat, softly narrowed band rather than an intentionally authored patella/tendon transition. The front-view leg spacing and inner/outer knee contours do not establish four-view reference agreement. The drawings are not calibrated orthographic scans, so I have not assigned a falsely exact anatomical knee-angle error.

### Protected torso and overall result

The waist and pelvic outline appear unchanged in the fixed-camera full-body views, consistent with the independently checked zero coordinate delta in those regions. The central chest also retains its source planes. No new whole-body scaling, head-size change or hand/foot relocation is visible in this local operation.

The result still contains faceted chest/hip/thigh planes, generic source facial anatomy and unresolved feet/stance. Those are not new regressions caused by this scoped edit, but they continue to prevent whole-character G2 acceptance. They should not be silently corrected by reopening the stopped global cage approach or by expanding the present edit outside its approved region.

## Is this the stopped global-cage method repeated?

**No: the causal geometry operation is materially different.** The earlier full-body trials transformed coordinates through height/width/depth stations and a region classification blend. This edit solves positions jointly using mesh-edge adjacency and hard exterior constraints, with anatomical handles only inside selected shoulder/leg patches. Its use of the original coordinates to identify the patch does not rerun the earlier global cage. The independent coordinate check confirms that the exterior is actually pinned, rather than only declared protected.

This is a Python-authored local vertex-surface edit. It is not manual GUI sculpting and not retopology. The old full-body cage family remains stopped after its two failed trials. This local adjacency-surface method is a first local attempt; it does not reset old counters.

## Gates and next useful body edit

- G1 body source: previously established PASS; not rerun here.
- Local surface-discontinuity improvement: narrowly scoped PASS as explained above.
- **G2 local canonical anatomy: FAIL; whole-body G2: FAIL.**
- G3 full character: NOT_RUN. My reopen, finite-coordinate, protected-region and topology-preservation checks are limited screens only. I did not certify self-intersections, manifoldness, UV distortion, skin deformation or rig behavior.
- G4: NOT_RUN.

Keep this genuine local improvement and its before/after evidence. The next scoped edit should intentionally shape the deltoid/axilla volume and the patella/shin transition against the existing reference views while retaining the proven fixed torso boundary. Do not equate additional generic smoothing with a solved anatomical target. Continue body QA before detailed face, hair, garments or rigging, and retain the source, the stopped cage trials and their failure history.

## Supplemental author diagnostics — separate from independent findings

The author subsequently reported shoulder extent error 18.58→2.33 px and knee extent error 26.94→4.27 px, while the protected waist/pelvis/chest bounding planes remain unchanged. These measurements are consistent with the visible local silhouette changes, but I have not independently rerun the target-band selection or treated those errors as calibrated anatomical accuracy.

The author also reported that large normal-change flags relative to the original body source change from 38 to 36, with **17 old flags removed and 15 new flags introduced** around the side-chest/axilla/upper-arm boundary. The smaller total therefore does not establish a clean technical improvement. The new flagged area coincides with my visual concern about a deep, abrupt axillary transition. A source-relative normal change is not on its own proof of inversion or self-intersection, but these new flags must remain an unresolved local technical concern; successful rendering and smoothing do not clear them.

A controlled anatomical surface patch with deliberately authored boundary flow is a credible next alternative if the deep axillary groove cannot be resolved by this local fairing method. Preserve the fixed central chest/waist/pelvis and the current improvement checkpoint. Do not spend repeated fairing iterations merely trading old flagged faces for new ones.
