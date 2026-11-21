# Morwen Layer 0 — precision blueprint to actual geometry handoff

Status: DIRECTOR-REQUESTED BLUEPRINT / **REFERENCE MEASURED, 3D GEOMETRY NOT BUILT**. Owner: existing Draft PR #427; no new PR or main merge.

## Verified inputs
- Original four-view images: PR #419 branch `feature/morwen-rebuild-01`, `tools/blender/production_mesh_08/references/{7809,7807,7810,7808}.png` for front/right/back/left.
- SHA256 and dimensions verified by GitHub Actions run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44679568515, artifact https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44679568515/artifacts/14602858760.
- Existing measured silhouette data: `reference_silhouette_landmarks.json` in artifact; documented in `docs/qa/MORWEN_LAYER0_FOUR_VIEW_MEASURED_SILHOUETTE_20261120.md`.
- Visual identity: `docs/qa/MORWEN_LAYER0_VISUAL_LANDMARK_REVIEW_20261120.md`.
- Main policies: `AGENTS.md`, `docs/production/SESSION_CONTINUITY_INDEX.md`, `docs/policy/MORWEN_BLUEPRINT_FIRST_BASE_SELECTION_20261120.md`.
- Reference blueprint v1 (PDF, JSON, four overlaid guide images) prepared separately; **not yet checked in as canonical GitHub files**. Its y-guide values are estimates only and must not be substituted for manual precise landmark measurements.

## Rendering/mesh blueprint contract — proposed, not official world coordinates
- Reference units: pixels, origin top-left; image dimensions 384x1024; alpha threshold >=128. Ground near y=1002 is a *visual estimate*.
- Working local axes: +Z up, -Y front, +X character right; origin ground between feet; absolute height unknown.
- Camera: orthographic is an *assumption to be verified* against the drawings. Use consistent normalized subject height and register subject center/ground for all four views.
- Geometry: independent editable modules for face/head, hair, body, clothing, accessories. Preserve asymmetric fringe and strap/buckle positions. Do not use reference image planes as the final mesh.
- Required mesh data: actual vertices, edges, faces, topology loops, normals, transforms, UVs, material slots, rig bones/weights, shape keys, scale metadata and provenance hashes. No fabricated geometry counts or topology.
- Material groups: skin, eyes, hair, purple fabric, gold trims, sheer/dark stockings. Verify PBR and licensing for actual textures.
- Outputs per candidate: native .blend, glTF/VRM when valid, four orthographic PNGs + three-quarter beauty/clay/silhouette, geometry JSON, QA JSON, source SHA and reproducible CI log.
- Metrics: image-registered alpha IoU, normalized 2D landmark error, hair/face silhouette, deformation readiness, UV validity, source rights and art QA.

## Bounded task allocation
1. **Codex**: read current main/PR #427, fetch the exact original PNGs and measured JSON; author a deterministic image registration + labeled pixel-exact landmark overlay. Store manual landmark annotations with view, coordinates, uncertainty, occlusion and evidence. Run on existing Actions without rerunning the already successful fixture smoke test.
2. **Codex**: inventory a legally usable editable VRoid/VRM candidate, an independently stylized sculpt and the CC0 comparator. If absent, mark BLOCKED. Compare candidates under identical cameras and materials; emit real geometry and render outputs, never proxy spheres/flat face grids.
3. **Claude (only if actually available)**: independently review face-plane volume, hair volume/asymmetry, eye/jaw proportions and costume consistency using the official images and actual candidate renders; record G2 PASS/FAIL with annotated evidence. Do not claim Claude ran unless a real review occurred.
4. **ChatGPT**: audit reproducibility, design reference alignment, SHA/provenance, QA gates, and game integration constraints. No formal adoption until G1–G4 PASS.

## Stop conditions
- Missing source SHA, uncertain canonical status or missing legal source: stop the affected candidate only.
- Repeating the same failed slab/voxel method twice: stop that method and change structure.
- Do not merge, publish, delete, overwrite canonical originals or create another PR without specific approval.

Current gates: G1 PARTIAL (verified image and silhouette, 2D anatomy not pixel-registered); G2/G3/G4 NOT_RUN.
