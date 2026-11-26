# G2 REVIEW 01 — LIND-ECO-01 eco_kit_v1 (Rilde vegetation kit)

- Gate: G2 independent art QA. The reviewer did not author this work. Read-only review.
- Date: 2026-11-17
- **Overall verdict: FAIL** (1 PASS, 9 FAIL, 2 BLOCKOUT_NOT_ART across 12 asset groups)
- Machine record: `/home/claude/qa/eco/g2-review-01.json`. Evidence crops and downsamples: `/home/claude/qa/eco/work/`

## 1. Inputs (SHA-256)
| File | SHA-256 |
|---|---|
| renders/eco_lineup_large_wind0.png | a69340457492310cf1a06b278782638b9b5375fec8151c075950460ca00779e4 (matches renders.json) |
| renders/eco_lineup_small_wind0.png | 955d78b5314a72eee9a434d125984353fa22e3775a91cf013b4ffc4270d8d96f (matches renders.json) |
| renders/renders.json | 4a969dfde064bf9f00d50d54cb1a156f498c52301af393a890688e400f6bf650 |
| textures/grass_card_lod1.png | fe11cba8211fd92e72422c9548babe0988d1f5ebba96f3e578b108e7457fd7b7 |
| textures/leaf_spray_apple.png | 03ddbc141a75a57da57f7fd84ec330b20cf144f55e9acb38752d9a0c37cb6277 |
| textures/leaf_spray_broadleaf.png | 2a86eb8b029d8bb7e887fedfd7ea457036d0fabd14f559cf4078478e47de3e44 |
| textures/leaf_spray_needle.png | 4dfc24ff3a9b6a78d9195207abfbf3b35b5ed6428c6769a5af5eb8d5922e818b |
| refs/lind_world_master_abbb3997.png | abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620 (**verified**) |
| approved/world/rilde_village.png | c55af0770e0aa7c876575e57e4016df3280816459efd41f7200fa5ed3b51726a |
| approved/game/cliff/sunset_background.png | db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07 |
| approved/game/rilde_story/raid/attack_background_only.png | a19e782ec0927f9ef983cf896cf31a18ace0aca8bf2b165714342b1cfe528c3e |
| docs/qa/lind/ecology/PRIOR_HISTORY.md | 23a0a1558bc9ca8d6ee8b0a408910031aeb10b7bdf5852a6182bb3de8ae81481 |
| (context only) /tmp/lind_eco/eco_kit_build.json | 8cb2a05aa3a88d6d2e05103215a38316333a55ff36e9969e6a67208d6dc53ac8 |

## 2. Provenance findings (blocking for any future PASS)
1. The lineup renders are dated 2026-11-16 18:20 and 18:27. The textures, generator scripts and `eco_kit_build.json` are dated 2026-11-17 00:44–00:45. **The renders predate the current build.** `renders.json` records no script, geometry or texture hashes, so the reviewed images cannot be tied to the current geometry or textures.
2. `render_eco.py` `shot_lineup_large` places `eco_tree_conifer_a` (x=7.6), `eco_rocks_river` (x=-12) and `eco_rocks_coastal` (x=-15.6). **None of them appear in the reviewed PNG.** The conifer slot between forest_tall and the hedgerow is empty. This confirms the render/build mismatch.
3. `eco_water_module_wind0_f12.png` changed while this review was running (it is now `f8f0817e…`; renders.json still says `f57e1e08…`). The manifest is stale and the kit is in flux. The water module is out of scope for this review.

## 3. Texture alpha check (PIL)
| Texture | Mode / size | α min/max | Fully transparent | Partial α | RGB under α=0 | Mip coverage (α-clip 0.5, full→32 px) |
|---|---|---|---|---|---|---|
| grass_card_lod1 | RGBA 256×512 | 0/255 | 78.6 % | 0.0 % | flat (70,93,51) = mean colour | 0.214→0.186 (**−13 %**, thins at distance) |
| leaf_spray_apple | RGBA 512² | 0/255 | 85.3 % | 0.0 % | (96,136,65) | 0.147→0.150 |
| leaf_spray_broadleaf | RGBA 512² | 0/255 | 81.5 % | 0.0 % | (90,133,59) | 0.185→0.187 |
| leaf_spray_needle | RGBA 512² | 0/255 | 78.7 % | 0.0 % | (69,100,66) | 0.213→0.257 (**+20 %**, bloats at distance) |

- Good: the alpha is real (not a checkerboard), and colour bleed under α=0 removes the risk of white or black halos. Edge (fringe) colour equals the mean leaf colour.
- Defect: the alpha is strictly binary, with no anti-aliased edges, so it works only with alpha-clip. That gives stair-stepping at close range and shimmer in motion.
- Defect: `grass_card_lod1` blades are rasterised as chains of dots (stipple). Thin strokes were drawn without supersampling. This shows on the magenta composite at `work/tex_on_magenta.png`.
- Defect: `leaf_spray_apple` and `leaf_spray_broadleaf` share the same generator layout (alpha IoU 0.654). Both are **pinnate compound sprays** (ash/sumac-like) with flat vector leaves of one hue and a luminance std of only 11–12. They read as clip-art, not painterly. Apple leaves should be simple ovate leaves in spur rosettes.

## 4. Colour coherence vs approved art (green pixels, HSV)
| Source | Hue med | Sat med | Value p5 / p50 / p95 |
|---|---|---|---|
| Render: tree crowns | 97 | 0.47 | 0.03 / 0.18 / 0.39 |
| Render: hedgerow | 92 | 0.38 | 0.27 / 0.41 / 0.53 |
| rilde_village.png (approved) | 86 | 0.40 | 0.13 / 0.31 / 0.53 |
| World master | 103 | 0.35 | 0.15 / 0.31 / 0.52 |

- The tree crowns are about 40 % darker at the median. Their core is crushed to near-black (p5 0.03 vs 0.13), and the sunlit tops are missing (p95 0.39 vs 0.52).
- The approved art has deep greens **plus** warm yellow-green light tops. The kit has only the dark half.
- The hedge is brighter and flatter than the trees, so the kit is not internally consistent.
- The preview uses neutral grey ground and blue-grey sky. Warm-light coherence is therefore NOT_RUN, but the albedo and value structure already fail.

## 5. Per-asset verdicts
Dimensions come from `eco_kit_build.json` (x, y, z in m). Human reference is 1.75 m.

### 5.1 Deciduous tree — `eco_tree_deciduous_a` (8.1×5.7×6.0) — **FAIL**
- **Silhouette:** the crown is a spiky starburst of fronds pointing outward. It reads as acacia/olive/palm, not as the rounded, cloud-massed oaks and ashes in rilde_village.png and the world master. It is lopsided to the left, and the outer rim shows individual sprays.
- **Card visibility:** cards are oriented along the branch direction, so every rim card shows its whole pinnate-spray outline. The spray texture repeats uniformly, with the same frond shape everywhere.
- **Interior:** there are black voids and near-black shading inside the crown (see §4). Likely causes are card normals following the geometry, no transferred or bent normals, and no translucency.
- **Trunk:** the trunk is smooth and untextured with a lavender-grey cast, with no bark breakup.
- **At 96/48 px** (`work/sheet48_grid.png`) it reads as a dark scribble on a stick. The tree is identifiable, but not as the art direction intends.
- **Structural fix:** build the crown from 5–9 lobed cluster volumes with leaves concentrated on the outer shell. Use leaf-cluster cards oriented to the crown normals with normal transfer from a crown proxy and back-lit translucency. Add a bark texture with a warm brown albedo.

### 5.2 Apple tree — `eco_tree_apple_a` (5.6×5.1×4.5) — **FAIL**
- It reads as a sprawling bush. The 1.3 m trunk and the open-centre scaffolds are hidden, and the crown is sparse and spiky.
- It uses the same pinnate spray as the broadleaf, which is wrong for the species.
- The 90 apples are red specks a few pixels wide. At 96 px they are barely visible, and at 48 px they are gone.
- **Fix:** expose the trunk and scaffolds under a rounded orchard crown. Paint an apple spur-cluster card (ovate leaves plus fruit). Group the fruit into clusters with enough contrast to read at 96 px.

### 5.3 Second tree — `eco_tree_forest_tall_a` (7.6×6.5×7.8) — **FAIL**
- It comes from the same generator and texture as 5.1, with the same starburst silhouette, black interior and visible sprays.
- Next to 5.1 it reads as a scaled copy: kit-level repetition with no species contrast. The build json marks it `PROCEDURAL_CANDIDATE_UNREVIEWED_VARIANT`.
- **Fix:** same as 5.1, plus a distinct crown archetype (taller ovoid, denser, darker) and a distinct leaf card.

### 5.4 Hedgerow — `eco_hedgerow` (4.7×0.9×1.3) — **FAIL**
- It is an extruded box with a sine-wave top and a uniform scatter of tiny identical leaves. There is no depth or value variation.
- Bare stems stick out at both ends like leftover branch stubs.
- It is brighter and flatter than the trees (§4), and the base does not blend into the ground.
- **Fix:** give it an irregular plan curve and height, darker interior AO, a mix of 2–3 leaf types and a grass/underplanting skirt. Clip or integrate the stubs.

### 5.5 Haystack — `eco_haystack` (3.2×3.1×2.7) — **PASS** (form and readability only)
- The beehive profile, straw strand fringe, ground scatter and pole are correct. It reads clearly at 48 px, and its scale is plausible.
- Non-blocking notes: the surface is a uniform fuzz with low value structure. Add a weathered grey-brown cap and rain streaks so it holds up next to the painterly art.
- Warm-light coherence is NOT_RUN.

### 5.6 Livestock — `eco_cow_blockout` (0.5×2.6×1.2) — **BLOCKOUT_NOT_ART**
- It is a metaball volume with white capsule legs, untextured, with odd black patches. It reads as a white goat, not a cow.
- 1.23 m height is low for a cow (1.3–1.5 m at the withers). Self-declared `STRUCTURAL_BLOCKOUT_NOT_ART`.
- **Fix:** a modelled and textured cow (or a confirmed species) with hooves, udder/belly mass, coat colour and correct withers height.

### 5.7 Wheat patch — `eco_wheat_patch` (3.5×2.2×1.3, 73k tris) — **FAIL**
- It is a rectangular block with hard straight edges. The straw is pale and desaturated with a hazy, see-through look, and no ears are readable at any size.
- The golden fields in the world master are far warmer and more saturated.
- **Fix:** warm golden albedo with green/gold variation, larger ear geometry or ear cards, a density taper and an irregular boundary at the edges, and some lodging variation. Plan a card or shell LOD, since 73k tris is heavy for this look.

### 5.8 Vegetable rows — `eco_vegetable_rows` (3.0×2.2×0.26) — **FAIL**
- The soil is a flat brown tray with hard rectangular edges and grey circular dots along the right edge (artefact).
- The cabbages are near-identical spheres on a strict grid, which is obvious repetition. It reads as a board-game tile.
- **Fix:** ridged furrow soil mounds displaced and blended into the terrain, jittered spacing, varied crop species and sizes, and weeds/edge grass.

### 5.9 Flowers — `eco_flower_patch` (2.7×1.6×0.7) — **FAIL**
- The clusters are sparse, with bare ground between them. Red poppies dominate, the purple spikes are barely visible, and the flowers float without a foliage base.
- At 48 px it reads as red speckle.
- The approved art has dense purple lupin/foxglove spikes and large white daisies growing out of a lush grass mass.
- **Fix:** grow the flowers inside a grass/leaf bed, make the purple spikes bigger and more frequent, enlarge the daisy heads, and cluster them more densely.

### 5.10 Fence — `eco_fence_post_rail` (6.8×0.22×1.16) — **FAIL**
- The rails are 7.6 cm round dowels ("broom handles") in a clean, uniform tan, with no grain, weathering or moss.
- The posts are near-identical, and the rail ends overhang the posts without visible fixing.
- The approved fence (rilde_village.png, attack bg) is heavy rough-hewn dark timber with chunky posts.
- **Fix:** split or rectangular rail cross-sections (8–12 cm), a wood-grain texture with a dark weathered value, varied post heights and tilts, nailed or notched joints, and moss and dirt at the base.

### 5.11 Chicken — `eco_chicken_hen_a` (0.26×0.59×0.48) — **BLOCKOUT_NOT_ART**
- The wings are flat rectangular slabs sticking out sideways, the bib is a floating dark slab under the head, and the tail is a flat grey fan.
- The body has no plumage material. Self-declared "no groom, no rig".
- At game scale it is about 30 px tall in the large lineup. The 48 px test had to upsample it, so the source resolution is insufficient.
- At 0.48 m it is slightly tall for a hen (about 0.35–0.45 m).
- **Fix:** shaped feather-group geometry (wing coverts, saddle, sickle tail), a plumage texture or vertex groom, and a head with comb and wattle integrated into the body.

### 5.12 Grass clumps — tuft_short / meadow / tall_lax / coastal_dune / sedge / reed + `eco_grass_card_lod1` — **FAIL**
- **PRIOR_HISTORY check:** this is **not** a repeat of the stopped VEG-F1 method. The code (`eco_assets.py` `build_grass`) uses off-centre tillers, length-dependent droop, V-folded blades, seed heads and dry blades, which is ECO-G1. No blade-count or seed-only change was seen.
- This is the **first G2 FAIL recorded against ECO-G1**. The code labels the current geometry "attempt 2". The counter carries forward.
- **Measurable hypothesis NOT MET.** At 96 and 48 px (`work/grass_ds96.png`, `grass_ds48.png`) the clumps read as thin wisps, not dense tufts. Seed stems drop to 1 px or vanish. The "darker core, lighter crown" difference is only marginally visible.
- **meadow and coastal_dune:** the tillers separate into two or more distinct tufts with gaps, so they do not read as one clump.
- **tall_lax:** the long blades lie flat on the ground like spaghetti. The droop is too strong at lengths over 0.6 m, and the tips touch or rest on the ground plane.
- **Colour:** muted, grey olive. The approved meadows are a saturated, sun-warmed yellow-green.
- **LOD1 card:** the hard planar card bases are visible as wedges in the small lineup, and the texture has dotted blades (§3).
- **Structural fix (not more blades or a new seed, which VEG-F1x stopped):**
  - Add a **basal mass layer**, a dense short-blade ring or shell at the crown, so the tillers fuse into one silhouette.
  - Use clump-level AO and colour (dark core to warm light crown).
  - Cap droop by height above ground.
  - Re-raster the LOD1 card with 4× supersampling and coverage-preserving mips.

## 6. Repetition and readability summary
- Kit-level repetition: one pinnate spray drives all three broadleaf trees (two textures that are about 65 % identical in layout), the cabbage grid is identical, and the posts are identical.
- At 48 px only the haystack, fence and hedge silhouette read unambiguously. The trees read as dark blobs, the cow as a white goat, and the flowers, chicken and wheat lose identity.

## 7. Not judged (NOT_RUN / NOT_RENDERED)
- Wind motion: **NOT_RUN** (no wind=1 frame or wind pair).
- Warm target lighting: NOT_RUN. The preview has neutral grey ground and a blue-grey sky.
- Game camera at 25–30° quarter view: NOT_RUN. The lineup camera is at about 16° elevation.
- Human 1.75 m scale proxy: absent. Scale was judged from build-json dimensions; the trees at 4.5–7.8 m, hedge 1.3 m, fence 1.16 m, haystack 2.7 m and wheat 1.3 m are all plausible.
- Conifer and rocks: NOT_RENDERED in the reviewed lineup.
- LOD transitions and in-engine mip behaviour: NOT_RUN; only offline coverage was measured.
- Performance budget: none given. Noted counts are wheat 73k, hedge 35k and flowers 30k tris.

## 8. Prioritised fix list
1. **Re-render from the current build.** renders.json must carry the script, geometry and texture SHAs. Include the conifer and rocks, a 1.75 m human proxy, the game camera at 25–30°, a warm key light matched to the approved art, and a wind=0/wind=1 pair.
2. **Rebuild the tree crowns** (deciduous, forest_tall). Use lobed cluster crowns with leaf-cluster cards oriented to the crown normals, plus normal transfer and translucency. This removes the starburst silhouette, the visible card rims and the black interior.
3. **Repaint the leaf textures.** Make them species-specific, with painterly hue and value variation, supersampled soft edges and coverage-preserving mips.
4. **Reform the apple tree.** Visible trunk and scaffolds under a rounded orchard crown, and fruit clusters that read at 96 px.
5. **Make a structural change to grass ECO-G1.** Add the basal mass layer, a warm saturated tip ramp and a droop cap, and re-raster the LOD1 card with anti-aliasing.
6. **Replace the cow blockout** with a modelled and textured cow at the correct withers height.
7. **Replace the chicken's slab wings, bib and tail** with feather-group geometry and a plumage texture.
8. **Rebuild the fence** with rough-hewn split rails and weathered dark timber, varied posts and seated joints.
9. **Fix the crop and flower beds.** Golden wheat with readable ears and an edge taper; vegetable furrows blended into the terrain with the tray edges and grey dots removed; flowers grown in a grass bed with larger purple spikes.
10. **Fix the hedgerow.** Irregular form, values matched to the trees, the end stubs removed and the base blended into the ground.
