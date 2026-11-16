# LIND 3D WORLD MASTER — adopted art & production kickoff
Date 2026-11-16. Status: DIRECTOR-APPROVED VISUAL MASTER / 3D PRODUCTION PREPARATION. Supersedes all legacy village geometry and the 15-anchor pixel overlay as placement authority.

## Approved image master
Generated and explicitly adopted in conversation 2026-11-16: fantasy world overview of Rilde coastal area, 1536x1024 RGB PNG, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`. This exact image is a canonical **visual composition**. **Binary has not yet been committed to GitHub**; register without modification and verify SHA before G1 source asset PASS. Do not substitute a lookalike or web image. Preserve original source unaltered.

## Canonical geography (private WORLD_MAP_CANON_20261108.md, directly verified)
Rilde village: western coastal agricultural/fishing settlement. West/northwest: Windward Cliffs, sunset over sea. Southwest: separate inlet and small fishing port. Village center: housing and storage. North: farmland and road toward Dunvall Fort (walking half-day to one day design guideline). East: river flowing north to south, bridge, distinct riverside cliff used in raid escape. Southeast/downstream: Moss Forest and ancient altar. Long-distance transport is not teleportation. Keep private lore private.

## Artistic map versus physical geography
The adopted image is a picturesque **not-to-scale illustration**, not a dimensioned orthophoto. Its drawn 0–5 km scale bar is **not an approved engineering scale**; never use it to infer terrain dimensions. The distant fort is drawn for readability and need not be in the village's playable scene. Scene layers can separate far vistas, coastal cliffs, harbor, village, east river, southeast forest, and distant fort. Text in image is decorative; in-game UI labels should be independently typeset and proofread.

## 3D construction partitions
- L0 WORLD: new terrain mesh and elevation, coast and harbor basin, upstream-to-downstream river, waterfall if consistent with event CG, two distinct cliff locations, traversable main paths; origin, meters/unit and camera proposed only, not locked.
- L1 VILLAGE: Aidan house master, inn, shop, elder house, houses, storage and plaza, entrances and interiors as independent modules. Use approved architecture/CG references, not legacy CSS.
- L2 FARM/NATURE: fields north, vegetation, orchard, livestock, fences, coastal rock formations; wind animation independent of flowing water.
- L3 EVENTS: approved sunset/night cliff CG views, raid riverside cliff, voluntary jump, downstream Moss Forest landing, return route, village fire; scene IDs and SAVE flags preserved.
- L4 ENGINE: Blender version pinned in Actions; deterministic seeds and asset hashes, modular exports, LOD and draw-call budgets, alpha/shadow QA; integration adapter for existing browser game without inheriting geometry.
- L5 INDEPENDENT QA: G1 canon+art-source integrity, G2 art at in-game size, G3 geometry/materials/collision/render, G4 game/Android/save/event regressions.

## Route graph (topological, not metric)
`harbor_sw <-> village_center <-> north_farms <-> road_to_dunvall`
`village_center <-> windward_cliffs_wnw`
`village_center <-> east_river_bridge <-> east_training_area` (training location must be reconciled with canon and new illustration)
`village_center -> raid_riverside_cliff -> downstream_landing -> moss_forest -> ancient_altar` (story direction only, not a continuous walkable route)
Cliff event location `windward_cliffs_wnw` and `raid_riverside_cliff` MUST NOT merge.

## Source and gate matrix
| Input | Status |
| --- | --- |
| User approval of illustration | PASS |
| PNG local pixel dimensions / SHA | PASS |
| PNG stored and hash verified in GitHub | BLOCKED — binary upload pending |
| Private adopted world-map geography | PASS |
| Event CG files direct visual comparison | NOT_RUN |
| New metric map, camera, elevation, navigation | NOT_RUN |
| Aidan master model art QA | NOT_RUN |
| Browser/Android QA | NOT_RUN |

## First production gate
1. Register original PNG unchanged in a dedicated source directory on PR branch; record SHA and original prompt provenance.
2. Collect **approved** event CGs and house visual references; record exact file paths and SHAs, reject reference-only images as canon.
3. Produce separate terrain and architecture **design sheets**, including visual horizons, river flow, sightlines and walking routes, for director approval.
4. Implement modular Blender scene with terrain/architecture independently and automated technical QA; no cubes as accepted final art.
5. Integrate only after G1–G4 pass; do not merge or publish without explicit approval.
