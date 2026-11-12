# MORWEN-BLENDER-03 — single 3D neutral prototype

**Status: CODE_READY / BLENDER_NOT_RUN / VISUAL_QA_NOT_RUN.** This is a proposed Blender builder, not a finished .blend. The source 4-direction 2.5D PR #246 remains untouched.

Run in a checkout containing PR #246 inputs:

```sh
blender -b -t 1 --python-exit-code 1 --python tools/blender/morwen_blender_03/build_unified.py
```

Expected outputs (only after a successful Blender run): `assets/candidates/morwen-blender-03/morwen_unified_neutral_candidate.blend` and `build_report.json`.

The script loads PR #246's existing .blend and adds a single 17-bone armature with one mesh **object** (16 rigidly weighted, disconnected ellipsoid segments). It does **not** claim a watertight skin, realistic anatomical depth, finished hair/costume, animation, approval, or a complete multiview reconstruction. The front image anchors drive X/Z; left/right profiles provide provisional Y depth; back anchors are not yet used to optimize geometry. This is deliberately a fast technical prototype for review.

## QA gate
1. Run Blender 4.x headless and confirm output, reopen and check all 17 bones, 16 vertex groups, valid mesh.
2. Inspect front/right/back/left orthographic projections against exact reference PNGs; measure reprojection error, preserve asymmetry and grounding.
3. Inspect pelvis, shoulder and head depth; hidden side landmarks are still uncertain. If visible errors are material, adjust source-driven constraints, not original art.
4. Run independent mesh/weight deformation QA. Only then start continuous skin and costume.

No main merge, formal adoption, runtime integration, website publishing or legacy cleanup. Source references remain REFERENCE_ONLY.
