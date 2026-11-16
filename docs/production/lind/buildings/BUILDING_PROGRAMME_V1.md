# LIND-BUILD-01 — Rilde village building programme v1 (inn / shop / dwellings / storage)

Status: **PRODUCTION SPEC CANDIDATE — NOT CANON, NOT ART-APPROVED.** Lane BUILD, branch `feature/lind-buildings-01`.
Spatial status: footprints, orientations and positions are **not locked** (WORLD contract not yet published). Buildings are authored isolated, origin at front-door threshold centre, front = -Y, Z-up, 1 BU = 1 m.
Interface status: HOME arch-kit contract **not yet published** → all dimensions live in `tools/map_blender/lind/buildings/kit_config.py` and the proposal `arch-kit-contract.PROPOSAL.json` (`PENDING_HOME_ALIGNMENT`).

## 1. Sources (G1 inputs)
| Source | Class | SHA-256 / revision | Use here |
| --- | --- | --- | --- |
| private bible v5.0 §8 Rilde (handoff main `af0d068`) | canon text | private | building list, lived-in priority, wind-moved signs/laundry |
| private `WORLD_MAP_CANON_20261108.md` | canon text (確定) | private | village centre = housing + storage/collection facilities; agricultural/fishing village, **not** a trade port |
| AGENTS.md §13 | repo rule | branch head `c0223b5` | inn, shop are important locations; peaceful buildings enterable; burning versions keep layout continuity |
| PR #307 | director-approved design decision | open PR | blue-gray slate roofs for all Rilde buildings |
| `assets/approved/world/rilde_village.png` | approved CG (village day) | `c55af0770e0aa7c876575e57e4016df3280816459efd41f7200fa5ed3b51726a` (matches `docs/art/approved-world-event-sha256.json`) | architecture language (primary) |
| `assets/approved/game/rilde_story/raid/attack_background_only.png` | approved CG (burning) | `a19e782ec0927f9ef983cf896cf31a18ace0aca8bf2b165714342b1cfe528c3e` | burning-state continuity |
| `assets/approved/game/rilde_story/aftermath/ruins_background_only.png` | approved CG (aftermath) | `78b0801f10b6a763c66aa44265ab381edc398f3b5adfb1b3d3dee0e6c6d917b2` | ruin state: stone shells survive, roofs reduced to charred rafters |
| `.../road/curve_reveal_APPROVED_user_reference.jpg` | approved user reference | `7989bca750f66ade1935c31fd1f15189505f7c8b481b3839d86cb5ab26c4c60b` | far silhouette: dense cluster of steep gables + one tower |
| `.../recovery/relief_with_characters_APPROVED_user_reference.jpg` | approved user reference | `564bf45da05f9bc1d64a5e83986d1ce8eee0ab2e6dea82dd3d62d2a0cc15cda5` | post-raid repair state |
| `data/maps/rilde_in_{inn_1f,inn_2f,shop,storage,barn,house_0x}.json` | game data (not canon, **not layout**) | branch head | storey count / which interiors exist (migration requirement only). Display names 「風見鶏」/「若葉の袋」 are game-data names, canon status 要コード照合 |

Not used: legacy DOM field, `img/field/**` sprites, `リルド村RPGアセット全体マップ.png`, 15-anchor overlay (excluded by packet).

## 2. Architecture language (from the approved village CG, inspected with Read)
Observed (verified in CG):
- Walls: irregular rounded fieldstone, warm honey/grey, thick mortar joints; larger dressed quoins at corners; stone surrounds at ground-floor doors/windows; walls continue up the gables (no flat gable panels).
- Roofs: steep (≈45–50°) dual-pitch, dark **blue-gray slate**, visible courses with uneven lower edges; deep eaves with visible timber rafter ends/brackets; verges with timber bargeboards; stone ridge.
- Stone gable-end chimneys with caps, smoke.
- Dormers (gabled) on 1½-storey cottages; small pent/gabled timber porch canopies over doors.
- Windows: small timber casements with warm interior light, some round-headed; wooden doors with ironwork.
- Lived-in: flower boxes, barrels, hanging bracket signboard (harp emblem on foreground building), market stall with canvas awning, ivy, crates of produce, Celtic banners on poles.
Inferred (not visible; marked as proposal): rear elevations, floor heights, interior structure, roof timber layout (but raid/aftermath CGs show exposed rafter rows after roofs burn → rafters-under-slate is consistent with approved images).

## 3. Building roles

### 3.1 Inn 宿屋 — `lind_bld_inn`
- Role: rest/heal, save-related, time change (bible 宿屋 function list is for the capital inn; for Rilde the existing game data has 1F + 2F interiors → 2 storeys required as migration constraint).
- Canon basis: bible §8 lists the inn among Rilde's main structures; AGENTS §13 "important locations".
- Size class **L** (largest in village after elder house — elder is out of BUILD-01 scope). Footprint proposal 12.0 × 8.0 m, 2 full storeys + attic, ridge ≈ 10.5 m.
- Silhouette (must read at 48 px): long eaves-front block **+ front cross-gable wing** over the entrance, **two** gable chimneys, two gabled dormers, deep timber entrance porch with bench, projecting bracket signboard, ridge weather-vane finial (optional, only if director confirms the game-data name 「風見鶏」), upper-floor shutters.
- Props: barrels, bench, lantern bracket, flower boxes, firewood stack, hitching post.

### 3.2 Shop 道具屋 — `lind_bld_shop`
- Role: item shop (bible §8 「道具屋」). Game data has a single-floor interior.
- Size class **M**. Footprint 8.0 × 6.5 m, 1½ storeys (ground floor + loft), ridge ≈ 7.6 m.
- Silhouette: **gable-front** to the street (contrast with inn eaves-front), wide **shopfront bay** with drop-down counter shutter, striped canvas **awning**, outside display (crates of produce, sacks, barrels), one side chimney, hanging bracket sign.
- Note: the approved CG pairs a market-stall awning with the harp-sign building; whether that building is the shop, the inn or neither is **OPEN (G1 question to director)**. Sign emblems are parameters (`harp`, `pouch_leaf`, `weathercock`, `blank`) with **no baked text**.

### 3.3 Dwellings 一般住宅 — `lind_bld_house_{a,b,c}`
- Role: villagers' homes (bible §8). 4 interiors exist in game data (house_01..04) → at least 3 exterior variants for reuse.
- Size class **S–M**. Footprint 7.0 × 5.5 m, 1½ storeys, ridge ≈ 7.0 m.
- Variants: A eaves-front + pent porch + dormer; B gable-front + gabled porch; C eaves-front + lean-to side extension + no dormer. One chimney each, flower boxes, laundry line anchor (wind channel for ECO/INTEGRATION).

### 3.4 Storage 倉庫 / barn 納屋 — `lind_bld_storage`, `lind_bld_barn`
- Role: collection/storage facility at village centre (world-map canon) and farm barn (bible §8 納屋／倉庫).
- Storage: size **M**, 7.5 × 6.0 m, stone ground storey, **timber weatherboard gable**, big double plank doors, loft door with **hoist beam**, slit vents, no chimney, raised stone plinth.
- Barn: size **L-low**, 11 × 7 m, low stone walls (2.6 m) with tall timber-boarded upper walls, very large roof, wide cart doors on the long side, no chimney.

## 4. Recognisability matrix (silhouette keys)
| Building | Front | Storeys | Chimneys | Dormers | Distinct key |
| --- | --- | --- | --- | --- | --- |
| Inn | eaves + cross-gable | 2 + attic | 2 | 2 | biggest mass, porch, bench, sign |
| Shop | gable | 1½ | 1 (side) | 0 | awning + bay counter + display |
| House A/B/C | eaves/gable/eaves+lean-to | 1½ | 1 | 1/0/0 | small, flower boxes |
| Storage | gable | 1 + loft | 0 | 0 | hoist beam, board gable, double doors |
| Barn | eaves | 1 + loft | 0 | 0 | low walls, huge roof, cart doors |

## 5. Peaceful vs burning continuity (AGENTS §13)
Required by approved raid/aftermath CGs: stone walls, chimneys, door/window openings and footprints **persist**; roofs lose slates and show **charred rafters**; window openings glow (burning) or are black (ruin); signs fall or hang burnt; porches/awnings collapse.
Kit rule: every building is generated with `state ∈ {peaceful, burning, ruin}` from the **same seed and same footprint**; only roof-covering, timber charring, opening emission and soft props differ. Fire/smoke VFX are not BUILD scope (anchors exported as empties `FX_fire_*`, `FX_smoke_*`).
Gameplay: during the raid buildings are inaccessible — doors in burning/ruin state get `collision_door_blocked` empties (G4 adapter decision belongs to INTEGRATION).

## 6. Quality rules for this lane
- No primitive massing presented as art; blockouts must be named `*_blockout*` / `STRUCTURAL_BLOCKOUT_NOT_ART`.
- Individual slates with per-slate dimension/tilt/colour variance; real wall apertures; UV on every mesh; PBR (CC0 Poly Haven, ledgered in PR #309) + procedural variation.
- Evidence: 27° ortho 3/4 render per building, lineup, 48/96 px downsamples, inspected with Read before any claim. G2 never self-approved.
