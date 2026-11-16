# MORWEN 3D — Production Method Reset (2026-11-16)

Status: PROPOSED PRODUCTION METHOD; NOT character/art approval.
Scope: feature/morwen-fable-eval-01 / Draft PR #339. Canonical source files are immutable.

## Decision
Adopt **full-body design first, high-quality base mesh + sculpting, modular component construction, retopology, rigging, baking, game optimization**. Do not iterate the current ellipsoid head + tubular strand generator toward final art. Retain it as rejected technical evidence.

## Evidence
- Actions run 43866841140, commit fb0f2b57: six jobs succeeded, five head renders saved.
- Five-view visual inspection: severe blown-out appearance, generic ellipsoid face, tubular strands; G2 FAIL.
- This is one distinct candidate method; do not reset attempts with superficial parameter tweaks.
- Blender Studio Stylized Character Workflow: https://studio.blender.org/training/stylized-character-workflow/
- Blender Studio Modeling: https://studio.blender.org/tools/artist-guide/asset-creation/modeling
- Blender Studio Rigging: https://studio.blender.org/tools/artist-guide/asset-creation/rigging
- MetaHuman stylized mesh/rig workflow: https://dev.epicgames.com/documentation/metahuman/metahuman-stylized-character-character-geometry-and-rig-creation

## Immutable inputs
assets/canonical/morwen/2026-11-16/MANIFEST.json and its five images. Verify hashes before every build. Target proportions: 7.5–8.0 heads per director approval, not a license to alter identity, asymmetric hat, accessories, or costume.

## Stage gates and outputs
0. Environment lock: record Blender/Python/bpy versions, render engine, color management, seed, hashes; establish neutral gray and material diagnostic renders. Detect clipped RGB areas on nontransparent subject pixels; **do not** label art QA PASS.
1. Full-body character design: fixed front/back/left/right silhouette, measured landmark table and camera reference, 7.75-head target; **no final asset until director/canon alignment**.
2. Anatomical base: use licensed, editable human topology or sculpt-ready mesh; sculpt head, torso, limbs to approved silhouette. Avoid purely procedural ellipsoid stand-ins.
3. Modular hero parts: sculpt bob hair as overlapping broad locks/surfaces; independently model eyes, round gold glasses, asymmetric hat, clothing, cloak, shoulder crest, bag/strap, vials, right-leg garter, socks, buckled boots. Keep asymmetric details asymmetric.
4. Sculpt review: neutral material turntable + color/material turntable; 5 orthographic views, close-ups, screen-size views. Art reviewer records discrepancies before retopo.
5. Retopology/UV/bake: animation-ready loops, texture atlas, normals/AO; validate manifold and intersections where needed.
6. Rig and deformation: armature, weight painting, face/limb pose QA; GLB export; Android/WebGL profiling, LOD if justified by measurements.

## CI separation
- technical QA: source hash, file existence, dimensions, mesh sanity, image visibility/clipping.
- art QA: explicit visual review, never inferred from CI green.
- game QA: Android/WebGL runtime measurements and interaction checks.
- canonical promotion: BLOCKED until G1/G2/G3/G4 PASS and explicit approval.

## Immediate actions
A. Implement **render visibility QA** for existing five PNGs, flag overexposure, prevent misleading PASS.
B. Establish a neutral-lit, calibrated diagnostic scene independently of mesh sculpt.
C. Locate or create a suitable legally usable high-quality human base mesh; record license/source and verify proportions.
D. Build full-body landmark sheet and module ownership plan before new detailed modeling.

## Current gate state
G1 BLOCKED (new mesh not matched to canon); G2 FAIL (five renders); G3 PARTIAL PASS (Blender saved 5 PNGs; image quality failed); G4 NOT_RUN.
