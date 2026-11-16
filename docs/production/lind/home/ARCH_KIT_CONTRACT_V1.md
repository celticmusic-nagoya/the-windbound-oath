# LIND ARCHITECTURE KIT CONTRACT v1 (HOME → BUILD / WORLD / INTEGRATION)

Status: **CONTRACT_V1 (version 1.1) CANDIDATE, PROVISIONAL, NOT_DIRECTOR_LOCKED**. Machine-readable twin: `arch-kit-contract.v1.json` (authoritative if the two differ). Owner: HOME lane (LIND-HOME-01). Canon gives no building dimensions; every number here is a production candidate. Footprints are **not locked** (PROVISIONAL). The world-map master `abbb3997…0620` is now registered (repo dc17dd4) and SHA-verified; it is a composition master, not to scale, and agrees with this kit's 1.5-storey side-gabled cream-stone + blue-gray slate cottage type.

## 1. Units, axes, pivots
- Metres, 1 BU = 1 m, Z-up, main entrance facade faces **-Y**, ridge / long axis along **X**.
- Building origin: centre of exterior footprint bbox, z = 0 at finished exterior grade at the main door. No baked rotation/scale; WORLD/INTEGRATION apply placement.
- Kit modules (wall panel, door, window) pivot at bottom-left-exterior corner on the wall face plane.

## 2. Levels
| Item | Range | Default |
|---|---|---|
| Finished floor above grade | 0.15–0.30 | 0.25 |
| Storey floor-to-floor | 2.6–3.0 | 2.75 |
| Clear ceiling (ground) | 2.4–2.7 | 2.55 |
| Knee wall (1.5-storey loft) | 0–0.6 | 0.30 |
| Wall-plate top (1.5 storey) | — | 3.30 |

## 3. Walls and masonry
Exterior stone 0.45–0.65 (default 0.55); mortar recessed 15–35 mm behind stone face; joints 8–22 mm; plinth course 0.28–0.40; courses 0.15–0.32; stones 0.20–0.65 long; quoins alternate long 0.48–0.62 / short 0.28–0.36. Hand-built tolerance: corners ≤ 0.04 m off-rectangle, ridge sag ≤ 0.04 m. Interior plaster lining 0.02 on stone; timber partitions 0.10–0.15.
Masonry method for this kit = **F9 layout-outline pillowed rubble** (see `docs/qa/lind/home/attempt-ledger.json`). Do **not** use stopped families F1–F5, F7 (see `docs/qa/lind/home/PRIOR_HISTORY.md`).

## 4. Openings (clear sizes, m)
| ID | W × H | Notes |
|---|---|---|
| Main door | 1.00 × 2.05 | frame 0.08, threshold stone |
| Secondary door | 0.90 × 2.00 | |
| W1 ground window | 0.80 × 1.05, sill +0.95 FFL | 2×3 panes |
| W2 gable/loft | 0.60 × 0.75 | 2×2 |
| W3 small | 0.45 × 0.55 | 1×2 |
Frame set back 0.14 from exterior face; oak lintel 0.18 high, 0.20 bearing each side; alternating jamb stones; ≥0.6 pier between openings; ≥0.7 opening-to-corner.

## 5. Roof — blue-gray slate (canon, PR #307)
Pitch 38–48° (default 42°); eave overhang 0.35–0.45; verge 0.25–0.35; rafters 0.08×0.15 @0.60; bargeboard 0.05×0.22.
Slates: individual pieces, gauge 0.15–0.20, length 0.34–0.44, width 0.18–0.32 random, thickness 10–20 mm, headlap ≥ 0.06, side-bond offset ≥ 0.06, bottom edge lifted ~2× thickness (lies on course below), chipped outline per slate, double eave course, angled saddle ridge pieces 0.30–0.40, slates 30–60 mm past bargeboard. Colour candidate HSV h200–215°, s0.08–0.15, v0.32–0.45 (match the approved CG under the same exposure; not canonical RGB). Lichen/moss biased to lower courses, never a uniform band.

## 6. Chimney
Plan ≈ 0.90 × 0.75, ≥ 0.6 above ridge, cap slab with 0.06 drip, 1–2 terracotta pots, lead flashing.

## 7. Materials (IDs fixed; full PBR ranges in JSON)
`MAT_STONE_RUBBLE_LIMESTONE_A`, `MAT_STONE_QUOIN_DRESSED_A`, `MAT_MORTAR_LIME_A`, `MAT_SLATE_BLUEGRAY_A`, `MAT_SLATE_RIDGE_A`, `MAT_TIMBER_OAK_WEATHERED_A`, `MAT_PLANK_FLOOR_A`, `MAT_DOOR_PLANK_A`, `MAT_PLASTER_LIME_INT_A`, `MAT_GLASS_CROWN_A`, `MAT_IRON_WROUGHT_A`, `MAT_TERRACOTTA_A`, `MAT_LEAD_FLASHING_A`, `MAT_FABRIC_WOOL_GREEN_A`, `MAT_LINEN_A`. Max 16 unique materials per building. Image maps: CC0 Poly Haven 1k (`rock_boulder_dry`, `rough_wood`, `weathered_brown_planks`; MD5 verified against provider API, SHA-256 in `tools/map_blender/lind/home/texture_sources.json`), else procedural fallback recorded in the build manifest.

## 8. Texel density / UV (revised v1.1)
LOD0 **569 px/m ±25 %** (1k map over the CC0 rock scan's real 1.8 m extent), LOD1 256 px/m. Tile per material: stone surface on modeled stones 1.8 m, rough_wood 2.0 m, planks 2.5 m. For a masonry **pattern** texture on flat LOD1 walls: tile_m = courses-in-texture × 0.24 m (an 8-course pattern → ~1.9 m). Judge stone size by modeled course height (measured in HOME f9_c01: mean 0.242 m, range 0.18–0.34, plinth 0.34; ~11–13 stones/m²), not by texture tiling. Every render mesh has UV map `UVMap`.

## 9. Naming / collections
`<PREFIX>_<BLDG>_<PART>[_<VARIANT>][_LOD<n>]`, prefixes `GEO` / `COL` / `ANC` / `LGT` / `CAM` / `STG` (staging, never exported). BLDG ids: `AIDANHOUSE`, `INN`, `SHOP`, `ELDERHOME`, `DWELL<nn>`, `BARN<nn>`. Collections: FOUNDATION, WALL_SHELL, MASONRY, TIMBER, ROOF_STRUCT, ROOF_SLATE, OPENINGS, CHIMNEY, PORCH, INTERIOR, PROPS_EXT, COLLISION, ANCHORS, STAGING.

## 10. Triangle budgets
House shell LOD0 ≤ 450k; exterior props ≤ 60k; interior ≤ 80k; LOD1 ≤ 60k; LOD2 ≤ 8k; collision ≤ 300. Generic dwelling shell LOD0 (BUILD) ≤ 300k.

## 11. Collision proxies
Boxes only, convex, non-rendered, 2.5 m tall, door gap = door clear width centred on the door anchor, one box per interior furniture item. Name `COL_<BLDG>_<part>`.

## 12. Anchors for event / SAVE adapters
Empties, z at FFL or grade, local +Y = facing on arrival. Door pair `ANC_<BLDG>_DOOR_<id>_EXT` (0.6 m outside) / `_INT` (0.6 m inside); `ANC_<BLDG>_SPAWN_<id>`; `ANC_<BLDG>_SAVE_<id>` (candidate; SAVE adapter G4 NOT_RUN); `ANC_<BLDG>_EVENT_<id>`. Custom props: `anchor_kind`, `links_to`, `runtime_map`, `runtime_id` (e.g. `rilde_in_aidan` / `tr_exit`, `from_bed`, `ev_bed_04`).

## 13. Render standard
Game camera ortho 27° elevation (25–30°), azimuth -45°; previews ≤ 1280 px; game-scale checks at 48 and 96 px; Cycles ≤ 64 spp + denoise; AgX.

## 14. Change control
- 1.0 (2026-11-16) initial. 1.1 (2026-11-17): master PNG registered note; texel density 512→569 px/m + tile_m per material + LOD1 pattern rule (BUILD request); measured scale targets; openings snap to courses (clear size ±0.15 m, actual sizes in build manifest). Footprint/opening/roof values unchanged.

HOME bumps to v2 only with a changelog entry; BUILD must not fork values silently. Variants (burning/ruined) keep footprint and openings: NOT_RUN.
