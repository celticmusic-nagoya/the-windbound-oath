# MORWEN｜精密3Dマスターブループリント方式 v0.1（検証仕様）
Status: RESEARCH / METHOD CANDIDATE / NOT CANON / NOT G2 PASS
Owner: Morwen character team, existing Draft PR #427. Map team blueprint method is a methodological reference only; no shared mesh or coordinate contract is assumed approved.

## Purpose
Produce an editable, machine-auditable Blender mesh and render that can be traced to a versioned blueprint, not a generated illustration masquerading as topology. Aim for commercial-quality stylized character art while preserving Morwen's approved Layer 0 four-direction design and original source hashes.

## Input hierarchy and provenance
1. Approved Morwen Layer 0 four-view images; record exact path, original SHA-256, pixels, orientation, alpha, provenance and formal adoption status. A visually equivalent copy is a production reference, not a byte-identical canonical replacement.
2. Existing candidate Blender Studio Human Base Meshes v1.4.1, ZIP SHA-256 `811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515`. The source is a candidate only, not a Morwen design or G2 PASS. Record license evidence before distributing derivatives.
3. Existing authored Blender meshes and four-view renders from PR #427, including known-failed face studies as negative controls. Do not restart known-failed quad-grid / voxel-sphere / boundary patch methods.
4. Licensed high-end stylized figurine, VTuber and game production references for topology, silhouettes, facial planes, hair clumps, garments, shading and deformation; no copying protected character designs.

## Blueprint schema (versioned, Blender-local coordinates)
`blueprint.json` shall include:
- `schema_version`, `asset_id`, `candidate_status`, `source_manifest` (URI/path, SHA-256, license, adoption status), `software` (Blender version, addon versions), `coordinate_contract` (handedness, forward/up axes, provisional units, origin and transform matrices), `assumptions`, `uncertainty`.
- `landmarks`: named reference points on face/body, source image/view, normalized 2D coordinates, projected 3D positions when known, confidence, measured-vs-inferred flag.
- `mesh_parts`: stable part ID, mesh datablock and object name, parent, transforms, vertex/edge/face counts, topology fingerprint, bounding box, world-space dimensions, seam IDs, sculpt stage, symmetry exceptions.
- `geometry`: vertex positions, face vertex indices, per-face material index, split normals/corner normals, UV coordinates per loop, optional tangents and vertex colors. For large assets, store as separate indexed binary/NPZ or glTF alongside a JSON manifest; do not embed millions of values in Markdown.
- `topology`: manifold boundary counts, non-manifold counts, isolated vertices, zero-area faces, intersecting shells where relevant, pole locations, face loop direction, edge flow notes for mouth/eyes/shoulders/elbows/knees.
- `materials`: principled shader parameters, image texture paths and hashes, color space, normal orientation, alpha mode, roughness/metallic, skin/hair/cloth variants.
- `rig`: bone IDs, hierarchy, rest matrices, weights per vertex, constraints, test poses, deformation error measures; null until authored.
- `render_contract`: engine, samples, resolution, color management, exposure, camera matrices/ortho scales, light types/power/positions, transparent background, image output names.
- `qa`: G1-G4 statuses with evidence files, thresholds, exceptions and failure reasons. No missing stage may be marked PASS.

## Production sequence
A. Freeze and verify approved four-view reference + input manifest; extract actual topology from candidate .blend using Blender 5.3 Python. This is **measured** data.
B. Analyze figure/game/VTuber modeling practices, select an original silhouette, topology and modular part strategy. Record which features are *inferred* from 2D, not directly measurable. Establish landmark tables and projection/camera assumptions.
C. Author a sculpted Morwen head (facial planes, eyelids, mouth, ears), hair masses, body, garment and equipment modules; do not merely recolor an unchanged generic body or build a box/quad-grid placeholder.
D. Retopologize with deformable edge flow; UV unwrap; author PBR materials; rig and test deformations. Record each mesh's numeric geometry and source SHA.
E. Generate consistent front/right/back/left/three-quarter Blender renders. Automated comparisons: silhouette IoU, normalized landmark reprojection error, part-level color distribution, image crop/alpha, topology integrity and reopenability. Review in final display size and with independent art QA.
F. Only after G1/G2/G3 PASS, evaluate game integration, WebGL/Android and G4. Never equate a successful Blender render or workflow with formal adoption.

## First bounded experiment (avoid duplicate production)
**Input:** Verified PR #427 Blender Studio candidate .blend and official Layer 0 four-view references.
**Output:** `blueprint.json`, `mesh_geometry.npz` or indexed glTF, `reference_landmarks.json`, `render_contract.json`, four-view comparison contact sheet, source manifest and QA report; actual editable Blender .blend.
**Gate:** schema-valid metadata, exact vertex/face counts vs Blender, round-trip geometry consistency within a declared tolerance, reproducible camera and renderer, source hashes checked. Independent art QA separately required; no G2 PASS from numeric consistency alone.
**Stop/switch:** two attempts with same root cause fail -> analyze and structurally change approach; retain failed evidence. Keep existing PR and branch; no new PR, canon overwrite, main merge or public release without explicit authorization.

## Current QA at authoring
G1 PARTIAL (approved reference is known, full current source inventory not reproduced in this document); G2 NOT_RUN for new blueprint method; G3 NOT_RUN for new method; G4 NOT_RUN. Existing source candidate render success does not imply Morwen sculpt success.

## Director-approved method correction and bounded next execution (2026-11-20)

**Mandatory main references:** `docs/policy/MORWEN_BLUEPRINT_FIRST_BASE_SELECTION_20261120.md` and `docs/policy/HIGH_END_3D_TECHNOLOGY_REASSESSMENT_AND_PRODUCTION_PIPELINE_20261120.md`. This section supersedes the older assumption that a realistic Blender Studio Human Base Mesh is the default input for the first experiment. A VRoid-derived anime-style base is an **equal, high-priority candidate**; old G2 failures are evidence against specific *outputs/methods*, not the VRoid base family.

**New order of operations:**
1. Read current main and obtain the actual official Layer 0 four-direction reference. Extract measurable landmarks and camera/scale uncertainties. Do **not** use candidate mesh vertex positions as substitute design targets.
2. Build a versioned reference-only blueprint before modeling: orthographic registration, normalized landmark table with source view and confidence, silhouette targets, front/side/three-quarter diagnostics, provisional coordinate contract, topology/rig/UV/material requirements and explicitly estimated areas. Confirm that the design blueprint is adequate for candidate selection; avoid premature multi-million-vertex geometry dumps.
3. Inventory *existing* VRoid/VRM candidate, current stylized sculpt and licensed CC0 candidate. Record per-source origin, redistribution rights, actual file hash, editable mesh and rig/Shape Key capabilities. If a candidate is absent, mark that arm BLOCKED rather than fabricate it or rerun failed old face repairs.
4. Compare all available candidates under identical cameras, neutral clay shading and scale. Record normalized landmark error, silhouette agreement, face-plane quality, topology/weights, expected correction effort and independent G2. Do not auto-select a realistic CC0 base or a new sculpt without this comparison.
5. Only then author the selected actual head/face/hair/clothing modules and proceed to G3/G4 when justified. Keep all experiments on the existing owning PR and preserve original files.

**Failure evidence already available:** `docs/qa/MORWEN_FACE_SURFACE_530_VISUAL_QA_20261120.md` (Blender 5.3 actual render, 5,525 vertices / 5,376 quads, G2 FAIL: flat facial slab) and `docs/qa/MORWEN_VOXEL_HEAD_VISUAL_QA_20261119.md` (22,772-vertex voxel head, G2 FAIL: disconnected-sphere anatomy). These establish why **flat quad-grid** and **generic sphere/voxel** families should not be repeated, not why VRoid is unsuitable.

**Current gate:** blueprint-first re-evaluation NOT_RUN; comparison NOT_RUN; no winning base formally adopted. Blender 5.3 independent smoke and official reference opening previously passed; do not repeat them. The next single executable task is reference landmark extraction and reference-only blueprint QA on this owning branch. Stop if required official reference provenance is missing; continue on verified subviews only.
