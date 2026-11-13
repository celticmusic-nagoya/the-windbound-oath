# MORWEN-PRODUCTION-06

**Stage:** canonical reference registration and orthographic Blender scene setup. The actual production character mesh is NOT_BUILT.

The director-supplied reference bundle (4 costume directions, 4 Layer-0 directions, 1 generated target) is packaged separately as MORWEN_PRODUCTION_06_BLENDER_REFERENCE_KIT.zip. Do not replace these references with earlier MORWEN-BODY-04 blockouts.

## Source priority
1. Official costume views and Layer-0 views provided by director
2. Confirmed approved asymmetry and accessory rules
3. Generated 3D visual target (quality target ONLY; never overrides source)

## Blender
Extract the bundle and run:
```sh
blender -b -t 2 --python tools/build_reference_scene.py -- --root .
```

The script checks SHA-256 for all 9 images, creates locked image empties for 4 directions, sets 4 orthographic QA cameras, and saves output/MORWEN_CANON_REFERENCE_SETUP.blend.

## Mandatory next milestone
Reference-plane alignment and camera orientation visual inspection, then reference-matched head/torso/limb continuous topology. No geometric fidelity or artistic PASS may be asserted before real Blender render and 4-view comparison.

## QA
- Local image SHA-256: 9/9 PASS
- Script syntax: PASS
- Blender runtime: NOT_RUN in current execution environment
- Production mesh: NOT_BUILT
- Art QA: NOT_RUN
- Main/canonical modifications: NONE
