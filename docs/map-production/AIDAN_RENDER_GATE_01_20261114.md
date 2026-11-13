# AIDAN-RENDER-GATE-01 — high-quality-first render contract

Status: **PRE-RENDER SPECIFICATION / NOT EXECUTED**. Do not promote the two existing failed Blender models to official art. The director's `ok` authorizes non-destructive preparation and comparison, not adoption or production replacement.

## Required references, in order
1. Current `AGENTS.md`, then private canonical world geography `WORLD_MAP_CANON_20261108.md` and current official bible/addenda.
2. `assets/approved/world/rilde_village.png`, SHA locked against `docs/art/approved-world-event-sha256.json`. Never overwrite the approved CG.
3. Director-approved blue-gray slate roof specification (PR #307), normalized village map JSON, and `AIDAN_HOUSE_EXTERIOR_DESIGN_CANDIDATE_20261114.md`.
4. Claude PR #309: `AIDAN_BLENDER_STRUCTURAL_AUDIT.md`, `AIDAN_ASSET_SOURCE_AUDIT.md`, 81-file SHA lock and source ledger. Preserve CC0 provenance.

## Hard stop before rendering
- Existing candidate A: 672 identical slate pieces, 60 identical chimney stones, no image PBR, UV gaps, wrong camera angle: **G2 FAIL**. Candidate B: thatch roof **G1 FAIL**. Do not spend a third iteration tweaking either method.
- New model must use continuous roof shell + varied row strips + individually sculpted silhouette-edge slates; irregular masonry shell with modeled corner/threshold stones; fitted timber joins; proper roof verge/eaves/ridge; textured materials and chimney cap.
- Do not treat low-poly blockout, untextured geometry, or a technically successful render as an approved model.

## Comparison render matrix
| Output | Camera | Target | Purpose |
|---|---|---|---|
| `game_27deg_1200.png` | orthographic 27° downward | 1200px working image | art comparison against adopted village CG |
| `game_27deg_290.png` | same camera, same model | 290px visible width | final-scale silhouette/door/window QA |
| `game_27deg_256.png` | same | 256px visible width | lower-size QA |
| `game_27deg_384.png` | same | 384px visible width | higher-size QA |
| `front.png`, `rear.png`, `left.png`, `right.png` | orthographic | 1200px | structural and asymmetry QA |

Camera angle is *depression angle from the horizontal*, not roof pitch. Verify numerically against camera vector. Fixed orthographic scale, object origin and ground anchor across all outputs. Use same world illumination/exposure for the color comparison. Include actual adopted CG as a separate comparison reference, not composited into the candidate asset.

## Material and licensing
- Preferred CC0 candidate maps: Poly Haven `roof_slates_03`, `yellow_stone_wall`, `rough_wood`, `weathered_brown_planks`, `cobblestone_floor_04`.
- Re-fetch using PR #309 source ledger; validate provider MD5 and committed SHA-256 lock before Blender reads assets. No fallback to monochrome geometry if a PBR map fails; fail the job instead.
- Slate hue 200–215°, saturation 0.08–0.15 is a **candidate** range only; match actual CG after exposure, do not assert canonical RGB. CC BY/Quaternius are excluded from this first render.
- Blender 5.2.4 LTS is a candidate production pin; verify executable checksum and compatibility before claiming the version is locked.

## G0–G4 acceptance evidence
- G0: dependency hashes; material UVs; slate/chimney repetition check; proper collection separation; 27° camera and 5-view definitions; deterministic seed; no silent fallback.
- G1: blue-gray slate and approved village CG alignment; no accidental invented canon for storeys, dormer, door or chimney.
- G2: independent human visual review at **290px** and full size; coherent roof edges, rubble masonry, realistic joinery, detailed doors, windows, domestic props. Art FAIL blocks approval even if Blender returns zero.
- G3: render hashes, valid PNG dimensions, alpha and edge inspection, no empty render, contact point, no clipping, no missing PBR/UV, actual .blend and manifest.
- G4: 25–30° game field camera, interaction/door anchor, collision and Android/SAVE regression, only after candidate adoption.

## Required artifact package
`candidate.blend`, production Python source, material manifest (source/URL/license/MD5/SHA256), `render_manifest.json` (Blender version/seed/camera/exposure/asset hashes), all 8 comparison PNGs, 290px contact sheet, QA JSON, attempt ledger with failure causes.

## Execution ownership / isolation
- Build and render on a **new dedicated feature branch** based on a reconciled current main; PR #309 and #307 are dependencies, not to be overwritten or cherry-picked blindly. A Draft PR must include artifact run URL, SHA, independent QA and any unresolved blockers.
- Current work is limited to this gate definition. No Blender execution, new model, comparison PNG or CI verification has occurred in this task. The existing CG, sprites, main, runtime and SAVE remain untouched.
