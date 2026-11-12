# MORWEN-BLENDER-08 independent visual QA — FAIL

Evidence: Actions run 43225065023, artifact 13946708199; four-view renders inspected.

## Technical results
- Blender workflow PASS, 17 bones, 146 continuous-core faces, 2240 retained limb faces.
- PNG margins PASS; this does not establish valid humanoid geometry.
- Generated core forms an extremely wide horizontal slab/bar across front and back, rather than a vertical torso. Side views show a similarly wide, shallow slab.
- Head is disconnected; arms/legs are slender isolated ellipsoids; colored source guide lines remain visible in render.
- Therefore **ART_QA=FAIL**, **HUMANOID_PROPORTIONS=FAIL**, **PRODUCTION_USE=false**.

## Structural cause
In build_continuous_core.py, the core uses hardcoded x radius 0.40–0.70 world units despite a body height ~0.99 world units, producing an implausibly wide torso. Z range is computed from pelvis/spine bones, not a calibrated shoulder-to-hip surface. Source guide line artifacts are also rendered (non-mesh objects not excluded). Numerical QA checked only nonzero polygon area and positive alpha margins, not anatomical ratios.

## Required next approach
- Do not repeat the same radius tuning blindly.
- Derive x/z bounds from the pinned front-view rig landmarks, and depth from side-view anchors with explicit upper bounds.
- Validate core width / full height ratio and torso height / full height ratio before saving; fail CI on out-of-range values.
- Hide ALL source guide objects, including curves, empties, armatures, except target mesh and camera; do not hide actual limbs.
- Render again and independently inspect all four directions before proceeding to any hair/costume.
