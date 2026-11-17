# Independent art QA — fixed anatomical quad-patch candidate v01

Reviewer: `/root/body_art_qa`, separate AI reviewer, not the patch author. Date: 2026-11-17 UTC. This is independent AI QA, not human artist review or Android/device QA. No geometry was changed by the reviewer.

**Local anatomical art acceptance: FAIL. Whole-body G2: FAIL.** Actual local topology replacement and protected-region preservation are verified. The saved candidate is an executed intermediate mesh, but it is not a successful anatomical reconstruction or a deformation-ready character.

## Evidence inspected

- Saved candidate: `assets/candidates/morwen-rebuild-01/body-quad-v01/MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED.blend`.
- Source: the retained `body-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend` and its existing after close-ups, which serve as the before images for this patch task.
- Candidate rest front/back/right/left, shoulder front/back/right close-ups, knee front/right close-ups, and actual polygon-edge shoulder/knee wire diagnostics.
- Corrected shoulder 30°/60° full and close diagnostic images, and knee 45°/90° close diagnostic images. Initial invalid shoulder-weight evidence was read separately, not treated as the final test or as a rest-mesh defect.
- `quad-patch-recipe.json`, `candidate-mesh.json`, `correspondence-qa.json`, `self-intersection-qa.json`, current `bend-qa.json`, the apply/diagnostic scripts, and the prior independent warning analysis. No canonical reference images were downloaded or rehashed.

I independently reopened the source and final saved candidate in Blender 4.3.2 with scripts disabled. I compared stored coordinates and the stable source-ID attributes. After the diagnostic setup correction, I also verified that the saved rest mesh coordinates still exactly match the pre-diagnostic candidate record.

## Independently verified mesh and protection facts

| Observation | Result |
|---|---|
| Original local source | 12,502 vertices / 12,500 faces |
| Fixed patch candidate | 12,436 vertices / 12,493 faces |
| Source faces retired | 747 |
| New patch faces | 740: 622 quads and 118 triangles |
| Whole candidate face types | 12,375 quads and 118 triangles |
| Retained exterior faces | 11,753 |
| Retained exterior ordered cyclic source-vertex ID lists | Preserved |
| Protected source vertices | 9,080, all stored local coordinates exactly preserved |
| Open boundary edges | 0 |
| Edges with more than two incident faces | 0 |
| Finite stored coordinates | Yes |
| Rest mesh equals saved Basis | Yes |
| Rest mesh equals pre-diagnostic candidate coordinates | Exactly |
| Four diagnostic shape-key values at save | All zero |

This is a **quad-dominant local topological replacement**, not an all-quad model and not another unchanged source scene. The source-ID mappings make the preservation claim reviewable despite changed vertex/face allocation. These facts are useful technical evidence but do not certify the anatomical surface, self-intersections, UV usability or production deformation.

## Art findings at rest

### Shoulders and axillae — visible regression

The local-v01 source had an overly broad shoulder cap and a deep axillary groove, but its upper shoulder contour had become comparatively continuous. The new patch introduces conspicuous radial ridges and narrow folded-looking depressions across the superior/anterior shoulder. They are visible in the front close-up and remain visible in the full-body render. The right close-up shows a sharp triangular indentation where the deltoid/axilla patch meets the retained chest. The back retains a deep, abrupt upper-arm-to-thorax channel.

The wire view proves that different faces were constructed; it does not show a successful anatomical deltoid, pectoral insertion or axillary surface. A plausible shoulder must carry continuous volume through that area. Here the numerical width is retained while the intervening surface becomes more visibly folded and uneven. I do not accept unchanged shoulder width as evidence that this region improved.

### Knees and shins — surface quality and curvature remain unacceptable

The source-local knee was soft and somewhat flattened. In the new front close-up, the patellar/front-knee area has a conspicuous alternating triangular/checkered shading pattern, especially on the image-right leg. The polygon wire confirms a new local face arrangement; the visible pattern is not sufficient evidence of clean anatomical flow. In profile, abrupt triangular plane changes remain above and below the knee and there is a marked directional break towards the calf.

The knee's measured outer extent remains close to the source-local value, but that does not establish a patella, tendon transition or a natural standing-leg silhouette. The new surface is not an artistic improvement sufficient for local acceptance.

### Protected body proportions and regressions outside scope

The retained central chest, waist and pelvis appear consistent with the source. Independent coordinate/source-ID checks support the protected-region claim. No additional global body scaling, head resizing or hand/foot relocation was found in the stored rest mesh.

Those protections do not rescue the changed shoulder and knee surfaces. The whole body still inherits generic source anatomy and the previously unresolved stance/feet. Face, hair, costume and final materials are outside this edit's scope; their absence is not the basis of this local FAIL, although no full Morwen identity or commercial-final-quality claim can be made.

## Warning tracking: valid evidence of work, not art acceptance

The author's correspondence report tracks four barycentric/harmonic-domain samples from each old flagged region onto actual new triangles. It reports 13/15 old warning regions inside its normal-angle threshold, with old regions 3859 and 10002 still failing at one or more samples. This is a materially better procedure than counting deleted face IDs as cleared warnings.

I read the correspondence method/results but did not independently rerun the full harmonic sample finder. The independent art finding remains FAIL because a source-relative normal threshold can improve while a new patch has folds or penetrations. The 13/15 result must not be described as 13 anatomically repaired regions.

The author's extent checks report shoulder width error unchanged at about 2.333 px, knee error 4.268→4.318 px, and chest/waist/pelvis extents unchanged. These describe retained dimensions within that measurement convention, not surface quality or a calibrated match to the illustration.

## Collision and quad-fold screening — still FAIL

I read the current explicit collision/fold diagnostics and checked the described failing regions against the visible rest candidate. These numerical tests are the author's execution results, distinct from my independent reopen/protection checks and visual findings.

- Rest candidate: 89 strict nonadjacent polygon-pair penetrations involving a new patch; adjacent-face interior penetrations are recorded separately (11 globally).
- Rest candidate: 27 new-patch quad-fold flags under the both-diagonals test; 40 flags across the entire body.
- Full-body strict polygon-pair counts in the same current diagnostic are 270 for the local source and 303 for the candidate. Since tessellation and polygon allocation changed, a raw pair-count difference is not itself an anatomical error measure. Nonzero confirmed candidate patch penetrations and folded quads are already sufficient to fail the changed-region screen.
- These counts are not directly comparable with the earlier independent analysis's 59-pair restricted local/triangulation screen. Scope, triangulation and adjacent-pair classification must remain explicit.

A closed mesh, finite coordinates and retained boundary topology do not exclude these defects. The candidate must not receive G3 acceptance from its successful save/reopen, its new quad count or its reduced old-warning count.

## Diagnostic shoulder-weight correction versus actual geometry

The initial shoulder diagnostic mistakenly selected waist/upper-thigh vertices as part of the moving region. Its misleading pelvic deformation belongs to a diagnostic weight-selector bug, not a new rest-body deformation. The initial JSON and a representative PNG were retained in `initial-diagnostic-setup/`.

I inspected the corrected shoulder 30°/60° images. The spurious pelvic participation is no longer visible, and the 60° framing includes the full pose. Broad axillary webbing and severe surface stretching still appear between the lifted arm and torso. Because this is a temporary rotation-weight shape-key stress test rather than authored production skinning, I do not attribute every aspect of the webbing solely to the new topology. It demonstrates that deformation readiness has not been established; it does not replace rest-mesh collision evidence, which already fails.

The saved Basis/rest coordinates exactly match the fixed pre-diagnostic candidate. Correcting the selector/framing did not constitute a second geometry attempt.

| Corrected diagnostic pose | Patch-involved strict penetration pairs reported | Patch quad-fold flags reported |
|---|---:|---:|
| Shoulder 30° | 42 | 23 |
| Shoulder 60° | 42 | 34 |
| Knee 45° | 89 | 27 |
| Knee 90° | 89 | 32 |

The knee diagnostic images also show substantial compression/folding around the bend. These are failed diagnostic deformation checks, not completed rig/animation work. The corrected bend validation remains FAIL.

## Method classification and handoff

The source-ID evidence and actual deleted/new face connectivity confirm a genuine change from the earlier coordinate-cage and topology-preserving fairing methods. This candidate performed local face replacement. It is not a third renamed run of the old whole-body cage, and no manual GUI sculpting or human-authored retopology is asserted.

However, an executed new method can still fail. The current harmonic/rest-rail patch construction has not demonstrated a coherent anatomical shoulder/knee surface. Keep the fixed candidate and all failure evidence; do not continue geometry retries or shading changes as though the stated acceptance conditions had passed. A later authorized alternative needs explicit anatomical volume/control decisions and collision-safe, orientation-consistent surface construction rather than simply optimizing the warning count.

- G1 body reference: prior PASS, not rerun here; final exterior design authority is separate.
- **G2 local anatomy: FAIL. Whole-body G2: FAIL.**
- G3 limited reopen/protection/topology-preservation checks: PASS in their stated scope.
- **G3 changed-region collision, quad-fold and diagnostic-bend screens: FAIL.** Complete production-character G3 remains uncertified.
- G4: NOT_RUN.

No source adoption, main merge, publication, detailed-face/hair/costume progression or production rig approval follows from this review.
