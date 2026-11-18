# WINDWARD CLIFFS — high-end master asset production brief v1.0

Status: **IMPLEMENTATION BRIEF / NOT AN APPROVED ASSET**. Parent method: `docs/policy/LIND_ART_DIRECTED_HYBRID_WORLD_PRODUCTION_V1.md` (director approved 2026-11-18). No scene geometry or final camera is approved by this document.

## Canonical boundaries
- Location: ocean-facing western/northwestern Windward Cliffs, accessible from Rilde village. Sunset/stargazing event silhouette and approved event CG views take priority over generic reference photography.
- NOT the separate eastern raid riverside cliff. No story-jump route from Windward Cliffs to downstream Moss Forest.
- World illustration: `assets/sources/lind-world-20261116/original.png`, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`. This is a composition source, **not a metric orthophoto**.
- Source status reconciliation: older kickoff says image binary missing; later scene interface records registration at commit `dc17dd4846f35ea1f5dea25168eec9ddb50a3838`. Verify binary at actual target HEAD before asserting G1 source PASS.
- Latest private lore and approved event CG SHA/path must be fetched and compared before silhouette signoff. No invented cliff height, coastal bearing, precise coordinates, scene scale or camera.

## Finished-quality visual acceptance design
1. **Macro silhouette:** asymmetrical headland, distinct eroded rock masses, believable stepped fractures and broken edges, no periodic stripes, repeated block geometry or obvious procedural noise.
2. **Mid-scale geology:** coherent strata and erosion directions with local variation, realistic overhangs/undercuts, separated but connected rock plates; physically plausible joins and no floating slabs.
3. **Micro detail:** cracks, chipped edges, weathered stone, sparse lichen/moss in plausible wet/shaded zones, vegetation rooted in soil pockets rather than uniformly painted on bare rock.
4. **Ground/water interface:** convincing grass/soil-to-rock transition, shoreline wetness and wave contact; avoid jagged texture banding and unsupported cliff base.
5. **Composition:** silhouette must read in approved sunset and night event CG sightlines, including final-game viewport; distant vista and near-playable terrain separated.
6. **Material/light:** coherent PBR albedo/roughness/normal and AO, UV or justified triplanar mapping; check daylight, warm sunset and moonlit conditions without hiding geometry defects.

## Recommended actual asset production
- Gather immutable adopted cliff event CGs, register SHA and source class. Use reference photos only for geological reasoning, not as replacements for canon.
- Author focal rock masses by sculpt or scan-guided mesh; keep high-resolution editable master. Sculpt detail deliberately; do not re-run failed heightfield/radial skirt families.
- Use heightfield only for the inland grassland transition; author coast and rock interface as distinct meshes. Scatter via Geometry Nodes with density/exclusion masks and controlled randomness.
- Generate retopologized game mesh, UV/PBR and baked maps, optional LODs, collision mesh and independent walkable surface. Optimize for WebGL/Android after quality signoff.
- Use existing CC0 rock candidates only after scale, silhouette, license, density and texture verification; `rock_face_01` is thin and only a local insert, `boulder_01` is heavy and not a full-cliff solution.
- Keep separate `LIND_TERRAIN`, `LIND_WATER`, `LIND_ECOLOGY` and `LIND_STORY_MARKERS` collections; no conflicting edits to Codex WORLD branch, ROUTE/Method C masonry, HOME/BUILD or character work.

## Deliverables and testable gates
- G1: exact original and adopted event-CG hashes, art-source matrix, approved viewpoint comparison, proposed metric/camera record separately approved. **BLOCKED** until source views and metric authority reconciled.
- G2: high-quality editable Blender source and PNGs (front/side/oblique/top plus approved CG viewpoints), wireframe + material closeups, independent human/art review at final display size. **NOT_RUN** for new cliff.
- G3: re-open Blender, finite/watertight where required, no zero-area faces, normals, UV/PBR/texture integrity, mesh/LOD/collision/walkable surface/shore contact, render reproducibility, performance budget. **NOT_RUN**.
- G4: WebGL scene integration, walkability, event viewpoint, save/event regressions and Android actual device. **NOT_RUN**.
- Store source hashes, provenance/license, editable `.blend`, preview PNG, comparison sheets, QA JSON, attempt ledger and Actions artifacts. Do not call a render or CI SUCCESS final art PASS.

## Production stop rules
If approved event CGs or precise world metric are unavailable, proceed only with source inventory, method evaluation and independent nonmetric rock modules. Do not claim a final silhouette or spatial G1 pass. Stop same causal/method family after two ineffective corrections; record the structural alternative before retry.

## Immediate independent work
1. Check the approved cliff event CGs and SHA, and the world PNG at target HEAD.
2. Inventory existing reusable CC0 rock candidates and prior art failures; avoid repeated download/render.
3. Produce CG-aligned art direction sheet and distinct sculpt/scan mesh strategy; **no procedural placeholder labeled as finished**.
4. Only after source reconciliation, create an editable cliff master candidate on a dedicated WORLD-owned branch and run G1–G3, with G4 after integration.
