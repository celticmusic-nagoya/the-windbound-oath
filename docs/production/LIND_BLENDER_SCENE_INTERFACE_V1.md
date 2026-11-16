# LIND Blender spatial scene interface v1 — candidate contract

**Scope:** Interface design only; no Blender mesh, geometry, dimensions, camera or adopted art is asserted here. This is a handoff for WORLD/HOME/BUILD/ECO and Codex integration, not a replacement for their in-progress work.

## Inputs and authority
1. Immutable visual reference: `assets/sources/lind-world-20261116/original.png` (commit `dc17dd4846f35ea1f5dea25168eec9ddb50a3838`, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`).
2. Latest private main lore and approved event CGs. Do not reproduce private text.
3. Proposed semantic graph: `docs/production/lind-new-world-topology.v1.json`. **Its candidate edges are not director-approved routes.** All physical metrics remain unapproved.
4. PR #345's isolated legacy assembler is not an input to this scene.

## Scene collection boundaries (proposed names, not canonical object names)
| Collection | Producer | Content | Required handoff |
| --- | --- | --- | --- |
| `LIND_TERRAIN` | WORLD | coast, cliff masses, soil, slopes, walkable land | topology node references, terrain/shore masks, source hash |
| `LIND_WATER` | WORLD | sea, river, inlet, downstream water | north-to-south river flow, water/shore interfaces |
| `LIND_ROADS` | WORLD | traversable roads and paths | route endpoints and explicit walk/story classification |
| `LIND_HERO_HOME` | HOME | Aidan's approved-quality house | independent origin/footprint/materials, no assumed village coordinates |
| `LIND_BUILDINGS` | BUILD | other modular buildings | per-building IDs and connection requirements, not arbitrary footprints |
| `LIND_ECOLOGY` | ECO | trees, grasses, farm vegetation | scatter masks, exclusion zones, source hashes |
| `LIND_STORY_MARKERS` | STORY | semantic event markers | CG provenance, scene transition type, no camera coordinates yet |

**No forced scene merge:** each lane delivers independent collections and metadata. Integration may link them in an assembly scene only after common metric and material contracts are reviewed.

## Typed handoff requirements
Each candidate collection must record:
- `lane`, `source_image_sha256`, `generator_version`, `blender_version`, `random_seed`, `input_hashes`, `output_hashes`, `art_status`, `qa_status`.
- `local_origin`, `bounding_box_m`, `world_transform`, `elevation_reference` **must remain null until metric approval**. No fabricated coordinates.
- `dependencies` and `exclusion_masks` are explicit; ECO must not scatter through houses, roads, water or story clearances.
- Art reference, generated candidate and adopted asset must have distinct status tags.

## Required semantic checks before geometry
- `windward_cliffs_wnw` is ocean-facing sunset/stargazing; `raid_riverside_cliff` is a separate eastern river location.
- `raid_riverside_cliff -> downstream_landing` is a directed **story jump**, not walkable navmesh.
- Northern farmland/road to Dunvall and southwest small fishing inlet remain identifiable.
- `east_training_area` and its path are marked `LOCATION_REVIEW_REQUIRED` in the proposed graph; do not treat that placement as adopted.
- The image's illustrative scale bar does not set Blender units or distances.

## Quality gates and acceptance
- **G1**: verify source SHA and latest canon/CG alignment; approve physical coordinates/footprints before final scene placement. Original PNG registration PASS, total G1 BLOCKED.
- **G2**: independently inspect final-quality silhouettes, architecture, surface materials, vegetation and event composition at actual game display size. NOT_RUN.
- **G3**: independently run Blender version-pinned render, collection integrity, normals, alpha, seams, mask exclusions, budgets and reproducibility checks. NOT_RUN for new world.
- **G4**: browser/game integration, save/load, performance and Android actual-device QA. NOT_RUN.

## Non-destructive next execution
1. Validate proposed graph and negative controls in isolation; do not use it to place meshes.
2. Audit Claude branch results and previous method failures before assigning new geometry.
3. Reconcile physical scale, transforms, hero-house footprint and camera viewpoints as an explicit decision record; mark missing evidence BLOCKED.
4. Render only accepted candidate assemblies for G2/G3, preserve source/seed/hash/render evidence.
