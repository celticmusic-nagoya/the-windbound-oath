# World Blueprint First — area gate audit (2026-11-23)

Status: **G1 BLOCKED; blueprint not complete; no new production authorization**. This is an application of existing **main** policy `docs/policy/ART_DIRECTED_HYBRID_WORLD_PRODUCTION_V2.md` (World Blueprint First, director approved 2026-11-23), not a replacement policy.

## Existing outputs versus required completed blueprint

| Required artifact | Cliff area | Other seven area candidates | Gate |
| --- | --- | --- | --- |
| Source-anchored region master plan with coastline, landmarks, area boundaries | Direction-only schematic; real boundaries unknown | Slots only | BLOCKED |
| Elevation, contours, longitudinal/transverse sections with units, datum, uncertainty | CG camera-projected silhouette only; not orthographic elevation | Slots only | BLOCKED |
| Hydrology, drainage, geology, fracture/collapse and soil/rock domains | Partial narrative/schematic references | Unknown | BLOCKED |
| Routes, traversable edges, collision, camera and protected gameplay interfaces | Narrative edges only; no verified world route geometry | Unknown | BLOCKED |
| Vegetation, architecture, water, palette, lighting and fixed camera specifications | Incomplete | Incomplete | BLOCKED |
| Coordinate frame, exact origin, local-to-region transforms, chunk seams and residuals | Axes X east/Y north/Z up, 1 BU=1m and sea Z0 approved; exact transforms unknown | Unknown | BLOCKED |
| Per-asset precise blueprints: silhouettes, sections, topology/UV, materials, contact and LOD | Not completed for whole area | Not completed | BLOCKED |
| Independent blueprint QA, source SHA, target/measurement/operation, tolerance and uncertainty | Partial CG SHA and pixel-trace QA only | Not completed | BLOCKED |

## Execution gate for all eight areas

1. **D0 source/canon:** latest main and private canon/approved CG SHA; owner PR, lease, latest HEAD and Actions/artifact provenance. Unverified owner => SYNC_UNVERIFIED for affected writes.
2. **D1 region blueprint:** complete C01–C07 regional plan, contours, water, geological and ecological zones, routes and cross-area interfaces. Document measured/reconstructed/provisional/unknown individually. Non-canonical candidate coordinates are permitted if explicitly designated, with no invented measured dimensions.
3. **D2 area master:** each area must have usable plan, four directional elevations where applicable, longitudinal/cross sections, detailed spatial layout, fixed cameras and machine-readable data. For the cliff, include major headland, plateau, fractures, overhangs, sea stacks, collapse zone, walkable routes, vegetation, rock/water contacts and geology. The existing 45-point CG pixel trace is *reference evidence*, not a complete D2.
4. **D3 detailed asset blueprint:** component IDs, shapes, physical dimensions and uncertainty, target/measurement/operation, coordinate transforms, topology/UV/PBR, protection, collision/LOD and connection rules. Unknown measurements remain BLOCKED; no guessed tolerance.
5. **D4 independent design QA:** check source alignment, geometry closure/continuity, engineering feasibility, area seams and story/traversal separation. Mark PASS only with independent evidence. Production of the affected new/materially changed scope starts **after applicable D1–D4 pass**; unrelated already-approved owned work continues under existing writer and lease.
6. **G1–G4 production QA:** native Blender edits, actual measurement/correction, saved/reopened source, fixed-camera renders, independent art QA, game integration and measured performance; do not conflate design QA with asset adoption.

## Priority and ownership

1. Finish **regional C01–C03** (real candidate coastline, elevation/contour, directed drainage) before claiming build-ready area positions; extend to C04–C07.
2. Finish **WINDWAITING_CLIFF area master** in #421 owner coordination, using approved CG and current C13/E/C12 without mixing their provenance. PR #482 can contribute **read-only design derivatives** but must not seize the #421 production writer.
3. Finish **RILDE_VILLAGE**, **COASTAL_MEADOW**, **RIVER_CORRIDOR**, **MOSS_FOREST_A1/A2/A3**, **DUNVAR_FORTRESS** with the same D0–D4 evidence gates. Regional integration #364, common engine #468, Studio #476 remain owned separately.

**Current determination:** all eight area master blueprints are **NOT COMPLETE**; no assertion that native production is complete or that G1–G4 passed. Preserve prior assets and existing qualified production without forced cancellation. No canon replacement, main merge, lease takeover, Actions dispatch, native asset change or publication performed by this audit.
