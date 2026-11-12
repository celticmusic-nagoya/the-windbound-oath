# MORWEN-BLENDER-19 | Stylized game / VTuber modeling direction

Status: **measurement and design baseline, not art approval**.

## Production reference principles
- Modern stylized game characters: strong silhouette, legible shape hierarchy at gameplay camera scale, low-frequency forms before costume detail.
- VTuber / VRM avatar workflows: deliberate face and torso proportions, edge-flow around shoulders and joints, smooth deformation under armature, consistent orthographic turnaround.
- Use general modeling techniques only; do not copy another artist's mesh or proprietary character design.
- **Canonical Morwen v3.0 PNGs remain the only design authority.** Preserve asymmetric costume, hairstyle, knee-high socks and existing left-facing exclusions. Do not add arms, legs, hair or costume to the current torso-only candidate until approved.

## Diagnose the previous failure
BLENDER-16/17/18 produced technically valid meshes, but width/depth parameters were guessed from **rig joint coordinates**, not the outer silhouette. The rig points at chest/waist/pelvis describe internal anatomical landmarks; they are not contour edges. The smoothstep interpolator cannot recover missing contour measurements.

## BLENDER-19 stages
1. Generate the BLENDER-18 baseline and measure actual torso cross-sections at canonical chest, waist and pelvis heights. Publish machine-readable values; do not claim image-fit.
2. Obtain the front, left, right and back silhouette contours of the **approved reference PNGs**. Distinguish costume outer edges from intended base anatomy; no arbitrary body geometry inferred from clothing.
3. Normalize scale and ortho framing. Establish front/back and left/right contour targets with a human-reviewed anatomy proxy; document uncertain sections.
4. Shape ribcage and pelvis as two primary masses, linked by soft oblique/waist planes; establish neck/trapezius and clavicle transition, lumbar lordosis and anterior abdominal plane.
5. Render unlit flat silhouette passes and neutral clay passes from all four orthographic cameras; compare silhouettes at identical framing, then inspect from 3/4 views.
6. Only after artistic approval: design shoulder/hip attachment edge loops and skinning.

## Gate
- Reference SHA-256 4/4 unchanged.
- Baseline measurements reproducible; 4 views and mesh topology pass.
- Silhouette contour QA and 3/4 art review **NOT_RUN** until contour targets are reviewed.
- Keep Draft PR; no main merge, production use or publication.
