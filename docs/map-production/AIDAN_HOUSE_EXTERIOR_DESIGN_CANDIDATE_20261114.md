# AIDAN HOUSE — exterior master candidate / 2026-11-14

Status: **DESIGN_CANDIDATE; NOT DIRECTOR-APPROVED EXTERIOR**. Scope: design and acceptance criteria, not a finished Blender model. No runtime or approved asset modifications.

## Verified prerequisites
- Read current branch `AGENTS.md` and `docs/map-production/rilde_layout_coordinates_candidate_v1.json`; current layout anchor `aidan_house=[620,385]` (normalized units, not meters), north-up, on the northeast side of the village.
- Private world-map canon remains the source of truth for regional geography. Aidan's home has no canon-fixed external floor count, door facing, dormer or chimney placement in the current lore; do not silently canonize these details.
- Director-approved village roofs: **blue-gray slate**, per PR #307; approved peaceful village CG `assets/approved/world/rilde_village.png` remains unchanged.
- Claude's PR #309 audit: both old Aidan candidates fail G2. Reuse source ledger and SHA locks but **do not copy** their low-quality modeling approach. Claude's material candidates are not automatically approved.

## Design proposal for director comparison
| Element | Candidate | Approval status |
|---|---|---|
| Massing | Compact 1.5-storey stone-and-timber cottage, asymmetrical handmade silhouette; ground floor plus usable loft | CANDIDATE |
| Roof | Steep 40–50° double-pitched natural slate roof, uneven eaves/edge courses, blue-gray muted PBR | Roof color CANON; pitch/shape CANDIDATE |
| Dormer | One modest dormer on road-facing roof, optional second comparison with no dormer | CANDIDATE |
| Entrance | Front door faces village approach/central-plaza path, not an absolute compass direction until road centerline is confirmed | CANDIDATE |
| Chimney | One stone chimney aligned with existing interior fireplace, roof penetration position to be checked against `data/maps/rilde_in_aidan.json` | CANDIDATE |
| Stonework | Rounded irregular cream-ochre rubble masonry; larger corner quoins and window surrounds | ART DIRECTION |
| Wood | Weathered timber lintels, framed door, mullions/shutters, exposed rafters, bargeboards | ART DIRECTION |
| Props | Firewood, barrels, flower boxes, vines, threshold stones, modest domestic garden | CANDIDATE placement |
| Terrain | Aidan-house plot follows master coordinates; no terrain flattening that breaks village road or drainage | REQUIREMENT |

## Production architecture — replace failed primitive repetition
1. `FOUNDATION`: uneven but structurally coherent plinth, ground contact and drainage.
2. `WALL_SHELL`: cut openings; physically coherent wall thickness; PBR `yellow_stone_wall` candidate; irregular modeled corner stones, not 477 same-course cubes.
3. `TIMBER_FRAME`: fitted joinery, lintels, braces, rafters and weathered planks; no floating beams.
4. `ROOF_SHELL`: continuous shell + strip meshes or Geometry Nodes slate bands; only silhouette-critical edge/eaves/ridge slates individually modeled. PBR `roof_slates_03` candidate, color-corrected blue-gray.
5. `ROOF_TRIM`: ridge stones, eaves, verge/bargeboards, flashing and moss distribution.
6. `DOORS_WINDOWS`: actual framed geometry, hinges, glazing and warm window light.
7. `CHIMNEY`: masonry shell, cap and pot; no 60 identical stones.
8. `PROPS_VEGETATION`: separate replaceable layers with licensing and hashes.
9. `COLLISION`, `ANCHORS`, `LOD`: independent, with origin/ground anchor and door trigger.

## PBR and reproducibility
- Use CC0 candidate set from PR #309: `roof_slates_03`, `yellow_stone_wall`, `rough_wood`, `weathered_brown_planks`, `cobblestone_floor_04`; keep attribution and provider/license ledger for traceability.
- Color candidate only: slate hue 200–215°, saturation .08–.15, value .32–.45, per Claude audit; **not canonical numeric RGB**. Compare against actual adopted CG at matching exposure.
- Blender 5.2.4 LTS is a **production pin candidate**, not yet repository-wide official. Verify compatibility with existing 4.x projects; record executable hash, seed, inputs and Blender version.
- First production render should use a **27° game-camera view** and front/back/left/right comparisons; also assess at 256, 290 and 384px. Camera angle and roof pitch are different parameters.
- Build from structured shell/trim/material modules rather than rebuilding the failed 1320-object/textureless asset. No repeated unproductive trials: max two attempts per failed approach, then diagnose and switch method.

## G1–G4 and blockers
- **G1 PARTIAL:** village roof canon and geography consistent; 1.5-storey/dormer/door orientation/chimney positions remain candidate until director approval and interior map alignment.
- **G2 NOT_RUN:** no new render. Require independent art review of silhouette, roof edges, masonry and life detail against adopted CG.
- **G3 NOT_RUN:** check mesh, UV, texture hashes, ground anchor, alpha, camera, seed and render reproducibility.
- **G4 NOT_RUN:** test field-scale 25–30° rendering, door interaction, collision, Android browser and SAVE regression before adoption.

## Dependency and branch hygiene
Do not edit PR #309 source ledger, PR #307 canon text, approved CG, production sprite, game map or main. Resolve their changes through review/merge strategy later. This document is a proposed implementation contract, not authorization to replace the original.
