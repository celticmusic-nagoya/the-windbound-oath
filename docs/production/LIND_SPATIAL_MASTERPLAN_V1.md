# LIND-SPATIAL-01 — リルド村・統合空間マスタープラン（制作提案／未採用）

## Objective
Build Lind/Rilde as one cohesive high-quality, explorable village environment, including Aidan's home, terrain, roads, river, bridge, farms, training ground, village buildings and foliage. The **entire village spatial composition** is the design unit; modular assets are subassemblies. This document does not adopt new canon or replace the playable field.

## Verified source precedence and current constraints
1. Current main AGENTS.md and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md; private handoff current main official bible v5.0, CANON_ADDENDUM.md, CANON_STATUS.md. Map-specific canonical visual reference: docs/art/reference/lind/リルド村RPGアセット全体マップ.png; hash inventory docs/art/reference/lind/inventory.json. **Image's actual topology/coordinates must be visually checked before geometry is locked.** Do not interpret the existing 2200x1550 DOM coordinates as approved geography.
2. docs/field/lind-production-step0.md records the prototype field 2200x1550, camera(), input, river/bridge, training, door data-room identifiers, and save/story integration. Prototype building coordinates conflict with the confirmed map; preserve existing event hooks but do not use these coordinates as final layout.
3. docs/field/lind-production-batch1.md records already-generated terrain, buildings, farm assets and DEV placement. Preserve originals and SHA, distinguish accepted/candidate/reference. Reuse only after individual canon/art/technical audits; never regenerate unchanged assets blindly.
4. Parallel building masonry work: Draft PR #331, G2 FAIL at last confirmed independent review. Parallel grass candidate A G2 FAIL and candidate B technical pipeline under PR #337. Neither is accepted for spatial master.
5. Existing field uses HTML/CSS/JS; no approved migration to real-time WebGL. Blender can author offline modular geometry and render camera-consistent sprites/atlases for current browser runtime. Real-time 3D is a separate architecture decision requiring performance and compatibility evaluation.

## Spatial production architecture
- **L0 Spatial source:** immutable approved plan image, source hashes, canonical camera/scale, coordinate conversion, terrain height/collision reference, north orientation, building footprints and event-anchor IDs. If visual verification or private canon unavailable, G1=BLOCKED; no final coordinate placement.
- **L1 Landform and hydrology:** terrain macro contours, banks, river path, crossing, path elevation and sightlines; authored as a continuous world. Water flow remains independent of wind-stop story event.
- **L2 Architectural ensembles:** Aidan's house as quality master, then inn/shop/elder/residences/farm buildings. Build walls, corners, roof, doors, trim, materials and weathering as separately QA-able modules. Maintain footprint, entrance, threshold and collision anchor contracts.
- **L3 Village ecology:** grass clumps, meadow patches, shrubs, flowers, trees, fences, stones, ground clutter. Scatter by biome/soil/foot-traffic masks and avoid obstructing entrances or quest objects; no random uniform placement.
- **L4 Lived-in storytelling:** laundry, carts, barrels, signs, garden beds, paths worn by use, focal views, landmarks. Story-state overlays (peaceful/attack) separated from base geometry.
- **L5 Runtime representation:** camera-matched orthographic/2.5D output, modular occlusion/depth masks, baked shadows/lighting variants where justified, object collision, input/touch, interaction hit areas and saved state. Use atlases and LOD for Android; maintain existing JS event identifiers.

## Asset and scene contracts (draft, NOT canonical measurements)
Each module: asset_id, role, source_ref, canon_status, source_sha256, Blender_version, generation_seed, world_transform, bounding_box, entrance_anchor, foot_anchor, occlusion_mask, collision_footprint, material_set, LOD_targets, texture_memory_estimate, render_camera_id, output_hashes, QA_status.
Spatial chunks: stable chunk_id, source plan region, transform, terrain mesh, prop instances, spawn/collision/nav masks, event anchors, story-state visibility and export manifest. Chunk boundaries must not create seams in river/road/terrain.

## Production order and quality-first acceptance
**Phase S0 — canonical spatial audit:** visually compare actual whole-village map image, existing terrain/buildings, Aidan masonry candidate and private canon. Build approved source inventory and discrepancy report. Gate G1; do not invent map topology or dimensions.
**Phase S1 — world blockout only for structural risk:** one spatial master Blender scene with landform, hydrology, paths and building footprint envelopes; no primitive blockout claimed as finished art. Validate camera, entrances, crossing, navigation, occlusion, sightlines and runtime conversion before detailed modeling.
**Phase S2 — one complete representative village slice:** Aidan's house + immediate road + garden + fence + terrain + foliage + lighting + interaction approach. Build to final visual standard, render full view and 48/96px crops. Verify G1–G3 and Android G4 before village-wide replication.
**Phase S3 — architectural and ecological expansion:** assemble approved modules across approved plan regions. Vary geometry by role, avoid repetition, validate each chunk and seams.
**Phase S4 — world integration:** peaceful/attack scene states, NPC routes, save compatibility, quest interaction anchors, accessibility/readability and Android performance. No main merge/publish without explicit director approval.

## Gates and evidence
G1: canon map image + latest private canon + source hashes + footprint and entrance placement verified; unavailable means BLOCKED.
G2: independent art review of spatial composition, Aidan house master, terrain transitions, silhouettes, weathering, palette, natural density and 48/96px final-scale images; CI never auto-passes.
G3: Blender executable/version, reproducible scene and seed, topology, transparency/UV, lighting and render outputs, manifest SHA, seam continuity, geometry/texture budgets, camera/export consistency.
G4: actual playable browser + Android Chrome QA for navigation, doors, bridge, occlusion, story flags, save/restore, FPS/memory and before/after regression.
Evidence: camera screenshots, whole-village overview, close-up hero slice, 48/96px crops, Blender .blend, scene manifest, SHA256, QA report and failure ledger.

## Parallel work packages (non-destructive)
- Spatial director: scene coordinate/camera contract and integration.
- Architecture: Aidan home master, roof/stone/wood modular sets; coordinate with PR #331 without replacing its work.
- Terrain/hydrology: banks, roads, terrain seam system.
- Ecology: vegetation/prop distribution, coordinate with PR #337.
- Runtime/export: sprite atlas, occlusion, collisions, events and performance.
- Independent QA: compare rendered and in-game outputs to approved references; track G1–G4 and causal method-family retries.
Each uses separate branches/Draft PRs. Agent assignment does not mean an external agent was invoked.

## Immediate next execution gate
Inspect the actual 1536x1024 approved whole-map image and source materials; verify map regions and camera before any formal scene geometry. Build scene manifest from verified facts only. Then implement S1 and one S2 hero slice in independent branches. No source replacement, merge, or publication in this plan.
