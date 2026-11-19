# 風待ちの崖｜Geometry-to-Blueprint / Codex 実装引き継ぎ v0.1

Status: TECHNICAL SPEC / UNAPPROVED BLUEPRINT / NOT A CANON CHANGE
Owner: map team, existing Draft PR #421; no new PR, no main merge.
Input: C9-B `assets/candidates/lind/windwaiting-cliff-c9/C9-B/C_UNAPPROVED.blend`; C10 script `assets/candidates/lind/windwaiting-cliff-c10/sculpt_c10.py`; latest C10 Actions artifact (SHA-verified). Consult main `AGENTS.md`, `docs/production/SESSION_CONTINUITY_INDEX.md`, private canonical refs, and approved cliff CG before drawing conclusions.
Known QA: C10 topology-only PASS (4 masses, 51 vertices / 36 faces each, no boundary/non-manifold/degenerate edges); independent visual G2 FAIL (visible diagonal green seam, abrupt rock junction, repetitive bands); G1 canonical CG comparison BLOCKED; G3 PARTIAL; G4 NOT_RUN.

## Objective and design principle
Create an **inspectable, numerical production blueprint** from the *actual* editable Blender scene, not a collection of separately hallucinated orthographic images. A blueprint may specify intended landmarks and geometry changes but never assert candidate geometry is canon-approved. Preserve the original .blend and all source hashes. Provisional local coordinates are permitted; world transforms remain pending.

## Codex task 1 — read-only extraction
Implement `tools/production_qa/export_lind_blueprint.py` as Blender 5.3 Python, invoked `blender -b <candidate.blend> --python ... -- <output-dir>`. Do not save/mutate input .blend. Produce deterministic, versioned `scene.json`, `mesh.json`, `materials.json`, `landmarks.json`, `manifest.json`, and `qa.json`. JSON must be sorted/stable and use documented coordinate convention, float precision and Blender version.

- Objects: persistent names, type, collection hierarchy, world/local 4x4 transforms, bounds, parent links, visibility, modifier stack and evaluated/non-evaluated geometry flag.
- Meshes: vertex IDs and local/world XYZ; edges with vertex pairs, seam/crease/sharp attributes when present; polygons with ordered vertex IDs, loop IDs, face material slot, normals, area and smoothing; UV per **face corner/loop** including island/seam metadata; custom attributes and vertex-group weights where present. Record evaluated mesh separately; never conflate sculpt cage and evaluated render geometry.
- Diagnostics: zero-area faces, loose vertices/edges, boundary/nonmanifold edges, normal orientation, duplicate faces, disconnected components, self-intersections and inter-object intersections when computationally feasible. Mark expensive/unavailable tests NOT_RUN, never PASS by omission.
- Materials: material slots, node graph types and socket links, image dependencies and SHA-256/license/provenance when known; do not invent licensing. Distinguish texture color space and missing images.
- Render contract: renderer, resolution, samples, color management, transparent/world settings, all seven named cameras with type, lens/ortho scale, clipping and transforms, lights with types/power/color/transforms, compositor settings and render seed if used.
- Landmark candidates: rock boundary, crest, central overhang, grass-rock transition, shoreline, road/walkable edge; record actual measurable coordinates separately from proposed art-director targets, with `source` and `confidence`. Unknowns = null / BLOCKED.
- Manifest: source and output SHA-256, input Git commit, provenance, status UNAPPROVED, generator version, runtime Blender exact version, dependencies.

## Codex task 2 — views and cross-view validation
Generate **six orthographic engineering views** (front/back/left/right/top/bottom) from the same evaluated geometry with world-axis labels, a provisional local coordinate grid, bounding dimensions, feature IDs, and a separate camera map. Also output existing seven production camera renders for visual comparison without modifying their positions. Produce vector SVG overlays for silhouette, landmarks and callout indices; heavy per-vertex data stays in JSON, not text printed on image. Provide face-ID/vertex-ID detail sheets only for selected rock junction regions. Do not infer hidden/backside shape from a single CG.

## Codex task 3 — reconstructibility QA
Write a read-only round-trip test: export mesh and scene, reconstruct in a temporary scene, compare topology counts, per-vertex positions (declared tolerance), face connectivity/winding, material assignments, UV loops, transforms and camera matrices. Run at least one fixed-view pixel comparison with documented engine and tolerance, distinguishing nondeterministic shading. A `rebuild.py` may be generated only after round-trip test demonstrates equivalence. Explicit QA statuses: G1 BLOCKED until canon comparison, G2 FAIL until independent art review, G3 PARTIAL until full checks, G4 NOT_RUN until game integration.

## Acceptance / stop conditions
1. All seven existing cameras and six new orthographic views reference **one source scene**.
2. Deterministic JSON hashes on two identical runs, except explicitly excluded timestamps/paths.
3. Complete vertex/edge/face/loop counts; UV and PBR data accurately attributed; source untouched.
4. Report source-vs-reconstructed maximum positional delta, winding/loop mismatches, missing textures and failed tests; no false PASS.
5. No production model sculpt, source overwrite, new PR, main merge, official adoption or game deployment in this first extraction stage.
6. Stop on missing canonical source only for dependent decisions; independent mesh extraction proceeds.

## Following phase (separate from extraction)
Art director compares actual orthographic geometry and official CG; defines a **measurable** landmark/shape target. Codex then implements a genuinely different local sculpt/integration method for the central junction, preserving C9/C10. Independent G2 reviewer compares fixed-camera render pairs and records PASS/FAIL before extending to entire cliff.

### Last verified status
This document is a concrete Codex work order only. Extraction scripts, blueprint JSON/SVG, round-trip test and new renders are **NOT_RUN** until a subsequent actual implementation/Actions execution verifies them.
