# Morwen real-canon-final-align-01: independent QA

Scope: `assets/candidates/morwen/real-canon-final-align-01/morwen_{front,right,back,left}_final.png` (1200x1600 RGBA, anchor 600,1540). Read-only review. All evidence files are in `/tmp/indep_fa/`.

Integrity check first: the sha256 of all 4 finals, the comparison sheet and both black-background sources matches MANIFEST.json.

---

## 1. Same person and outfit across 4 directions: PASS_WITH_NOTES

- The required items are present everywhere they can be seen: purple bob, round gold glasses, violet eyes, purple hat with gold trim, purple flower with green leaves, ribbon, crystal at the hat tip, crystal earrings, gold book crest, shoulder bag, 2 vials with chain, plaid pleated skirt, over-knee socks with garters, lace-up boots. Crops: `heads_x1.png`, `torso_x1.png`, `legs_x1.png`, `lm_*_body.png`.
- Contradictions are listed in item 5. The most serious is that the hat ornament appears to be mirrored in the left view.

## 2. Proportions: PASS_WITH_NOTES (one FAIL item: back boot height)

Rows are canvas y values, read from 2x and 0.75x gridded crops (`lm_*_head.png`, `lm_*_body.png`, `grid_boottop_FRBL.png`). Hand rows come from skin-mask components.

| landmark | front | right | back | left |
|---|---|---|---|---|
| eye / glasses row | ~268 | ~248 | n/a | ~270 |
| chin | ~338 | ~323 | n/a | ~344 |
| eye to chin | 70 | 75 | n/a | 74 |
| hair bottom (sides or nape) | ~350 | ~368 | ~393 | ~370 |
| waist belt | 647-673 | 633-647 | hidden | 660-680 |
| wrist cuff to fingertip | 779-879 | 785-883 | 755-827 | 775-880 |
| skirt hem (front edge) | ~864 | ~873 | hidden | ~860 |
| sock top / thigh skin | 863-909 | 894-924 (back of leg 941) | hidden | 859-901 |
| boot cuff top | ~1270 | ~1278 | **~1300** | ~1271 |
| upper boot buckle | ~1320 | ~1324 | **~1350** | ~1325 |
| sole | 1540 | 1540 | 1540 | 1539 |

Comparison against front:
- Eye to sole: front 1272, right 1292 (+1.6%), left 1270 (-0.2%).
- Chin to sole: front 1202, right 1217 (+1.2%), left 1196 (-0.5%).
- The left 1.07 scale brings left into line with front. Right sits about 20 px higher from the eyes down to the belt. It is the official image and stays inside 3%.
- **Back boot shaft (cuff to sole) is 240 px against 270 in front: about 11% shorter. This is above the 3% limit, so FAIL.**
- Back hands are about 30 px higher at the wrist (about 2%). The fingers are curled and the hands are about 72 px long against 100 in front. Hand separation is 535 px against 438 in front (+22%): the arms are held further out. This is a pose difference, not a skeletal one. Evidence: `hands_front_vs_back_x2_lines779_879_755_827.png`.
- Back hair reaches about 23-43 px lower than the other views. That is plausible for a nape seen from behind. Minor.
- Head size: eye-to-chin is 70/75/74. Front is foreshortened, so this is consistent.

## 3. Ground anchor: PASS_WITH_NOTES

Lowest opaque row (alpha ≥ 128):

| view | lowest opaque row | opaque px on row 1540 | notes |
|---|---|---|---|
| front | 1540 | 55 | both boots on the line |
| right | 1540 | 31 | heel 534-552 and forefoot 627-643 both touch 1540 |
| back | 1540 | 61 | both boots on the line |
| left | about 1539 | 0 | 1540 has only alpha < 128; heel 648-673 and forefoot 540-587 are fully opaque only at 1538, so left floats about 1-2 px |

Stray alpha pixels:
- Back has 1 px of low alpha at y=1551 (x=617), which pushes the alpha bbox down to 1551. Front and right end at 1541.

Horizontal centre (x):

| view | full outer sole extent | midpoint of actual heel and forefoot contact |
|---|---|---|
| front | 601 | |
| back | 599 | |
| right | 601 (rows 1528-1531) | about 589-591 |
| left | 598 (rows 1528-1531) | about 606 |

- With the outer-sole definition, all 4 views are within ±4 px.
- With the contact-midpoint definition, right is -10 and left is +6, which fails ±4.
- The heel positions mirror well between the side views: heel centre 541 in right against 658 in left (±58 from 600), and toe tip 687 against 513 (±87).
- The project needs to choose one anchor definition.

Right heel fix: PASS.
- I diffed the final against the original after the (-6,+16) placement and the alpha thresholding. Changes are limited to x 512-593, y 1458-1541 (canvas). There are 0 changed pixels outside the declared box.
- The heel bottom moved 6 px (column 540: 1534 to 1540).
- At 4x and 8x zoom there is no visible stretch and no seam. The buckle is intact. The left half of the buckle, inside the box, moved by sub-pixel amounts only (RGB delta ≤ 20 at y 1477).
- Evidence: `right_boot_x4.png`, `right_boot_orig_x4.png`, `right_heel_diff_x4.png`, `right_buckle_seam_x8_final_vs_orig.png`.

## 4. Colour, brightness, rendering match: PASS_WITH_NOTES

Medians in CIELAB. Script: `color.py`.

| measure | front | right | back | left |
|---|---|---|---|---|
| whole-figure mean L | 34.1 | 32.6 | **37.0** | 35.7 |
| cape purple, torso band: L | 23.1 | 20.4 | **25.9** | 22.5 |
| cape purple, torso band: chroma | 31.8 | 30.8 | **38.3** | 29.7 |
| vivid purple on hat: L | 39.1 | 36.8 | **51.9** | 43.6 |
| gold L | 77.6 | 77.2 | 81.6 | 78.6 |
| gold hue (deg) | 31.6 | 29.4 | 32.0 | 30.6 |
| gold area in torso band (px) | 18.5k | 7.5k | **27.9k** | 13.1k |
| leather (bag/strap) hue (deg) | 21.7 | 18.4 | **348** | 19.3 |
| leather (bag/strap) b* | 10.8 | 11.4 | **6.6** | 12.2 |
| shadow L p5 | 6.2 | 5.5 | 7.8 | 6.5 |
| highlight L p95 | 83.2 | 81.6 | 86.1 | 85.0 |
| Laplacian variance (sharpness) | 417 | 434 | 449 | **499** |

Remaining visible differences:
- **Back cape and back hat crown:** about +3 L and +20% chroma against front. They read as a brighter, more vivid violet. The hat highlights are much brighter (vivid purple L 52 against 39).
- **Back leather is pinkish-mauve, not brown.** Evidence: `bag_leather_compare_FRBL_x2.png`.
- **Back rendering density is higher:** much denser gold thorn embroidery on the cape (about 1.5x the gold area of front). Shadows are slightly lifted (p5 7.8 against 6.2), so shading reads a little flatter and glossier.
- **Left is the closest match** in colour. It is about 15-20% sharper than front/right (Lanczos upscale plus the source), so its outlines look crisper and harder.
- **Gold hue matches** in all four views (29-32 degrees). Back gold is about 4 L brighter.

## 5. Ornament contradictions: FAIL

1. **Hat flower and ribbon side, left view: likely mirrored (FAIL).**
   - In front and back, the flower, ribbon and long ribbon tails are on the character's right side. Front shows them at viewer-left, back at viewer-right. Right view shows them on the near side.
   - In the left view (the character's left side faces the viewer), the full flower cluster, the bow and both ribbon tails are drawn on the near side, in front of the hair and brim. If they were on the right side they would be mostly hidden behind the crown and head.
   - Evidence: `left_hat_x2.png`, `back_hat_x2.png`, `front_hat_x2.png`.
2. **Hat laurel: one tier, PASS.**
   - Back and left show a single sprig running along the band.
   - Front and right (the official images) show a single sprig rising diagonally from the flower up the crown.
   - This is a change of orientation, but there is no second tier anywhere.
   - Back and left also show a second thin dotted or lattice band under the main band. It reads as an extra band compared with front. Minor.
3. **Flowers: PASS.**
   - Hat cluster: 1 large and 1 small flower in every view.
   - Hair clips: 2 in front, 1 in each side view, as expected.
   - Collar brooch flower in front. The collar bow shows in the side views.
   - Leaves are green in every view. Front also has gold laurel-style leaves in the cluster.
4. **Crystals: UNSURE.**
   - The hat-tip crystal on its chain is present in all 4 views.
   - Earrings show in front, right and left.
   - A ribbon-knot crystal appears in right and left but not in front or back. Front and right are both official, so the inconsistency already exists in the reference.
5. **Bag: PASS on side and strap direction.**
   - The bag is on the character's right hip in front and back. It shows in the right view and is hidden in the left view.
   - The strap runs from the left shoulder to the right hip in front, back and left.
   - Note: back shows the bag's emblem flap and buckle face, the same face that front shows. A bag cannot face both front and back. Right already shows that face from the side, so this inconsistency starts in the official images and back adds to it.
6. **Vials and chain: PASS.** There are 2 vials with a chain in front, right and left. Back hides them, as it should.
7. **Socks and garters: PASS in front, right and left. UNSURE in back.** There is a skin gap above the sock top and a garter clip. In back the cape covers the sock tops, so I cannot tell socks from tights there.
8. **Boots: PASS on design, FAIL on shaft height.** Laces show in front and the side views and are hidden from behind. The back shaft is about 30 px shorter (item 2).

## 6. Transparency and edges: FAIL (back and left)

Edge tiles at 4x on near-black, white and green: `edges_{front,right,back,left}_x4_black_white_green.png`. Fringe maps: `left_fringe_map_red.png`, `back_fringe_map_red.png`.

Faint pixels (alpha > 0) more than 2 px outside the opaque core:

| view | px > 2 px out | px > 4 px out | mean Y of these | detached specks |
|---|---|---|---|---|
| front | 77 | 0 | | 5 |
| right | 72 | 8 | | 0 |
| back | 1704 | 88 | about 31 | 320 |
| left | 2235 | 185 | about 23 | 270 |

What this means:
- Back and left keep a **faint dark fringe and speckle** from the black-background cut-out. It shows as grey smudges on white around the hat tip, ribbons, hair tips and cape points. Evidence: `left_white_halo_ribbon_x3.png`, `back_white_halo_ribbon_x3.png`.
- Back and left have **few semi-transparent edge pixels** (back 7,755 and left 13,063, against front 21,595). Most of them have alpha < 64. The edges are harder and more aliased than the officials.

Specific defects:
- **Left hat-tip pendant ring:** the ring's inner hole is opaque near-black (Y 6-20). Front and right have see-through ring holes (enclosed transparent holes: front 14, right 10, left 5 single pixels). This is background that the cut-out left behind. Evidence: `left_final_tip_ring_white_x8.png`, `left_src_tip_ring_x8.png`.
- **Back leg gap:** dark-red and black fringe pixels line the inner leg edges. The transparent gap breaks into 42 fragments, and there are about 30 single-pixel pinholes along the cape and leg edges. Evidence: `back_leggap_white_y1180_x4.png`, `back_leggap_white_y1400_x4.png`.
- **Back heel arches and the hair/shoulder junction:** these are opaque near-black (source Y about 17-19, not pure black). This is probably painted shadow, so UNSURE. Evidence: `back_hair_shoulder_gap_x8_white.png`.

What is fine:
- There is no translucency inside the figures (interior alpha < 255: back 0 outside the leg gap, left 2 px).
- Nothing is cropped. All bboxes are inside the canvas, with the top at y ≥ 13.

## 7. Official originals unchanged: PASS

sha256 against `data/morwen-hd-canonical-v2.json`:
- `real.front` f9a0272c... matches.
- `real.right` b435dde0... matches.
- `real.back` and `real.left` (the older files in `originals/real/`) also match.

Note: the registry still lists `real.back` and `real.left` as CANONICAL. Those are older files, not today's 11/11 sources (6cc28f00..., 3492dc1c...). The registry should be updated before adoption.

---

OVERALL: FAIL

Remaining issues, most severe first:
1. The left view shows the hat flower, bow and ribbon tails on the near (left) side. Front and back put them on the character's right. This is likely a mirrored ornament (item 5).
2. Back and left still carry black-cut-out residue:
   - about 1.7k-2.2k faint dark fringe pixels and 270-320 specks;
   - an opaque black hole in the left hat-tip ring;
   - a dark fringe in the back leg gap;
   - harder, aliased edges than front/right (item 6).
3. The back boot shaft is about 11% shorter (cuff ~1300 against 1270-1278) (item 2).
4. Back colour and rendering do not match front/right yet (item 4):
   - the cape and hat crown are brighter and more saturated (about +3 L, +20% chroma);
   - the leather is mauve instead of brown;
   - the gold embroidery is denser and the shadows are lifted.
5. Anchor notes (item 3):
   - left sits about 1-2 px above row 1540;
   - measured at the heel/forefoot contact midpoint, right is -10 and left is +6 from x 600 (they pass if the outer sole is used);
   - back has a stray 1 px at y=1551.
6. Minor (items 2, 4, 5):
   - left is about 15-20% sharper than the officials;
   - back hands are curled and held wider;
   - back and left show an extra thin hat band;
   - the bag face is visible from both front and back;
   - the ribbon crystal appears only in the side views (already inconsistent in the official images).
