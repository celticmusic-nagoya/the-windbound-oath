# Rilde integrated architecture and precision blueprint contract — 2026-11-21

Director approved the production method in chat on 2026-11-21: exterior/interior integrated architecture, independently loaded interiors, roof/front-wall visibility control, photo-derived PBR, precision production drawings. This approves the method, not individual floor plans, assets, world coordinates, or main merge.

## Inputs and ownership
- HOME #355, BUILD #356: read-only inputs for INTEGRATION #364. Cliff #421 remains Codex-owned.
- Verify latest main policies, private canon, official CG and existing interior map data before layout. Preserve legacy gameplay routes and event anchors.
- Pin input commit, file SHA256, actual mesh bounds, transform and license. Use local Z-up, entrance -Y, origin footprint centre at grade as existing BUILD contract; provisional scale only. Never infer exact dimensions from perspective art.

## Required blueprint package per building
1. Orthographic front/rear/left/right/top views, 1F/2F/loft floor plans where applicable, transverse and longitudinal sections, roof-off axonometric and exploded structure. Dimension chains, units, scale bars, datum, wall thickness, clear opening dimensions, floor heights, stairs, headroom, roof pitch and material IDs. Distinguish measured mesh values, canon, proposed values, blocked values.
2. Machine-readable JSON: source hashes, coordinate system, mesh objects and collections, vertex/face/triangle counts, bounds, opening and door portal transforms, floor polygons, stair connectors, collision volumes, furniture bounds and interaction anchors. Export actual mesh coordinates from Blender (not guessed vertex positions); retain native blend as geometry authority. Separate plans from render perspectives.
3. Exterior/interior alignment: same footprint, door/window openings, roof/beam structure, floor levels and state transitions; no invisible collision obstructions. Reuse original exterior meshes without modifying owner branches. Build interior shell, floors, partitions, stairs, furniture and lights as isolated modules. Exterior shell and interior chunks share local transform and portal IDs.
4. Runtime: load only needed interior chunk, hide roof and camera-occluding walls using separate visibility groups, preserve collision independently; restore exterior on exit. Preserve NPC/event/save/return anchors from current map data. No change to shipped game until integration QA.
5. Materials: ledgered CC0 photo PBR, real texel scale, UV, authored tint, no missing-map fallback accepted as final. Use approved furniture designs as reference after verifying actual assets.
6. Deliverables: dimensioned SVG/PDF drawings, JSON, editable blend, GLB chunks, orthographic renders, cutaway and fixed-camera renders, actual gameplay preview, hash manifest, independent QA. Drawings generated from measured geometry or labeled proposed; update when geometry changes.

## Order and gates
Aidan home first, inn 1F/2F next, shop, dwellings, storage/barn. Inn existing exterior 12 x 8 m plus 4.4 x 1.5 m front wing and eave 6.05 m are BUILD v1 provisional source values, not approved interior dimensions. Barn not built in BUILD v1. No new rooms or NPC roles canonized by this method.
G1 source/design/portal alignment; G2 independent art review; G3 geometry, UV, dimensions, collision, native reopen and exports; G4 playable entry/exit, stairs, interaction, save/load, Android memory/frame-time. PASS only on evidence. No merge or formal asset adoption without explicit approval.
