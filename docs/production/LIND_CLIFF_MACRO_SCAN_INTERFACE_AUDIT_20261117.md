# LIND cliff macro support ↔ scan dressing interface audit — 2026-11-17

**Status:** CANDIDATE DESIGN / NOT IMPLEMENTED. WORLD-only, no geometry generated, no approved scale, no runtime migration.

## Authoritative inputs inspected
- Current main `AGENTS.md`: causal retry policy v2, preserve source and latest canon; old 2.5D art is not a binding full-3D target.
- `feature/morwen-fable-eval-01:docs/production/MAP_TEAM_FULL_3D_HANDOFF_20261116.md`: 3D migration decision; source image SHA `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`; physical units, camera, renderer and Android budgets unapproved.
- `feature/lind-agent-blender-handoff-01:HANDOFF.md`, `Blender.md`, `docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md`: collection ownership, semantic geography, mandatory null metric transforms and source tracking.
- `feature/morwen-fable-eval-01:js/field/lind-terrain-layout.js`: historical 2D review canvas 2200×1550 and routes; **NOT** 3D meters, geometry, or approved navmesh.
- `docs/qa/lind/LIND_VOXEL_ROOTCAUSE_MEASURED_20261117.md`, `LIND_LOCAL_SCAN_PATCH_INDEPENDENT_ART_QA_20261117.md`, `LIND_INTERIOR_CORE_INDEPENDENT_ART_QA_20261117.md` on this PR ancestry.
- Source scan: Poly Haven Coastal Cliff 04, CC0; glTF SHA `645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11`. Reference/detail source, not geographically proven Irish cliff.

## Distinct geological structures (DO NOT conflate)
| Region | Semantic role | Constraint |
|---|---|---|
| `windward_cliffs_wnw` | western/northwestern **ocean-facing** coast | ocean shoreline, sunset/stargazing framing; no assumed height |
| `raid_riverside_cliff` | separate **eastern river** cliff | cliff-edge story beat; not a western ocean asset duplicated in place |
| `downstream_landing` | southeastern downstream landing | directed story jump from eastern cliff, **not** a traversable navmesh edge |
| southwest fishing inlet | harbor/shore interface | separate from river landing |
| northern farms / Dunvall road | landward routes | preserve semantic continuity, no inferred coordinates |

## Two-layer geometry contract (proposal)
1. **Macro support (WORLD):** continuous terrain mass authored from approved semantic geography. Maintain real connected soil/rock strata, plausible gravity support, slopes and shore erosion. Distinct visual and collision/navmesh surfaces; no raw scan acting as a watertight collision mesh.
2. **Scan dressing (WORLD):** localized source-scan patches selected for useful fracture patterns and material variation. Each patch must be explicitly fitted into macro support, with overlap/transition mask and hidden cut edges; source provenance, local transform and texture footprint tracked.
3. **Contact-zone test:** at the planned camera, verify no hovering, obvious planar seams, z-fighting, spikes, accidental tunnels, or floating fragments. Match rock color/roughness/normal response under a single scene lighting configuration.
4. **Game delivery:** separate high-quality source `.blend` from optimized WebGL/Android glTF, LOD, atlas and collision. Browser adapter and performance budgets remain unresolved and require G4.

## Machine-readable candidate handoff fields
- `source_image_sha256`: pinned approved source image SHA above.
- `scan_source_sha256`: pinned publisher glTF SHA above.
- `scene_collection`: `LIND_TERRAIN` (WORLD ownership).
- `region_id`: one of `windward_cliffs_wnw`, `raid_riverside_cliff` for the cliff patch.
- `local_origin`, `bounding_box_m`, `world_transform`, `elevation_reference`: **null** pending approval.
- `camera_projection`, `game_renderer`, `character_nominal_height`, `lod_budgets`, `collision_contract`: **null** pending cross-team approval.
- `source_scan_is_collision`: **false**.
- `story_jump_is_walkable`: **false**.
- `art_status`: `REFERENCE_ONLY` until independent art QA.
- `qa_status`: G1 BLOCKED, G2 NOT_RUN, G3 NOT_RUN, G4 NOT_RUN for any new macro+scan integration.

## Stopped approaches and distinct mechanism
- Global Decimate: white hairline artifact unresolved; stopped.
- Global Voxel Remesh + Smart UV: 95.6% face-area loss and 0.11% atlas occupancy; stopped.
- Blind boundary ring erosion: 36 disjoint interior components and 551 new open edges; stopped.
- **New mechanism:** macro support authored for physical terrain continuity **first**, then high-frequency scan as localized dressing, not a scan-only free-floating cliff mesh. No parameter-only rerun.

## BLOCKERS and release criteria
- G1: private canon/latest approved world placement and cross-team metric interface not fully accessible/approved. Do not infer.
- G2: full scene silhouettes, material matching, contact-zone art QA at final display size.
- G3: macro support topology, patch interfaces, collision, UV/bake, source hashes, actual Blender renders/reopen.
- G4: isolated runtime feature flag, movement/collision/SAVE regressions, Android Chrome performance and real-device review.

**Decision:** Next implement an isolated **semantic-only** cliff macro scene with uncommitted/nullable placement fields and candidate renders only after a physically coherent geometry design is approved. No production adoption or main merge.
