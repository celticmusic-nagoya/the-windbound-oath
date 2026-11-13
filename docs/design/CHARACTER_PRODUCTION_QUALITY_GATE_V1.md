# Character Production Quality Gate v1.0

Status: ACTIVE FOR NEW CANDIDATES; existing approved assets are immutable. Scope: character Layer 0, Layer 1–3, rig, animation, sprites and their QA. This document supplements AGENTS.md; conflicts defer to AGENTS.md and approved canon.

## Mandatory production sequence
1. **Canon intake**: identify the exact approved front/side/back reference, record SHA-256 and provenance; do not infer unseen surfaces. Preserve left/right asymmetry, accessories, hair, clothing and character age.
2. **Reference calibration**: use orthographic reference planes in Blender, align camera, scale and floor anchor. Establish measurable landmarks from the actual pixels, with confidence labels. Never treat rough estimates as measured truth.
3. **Production mesh**: create an intentional stylized character mesh with deformation-ready topology and edge loops at shoulders, elbows, hips, knees and neck. Primitive cones/spheres are allowed only as disposable blockout, never as art-ready evidence.
4. **Visual gate BEFORE rigging**: render front/right/back/left under identical camera scale, lighting and neutral pose. Compare silhouette, proportions, facial/hair profile and asymmetric details against each corresponding approved view. Record mismatches, not just technical output status.
5. **Rig/skin**: reuse the compatible master rig; apply continuous weight gradients near joints and evaluate deformation with diagnostic poses. Rigid 100% part weights are permitted for nondeforming props, not a production humanoid body.
6. **Motion**: test foot plant, knee direction, arm swing, floor contact, seamless loop and 4-direction consistency. Produce 32-frame sprite sheet only after mesh/rig art gates pass.
7. **Delivery**: keep candidate files in assets/candidates/, generate independent QA report, visual comparison and artifact ZIP. Promotion to canonical assets requires explicit director approval.

## Stop / switch rule
- **Immediately STOP** a method when it cannot reproduce approved design or meet production quality, even if CI is green.
- Two materially similar failed attempts maximum. Do not keep tweaking a primitive placeholder. Document structural cause and switch to a different method (retopology over orthographic references, sculpt + retopo, or deliberate manual mesh edits).
- Do not claim art PASS based on Blender execution, frame counts, transparency or hashes.
- When the original reference cannot be accessed or visually compared, status is BLOCKED, never PASS.
- Prefer proven Blender mesh/UV/rigging practices and game-production workflows; adapt them to this project's 2.5D/orthographic sprite pipeline, without copying proprietary game assets.

## Decision for MORWEN-BODY-04
**STOP AS ART PATH.** The primitive body candidate and head-width adjustments are archived as technical experiments only. Further parameter tweaking of the same geometry is prohibited as a route to canon. The next implementation is a reference-aligned continuous topology mesh, then an independently reviewed 4-view silhouette gate. The previous green CI remains valid for technical execution only.

## QA report fields
`source_sha256`, `reference_available`, `view_alignment`, `silhouette_comparison`, `topology_deformation`, `asymmetry_check`, `art_qa`, `technical_qa`, `promotion_eligible`, `attempt_count`, `next_method`.

Every field must be explicit; unknown = NOT_RUN or BLOCKED, never silently assumed PASS.
