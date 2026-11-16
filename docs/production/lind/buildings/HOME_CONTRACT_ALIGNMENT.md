# LIND-BUILD-01 — alignment with HOME arch-kit contract v1

Contract: `arch-kit-contract.v1.json` (LIND-HOME-01, `CONTRACT_V1_CANDIDATE_NOT_DIRECTOR_LOCKED`), SHA-256 `a415170dfac2d03a71dc973905f5a0ddf707392f10af1c7a755e3f0f37e3c651`.
Vendored byte-identical (read-only) at `vendor/arch-kit-contract.v1.json` + `.sha256`. `kit_config.load_config()` accepts a contract file only if its SHA matches the pin; otherwise it uses an embedded snapshot, records `fallback_used: true`, and `qa_buildings.py` reports `CONTRACT_LOAD = FAIL` (never PASS). Evidence: `docs/qa/lind/buildings/contract_load_evidence.json`.

## Values consumed as-is
Units/axes/origin (footprint-bbox centre at grade, Z-up, entrance -Y); FFL 0.25; storey 2.75; knee 0.30; 1½-storey wall plate 3.30; wall 0.55; quoins long 0.48–0.62 / short 0.28–0.36; door 1.00×2.05, secondary door 0.90×2.00, W1 0.80×1.05 sill +0.95 FFL, W2 0.60×0.75, W3 0.45×0.55; frame setback 0.14; oak lintel 0.18 high, 0.20 bearing; min pier 0.6; min opening-to-corner 0.7 (all checked by QA); eave 0.40; verge 0.30; rafters 0.08×0.15 @0.60; bargeboard 0.05×0.22; slate length/width/thickness ranges; slate colour = centre of contract HSV candidate; chimney plan 0.90×0.75, ≥0.6 above ridge, 0.06 cap drip, 1–2 terracotta pots, lead flashing; ≤16 materials; UV map `UVMap`; naming prefixes `GEO_/COL_/ANC_/LGT_/CAM_/STG_`; contract collections; door anchor pair offsets (0.6 m outside at grade / 0.6 m inside at FFL); camera ortho 27°, az -45°; Cycles ≤64 spp + denoise; AgX; textures `rock_boulder_dry`, `rough_wood`, `weathered_brown_planks` 1k JPG (MD5/SHA identical to HOME's `texture_sources.json`).

## BUILD choices inside contract ranges (documented, compliant)
| Item | Contract | BUILD | Why |
| --- | --- | --- | --- |
| Roof pitch | 38–48 (default 42) | 44 | approved village CG reads steeper than 42; still inside range |
| Slate exposed gauge | 0.15–0.20 | 0.18 | |
| Plinth course | 0.28–0.40 | 0.32 | |
| Quoin course height | 0.15–0.32 | 0.22–0.32 | quoins larger than coursing (open defect in F8 history) |

## Deviations — NOT compliant, requested contract changes for HOME v2
| ID | Item | Contract | BUILD v1 | Reason / request |
| --- | --- | --- | --- | --- |
| DEV-1 | Wall-field texel density | 512 px/m ±25 % | **320 px/m** (1k `yellow_stone_wall` over 3.2 m) | BUILD wall field is a shell + wall-pattern PBR (not modelled stones). At 2.0 m tile the stones rendered ~0.15 m (brick-like, see `docs/qa/lind/buildings/attempt-ledger.json` BLD-VIS-01); CG stones ~0.3–0.5 m. Request: allow per-map tile size for wall-pattern maps, or BUILD switches to 2k map at 3.2 m (≈640 px/m) once memory budget allows. |
| DEV-2 | Wall-field map | `rock_boulder_dry` (stone surface map for modelled stones, F9) | `yellow_stone_wall` (CC0, PR #309 ledger) | a flat shell needs a coursed-rubble *pattern* map; `rock_boulder_dry` has no joints. Albedo desaturated into contract range (measured texture mean sRGB HSV 34°, s 0.32, v 0.69 before tint/desat). |
| DEV-3 | Ridge along X | "X = ridge" and "-Y = entrance" | gable-front types (shop, house_b, storage) have ridge along **Y** | for a gable-fronted building both rules cannot hold; BUILD keeps the entrance rule (anchors, doors). Request: contract states which rule wins for gable-front buildings. |
| DEV-4 | Material IDs | 15 contract IDs | adds `MAT_PAINT_SIGN_GREEN_A`, `MAT_PAINT_GILT_A` (signboard, no text), `MAT_PROP_PAINTED_A` (single palette material for flowers/produce/soil, keeps count ≤16), `MAT_FIRE_GLOW_FX_A` (burning variant only) | request addition; QA `material_ids_in_contract` = FAIL until added. |
| DEV-5 | Building ID | `AIDANHOUSE, INN, SHOP, ELDERHOME, DWELL<nn>, BARN<nn>` | storage = `STORE01` | storehouse is not a barn (game data has separate `rilde_in_storage` / `rilde_in_barn`). Request `STORE<nn>`; QA `bldg_id_in_contract` = FAIL until added. |
| DEV-6 | Opening types | door, door2, W1–W3 | adds `bay` 2.20×1.35 (shop front), `ddoor` 2.20×2.45 (storage cart doors), `slit` 0.14×0.70 (storage vents) | QA reports WARN; request contract entries. |
| DEV-7 | Masonry method | F9 modelled pillowed rubble (HOME) | wall shell + PBR + modelled dressings (quoins/jambs/sills/plinth as irregular-outline extrusions with crowned faces) | secondary buildings at village scale; consistency with Aidan house at 48/96 px is an **open G2 question** for independent QA. |

## Not yet implemented vs contract
- Interior plaster lining, timber partitions, furniture collision boxes (exterior shells only in v1).
- `SPAWN`/`SAVE` anchors (only door pairs + FX event anchors); runtime ids are `CANDIDATE_UNMAPPED` (STORY/INTEGRATION).
- LOD1/LOD2 meshes.
