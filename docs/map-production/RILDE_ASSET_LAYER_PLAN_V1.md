# RILDE MAP LAYER / ASSET PRODUCTION PLAN v1

Status: DESIGN_CANDIDATE. Reference: `rilde_layout_coordinates_candidate_v1.json` (normalized 0–1000 coordinates, not meters). Art direction: adopted peaceful village CG; blue-gray slate roofs. Canon: private `WORLD_MAP_CANON_20261108.md`. Do not override approved CG or runtime.

## Data ownership and hierarchy
- `TERRAIN`: coastal cliff, natural ridge hiding village from Windwatch Cliff, northern uplands, southeast forest foothills, east riverbank cliff; heightfield/mesh with separately authored walkable surfaces.
- `WATER`: open sea, southwestern fishing inlet, north-to-south river, northwest waterfall; render meshes separate from collision, flow direction tagged.
- `ROADS`: northern fortress road, village stone paths, southwest harbor road, western cliff footpath, church evacuation route, southeast forest approach. **Forest footpath crosses only at the east stone bridge**; cliff-to-river escape is an event, not a walkable road.
- `BRIDGES`: east stone bridge as independent structural asset; river clearance, pedestrian collision and navmesh portal QA.
- `BUILDINGS`: modular stone foundation/walls, timber joinery, blue-gray slate roofs, chimneys, windows, doors, shop props; master Aidan house separate from generic homes.
- `CHURCH`: hilltop exterior, entrance, interior shelter capacity, evacuation approach, event doors and crowd anchors; religious lore and exact occupancy TBD.
- `WATERMILL_PASTURE`: waterwheel and race, mill building, pasture, barns, livestock fences, props; water flow/rotating wheel separate.
- `TRAINING_YARD`: dedicated east-bank fenced practice ground, dummy, racks and triggers; no overlap with pasture.
- `VEGETATION`: authored trees, grass, wildflowers, orchard, ivy, moss, deep forest occlusion canopy; performance LOD and wind response.
- `PROPS`: barrels, flower boxes, carts, market stalls, firewood, banners in village. **Windwatch Cliff excludes all artificial objects**, including benches and banners.
- `COLLISION`: independent walkable meshes, water bounds, cliff fall zones, buildings, training-yard boundaries.
- `EVENTS`: raid escape riverbank cliff, church shelter flow, village entrance, harbor exit, forest exit; preserve adopted script/SAVE behavior.
- `LIGHTING`: day/dusk/raid/aftermath variants with identical scene coordinates; shadow/visibility checks.

## Blender hierarchy proposal
`RILDE_MASTER / {TERRAIN, WATER, ROADS, BRIDGES, BUILDINGS, CHURCH, WATERMILL_PASTURE, TRAINING_YARD, VEGETATION, PROPS, COLLISION, EVENTS, LIGHTING}`. Reuse unique asset IDs; separate geometry and authored CG references. Use deterministic generation parameters and recorded Blender version, seed and material manifests. Avoid placeholder geometry as approved art.

## Spatial and narrative constraints
- The southeast Moss Forest ancient altar must be deep in the forest and **not visible** from any village overview. No ruins or ritual stones in overview.
- Natural Windwatch Cliff is ocean-facing and sunset-facing, without bench, railing, tower, sign, banner or platform; ridge must block direct line of sight to village during raid.
- East riverbank cliff is separate, and downstream leads toward Moss Forest. Raid escape into river is not the same as ordinary forest path.
- Village church is primary civilian shelter in raid, with at least one verified accessible path from plaza.
- Training yard is east of the river and independent. Mill and pasture are adjacent to the river, but exact bank and footprints remain candidate.
- Fishing harbor is southwest, distinct from cliff and from any large trade port.

## G1–G4 acceptance plan
- G1: verify every anchor and world sector against canon; confirm road crossings and river flow; audit existing approved CG conflicts before proposing revisions.
- G2: visual inspection at final game size; slate roof layering, irregular masonry, timber details, lived-in vegetation and landscape; independent art QA.
- G3: Blender scene/seed/material hashes, no missing assets, watertight geometry where required, collision and navmesh, reproducible renders, LOD budget measured.
- G4: game camera 25°–30° oblique field view, Android performance, shelter and training paths, script triggers, SAVE migration and regression tests.

## Known blockers
Exact meters, building footprints, elevation and cliff occlusion are not verified. SVG is a plan view, not an elevation proof. The approved cliff CG and approved village CG must remain byte-identical until a separately reviewed replacement is authorized. No runtime change or main merge is authorized.
