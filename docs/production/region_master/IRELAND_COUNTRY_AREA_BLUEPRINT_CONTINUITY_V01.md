# TWO — Ireland-inspired country / area blueprint continuity v0.1

Status: **DESIGN_CANDIDATE / G1 BLOCKED**. This is a durable, non-canonical design inventory and next-work contract, **not** an approved world map or finished drawings. Director priority (2026-11-23): finish the country-wide and per-area blueprints **before** resuming detailed cliff sculpt. Other continents/countries deferred.

## Authoritative sources and ownership

- Main: `AGENTS.md`, `docs/policy/TWO_PRODUCTION_OS_V1.md`, `docs/policy/CONTINUITY_AND_PRODUCTION_READINESS_20261123.md`, `docs/policy/ART_DIRECTED_HYBRID_WORLD_PRODUCTION_V2.md`.
- Existing measured regional source: `docs/production/region_master/aidan_region_master_blueprint_v1.json`, Git blob `d85989416e5ab769ef9a1a74439be5faf96e6348`. Revalidate SHA on reuse.
- Existing GSI coverage probe: `tools/map_blueprint/gsi_coverage_probe.py`, workflow `two-region-gsi-coverage.yml`. A one-point NO_INTERSECTION in one layer is **not** country-wide DEM rejection.
- PR #364: regional integration/coordinate owner; PR #421: cliff input and protected C-series candidate work; PR #468: shared production infrastructure. Do not overwrite active writer, leases, protected assets or official CG. Private canon must remain private.
- Actual official CG/canon SHA, live writer/lease, country DEM raster SHA and vertical datum are **not verified here**.

## Fixed contract vs unknowns

**Fixed:** X east, Y north, Z up, right-handed, 1 Blender unit = 1 metre, fictional sea-level Z=0; provisional local modules permitted. Ireland geography is **visual/geological reference**, not canonical geolocation.

**Unresolved:** country boundary, exact Rilde origin, chunk size, absolute elevations, watershed geometry, roads, inter-area metric transforms and real-world-to-fictional datum. The legacy cliff map 4800×4800, tile 8, unitScale 2.5 is **not verified in metres**. Never assign its coordinates directly to world XYZ.

## Country-wide drawing package (required, not yet completed)

1. Plan: coast, bays, promontories, mountains/uplands, river basins, settlement/fortress and paths.
2. Topography: elevation source provenance, CRS, vertical datum, DEM resolution/SHA, contours, ridges, valleys and slopes.
3. Hydrology: catchments, river outlets, wetlands, bridges, erosion, drainage and sea interface.
4. Geology: rock strata, faults/fractures, cliff-to-plateau transitions, landslides, sediment.
5. Ecology/art: coastal grassland, farmland, temperate woodland, hedgerows, stonework and art-directed palettes.
6. Traversal/story: walkable connections, hazards, cinematic jump transitions, camera compositions, gameplay clearance.
7. Seam sheet: adjacent-area boundaries, local-to-region transforms, shared elevations, normals, collisions and QA.

## Area blueprint inventory (design candidates, not canon)

| Area ID | Drawing focus | Production method / owner |
| --- | --- | --- |
| RILDE_VILLAGE | settlement plan, harbour, riverbanks, farmland, house footprints, ground contact | heightfield + precise buildings; #364 coordination, existing HOME/BUILD owners |
| WINDWAITING_CLIFF | sea-facing silhouette, plateau, strata, fractures, collapse, ascent and hazard boundaries | precise sculpt/mesh; #421 |
| COASTAL_MEADOW | rolling terrain, grass, farmland, hedges, drainage, trails | heightfield + GN; ECO/WORLD owner |
| RIVER_CORRIDOR | longitudinal river profile, catchment, crossings, banks and bridge foundations | hybrid terrain + authored interfaces; WORLD/ROUTE owner |
| MOSS_FOREST_A1 | forest-edge contours, entrance and traversable paths | hybrid + GN; ECO/WORLD owner |
| MOSS_FOREST_A2 | wooded valley, stream, canopy, understory and obstacles | hybrid + GN; ECO/WORLD owner |
| MOSS_FOREST_A3 | rocky woodland, ravine, exit and cliff/fortress transition | precise rock + hybrid forest; ECO/WORLD owner |
| DUNVAR_FORTRESS | defensive upland, approaches, foundation and runoff | precise mesh + terrain; BUILD/WORLD owner |

For **each** area deliver plan, elevations, longitudinal and transverse sections, contour and slope sheet, material/UV and mesh topology intent, biome and geology map, contact/collision/navigation, camera views, boundary and uncertainty ledger. Numeric dimensions stay `null` until grounded by approved CG, measured native geometry or explicitly marked provisional design.

**Story topology preserved:** lind_village → river_escape → cliff_collapse → moss_forest_A1 → moss_forest_A2 → moss_forest_A3 → dunvar_fortress. These are narrative edges, **not** proven physically walkable links.

## Blueprint acceptance and execution

- D1: verify approved CG/private canon/source licenses, hashes, DEM CRS/vertical datum.
- D2: country-scale coastline, contours, hydrology, ecology, area extents and transform consistency.
- D3: each area orthographic/section sheets, interfaces, route continuity and geometry tolerances.
- D4: independent blueprint/art QA and explicit approval for formal adoption.
- Then qualified Blender 5.3 native authoring, measured residual correction, checkpoint SHA, separate-run reopen and matched-camera renders; G1–G4 remain distinct.
- No unverified source is a PASS. Unknowns: `BLOCKED`; runtime/native/art not performed: `NOT_RUN`.
- Every new chat must read main AGENTS/session index, this document and main region JSON; verify current PR writer/lease/HEAD/Actions/artifacts before mutation. Continue only independent nonconflicting work.
