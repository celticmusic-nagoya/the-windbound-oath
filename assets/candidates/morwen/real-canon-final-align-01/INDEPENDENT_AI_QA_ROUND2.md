# Morwen real-canon-final-align-01: recheck after rebuild (items 3, 4, 6, plus the unfixable FAILs)

The rebuilt files match MANIFEST.json:

| file | sha256 (first 8) |
|---|---|
| morwen_back_final.png | 4c4f1058 |
| morwen_left_final.png | 12a10a2c |
| morwen_front_final.png | acdc6556 (unchanged) |
| morwen_right_final.png | ff8d8d98 (unchanged) |
| comparison_4directions.png | 3b9951b9 |

real.front and real.right still match `data/morwen-hd-canonical-v2.json`. I changed no repository files. Evidence files are in `/tmp/indep_fa/` and start with `re_`.

## Item 3. Ground anchor: PASS_WITH_NOTES (improved)

Opaque means alpha ≥ 128.

| view | lowest opaque row | opaque px on 1540 | opaque px on 1539 | alpha bbox bottom |
|---|---|---|---|---|
| front | 1540 | 55 | 89 | 1541 |
| right | 1540 | 31 | 79 | 1541 |
| back | 1540 | 61 | 70 | 1541 |
| left | 1540 | 12 | 75 | 1541 |

- The back stray pixel at y=1551 is gone.
- Left now reaches 1540. Row 1540 holds only 12 scattered opaque pixels, against 31-61 in the other views. The solid sole row is 1539, so left reads about 0.5 px lighter on the ground than the others. That is acceptable.

Horizontal centre (x):

| view | full outer sole extent | midpoint of heel and forefoot contact |
|---|---|---|
| front | 601 | |
| back | 599 | |
| right | 601 | about 590 |
| left | 598 | about 606 |

- These numbers are unchanged from the first report.
- With the outer-sole definition, all 4 views are within ±4.
- With the contact-midpoint definition, right is about -10 and left about +6. The note still stands: the project needs to fix which definition the anchor uses.
- The right heel fix is unchanged (same file hash). It still passes.

## Item 4. Colour: PASS_WITH_NOTES (bag fixed, back cape not)

| measure | front | right | back | left |
|---|---|---|---|---|
| leather hue (deg) | 21.7 | 18.4 | **16.6** (was 348) | 19.3 |
| leather b* | 10.8 | 11.4 | **12.0** (was 6.6) | 12.2 |
| cape purple, torso band: L | 23.1 | 20.4 | **25.8** | 23.1 (was 22.5) |
| cape purple, torso band: chroma | 31.9 | 30.7 | **38.4** | 31.0 (was 29.7) |
| whole-figure mean L | 34.1 | 32.6 | 37.1 | 36.1 |
| gold hue (deg) | 31.6 | 29.4 | 31.1 | 30.6 |
| Laplacian variance (sharpness) | 417 | 434 | 448 | 496 |

- **Back bag and strap: fixed.** The leather is now brown and matches front/right visually (`re_bag_leather_F_R_Bbag_Bstrap_x2.png`).
- **Left cape: matches.** It sits between front and right.
- **Back cape and hat crown: still not fixed.** The cape is still about +3 L and +20% chroma against front. The hat crown highlights are still brighter. Visible remaining differences:
  - **(a)** The back cape is a brighter, more saturated violet.
  - **(b)** Back gold embroidery is denser and its shadows are lifted. This is the drawing itself and cannot be fixed by recolouring.
  - **(c)** Left is still about 15-20% sharper than front/right.
- **Gold hue:** consistent across all views.
- **Documentation gap:** the cape tweak (c) is not recorded in the left `steps` of compose_meta.json.

## Item 6. Edges, halo, specks, holes: PASS_WITH_NOTES (was FAIL)

Faint pixels (alpha > 0) more than 2 px outside the opaque core:

| view | px > 2 px out (before → now) | px > 4 px out | detached specks (before → now) |
|---|---|---|---|
| front | 77 | 0 | 5 |
| right | 72 | 8 | 0 |
| back | 1704 → **8** | 88 → **0** | 320 → **6** |
| left | 2235 → **54** | 185 → **1** | 270 → **33** |

- **Halo:** on white, the grey haze around the hat tip, ribbons, crystal and cape points is gone. Evidence: `re_left_white_ribbon_x3.png`, `re_edges_back_x4_kwg.png`, `re_edges_left_x4_kwg.png`.
- **Left hat-tip ring:** the hole is now transparent (40 px hole at 917,199). A tiny dark crumb is left inside the ring (`re_left_ring_x4_kwg.png`). Minor.
- **Back leg gap:** transparent, and the grey blobs are gone. A 1 px dark-red/black line still runs along both inner leg edges. It reads as outline and is acceptable. The gap is still split into 45 fragments by 1-px bridges (`re_back_leggap1180_x4_kwg.png`). Minor.
- **Back hair-side gap:** transparent (248 px hole at 468,347). Its edges are stair-stepped with dark crumbs, plus one faint grey dot at the gap bottom on white (`re_back_hairgap_x4_kwg.png`). Minor.
- **New back hole between hat crown, drooping tip and leaf (about 711-729, 129-154):** this is correct. The source is black background there (`re_back_src_hatgap_x8.png` against `re_back_hat_pinholes_white_x8.png`). A few light speckled pixels sit on its edge.
- **New left cape/boot gap (120 px at 847,1300):** correct as transparency. Its edge on white shows grey and black speckle along the inner side (`re_left_hole_847_1300_x4_kwg.png`). Minor and visible at zoom only.
- **Edge softness:**
  - back has 2,949 semi-transparent edge pixels (was 7,755);
  - left has 9,668 (was 13,063);
  - front has 21,595.
  - Back and left edges are therefore harder and more aliased than the officials. There is no halo, but at 1x on light backgrounds the outline looks slightly crisper and stair-stepped.
- **No damage elsewhere:** no translucency inside the figures, and nothing is cropped (bboxes: back 211-1003 x 30-1541, left 424-993 x 16-1541).

## Unfixable FAILs: still present and accurately described

- **Back boot shaft:** the cuff top is still about 1300 (against 1270-1278 in the other views). The shaft is about 240 px against 270, about 11% shorter. The geometry did not change. **FAIL.**
- **Left hat flower, bow and ribbon tails:** still drawn on the near (left) side, in front of the hair and brim. Front and back place them on the character's right. This reads as a mirrored ornament. **FAIL.**
- **Back gold embroidery:** still about 1.5x denser than front. Note.
- **Ribbon-knot crystal:** only in right and left. This was already inconsistent in the official front/right. Note.

---

OVERALL: FAIL

Items 3, 4 and 6 are now PASS_WITH_NOTES. The overall result stays FAIL only because of the 2 issues that need redrawing.

Remaining issues, most severe first:
1. The left view's hat flower, bow and ribbon seem mirrored onto the near side. This needs a redraw.
2. The back boot shaft is about 11% shorter. This needs a redraw.
3. The back cape and hat crown are still about +3 L and +20% chroma against front/right. A recolour could fix this, but it was not part of the rebuild.
4. Back and left edges are harder and more aliased than the officials. Small dark crumbs and speckle remain at the new gaps: the left ring, the back hair-side gap, the left cape/boot gap and the back leg gap.
5. Anchor notes: the contact-midpoint definition puts right at -10 and left at +6, while the outer-sole definition passes. Left's row 1540 is thin (12 px).
6. Notes:
   - back gold density is still higher;
   - left is about 15-20% sharper;
   - the ribbon crystal appears only in the side views;
   - the left cape tweak is missing from compose_meta.json.
