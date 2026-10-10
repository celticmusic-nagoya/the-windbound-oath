# Moss Forest — asset requests (ASSET GENERATION REQUIRED)

Drop finished PNGs in `img/field/moss/` and add one rule **before** the stand-in rules in `img/field/moss/manifest.json` (`{"match":"^name","file":"name.png","w":..,"h":..}`; w/h = world px, bottom-centre anchored). No code change is needed.

Rules: 1 frame = 1 transparent RGBA PNG; painterly hand-drawn chibi style matching the Lind field art; no text in images; Fiona has human ears and no wings; Lou is palm-sized (「ルー」); weapon is 誓いの剣 (never a dagger); the threat's true name is never shown.

## A. Characters / gimmicks (new frames)

| Asset | Frames | Notes |
|---|---|---|
| `fiona_field_{idle,walk}_{down,left,right,up}` | idle 1 + walk 4 per direction | same canvas/anchor convention as `aidan_*` (1536×1024, feet anchor), ~16yo human healer, no elf ears/wings |
| `lou_field_hover` | 4–6 hover frames | palm-sized fairy, large translucent blue/gold wings |
| `moss_corruption_symbol` | idle 4 + defeated 4 | black-purple corruption sigil/creature, ~48×62 world px |
| `a3_seal` | closed 1, corrupted 2, opening 6 | ancient wind seal, rect 128×18 collision at its base, visual ~144×90 world px |
| `treasure_chest` | closed 1, glint 4, open 1 | ~48×36 world px |
| `fx_treasure_glint`, `fx_seal` | 4–6 each | additive sparkle / seal energy |

## B. Map assets with no stand-in yet

| Asset | Used in | Stand-in today |
|---|---|---|
| `anc_arch_broken_01` | A3 prop | coloured placeholder |
| `anc_boundary_stone_01` | A3 prop | coloured placeholder |
| `anc_boundary_stone_02` | A3 prop | coloured placeholder |
| `anc_rune_broken_01` | A3 prop | coloured placeholder |
| `anc_rune_broken_02` | A3 prop | coloured placeholder |
| `anc_rune_decal_01` | A3 prop | coloured placeholder |
| `anc_rune_decal_02` | A3 prop | coloured placeholder |
| `anc_rune_decal_03` | A3 prop | coloured placeholder |
| `anc_rune_decal_04` | A3 prop | coloured placeholder |
| `anc_shrine_frag_01` | A3 prop | coloured placeholder |
| `anc_shrine_frag_02` | A3 prop | coloured placeholder |
| `anc_standing_L_01` | A2 prop, A3 prop | coloured placeholder |
| `anc_standing_L_02` | A3 prop | coloured placeholder |
| `anc_standing_L_03` | A3 prop | coloured placeholder |
| `anc_stone_marker_old_01` | A2 prop | coloured placeholder |
| `prop_bridge_post_01` | A2 prop | coloured placeholder |
| `prop_bridge_wood_01` | A2 prop | coloured placeholder |
| `prop_campfire_cold_01` | A1 prop, A3 prop | coloured placeholder |
| `prop_fence_broken_01` | A2 prop | coloured placeholder |
| `prop_lean_to_01` | A1 prop, A3 prop | coloured placeholder |
| `prop_marker_fork_01` | A1 prop | coloured placeholder |
| `prop_marker_signpost_01` | A1 prop | coloured placeholder |
| `prop_post_boundary_wood_01` | A1 prop | coloured placeholder |
| `prop_post_boundary_wood_02` | A1 prop | coloured placeholder |
| `prop_root_arch_01` | A2 prop | coloured placeholder |
| `prop_root_steps_01` | A2 prop | coloured placeholder |
| `prop_torn_banner_01` | A3 prop | coloured placeholder |
| `veg_fairy_flower_01` | A3 prop, A3 scatter(node) | coloured placeholder |
| `veg_fairy_flower_02` | A3 prop, A3 scatter(node) | coloured placeholder |
| `veg_fairy_flower_03` | A3 prop, A3 scatter(node) | coloured placeholder |
| `veg_moss_clump_01` | A2 scatter(layer) | coloured placeholder |
| `veg_moss_clump_02` | A2 scatter(layer) | coloured placeholder |
| `veg_moss_clump_03` | A2 scatter(layer) | coloured placeholder |
| `veg_moss_patch_01` | A3 scatter(layer) | coloured placeholder |
| `veg_moss_patch_02` | A3 scatter(layer) | coloured placeholder |
| `veg_moss_patch_03` | A3 scatter(layer) | coloured placeholder |
| `veg_moss_patch_04` | A3 scatter(layer) | coloured placeholder |
| `veg_mushroom_brown_01` | A1 prop, A1 scatter(layer), A2 scatter(layer) | coloured placeholder |
| `veg_mushroom_brown_02` | A1 prop, A1 scatter(layer) | coloured placeholder |
| `veg_mushroom_red_01` | A1 prop, A1 scatter(layer), A2 scatter(layer) | coloured placeholder |
| `veg_mushroom_red_02` | A1 prop | coloured placeholder |
| `veg_reeds_01` | A1 prop, A1 scatter(layer), A2 scatter(layer) | coloured placeholder |
| `veg_reeds_02` | A1 prop, A1 scatter(layer), A2 scatter(layer) | coloured placeholder |
| `veg_thorn_L_01` | A3 prop | coloured placeholder |
| `veg_thorn_L_02` | A3 prop | coloured placeholder |
| `fx_waterfall_01` | A2 prop | coloured placeholder |
| `gnd_leaflitter_01` | A1 scatter(layer), A2 scatter(layer) | coloured placeholder |
| `gnd_leaflitter_02` | A1 scatter(layer), A2 scatter(layer) | coloured placeholder |

## C. Stand-ins in use (derived from Lind art; replace for the final look)

- `rock_M_01` (A1 prop, A1 scatter(node))
- `rock_M_02` (A1 prop, A1 scatter(node))
- `rock_M_03` (A1 prop)
- `rock_S_01` (A1 prop, A1 scatter(node))
- `rock_S_02` (A1 prop, A1 scatter(node))
- `rock_S_03` (A1 prop, A1 scatter(node))
- `rock_S_04` (A1 prop, A1 scatter(node))
- `rock_moss_L_01` (A2 prop, A3 prop, A3 scatter(node))
- `rock_moss_L_02` (A2 prop, A3 prop)
- `rock_moss_M_01` (A2 prop, A2 scatter(node), A3 prop, A3 scatter(node))
- `rock_moss_M_02` (A2 prop, A2 scatter(node), A3 prop)
- `rock_moss_S_01` (A1 prop, A2 scatter(node), A3 scatter(node))
- `rock_moss_S_02` (A1 prop, A2 scatter(node), A3 scatter(node))
- `tree_ancient_great_01` (A3 prop)
- `tree_ancient_sentinel_01` (A3 prop)
- `tree_birch_M_01` (A1 prop, A1 scatter(node), A2 scatter(node))
- `tree_birch_M_02` (A1 prop, A1 scatter(node))
- `tree_dead_taint_M_01` (A3 prop, A3 scatter(node))
- `tree_log_fallen_D_01` (A1 prop)
- `tree_log_fallen_H_01` (A1 prop, A2 prop)
- `tree_log_hollow_A3_01` (A3 prop)
- `tree_mossy_L_01` (A2 scatter(node), A3 scatter(node))
- `tree_mossy_L_02` (A2 scatter(node), A3 scatter(node))
- `tree_mossy_L_03` (A3 scatter(node))
- `tree_mossy_M_01` (A2 prop, A2 scatter(node))
- `tree_mossy_M_02` (A2 scatter(node))
- `tree_oak_L_01` (A1 prop, A1 scatter(node), A2 scatter(node))
- `tree_oak_L_02` (A1 prop, A1 scatter(node), A2 scatter(node))
- `tree_oak_L_03` (A1 prop, A1 scatter(node))
- `tree_oak_M_01` (A1 prop, A1 scatter(node), A2 scatter(node), A3 scatter(node))
- `tree_oak_M_02` (A1 scatter(node), A2 scatter(node), A3 scatter(node))
- `tree_stump_01` (A1 prop)
- `tree_stump_02` (A1 prop, A3 prop)
- `veg_fern_L_01` (A1 prop, A2 scatter(layer), A3 scatter(layer))
- `veg_fern_L_02` (A1 prop)
- `veg_fern_M_01` (A1 scatter(layer), A2 scatter(layer), A3 scatter(layer))
- `veg_fern_M_02` (A1 scatter(layer), A2 scatter(layer), A3 scatter(layer))
- `veg_fern_S_01` (A1 scatter(layer), A2 scatter(layer), A3 scatter(layer))
- `veg_fern_S_02` (A1 scatter(layer), A2 scatter(layer))
- `veg_flower_blue_01` (A1 scatter(layer))
- `veg_flower_white_01` (A1 scatter(layer), A2 scatter(layer))
- `veg_flower_white_02` (A1 scatter(layer), A2 scatter(layer))
- `veg_flower_yellow_01` (A1 scatter(layer), A2 scatter(layer))
- `veg_flower_yellow_02` (A1 scatter(layer))
- `veg_grass_tuft_01` (A1 scatter(layer), A2 scatter(layer))
- `veg_grass_tuft_02` (A1 scatter(layer), A2 scatter(layer))
- `veg_grass_tuft_03` (A1 scatter(layer), A2 scatter(layer))
- `veg_grass_tuft_04` (A1 scatter(layer), A2 scatter(layer))
- `veg_grass_tuft_moss_01` (A3 scatter(layer))
- `veg_grass_tuft_moss_02` (A3 scatter(layer))
- `veg_grass_tuft_moss_03` (A3 scatter(layer))
- `veg_shrub_M_01` (A1 scatter(node), A2 scatter(node))
- `veg_shrub_S_01` (A1 scatter(node), A2 scatter(node))
- `veg_shrub_S_02` (A1 scatter(node), A2 scatter(node))
- `veg_shrub_berry_01` (A1 scatter(node))

## D. Ground

`img/field/moss/standin/ground_grass.png` / `ground_dirt.png` are seamless tiles derived from Lind terrain. A mossy ground tile and a mossy-dirt path tile are wanted (set `ground` in the manifest).
