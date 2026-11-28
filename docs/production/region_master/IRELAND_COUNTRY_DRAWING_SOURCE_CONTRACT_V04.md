# Ireland-inspired country plan — evidence-based design constraints v0.4

Status: **DESIGN CANDIDATE / NOT CANON / G1 BLOCKED**. This document is a non-destructive source-to-drawing contract; it does **not** claim completed terrain geometry, DEM acquisition or official CG approval. Prioritize country/area blueprint before cliff sculpt.

## Verified GitHub source ledger
- `docs/production/region_master/aidan_region_master_blueprint_v1.json` — blob `d85989416e5ab769ef9a1a74439be5faf96e6348`. Coordinate axes X east / Y north / Z up; right-handed; Blender unit 1 metre; fictional sea-level zero. Origin, chunk size, coastline, hydrology, contours and geology are null. Ireland is a reference, not canonical geolocation.
- `docs/production/region_master/IRELAND_COUNTRY_AREA_BLUEPRINT_CONTINUITY_V01.md` — blob `c41e42a0a1c31a1e97f27086e7883b26b9eeba6d`. Eight area **design candidates**, required drawing package, G1–G4 and D1–D4.
- `data/maps/cliff_moher_01_spiral_ascent.json` — blob `8ae0db3e7921801b29b9d8eea23e39b4d7dc0395`. Legacy runtime map `4800×4800`, tile `8`, unitScale `2.5`; **not verified metres**. Spawn from_lind (150,3658.3778132003163), summit (2280,1262.3578904783485) are legacy coordinates, not world XYZ.

## Macro drawing plan (all geometry unconfirmed)
| Sheet | Source-required feature | Deliverable geometry | Must not infer |
| --- | --- | --- | --- |
| C-01 country plan | fictional Ireland-inspired coast, uplands, basins | closed shoreline polygon, labelled bays/headlands, area polygons | real Ireland outline as canon |
| C-02 elevation | ridges, valleys, cliff-to-plateau | elevation raster/mesh, contours, slope raster, datum | heights from 2D map |
| C-03 water | river escape, estuary, bridges | directed river graph, watershed polygons, mouth at sea | arbitrary river course |
| C-04 geology | cliff strata, fractures, weathering | rock-domain polygons, strata dip, erosion/collapse zones | scan asset equals exact strata |
| C-05 ecology | coastal meadow, farm, moss woodland | biome polygons, habitat transitions, GN exclusion masks | uniform biome by tile |
| C-06 circulation | village → river → collapse → forest A1–A3 → fortress | story edge graph + separately verified traversable nav edges | narrative order proves physical path |
| C-07 integration | shared seams, terrain/building contact | per-area local-to-region 4×4 transforms, edge sampling and residuals | legacy unitScale=metres |

## Area-to-sheet production matrix
| Area candidate | Plan and section priority | Adjacent interface to verify |
| --- | --- | --- |
| RILDE_VILLAGE | harbour/settlement footprint, riverbank sections | river, coastal meadow, cliff route |
| WINDWAITING_CLIFF | cliff face, plateau, fracture and low-angle silhouette sections | village route, collapse and forest |
| COASTAL_MEADOW | rolling slope, hedge and drainage sections | village, coastal water |
| RIVER_CORRIDOR | longitudinal river profile and bridge-bank sections | village, forest/story escape |
| MOSS_FOREST_A1 | edge transition and trail sections | cliff-collapse narrative entry, A2 |
| MOSS_FOREST_A2 | canopy, valley, stream and traversal sections | A1, A3 |
| MOSS_FOREST_A3 | rocky ravine and exit sections | A2, fortress |
| DUNVAR_FORTRESS | upland foundations, approach and runoff sections | A3, approach routes |

These are **interface review requests**, not verified geographic adjacency or formal map connections.

## Evidence and acceptance requirements
1. **Source gate:** verify approved CG SHA and private canon with owner; preserve private assets. For DEM verify actual raster bytes SHA, licence, CRS, horizontal resolution, vertical datum and region coverage. GSI single-point NO_INTERSECTION is insufficient to reject country coverage.
2. **Coordinate gate:** record stable local origin, invertible transforms and numeric round-trip error tolerance; no conversion of legacy `4800×4800` to metres without a measured transform.
3. **Geometry gate:** shoreline polygon closed/non-self-intersecting; stream direction to sea; watershed continuity; cross-area contour and slope residuals measured against explicit tolerances and uncertainty.
4. **Story/traversal gate:** narrative edges separately from physically navigable routes, collisions, terrain contact, camera visibility and event handoffs.
5. **Review gate:** independent design/art review, then qualified Blender native authoring, save/reopen, matched-camera renders, G1–G4. No PASS for unperformed checks.

## Work ownership / safety
PR #364 owns region integration, #421 cliff, #468 production infrastructure. This document changes **no existing native file, runtime map, official image, protected policy, lease, or canonical geometry**. Before actual edits/Actions, synchronize latest owner ACK, lease, HEAD, workflow events and artifacts. Missing evidence => SYNC_UNVERIFIED for affected writes. Director approval required for formal adoption and main merge.

## Next executable action
Retrieve and hash approved country/village/forest/cliff CG; identify licensed terrain raster with verified CRS/datum; produce C-01/C-02/C-03 measured candidate drawings, followed by eight area sections. Until then keep coordinates/elevations null and G1 BLOCKED.
