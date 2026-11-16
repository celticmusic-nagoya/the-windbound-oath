# LIND-BUILD-01 — prior architecture history (read-only import)

Task: LIND-BUILD-01 (BUILD lane). Collected 2026-11-16 via `gh api` (read-only). Nothing in these PRs was modified.
Purpose: avoid repeating method families that previous attempts already stopped (CAUSAL_RETRY v2 §6: history is imported, counters are not reset).

## Sources read
| PR | Branch | State (2026-11-16) | What was read |
| --- | --- | --- | --- |
| #307 | `feature/rilde-roof-canon-bluegray-20261114` | open, unmerged | patch to `docs/design/FIELD_VISUAL_OVERHAUL_20261108.md` |
| #309 | `feature/aidan-asset-prep-01` | open, unmerged | PR body, `docs/map-production/AIDAN_BLENDER_STRUCTURAL_AUDIT.md`, `aidan_blender_config.json`, `aidan_asset_ledger.json` |
| #323 | `feature/aidan-architecture-v3-01` | open, unmerged | PR body, `docs/aidan-masonry-g2-recovery-design-2026-11-16.md`, `tools/map_blender/AIDAN_MASONRY_INDEPENDENT_AUDIT.md`, `tools/map_blender/AIDAN_V3_PRODUCTION_HANDOFF.md` |

## Facts carried forward
- **Roof canon (#307, director-approved 2026-11-14):** Rilde roofs are blue-gray slate (stone-plate). Replaces the older red-brown roof wording. Base reference is the approved daytime Rilde CG. Natural stone walls with timber, firewood, flower beds, cobbled paths; per-building colour variation and irregular masonry.
- **Base CG (#309):** `assets/approved/world/rilde_village.png` SHA-256 `c55af077…726a` (re-verified here, see BUILDING_PROGRAMME_V1 §1).
- **Camera (#309 config, proposed):** ortho game quarter view, elevation 25–30° (default 27°), azimuth -45°; metric, 1 BU = 1 m, Z-up, front = -Y. Seed base 1311 (+component index). Adopted here as the BUILD default render camera.
- **CC0 texture shortlist (#309 ledger):** `roof_slates_03` (neutral gray, needs blue-gray correction), `yellow_stone_wall`, `rough_wood`, `weathered_brown_planks`, `cobblestone_floor_04`. Thatch (`reed_roof_03`) REJECTED (canon). Quaternius BLOCKED (licence). Poly Haven `Barrel_01`, `Lantern_01`, `hatchet` rejected visually.

## Stopped / failed method families (do NOT repeat)
| ID | Where | Method family | Recorded defect | Status |
| --- | --- | --- | --- | --- |
| H-A | #309 audit of `aidan_home_production_candidate.py` | primitive duplication + flat colour: 672 **identical** slate cubes, 60 identical chimney stones, equal-height (0.24 m) stone courses, 0 textures, 512 meshes without UV | reads as one dark plate at game size; brick-like walls; gable walls flat; camera 38° (out of spec) | G2 FAIL — stop family |
| H-B | #309 audit of Kenney massing | kit massing with thatch | thatch violates roof canon; open meshes (6,196 non-manifold edges) | G2 FAIL — rejected |
| H-C | #309 audit, `roof_slate_system_02.py` | per-slate chips/warps with red slate material | colour violates canon (red) | not rendered; colour rejected |
| H-D | #323 v3 architecture | uniform box walls/porch polished as "final" | "do not polish v3 uniform boxes" | G2 FAIL |
| H-E | #323 corner bond v1/v2 | bevelled cube quoins + random bevel/displacement + two-chip | corners read as regular prisms; 7 mm bevel / 3 mm displacement invisible at game size | **2 failures → family STOPPED** |
| H-F | #323 masonry v1 | per-row stone placement with whole-row exclusion at openings, `_intervals` sliver suppression | potential uncovered wall intervals, unused backing mortar (transparent gaps) | audit open, not repeated |

## Consequences for LIND-BUILD-01 method choice
1. Walls: **no** per-stone bevelled-cube masonry (H-A/H-E/H-F). Use a continuous wall shell with real boolean-free apertures (wall built from panels around openings), UV-mapped by real-world metres, CC0 rubble-stone PBR (`yellow_stone_wall`) + shader colour variation. Only quoins, sills, lintels and door/window surrounds are real geometry, built as **irregular extruded planar outlines** (random polygon silhouette, tilted face plane) — structurally different from H-E (bevel/displace a cube).
2. Roof: individual slates, but **every slate has its own width, length, thickness, tilt, colour and texture offset** (H-A defect was identical size); slate rows are laid on battens over modelled rafters so the burning state can expose the structure (approved raid/aftermath CGs show stone shells with charred exposed rafters). Blue-gray PBR correction of `roof_slates_03` (H-C defect was red colour).
3. All meshes get UVs; collections split by part (walls / timber / roof / openings / chimney / props / signage).
4. Renders at 27° ortho, plus 48/96 px downsamples, inspected before any statement.
5. Attempt ledger seeded with H-A…H-F as imported history (`attempt-ledger.json`).
