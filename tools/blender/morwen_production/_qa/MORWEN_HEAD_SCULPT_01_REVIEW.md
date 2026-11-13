# MORWEN-HEAD-SCULPT-01 — visual gate and method change

## Sources and policy
- Task-start checked: main `AGENTS.md`; `docs/art/QUALITY_FIRST_3D_PIPELINE_V1.md`; shared `docs/design/3D_PRODUCTION_POLICY_LOOP_GUARD.md` from `feature/aidan-home-quality-master-01` (not merged to this branch).
- G1 design authority: v5.61 locked Morwen design; approved 3D quality target: `assets/companions/morwen/reference/file_00000000301c8209af49625fd11d7670.png` on `feature/morwen-reference-binary-01`, SHA256 `7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957`.
- Imported VRM source SHA256 `1995f174f6c8f2211f3c56c9e5fe4f9daf27ee5e648f129479582a259238149b` (unchanged).
- Actual render evidence: GitHub Actions run #43503356166, artifact #14075955288, `sculpt_candidate_01_clay/{front,right,back,left}.png`.

## Current attempt result
- Method family: `VRM_LOCAL_JAW_TAPER`. First sculpt candidate: 4.5% maximum local x compression with smoothstep; Face 384 and Body 174 vertices touched according to generated report.
- G1: source protected; **canonical facial resemblance not yet demonstrated**.
- G2: **FAIL**. Four-view inspection: generic face/jaw and disconnected-looking eye-area components, no approved purple bob, hat or glasses, insufficient sculptural and material finish to reach the director's 3D quality target. This is not production-ready.
- G3: **PARTIAL PASS**: four 512px PNGs and artifact uploaded; topology, alpha distribution and image-difference vs baseline not yet independently audited.
- G4: **NOT_RUN**.
- Root cause class: **shape/structure**; stock VRoid face and accessory-less neutral clay rendering cannot achieve canonical likeness through a small cheek taper.
- **STOP** local jaw-taper micro-adjustments for this defect; do not spend another render on a near-identical percentage edit.

## Next method: component-based canonical-fit sculpt
1. Extract front/right/back/left silhouette and landmarks from actual approved design views; distinguish perspective uncertainty from reliable measurements.
2. Make a dedicated, non-destructive face/eye assembly with explicit landmark constraints; retain the source VRM skeleton and body only if compatible.
3. Build volumetric bob hair in independently controllable locks, then hat and glasses as separate parts, not face texture tricks.
4. Render matched orthographic comparisons to the final 3D quality target, record measurable deltas and a human-readable G2 verdict before any production promotion.
5. If manual sculpt is needed, use a legally reusable high-quality mesh base or Blender sculpting; do not substitute primitive-only geometry.

No main merge, no canonical replacement, no production deployment.
