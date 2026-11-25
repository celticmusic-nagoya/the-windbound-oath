# TWO / LIND — Art-Directed Hybrid World Production v1.0

Status: **DIRECTOR APPROVED — PRODUCTION METHOD** (2026-11-18). Scope: environment, world map, geology, roads, water, ecology and scene integration. Does not authorize any candidate asset, world metric, coordinate, camera, main merge, deletion or publication.

## Method decision
The former single procedural heightfield/Python-generated terrain approach is **retired as the primary final-art method**. Preserve its existing candidates and evidence; do not resume the twice-failed smooth/periodic geological-art method family. Heightfields remain appropriate for broad gentle terrain, farms, slopes, masks and distant landscape. Python remains an orchestration, deterministic construction, verification and CI tool, not a substitute for art direction.

Adopt **Art-Directed Hybrid World Production**:
- Official art direction and immutable source CG + approved private lore first.
- Sculpted/authored 3D meshes for signature cliffs, overhangs, fractures, coastal erosion, structural rock transitions and story silhouettes; retopology, UV/PBR, baked normals/AO and LOD.
- Geometry Nodes for vegetation/rock distribution with exclusion masks, irregularity and seed/hash provenance; authored placements for focal details.
- Licensed existing 3D scans/PBR (CC0 preferred) as candidates, only after license, silhouette, scale, source compatibility and QA checks. No automatic adoption.
- Independent road/bridge/harbor engineering: traversable grade, bridge abutments, physical support, junctions, collision and navmesh; a non-buried floating road is FAIL for complete structure.
- Separate editable high-quality Blender masters from optimized WebGL/Android deliverables. Integrate modules through versioned interfaces and scene contracts; do not merge teams' geometry prematurely.

## Priority and spatial protection
1. First high-quality environmental **master candidate**: Windward Cliffs (western/northwestern ocean-facing sunset/stargazing), using official approved event CG and registered world illustration as binding visual references. It is a *candidate* until all gates PASS.
2. East riverside raid cliff is **a different place**. Directed jump to downstream landing is a story transition, not an ordinary walkable edge.
3. Rilde village center/houses, northern farms/Dunvall route, southwest harbor, eastern river/bridge and southeast Moss Forest must preserve approved semantic geography.
4. Adopted illustration SHA-256: `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`. It is picturesque, not a metric orthophoto; decorative scale bar must never set Blender meters. Origin, scale, camera, elevations and final anchors remain **UNAPPROVED / G1 BLOCKED** until director review.
5. Preserve Codex WORLD candidate D and prior c01 as evidence/technical studies, not accepted final terrain. Candidate D has 1557/1557 sampled nonburied points but max 0.444855 candidate-unit support gap, G2 FAIL, and no full G3/G4 acceptance. Prior QA and retry ledger remain authoritative.

## Production sequence
1. Source lock: verify latest main AGENTS, private canon, source SHA, adopted event CG, existing Draft PRs, owners and failures.
2. Art-direction sheet: silhouette, focal views, cliff fracture/erosion logic, grass/stone interface, water/shore contact, weathering, lighting and target final display size; propose common metric and camera for approval, never infer them.
3. Method-specific production: sculpt/scan-guided mesh for focal cliff, heightfield only for soft landscape, masks/instances for ecology, authored structures for roads/bridge/harbor. Avoid low-quality placeholder cycles.
4. QA separately: G1 official CG/source/spatial concordance; G2 independent art at final display size and multiple views; G3 Blender reopen, normals/UV/PBR, topology, seam, support/collision/navmesh, reproducibility, performance budgets; G4 browser/WebGL/Android real device, events/SAVE and regression.
5. Store editable .blend, source provenance/license, textures, render PNG, SHA manifest, QA JSON and failure ledger in branch/Actions Artifacts. Failed candidates are never adopted. Stop same root-cause/method after two ineffective attempts per CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md.

## Ownership and release gates
- WORLD terrain/cliffs; HOME and BUILD architecture; ECO ecology; ROUTE roads/bridge and masonry Method C; character team separate. Coordinate through existing PRs, avoid concurrent edits and duplicated work.
- Non-destructive design, research, candidate assets and QA may proceed autonomously on dedicated branches/Draft PRs.
- **Explicit approval still required** for canonical source replacement, official setting changes, destructive deletion, main merge and publication.
- This is a **method adoption only**. No G1–G4 gate becomes PASS by approving this policy.

## Existing related evidence
- `docs/policy/HIGH_END_3D_CHARACTER_AND_WORLD_PRODUCTION_V1_1.md`
- `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`
- `docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md` (candidate interface on WORLD branch)
- Draft PR #416: WORLD candidate D independent evidence, Blender reopen, visual-render workflow.
