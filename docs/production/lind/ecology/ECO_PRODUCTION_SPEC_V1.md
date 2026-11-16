# LIND-ECO-01 — Rilde ecology production spec v1 (CANDIDATE)

Status: **CANDIDATE_NOT_ADOPTED**. Lane ECO, branch `feature/lind-ecology-01`. G1 BLOCKED, G2 NOT_RUN (independent review pending), G3 see `docs/qa/lind/ecology/eco_tech_qa.json`, G4 NOT_RUN. Nothing here is final art; one asset is an explicit structural blockout.

## 1. Sources and constraints
- Canon (private handoff, read-only; paraphrased minimal facts only): Rilde is an agricultural and livestock village with wheat, vegetable and flower fields, apple trees, hay, and cattle, pigs and chickens. The riverbanks are planted. The SW coast has an inlet, the SE has forest toward Moss Forest, and N is farmland. Wind moves vegetation, signs, laundry and leaves. The wind-stop event halts wind-driven motion but **not** water flow. (The bible also lists farmland/livestock S–SE, while the 2026-11-08 world-map canon puts farmland N; ECO follows the newer world-map canon and keeps zones provisional.)
- Visual master (vegetation character only, not to scale): `assets/sources/lind-world-20261116/original.png`, SHA-256 `abbb3997…0620` (dc17dd4). It shows dense deciduous/conifer mixed woodland, golden fields to the north and lush riverbanks. Not copied into this lane.
- Prior history: `docs/qa/lind/ecology/PRIOR_HISTORY.md` (PR #337). The family **VEG-F1** (single-centre radial per-blade scatter) is STOPPED and not reused.
- WORLD lane stopped (Codex owns terrain, PR #346/#352). **All placement here is PROVISIONAL_NOT_LOCKED.** Preview ground, banks, sky and water staging are not terrain deliverables.

## 2. Asset list (eco_kit_v1)
Full machine-readable table with tris, budgets, seeds, hashes and wind parameters: `eco-asset-manifest.v1.json`.

| Group | Assets | Method |
| --- | --- | --- |
| Trees | `eco_tree_deciduous_a`, `eco_tree_apple_a` (open-centre orchard, 90 apples), `eco_tree_forest_tall_a`, `eco_tree_conifer_a` | Recursive branching skeleton (golden-angle azimuth, pipe-model radii, gravitropism/droop, root flare, buttress roots) swept as parallel-transport tubes. Crown = painted RGBA leaf-spray alpha cards (TREE-L2). Conifer = whorled branches + needle-spray cards. |
| Grass | `eco_grass_tuft_short`, `eco_grass_meadow`, `eco_grass_tall_lax`, `eco_grass_coastal_dune`, `eco_sedge_bank`, `eco_grass_card_lod1` | ECO-G1 tiller architecture: off-centre tillers with own lean, V-folded blades with length-dependent droop (clamped), basal sheath layer, dry blades, seed panicles, vertex-colour base→tip gradient. LOD1 = 3 crossed alpha cards. |
| Riverside / coastal | `eco_reed_riverside` (cattails), `eco_sedge_bank`, `eco_rocks_river`, `eco_rocks_coastal` | Rocks: icosphere, 5-octave Perlin plus cleavage-plane clamps. River rocks have wet bases and moss tops. Coastal rocks have sedimentary banding, tide line, lichen and a turf cap. |
| Water module | `eco_river_water`, `eco_river_bank` | Meandering ribbon with `flow_u`/`flow_v` attributes, deep/shallow vertex colour and its own flow channel. Bank = module-local preview terrain (bed, mud, slopes). |
| Fields | `eco_wheat_patch` (seeded jittered drill rows, ~600 stalks, ears+awns+leaves), `eco_vegetable_rows` (ridged soil, cabbages, carrot tops), `eco_flower_patch` (colony-clumped daisy/poppy/spike forms + turf) | Seeded python scatter |
| Boundaries / props | `eco_hedgerow`, `eco_fence_post_rail` (split rails, sag, irregular posts), `eco_haystack` (beehive stack, 2200 straw strands, skirt, pole) | Procedural |
| Livestock | `eco_chicken_hen_a` (metaball body/neck/head + comb, wattles, beak, eyes, folded wings, sickle tail, legs, toes); `eco_cow_blockout` | Hen: **PROCEDURAL_FORM_CANDIDATE_NO_GROOM_NO_RIG**. Cow: **STRUCTURAL_BLOCKOUT_NOT_ART** (do not place). Pig: NOT_STARTED. |

Species are generic temperate forms. None of them is claimed as canon.

## 3. LOD / instance budgets
- LOD0 triangle budgets per asset are listed in the manifest (`budget_tris_lod0`): trees ≤25k (apple ≤20k), grass clumps ≤6–7k, wheat patch (6.4 m²) ≤80k, hedgerow (4 m) ≤40k, hen ≤8k. The QA script enforces them.
- Instance budgets are per 50×50 m world tile (`instance_budget_per_50m_tile`), e.g. grass clumps 300–600, trees 30–60, chickens 20. Copies share mesh data (linked duplicates).
- LOD1 plan: trees get impostor billboards (TODO), grass uses `eco_grass_card_lod1` (3 alpha cards, 6 tris), wheat/flowers get card strips (TODO). The runtime is the 2D browser game, so final delivery is rendered sprites/atlases (L5). Budgets therefore bound render time and memory, not live GPU load.

## 4. Seeds and determinism
- Master seed `20261116`. Each generator salts a `random.Random("<seed>:<asset-salt>")` (string seeding is stable across processes and PYTHONHASHSEED).
- `geometry_sha256` per asset hashes rounded vertex positions, face indices, material indices, vertex colours and `wind_weight`. The QA rebuilds twice in fresh scenes and compares against the build used for rendering.
- The .blend bytes are not deterministic (timestamps). The geometry hashes are the reproducibility contract.

## 5. Wind channel (single global parameter)
- **Input:** `scene["lind_wind_strength"]`, float 0..1. **0 = wind-stop event.** It is the only wind input.
- **Binding:** a non-python driver (type AVERAGE, SINGLE_PROP) mirrors it to `LIND_WIND_CTRL.location.x`. The geometry-node group `LIND_WindSway` reads it through Object Info. No python drivers are used, so it works with auto-exec disabled. After a scripted change, call `eco_lib.set_channel()` (it tags the scene so the driver re-evaluates).
- **Per-asset:** a `LIND_Wind` GN modifier carries Amplitude (m), Frequency (Hz) and Flutter. A per-vertex `wind_weight` (0 = rigid root, 1 = free tip) comes from path length (trees), blade parameter^1.5 (grass/wheat) or height (hedge).
- **Motion:** offset = W·A·w^1.4·(0.62+0.38·sin(2πft − k·pos)) downwind (+X world), plus a flutter term and a small droop. A gust wave travels across the field, and the phase uses world position, so copies do not sway in lockstep. The offset is rotated into object space (Blender ≥4.1), so rotated copies bend the same world direction. On Blender 4.0 it falls back to object-local direction (flag `lind_world_space_wind`).
- **Guarantee:** at W = 0 every term is exactly 0, so geometry equals the rest pose (verified numerically per asset, max |Δ| = 0.0).
- **Other lanes:** signs, laundry and banners (HOME/BUILD) should reuse `LIND_WindSway` plus a `wind_weight` attribute. That gives them the same single channel.

## 6. Water channel (independent)
- `scene["lind_water_flow"]` 0..1 → `LIND_WATER_CTRL.location.x` → `LIND_WaterFlow` GN group. It has **no wind input**.
- It produces a downstream travelling ripple from `flow_u` (metres along) and `flow_v` (across), stronger mid-channel.
- The wind-stop event sets only `lind_wind_strength = 0`, so water keeps flowing. QA verifies three things: water moves at wind=0, changing wind has zero effect on water, and water=0 freezes water.

## 7. Provisional zone mapping (not locked)
N farmland gets wheat, vegetables, flowers, haystacks, hedgerows and fences. The orchard is apple trees over tall_lax/meadow grass. Village verges get tuft_short, hens and fences. The E river gets the water module, reeds, sedge and river rocks. SW coast gets dune grass and coastal rocks. SE toward Moss Forest gets forest_tall + conifer + deciduous. Real coordinates come only from the approved WORLD spatial contract.

## 8. How to run
```
flock /tmp/blender.lock timeout 900 python3 tools/map_blender/lind/ecology/build_eco_assets.py --out /tmp/lind_eco
flock /tmp/blender.lock timeout 1500 python3 tools/map_blender/lind/ecology/render_eco.py --shot all
python3 tools/map_blender/lind/ecology/postprocess_eco.py
flock /tmp/blender.lock timeout 900 python3 tools/map_blender/lind/ecology/qa_eco.py
python3 tools/map_blender/lind/ecology/write_manifest.py
```
Blender binary: `blender -b --python <script> -- <args>`. Scripts guard 5.x-only APIs (modifier input API, rotation nodes, `surface_render_method`) so they can run on Blender 4.0.2 CI; that path is NOT_RUN locally.
