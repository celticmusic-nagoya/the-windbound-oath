# MORWEN EYELID-09 | Failure prevention and hybrid production gate

Status: candidate-only design review; no canonical changes.

## Verified failure ledger (do not reset counts on renames)
1. BLENDER-16: four-view technical render PASS, independent art QA FAIL (official silhouette and detail). A renderable mesh is not an approved character.
2. EYELID-09: 18 lash strips, 216 vertices, 90 faces; cage BVH triangle-pair intersections R=59, L=64 (123 total), eye overlaps=0. This is a geometric FAIL, not a CI infrastructure failure.
3. Blender 5.3 Set Mesh Normal attempt: requested a nonexistent enabled Normal socket while node was in default Sharpness mode. Do not retry identical API assumption. The official Blender 5.3 manual documents mode-specific Custom Normal inputs (Free/Tangent Space); mode must be set before socket access, and actual enabled sockets inspected.
4. Blender 5.3 Set Shade Smooth attempt: mesh input has display name Mesh but stable identifier Geometry. Corrected by inspecting sockets; CI run 43781290221 PASS.
5. Synthetic flat/smooth rendering: run 43781843437 PASS technical; 8 vertices/5 faces each; PNG evidence hash a144800419ad9f1001760017191d1802ae520fb2d41418aabd13450d8e2dbffb. Art QA NOT_RUN; this does not prove successful Morwen hair or eyelash geometry.

## Root cause / prevention
- World-up lash direction in build_candidate_strips_09.py is a scaffold independent of actual eyelid tangent and outward surface normal. The root offset 0.00015 m and increasing offset are not verified to clear the 50%-closed cage. Stop blind parameter nudging.
- Diagnose per-strip BVH pairs and root index before modifying geometry; preserve the previous failing artifact and input SHA.
- Use a local frame derived from 75 saved lid-margin points per side: tangent from neighboring points; cage outward normal orientation validated against eye center and signed surface clearance; growth direction and thickness independently constrained. If orientation cannot be proven, BLOCKED.
- Sweep eyelid closure and compare against eye/cage geometry; no single-frame PASS can substitute for swept collision and containment/occlusion QA.
- Rendering sequence: geometry clearance and topology -> normal/shading -> UV/material/projection/bake -> orthographic four-direction comparisons -> 48px/Android view. Record per-stage hashes; never use image projection to hide silhouette or collisions.
- Do not call a technically valid PNG art PASS. Independent human art review must compare to approved canonical design.

## Hybrid technique selection
A. Blender Python / Geometry Nodes: deterministic surface-aware construction, BVH and technical QA, headless GitHub Actions; primary automated route.
B. Curve-guided stylized hair meshes and modular strand groups: model hair volumes with deliberate quad topology and localized rerendering; keep eyelash root geometry separate from hair. The HairMesh Blender 5.1+ add-on (https://github.com/riel-gab/hairmesh) uses curve walls to build quad locks; GPL-3.0-or-later source must be reviewed before integrating code, and headless API compatibility remains NOT_RUN.
C. HairHarpy v2.0: reference technique for curve/volume silhouette, not assumed runnable in headless CI; GUI/Vulkan dependency and license must be reviewed separately.
D. Canonical image-guided UV/PBR/projection: only after geometry clearance and verified original images. Left-side asymmetry, approved accessories, and knee socks must remain intact.

## Quality gates
G1 BLOCKED: actual v5.61 canonical image binaries not matched.
G2 NOT_RUN: independent art QA and final-size views.
G3 FAIL: 123 cage triangle-pair intersections for prior strips; synthetic shading render PASS only.
G4 NOT_RUN: game integration, performance and Android device.

## Immediate exit criteria
- Collision diagnosis report for all 18 strips with exact counts and hashes.
- One mathematically defined surface-aware construction approach; no repeated world-up scaffold tweaks.
- Only when BVH overlaps=0 and additional containment/motion checks are available: begin candidate four-direction rendering. Otherwise retain FAIL and revise structural design once.
- No main merge, canonical replacement, or publication without explicit authorization.

## Reference sources (research, not imported assets)
- Blender 5.3 Set Mesh Normal: https://docs.blender.org/manual/en/5.3/modeling/geometry_nodes/mesh/write/set_mesh_normal.html
- Blender 5.3 Set Shade Smooth: https://docs.blender.org/manual/en/5.3/modeling/geometry_nodes/mesh/write/set_shade_smooth.html
- HairMesh (curve-wall quad workflow): https://github.com/riel-gab/hairmesh
- HairHarpy evaluation: HAIRHARPY_EVALUATION_01.md
- 3dnchu technique shortlist: 3DNCHU_TECHNIQUE_WATCH_20261116.md
