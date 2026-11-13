# MORWEN-LAYER0-PRODUCTION-GATE-01

Status: DESIGN / NOT APPROVED AS AN ASSET. Created after successful 16-frame diagnostic render on GitHub Actions run 43373568803 (commit a382e36). This document does not replace any canonical reference.

## Canonical source policy
- The latest formally approved Morwen Layer 0 four-view images are the visual source of truth. Do not derive final proportions from the primitive diagnostic mesh.
- Official images must be present in the GitHub Actions job, with filenames, image dimensions, and SHA-256 recorded in a source manifest, before any claim of G1 approval.
- Preserve the original images byte-for-byte. Unknown design details remain UNVERIFIED, never invented.
- Character local +X is character-right. In front view, the single garter appears screen-right; in back view, screen-left. Garters are NOT symmetrical.
- Knee-high socks, not tights. Final Layer 0 must match the actual approved Layer 0 image rather than costume-layer geometry.

## Layer 0 construction (quality-first)
1. Register front/right/back/left official references as orthographic image planes in a common coordinate system; lock scale, floor anchor, eye line, and camera orientations.
2. Construct an anatomically coherent continuous base mesh (head, neck, torso, shoulders, arms, hands, hips, legs, feet), with meaningful topology around shoulders, elbows, hips, knees and ankles. Primitive assemblies are allowed only for intermediate measurements.
3. Use a reproducible Blender Python build script with recorded Blender version, parameters and deterministic seed. Separate base geometry from hair, clothing and accessories.
4. Render orthographic RGBA front/right/back/left at identical scale, fixed floor contact, neutral pose and lighting. Keep render configuration and output manifest in the artifact.
5. Review four views at full resolution and final in-game display size. Do not promote to production without independent art review.

## Quality gates
- G1 Canon: reference hashes present and verified; front/side/back proportions, silhouette, orientation and asymmetric details inspected against approved references.
- G2 Art: no primitive-only final silhouette; believable anatomy and topology, smooth transitions, refined forms and intentional materials; review all four views.
- G3 Technical: Blender run SUCCESS; four valid RGBA PNGs, consistent dimensions, anchors and scale; Blender source, source manifest, build metadata and QA JSON included.
- G4 Integration: evaluate intended pixel footprint, transparency, memory/render cost and compatibility without changing existing game assets.
- A successful technical render is **not** G1/G2/G4 approval. Diagnostic 16 PNGs are NOT production assets.

## Execution rule
Use feature branch and Draft PR only; do not merge to main, overwrite canon, deploy to game or publish website. Stop after two failures of the same method and analyze the root cause.
