# LIND-SPATIAL-CODEX-01 — WORLD candidate production

Producer: Codex WORLD. Baseline d18f7a5. No approved coordinates, dimensions or meters/unit were inferred. Existing source-review implementation was reused separately by TECH; terrain production started after TECH notified source-review PASS. No existing Claude WORLD/HOME/BUILD/ECO package was overwritten.

## Sources and actual research

Directly viewed original PNG (SHA abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620), approved sunset_background.png and raid attack_background_only.png. Source hashes are in tools/map_blender/lind_world_codex_01_config.json. Read adopted master/new-topology: sea-facing west/northwest bluff and eastern raid river bluff are distinct; harbor southwest, farming north. Decorative scale bar and DOM map coordinates were not used.

The actual CG cliff has articulated bedrock joints, erosion benches and turf cap; the raid CG uses layered riverbanks and a masonry arch. These are substantially more complex than the generated study. Material technique research compared layered procedural rock, slope-dependent turf and continuous erosion geometry rather than repeating decorative cubes. No external asset downloaded; all study shader networks authored in this script, so no third-party material license adoption claimed. Scanned/PBR intake and geologist validation remain NOT_RUN.

Historical masonry failures were checked by coordinator: PR331 ledger blob e294bd324aa145e8b4329f2a3d01c83db1e98407 records rectangular chips/periodic rings/perturbed cubes/scan boulder contact defects. Those are reference warnings, not terrain attempt counters. No historical masonry geometry or production assets were imported.

## Actual geometry, not final art

A continuous 241×241 terrain mesh with signed-distance coastline and a separately incised meandering river was created. Western raised grass plateau, a southwest lowered inlet/access fan, eastern river bluff, central connected upland and north cultivated-ground ribbons exist as meshes. The eastern candidate bridge is an extruded single arch mesh, not an accepted building module. Harbor deck is a candidate landing cue, not a finished harbor asset.

A: Initial surface-draped roads failed: some endpoint levels were below water and bridge approaches fell to the channel floor. Rock walls looked like striped smooth extrusions and regional patch boundaries were visible. G2 final art FAIL.

B: Changed geometric coast distance field, stronger bays/fluting, river incision depth referenced to higher river surface, wider water, extended regional domain. River became visible and terrain edge clipping reduced. This remained insufficient: regular cliff/shader form and ungraded route crossings persisted. G2 final art FAIL. After two art failures, this procedural-heightfield geological-art method is stopped; no third same-family geology tuning is planned.

C: Structurally different **route-driven cut/fill** method, addressing route continuity, not a third geological-art improvement. Road centerline elevation profiles are designed before terrain fitting. Terrain vertices are graded with compact shoulders; river bridge span is excluded from fill, and crossing surface follows the bridge crown with 0.05 candidate-unit clearance. Coastal endpoint moves landward; harbor landing has a proposed 1.7-unit profile. Routes report maximum grade against a provisional 25° technical threshold. This is not an approved gameplay/navmesh limit. B geological-art limitations remain; C does not claim final G2 PASS.

## Reproducible outputs

- A generator snapshot: tools/map_blender/lind_world_codex_01_a.py; world/world.blend is the preserved pre-render failure file. world/world-renderable.blend is render-recovered without geometry regeneration.
- B generator: tools/map_blender/lind_world_codex_01.py; world/candidate-b/world.blend.
- C route operation: tools/map_blender/lind_world_codex_01_route_grade.py run against B blend; world/candidate-c/world.blend.
- All three study views (overview/coast/river), blend hashes and Blender version are in each candidate manifest. All units are proposed scene units, with meters_per_unit null.

## Failure preservation and gates

First launch failed because adopted source path was absent in this worktree; exact registered source was copied without alteration. Next render failed because installed Blender lacks OpenImageDenoise. Geometry was already saved, so rendering recovered from that geometry with denoise disabled and original image fake-user set. Both logs preserved; these are distinct environment root causes, not two same-family art attempts.

G1 source bytes protected; full concordance BLOCKED pending approved spatial/event review. G2 final art FAIL (independent QA separately recorded). G3 partial mesh/source/render/route-grade evidence only; collision, navmesh, watertightness, LOD and game budgets NOT_RUN. G4 NOT_RUN. This is a real terrain-production start, not a complete village or accepted final artwork.

Next: replace smooth heightfield bluff walls with explicitly sculpted jointed rock/erosion topology and reviewed geological material/scan intake; author river estuary and distant-terrain continuation, bridge abutment engineering and dock support; obtain director metric/camera approval; independent art/technical/game QA before integration. No main merge, canon replacement or release.
