# Alveria world/continent and Rilde inset — concept review v0.1

**Status:** IMAGE CONCEPT ONLY / NOT CANON / NOT METRIC / D0 PARTIAL, D1–D4 BLOCKED. Generated image shown in the design chat 2026-11-23; not registered as an approved original, native geometry, world map or licensed terrain dataset. Image asset is not committed here; the exact generated image provenance/SHA and upload pipeline require separate verification before any durable publication.

## Prework / sources
- Latest-main mandatory prework policy: `docs/policy/MANDATORY_PREWORK_RULE_RECONCILIATION_20261123.md` (Git blob `84f4f62dd895005b8c52668814eef75d33bd9699`).
- Region master: `docs/production/region_master/aidan_region_master_blueprint_v1.json` (blob `d85989416e5ab769ef9a1a74439be5faf96e6348`); X east, Y north, Z up, 1 BU=1 m, fictional sea Z0, but origin/shoreline/elevation/river/area transforms unknown.
- Existing design candidate: `RILDE_C01_C03_TOPOLOGY_CONSTRAINTS_V01.json` (commit `63bc965466627508e6866a60b1255da79ac89180`).
- Existing owners: regional integration #364, cliff production #421, shared engine #468; this design PR #482 does not claim native writer rights or dispatch Actions.

## Visual concept — candidate versus evidence
- **Candidate only:** an illustrative Ireland-inspired fictional continent with an inset of western Rilde coastal village, sea-facing cliffs, southwest fishing cove, northern fortress, eastern north-to-south river and southeast forest. Mountain ranges, continental coastline, roads, river meanders and all absolute distances are invented illustration details, **not source-grounded canonical geography**.
- **Directional checks (provisional):** cliff on west/northwest sea coast, fishing cove southwest, Dunvar north, river east, Moss Forest southeast are visually compatible with the directional contract. **No projection, grid, coordinates or GIS validation has been performed**.
- **Known issue:** continent silhouette, mountain/river drainage logic and the Rilde inset-to-continent locator are not georeferenced. Inset orientation and world map alignment are suggestive only. River source/mouth, coastline closure, watershed, settlement distances and the separate riverbank cliff remain unresolved. The world map must not be used to back-calculate physical measurements.

## Mandatory stage order (no skipping)
1. D0: independently verify latest private canon/approved source SHA and owner/lease; preserve exact source and generated-image provenance separately.
2. W01: country topology and regional locator candidate: sea/land components, cultural regions, no unapproved kingdom borders; independent story/topology review.
3. W02: country C01 closed candidate coastline and eight-area boundaries, machine-readable coordinate frame; source status labelled provisional; geometry closure QA.
4. W03: C02 elevation/contours and geological constraints with explicit vertical datum, uncertainty and licensed source, or document why procedural provisional elevations are needed; no fake measured heights.
5. W04: C03 river directed network, catchments, bridge and sea mouth; topological continuity QA, separate sea cliff vs eastern riverbank cliff.
6. W05: C04–C07 geology, ecology, routes and seam transforms; compare world/kingdom/region/area plans and record conflicts.
7. W06: regional inset and whole-cliff-area precise plan, elevations and sections; independent D4 design QA; only then newly affected Blender precision production, native G1–G4.

**Acceptance:** all needed source/scale/transform/geometry/QA evidence must exist and be verified. Illustration aesthetics alone never satisfy W02–W06 or D1–D4. Current G1 BLOCKED; G2/G3/G4 NOT_RUN. No main merge or formal design adoption requested by this document.
