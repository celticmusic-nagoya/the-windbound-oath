# RILDE WORLD-FIRST GEOGRAPHY MASTER — canon-based, 2026-11-13

Status: CANON RELATIONSHIPS VERIFIED / MAP GEOMETRY NOT YET PRODUCED.
This is a *new* terrain/world design. Existing game maps and coordinates are NOT constraints, by director's explicit 2026-11-13 instruction.

## Canon provenance (private source; do not copy spoilers or full source into public files)
- `the-windbound-oath-handoff/reference/lore/WORLD_MAP_CANON_20261108.md` (main blob 5a3cd66e4131a34de363782a2af8f0e4bb145464)
- `the-windbound-oath-handoff/reference/lore/SCENARIO_CANON_20261108.md` (main blob 74a1a9dedfeb08a22efa34eb0b083981c092bd1b)
- `the-windbound-oath-handoff/reference/lore/CANON_ADDENDUM.md` (main blob e1000869aaf232d989761d15c982ed798378b49d)
- `the-windbound-oath-handoff/reference/lore/CANON_STATUS.md` (main blob ec5940c2ca6466150810f93c7fc6a463ef7ebec3)
- `the-windbound-oath-handoff/reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md` (main blob c20fc9b7ea7aaa0de7449e110463225dab07573e)
Check latest main on each production task; blob SHAs are an audit snapshot, not permanent canon.

## Verified physical geography (world directions, not legacy map directions)
- Rilde: western coastal agricultural/fishing village of Alveria Kingdom; modest fishing, not a major trade port.
- West/Northwest: Windward Cliffs, walkable coastal high ground overlooking open sea and sunset.
- Southwest: separate inlet and small fishing harbor.
- Village center: houses and storage; north side: farmland and main road.
- North: Dunvall Fortress, approximately half to one day on foot (design target, not finalized measured distance).
- East: river flowing north-to-south, bridge and *riverbank cliff*; site of deliberate river jump during raid. This is NOT the sunset coastal cliff.
- Southeast/downstream: Moss Forest and ancient altar; river carries protagonists there, and Lou later guides them back.
- Trade route: Rilde -> Dunvall -> inland hubs -> Caerdyn.

## Required story-space continuity
1. Aidan's house -> village free exploration -> old magical training dummy -> Emma's refreshments.
2. Village outskirts hunt (normal goblin/moss slime) -> grassland/shallow wooded trail -> return report.
3. Village -> coastal Windward Cliffs for sunset promise -> night and return/raid.
4. During raid: rescue civilians -> bridge obstructed -> east riverbank cliff -> protagonists deliberately jump together -> flow downstream to southeastern Moss Forest.
5. Forest and altar -> revisit ruined Rilde (same terrain identity) -> departure toward northern Dunvall.
6. Preserve Emma's optional charm at bridge-side riverbank near collapsed crate on post-raid revisit.

## Geographic layout constraints for NEW terrain model
- North-up planning coordinates only (conceptual). Do NOT map to game pixel coordinates.
- Coastal cliff and riverbank cliff must be separated by distinct landform and navigation paths.
- River downhill flow must be physically legible north -> south and southeast to forest; avoid upstream teleportation.
- Village should support both peaceful and burned states via independent non-destructive environment layers.
- Home location inside village is not given an exact cardinal quadrant in canon; do not promote a guessed location to official.
- Keep traversable approach from village to cliff, training, hunting and northern road, and escape route toward east river.
- Distances other than Dunvall travel-time guidance are not fixed; design candidate scales only, explicitly labeled.

## Quality gates before committing any 3D world master
G1: approved geography, prologue ordering, canon house references; no speculative locations silently marked canon.
G2: convincing coastline, river hydrology, cliff morphology, agricultural village and vernacular architecture at game camera.
G3: Blender procedural seed/version, manifold terrain and coherent UV/material scale, deterministic renders, manifest hashes.
G4: scene transitions, peaceful/ruin states, collision, mobile browser performance, player route readability.
All G1-G4 must pass for final adoption; currently G1 geography PASS (layout geometry pending), G2-G4 NOT_RUN.

## Next deliverables
- Topology diagram and scale-independent site plan with labels (candidate positions inside verified regions).
- Aidan's Home full production-grade model grounded in approved exterior artwork, not legacy map footprint.
- GitHub Actions multi-view preview renders, uploaded PNG and .blend, and in-chat actual render images.
- No main merge, publication, runtime map rewrite or canon edits without explicit authorization.
