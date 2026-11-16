# Aidan masonry — production method switch / scan-derived organic shells (2026-11-16)

## Decision / root-cause evidence
Prior block-based relief run 43789139055 passed bounded technical checks but **failed G2** after visual review: rectangular silhouettes, unnaturally smooth flat caps and insufficient detail at 48px. This is a **method-family stop** for primitive blocks + procedural noise. Do not increase noise amplitude or subdivision counts to claim an art fix.

## Canonical constraints
Preserve all canonical house assets, colors, dimensions, asymmetry and source files. The architecture master dimensions are not yet verified (G1 BLOCKED). No main merge, publication or overwrite. Only CC0 scan `rock_moss_set_01_8k.blend` with pinned SHA256 `23d6220c6c7613c4d7006d902ac99acebc7e7859f1368ba6dc0ae4123551cdc6` may be used as a source until further licenses are documented.

## New construction method
1. Build each stone as an **independent organic sculpt/scan-derived shell**. Fit its 3D silhouette to a joint-first contact envelope; do not start with cubes and perturb their faces. Retain original scan mesh or authored sculpt separately and record its hash.
2. Derive the hidden bearing and mating interfaces by **non-destructive trim/Boolean intersection**, then remesh or stitch the cut rim while retaining an exactly planar contact patch. Any trimming must preserve at least the original supported contact area. Prefer robust manifold Boolean + explicit triangulation over manually guessing gaps.
3. Ensure stones have visible irregular outer contours and distinct broad/medium/fine features, weathering, and meaningful edge breaks at game view. Do not hide visible cavities with a solid slab.
4. PBR: use documented CC0 texture maps or authored materials; save source/license and color-space metadata. Do not claim source textures were used unless actual Blender nodes and files prove it.
5. Deliver three camera views, **48x48 and 96x96** image crops, source Blender/Python, source asset SHA, exact Blender version, deterministic seed and JSON mesh QA. Show the final 48px result without zooming.

## Independent QA (Codex or local automated checks)
- Actual mesh geometry: manifoldness, zero boundary edges, face normal consistency, degenerate triangles, signed interpenetration (distinguish touching BVH candidates), unsupported upper contact area, and visible gaps.
- Contact surface: compare exact evaluated cap coordinates/area against baseline from run 43789139055; report any change.
- Rendering: PNG dimensions, transparency requirements if game sprite, alpha correctness, PBR nodes and texture licensing.
- G2 requires human independent comparison of 48px and three-angle views to canonical house reference. CI alone never makes G2 PASS.

## Delegation trigger
Claude: organic modeling and material authoring, isolated candidate branch. Codex: independent geometry QA and negative tests, isolated QA branch. ChatGPT: baseline protection, artifact review, QA classification. These are **instructions, not evidence of Claude/Codex execution**. Trigger when an agent is actually connected/available; no paid API automatically.
