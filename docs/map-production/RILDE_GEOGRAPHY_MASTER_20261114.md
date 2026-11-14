# RILDE GEOGRAPHY MASTER — 2026-11-14
Status: CANON_GEOGRAPHY_CONFIRMED / VILLAGE_LAYOUT_DESIGN_CANDIDATE / NO_RUNTIME_CHANGES

## Sources and precedence
1. Private canonical `reference/lore/WORLD_MAP_CANON_20261108.md` (verified in private handoff repository on 2026-11-14; SHA 5a3cd66e4131a34de363782a2af8f0e4bb145464).
2. Private `reference/lore/CANON_ADDENDUM.md`, latest main.
3. Director-provided geographic schematic (2026-11-14; image is a directional reference, not georeferenced coordinates).
4. Director-approved village design decisions (church/shelter, watermill with pasture, separate training ground).
Old concept panoramas are NOT coordinate truth.

## World topology — confirmed
| Relative sector | Fixed content |
|---|---|
| West–northwest | Sea and Windwatch Cliff / 風見の断崖; sea-facing high ground, sunset |
| Southwest | Separate inlet and small fishing harbor; coastal fishing, not large trade port |
| Center | Rilde Village; houses, storage and gathering |
| North | Fields and main road to Dunvar Fortress, approximately half-day to one day on foot (planning guide) |
| East | River flowing north to south, bridge and riverbank cliff |
| Southeast / downstream | Moss Forest and ancient altar |
| Long-range trade | Rilde → Dunvar Fortress → inland trade relay → Caerdin |

The ocean-facing cliff and the riverbank cliff are different places. The riverbank cliff is relevant to the raid escape and downstream forest arrival. Moss Forest is NOT on the northbound road to Dunvar Fortress. Coastline geometry, exact distances, absolute coordinates and building positions remain undetermined.

## Village-level planning candidate — subject to art/scene QA
- Central plaza: wind stone, well, market, inn, item shop; preserve approved village CG visual language (blue-gray slate roofs, natural stone, timber, flowers).
- North-west within village: waterfall and elder's home (older village layout reference; reconfirm with newer canon if conflicting).
- North elevated village site: church and main civilian raid shelter, with evacuation access from central plaza. Church denomination, size, exact elevation and capacity remain TBD.
- Northeast village: Aidan's home is a layout candidate, not a confirmed world coordinate.
- East, across the river: training yard independently fenced and separated from housing, reachable by bridge.
- Along river: watermill and adjacent pasture, grazing areas, barns; exact riverbank TBD.
- South / southeast village fringe: vegetable fields, orchards, animal husbandry; ensure Moss Forest exit remains distinct from northbound fortress road.
- Southwest exit: route toward small harbor/inlet; west/northwest path toward sea cliff. Do not imply the harbor is at the cliff.

## Scenario continuity / technical requirements
- Village raid → escape along river → riverbank cliff → downstream Moss Forest. Church shelter is a new design direction; do not alter adopted dialogue or named survivors.
- Fixed topology must be reused across peace/dusk/raid/aftermath images. Establish one master coordinate frame before rendering variants.
- Blender collections: TERRAIN, ROADS, WATER, BRIDGES, BUILDINGS, CHURCH, WATERMILL_PASTURE, TRAINING_YARD, VEGETATION, PROPS, COLLISION, EVENTS, LIGHTING. Keep geometry, textures, event triggers and collisions separate.
- G1 canon & approved CG, G2 art quality, G3 alpha/geometry/material/technical validation, G4 game display/performance/SAVE regression. Do not mark production complete without evidence.
- Existing approved PNGs and runtime assets remain untouched. Any changed CG must be separately versioned and reviewed.

## Unresolved / no invention
Exact compass azimuth of paths inside the village, building counts, building footprints, coast-to-village distances, harbor design and church name/capacity are not fixed by the world canon. Do not turn diagram approximations into canonical meters.

## Director update — 2026-11-14: Moss Forest visibility and Windwatch Cliff
- **Moss Forest ancient altar must NOT be visible in any whole-village overview.** Only the southeastern forest edge/entrance and dense canopy may appear. The altar is deep inside the forest and belongs to a separate interior forest map; avoid visible ruins, standing stones, magic circles or altar labels within the overview illustration.
- **Windwatch Cliff** must match the director-provided adopted sunset-cliff CG (2026-11-14): natural coastal high grass, flowers, weathered cliffs, open sea and sunset. Remove the existing in-game bench from the redesign; no fences, watchtowers, banners, platforms, signposts or other surplus man-made structures on the cliff. Existing source CG remains protected.
- Distinguish cliff visual art from gameplay navigation: accessible walking ground can be represented without adding a visible built overlook. Verify occlusion from the village at the actual scene camera angle.
- This change affects new candidate map art and future replacement assets, NOT an immediate deletion of existing runtime bench or approved CG. Review exact asset references before changing runtime.
- QA for overview candidates: reject if altar is visible, cliff has artificial objects, or the east riverbank cliff is confused with the coastal cliff. An automatically generated scale bar is not canon until dimensions are established.
