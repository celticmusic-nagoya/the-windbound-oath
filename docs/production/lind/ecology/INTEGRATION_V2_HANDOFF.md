# LIND-ECO-01 — Vegetation integration package v2 (handoff to Codex field integration)

Status: **CANDIDATE_FOR_INTEGRATION_TEST.** Nothing here is adopted art. G2 independent review is NOT_RUN for every v2 asset. G4 (WebGL/Android) is NOT_RUN. No WORLD placement. The cliff-local moss/grass sculpt work is **frozen** (director instruction 2026-11-20), and PR #421 rock source is untouched.

- Owner (asset production): Claude, on this PR (#357, branch `feature/lind-ecology-01`). Runtime integration and G4: Codex. Independent art QA: ChatGPT or another non-author.
- Package: `assets/candidates/LIND-ECO-01/integration_v2/`. Verify with `sha256sum -c SHA256SUMS`, which covers every file including `manifest.v2.json`.
- Rebuild (deterministic geometry): `build_eco_assets.py` → `eco_integration_v2.py` → `eco_integration_v2_render.py` → `package_integration_v2.py`. All four run on Blender 5.3.0 with the official SHA. CI: `.github/workflows/lind-eco-integration-v2.yml` uploads artifact `lind-eco-integration-v2-package` (30-day retention) and fails if geometry hashes or tri counts differ from this commit.
- Reused kit geometry: combined hash `344e32294e0c66f769979c7be1d5f594911646bf51c5fcb393eb83190fa66cba`. This matches CI runs 44668236655, 44669246234 and 44670622140. Every packaged kit asset's per-object hash matches `eco_kit_build.json`.

## 1. Inventory and selection (PR #357 HEAD 54e7d85)
Verdicts: PACKAGE = integrate for testing. SUPERSEDED = replaced in v2. DEFER = kept in the kit but outside this vegetation pass, or owned by another lane. EXCLUDE = known FAIL or blockout.

| Asset | LOD0 tris | Verdict | Reason |
|---|---|---|---|
| `eco_tree_deciduous_a` | 10647 | PACKAGE | oak cloud crown; matches rounded oaks of rilde_village.png and cliff CG foreground tree |
| `eco_tree_forest_tall_a` | 12539 | PACKAGE | beech ovoid; woodland edge / Moss Forest approach |
| `eco_tree_apple_a` | 7829 | PACKAGE | orchard only; not in cliff zone |
| `eco_tree_conifer_a` | 19122 | PACKAGE | conifers visible on rilde_village.png hills; background/forest only |
| `eco_hedgerow` | 5016 | PACKAGE | HEDGE-F2 cluster shell; field boundaries |
| `eco_grass_tuft_short` | 2652 | PACKAGE | ECO-G2 accent tuft over turf; paths/verges |
| `eco_grass_meadow` | 3838 | PACKAGE | ECO-G2 accent clump with seed stems |
| `eco_grass_tall_lax` | 4840 | PACKAGE | field margins, fence feet |
| `eco_grass_coastal_dune` | 4412 | PACKAGE | wind-combed accent for exposed cliff edge only; never as the carpet |
| `eco_sedge_bank` | 3002 | PACKAGE | river banks (rilde_village.png river) |
| `eco_reed_riverside` | 2510 | PACKAGE | river banks, sparse |
| `eco_grass_card_lod1` | 6 | SUPERSEDED | stippled binary-alpha card (G2-01 defect); replaced by per-asset LOD2 impostors |
| `eco_flower_patch` | 44952 | SUPERSEDED | red poppies absent from both approved CGs; split into CG-matched clumps below |
| `eco_wheat_patch` | 59902 | DEFER | farmland crop, not in this vegetation pass |
| `eco_vegetable_rows` | 19122 | DEFER | farmland crop, not in this vegetation pass |
| `eco_haystack` | 7218 | DEFER | farm prop |
| `eco_fence_post_rail` | 592 | DEFER | boundary prop, not vegetation |
| `eco_rocks_river` | 8960 | DEFER | rock lane (PR #421 owns cliff rock); used only as a moss-placement preview surface |
| `eco_rocks_coastal` | 17920 | EXCLUDE | independent G2 FAIL: inflated smooth proxy boulders |
| `eco_river_water` | 3840 | DEFER | water lane |
| `eco_river_bank` | 3360 | DEFER | preview terrain, replaced by WORLD terrain |
| `eco_chicken_hen_blockout` | 5232 | EXCLUDE | STRUCTURAL_BLOCKOUT_NOT_ART |
| `eco_cow_blockout` | 6897 | EXCLUDE | STRUCTURAL_BLOCKOUT_NOT_ART |

## 2. What v2 changes
1. **TURF-T1 `eco_turf_meadow_a`** (new method; see the ledger for the causal difference). This is a continuous 2 m feathered turf tile with yellow-green lit patches and a little straw. It answers the repeated G2 defect "isolated tuft footprints". The accent clumps (ECO-G2) now sit *on* the carpet instead of being the carpet.
2. **CG-matched flowers.** The poppy patch is replaced by three single-species clumps: `daisy_clump` (cliff CG foreground and village verges), `violet_cushion` (violet points in the cliff CG; clifftop cushion habit), and `spike_clump` (lupin/foxglove spikes in rilde_village.png).
3. **Moss** (none existed before). `moss_cushion_a` sits at rock and wall bases. `moss_mat_b` covers upward-facing tops. `textures/moss_tile_*` (basecolor/normal/ORM/height, 0.5 m tile) is the recommended **rock-shader blend** for PR #421 rocks, so no geometry is added to their source.
4. **Low shrub `eco_shrub_round_a`.** It uses the TREE-L3 cluster crown as a runtime preset; `eco_assets.py` is unchanged.
5. **Game materials.** Each asset uses a glTF Principled material: COLOR_0 × baseColorTexture, a derived card normal and ORM, and alphaMode MASK at 0.5 (double-sided). Albedo gain is calibrated toward the approved-CG value structure (crowns ×1.25–1.30, grass ×1.12, bark ×0.95).
6. **LODs.** LOD1 removes whole foliage islands deterministically, scales the kept islands up about their roots, and collapse-decimates bark to 0.3. LOD2 is a two-quad crossed impostor (albedo × AO bake). For turf, LOD2 is a flat top-down decal, which is a **self-FAIL** (see §5).

## 3. Package (tris LOD0/LOD1/LOD2, GLB KiB)
| Asset | Category | Tris | KiB | Placement rule |
|---|---|---|---|---|
| `eco_tree_deciduous_a` | tree | 10647/2446/4 | 958/538/574 | `tree_broadleaf` |
| `eco_tree_forest_tall_a` | tree | 12539/3051/4 | 1095/652/576 | `tree_woodland` |
| `eco_tree_apple_a` | tree | 7829/2030/4 | 728/476/414 | `tree_orchard` |
| `eco_tree_conifer_a` | tree | 19122/5988/4 | 1928/1083/537 | `tree_conifer` |
| `eco_hedgerow` | shrub | 5016/1317/4 | 658/465/171 | `hedgerow` |
| `eco_shrub_round_a` | shrub | 2473/621/4 | 541/457/444 | `shrub_low` |
| `eco_grass_tuft_short` | grass | 2652/1240/4 | 99/47/148 | `grass_accent` |
| `eco_grass_meadow` | grass | 3838/1571/4 | 136/57/169 | `grass_accent` |
| `eco_grass_tall_lax` | grass | 4840/2152/4 | 175/79/155 | `grass_margin` |
| `eco_grass_coastal_dune` | grass | 4412/1862/4 | 159/67/167 | `grass_cliff_edge` |
| `eco_sedge_bank` | grass | 3002/1369/4 | 109/51/144 | `riverbank` |
| `eco_reed_riverside` | grass | 2510/1110/4 | 89/40/143 | `riverbank` |
| `eco_turf_meadow_a` | turf | 6590/1850/2 | 364/103/914 | `turf_carpet` |
| `eco_flower_daisy_clump` | flower | 4718/2844/4 | 194/119/393 | `flower_meadow` |
| `eco_flower_violet_cushion` | flower | 3390/2025/4 | 130/77/390 | `flower_cliff_cushion` |
| `eco_flower_spike_clump` | flower | 1330/750/4 | 71/40/249 | `flower_village` |
| `eco_moss_cushion_a` | moss | 680 | 641 | `moss_cushion` |
| `eco_moss_mat_b` | moss | 572 | 637 | `moss_mat` |

GLB contents: POSITION, NORMAL, COLOR_0 and `_WIND_WEIGHT` (0 at the root, 1 at the tip), plus TEXCOORD_0/TANGENT on carded or textured meshes. Node extras `eco_wind` carry amplitude_m, frequency_hz and flutter. Axes are Y-up with the pivot at ground contact, in metres, in provisional asset-local coordinates.

## 4. Integration contract (`placement_rules.v2.json`)
- **LOD by role, not distance.** The game camera is a fixed 28° orthographic view, so LOD1 is the in-game default, LOD0 is for cutscenes and close cameras only, and LOD2 is for background rows, distant hills and the Android low tier.
- **Wind.** A single global channel `lind_wind_strength` 0..1 drives sway as `_WIND_WEIGHT` × amplitude. At 0 (the wind-stop event) all sway must be exactly zero. Water stays on its own separate channel.
- **Prevailing wind.** xy (0.959, -0.282) in asset space. `eco_grass_coastal_dune` is pre-combed, so align its yaw to this vector ±15° and use it only within 3 m of the cliff lip.
- **Turf.** Place tiles on a jittered 1.3 m grid (±0.35 m, ~30 % overlap, random yaw, scale 0.95–1.15) and leave worn bands bare along ROUTE paths. Rules for zones, slopes, densities and exclusions are in the JSON.
- **Budget warning for G4.** The 28° game-view test scene (about 46 × 26 m visible) used LOD1 turf at 1,850 tris per tile. At that density turf alone is roughly 1.2–1.3 M tris per screen. That is above a realistic Android budget, so G4 must measure it. Options for Codex, in order: (a) LOD1 turf only in a band around the player and on foreground rows, with a terrain splat elsewhere using a meadow albedo built from the LOD1 look (not the failed decal); (b) GPU instancing of one tile mesh; (c) turf density ×0.6 with larger accents. The decision belongs to the runtime owner and needs a G4 measurement.

## 5. Evidence and self/technical QA (not G2)
Renders (Cycles CPU + OIDN, 24 spp) use the **game** materials. Terrain, sea, sky and the 1.75 m capsule are staging proxies. Hashes are in `renders/renders_v2.json`, which ties each render to the input .blend, the build JSON and the render script.
- `v2_cliffmeadow_sunset_lod0.png`: the carpet is continuous with lit/shade patches. The staging sky is flat and there is no cliff or sea in frame, so this does not show integration with the approved CG or PR #421 geometry.
- `v2_gameview_28deg_ortho_fig48px_turflod1.png` / `…turflod2.png`: same layout, LOD1 vs LOD2 turf. The figure measures 45 px (1.75 m × cos 28° foreshortening at 27.4 px/m). LOD2 turf reads as smeared paint: **self-FAIL**.
- `v2_lod_ladder_lod{0,1,2}.png`: matched camera per LOD. The tree LOD1 crown holds its shape. The LOD2 crossed planes are visible at oblique angles, so use LOD2 only for far or background placement.
- `v2_closeup_small_lod0_day.png`, `v2_lineup_lod0_day.png`, and `v2_compare_cg_cliff_vs_v2.png` (approved cliff CG | v2 vignette | v2 game view).
- `tech_qa_v2.json`: 88/88 technical checks PASS. These cover GLB attributes and alpha modes, monotonic LOD tris, render provenance, reused-kit hash match and unchanged approved-CG SHA.
- Colour against the CG (green pixels, HSV): crown value p5/p50/p95 is 0.078/0.275/0.529, against 0.03/0.18/0.39 in G2-01. The p95 target (≥ 0.45) is met; the p5 target (≥ 0.10) is **not met**. Cliff vignette value p50/p95 is 0.235/0.384, against CG 0.227/0.388. Saturation is 0.93 against CG 0.49, because the staging sunset light over-saturates; judge the light rig, not the albedo.

Gates: G1 NOT_RUN (no canonical vegetation specification; CGs are art references). G2 NOT_RUN (independent reviewer required). G3 PARTIAL (export, LOD and hash checks only; no in-engine validation). G4 NOT_RUN.

## 6. Known limits
- Daisy and violet heads are 1–3 px at the game camera. The CGs exaggerate flowers, and the rules allow scale 1.0–1.4. An art-direction call on stylised oversizing is pending.
- Moss mat on the proxy rocks cannot be told apart at vignette scale. The rock-shader blend is the intended route.
- Wind was not rendered (wind 0 only). Wind 1 and the wind-stop transition are NOT_RUN in v2 and need a runtime test.
- Bark is vertex-colour only, with no bark texture in the glTF. It is acceptable at the game camera but not for close-ups.

## 7. Next single executable tasks
- **Codex (runtime):** load LOD1 GLBs into the field prototype in provisional local space, implement the `_WIND_WEIGHT` × `lind_wind_strength` sway with exact zero at wind-stop, and measure draw calls, tris and frame time on the Android target (G4). Stop if turf exceeds budget; report numbers on this PR.
- **Independent art QA (non-author):** run G2 on `v2_gameview_*`, `v2_closeup_small_*` and `v2_compare_*` against the approved CGs. Rate TURF-T1, FLOWER-F2, MOSS-M1 and the shrub separately.
- **Claude (after G2 feedback):** design a structurally different turf far-LOD to replace the failed decal, such as a shell or terrain-splat bake from LOD1 with a normal map. Do not retry the flat-decal family without a causal change.
