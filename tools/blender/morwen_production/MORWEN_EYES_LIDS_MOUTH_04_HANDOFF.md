# MORWEN-EYES-LIDS-MOUTH-04 — production handoff

Status: authorized next non-destructive task; NOT YET IMPLEMENTED. Base: Draft PR #313 (`feature/morwen-local-retopo-03-review`), which reviews #312. Create a new dedicated branch and Draft PR; do not alter #313, #312, main or canonical assets.

## Sources and decisions
Before execution read latest main and branch AGENTS.md, docs/art/QUALITY_FIRST_3D_PIPELINE_V1.md, HEAD_STRUCTURE_01_AUDIT.md, HEAD_LANDMARK_02_REPORT.md, MORWEN_HEAD_TOPOLOGY_LAYER_ROADMAP_02.md, NOSE_RETOPO_03_REPORT.md, REVIEW_03R.md and the cumulative attempt ledger. Recheck official private lore/addenda/status and Layer 0 four-view source SHA; v5.61 canonical binary is still unverified/unavailable and full G1 remains BLOCKED. Approved 3D quality target SHA256: 7640822cfeb6c3de5b988a79e438babfaf7e3dafbdbc8433ae6cde78f3988957.

**Locked candidate for subsequent construction only**: retain the exact PR #312 nose geometry and `MORWEN_DESIGN_NoseDepth=0.5`; conditional local art acceptance is not full-head G2 PASS. Preserve original shape hash, source, shape-key transfer and 0.5 setting. Do not retry RBF nose edits or remake the nose.

## Priority A: eyelid intersection fix + eye design
1. Measure the actual intersections of blink plate/eyelid/skin in neutral, Blink, Blink_L, Blink_R, Joy and Surprised, with coordinates, penetration depth and affected faces. No blanket z-offset or arbitrary floating eyelash cards as final fix.
2. Create anatomically coherent eyelid rim loops (three concentric loops as starting topology, adjust only as warranted by deformation) with closed-eye arc and stable corners. Rebuild or rebind eyelash/eyeliner/eyebrow cards to the lid deformation as needed, preserving independent canonical asymmetry.
3. Rebuild the independent sclera/iris/pupil/highlight geometry and material to match official violet eyes; do not stretch old texture plates to fake the proportions. Confirm actual eye opening, pupil spacing and left/right asymmetry against calibrated four-view references.
4. Validate transparency wiring, face culling and alpha edges, including the front hair and future glasses occlusion envelope. Hair and glasses are NOT required to be completed in this task.

## Priority B: mouth
1. Establish mouth corner and lip loops (four concentric loops as a starting design), maintain continuous cheek topology and mouth interior, and check A/I/U/E/O, Joy, Angry and Surprised without tearing, self-intersection or pinched corners.
2. Transfer and map the existing 56 expression keys and rig weights where supported. Map `target_*` keys to actual VRM blendShapeMaster semantics, not guesses. Report any unmapped or visually unreviewed keys as BLOCKED.
3. Do not alter the jaw/cheek/neck silhouette without calibrated evidence and art approval.

## Review and technical acceptance
- Compare neutral and expression renders at fixed cameras, consistent world-space lighting, front, right/left 45 degrees and full side views; include clay, wireframe, shaded stylized-toon and close-up, and final game-size preview. Final shader is not yet chosen: Cycles Toon BSDF is evaluation-only; investigate actual browser renderer before committing MToon or an engine-specific pipeline.
- Measure penetrations in mm, nonmanifold and inverted faces, UV and alpha issues, eye plate sorting, deformation stretching, and Face/Body seam continuity. Record baseline vs candidate and test against blink/one-eye blink, Joy, Angry, Surprised and all vowel keys. Preserve the 18 still-unreviewed expression keys as BLOCKED until specifically evaluated; prioritize Sorrow, E and 16 unnamed keys by actual affected region and displacement.
- G1 source preservation may PASS, full canonical agreement BLOCKED until v5.61 binary verified. G2 independent art review is mandatory and NOT_RUN until done; G3 PASS only for executed checks; G4 NOT_RUN until actual in-game testing.
- Log each failure with cumulative method family and source hashes; two failures per same method/defect triggers stop and a method switch. No prototype primitives accepted as final.

## Deliverables
Blender Python scripts, reusable param files, measured JSON, render comparison sheets, deformation/penetration reports, CI workflow, shared attempt ledger, exact SHA and Draft PR link. Preserve .blend in CI artifact if too large for Git. No merge, canon replacement or release.
