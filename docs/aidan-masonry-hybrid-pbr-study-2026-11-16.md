# Aidan masonry hybrid PBR study — candidate-only production specification

Parent: Draft PR #323 / feature/aidan-architecture-v3-01. Separate branch: feature/aidan-masonry-pbr-study-01.
Status: DESIGN ONLY; NOT_RENDERED; NOT_APPROVED. Never replace official assets or alter parent branch.

## Evidence baseline
- Existing G2 recovery design: docs/aidan-masonry-g2-recovery-design-2026-11-16.md
- Existing candidate generator: tools/map_blender/aidan_corner_bond_v2.py
- Existing geometry: six-course integral L-quoin study; local bevel/displacement/Boolean chips were visually rejected for regular silhouette.
- Existing script reports evaluated mesh boundary, nonmanifold, connected components and signed volume. It does not establish self-intersection-free geometry, clearance, visual acceptance or game performance.
- Canonical house reference and dimensions must be fetched and verified independently; G1 BLOCKED until then.

## Asset acquisition and licensing
1. Pinterest / historic Irish cottages / fieldstone walls: composition and geometry references ONLY. Record creator, URL, access date and permitted usage. Do not embed Pinterest photographs in the game.
2. Prefer CC0 PBR textures from Poly Haven or ambientCG; record exact asset ID, URL, author, license snapshot, resolution, checksum, and color space. Do not assume a reference photograph is licensed for texture extraction.
3. If a texture is not downloaded or inspected, mark ASSET_NOT_ACQUIRED. Never invent files or manifests.

## Candidate modeling strategy
1. Keep current generator and existing manifests immutable. Build an isolated single-quoin candidate and matching infill stone in a new script, separate output directory and seed.
2. Preserve inner mating faces, envelope and mortar clearances. Shape visible outer silhouette with a few broad asymmetric fractured planes and hand-dressed face variations, not micro-noise or two localized chips.
3. Apply a shared stone material to quoin and infill. UV/triplanar mapping with scale calibrated to stone dimensions; use base color, roughness and normal, and optionally restrained displacement. Control texture repetition and seam continuity.
4. Match reference and candidate renders in camera, light, resolution and exposure. Produce old/new single-stone, two-course wall, front/return and game-scale crop.
5. Optimize for 2.5D on-screen readability; use baked maps or LOD where beneficial. Avoid excessive geometry invisible at target scale.

## Quality gates
G1: approved house reference, geometry envelope, material palette and design consistency confirmed, else BLOCKED.
G2: independent review of silhouette, stone size rhythm, visible joints, surface scale, corners and texture seams; CI PASS is insufficient.
G3: evaluated manifoldness, connected components, positive volume, normals, self-intersection where measurable, inter-stone clearance, UV seams, texture path resolution, image hash, deterministic seed and Blender version.
G4: integration in actual 2.5D scene, final pixel size, loading/performance and Android device check.
A final adoption requires G1–G4 PASS. Keep FAIL/BLOCKED/NOT_RUN distinct.

## Stop rule and safety
At most two substantive attempts per root cause/approach. After two failures, stop and investigate sculpt + retopology or legally licensed scanned stone rather than parameter nudges. Do not change canonical assets, merge to main, publish or interfere with night QA/Morwen jobs.

## Execution state
Reference licensing research: NOT_RUN
PBR asset acquisition: NOT_RUN
New geometry script: NOT_RUN
Blender render / CI: NOT_RUN
G1: BLOCKED
G2 new candidate: NOT_RUN
G3 new candidate: NOT_RUN
G4: NOT_RUN
