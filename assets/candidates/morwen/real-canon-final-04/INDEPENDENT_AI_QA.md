# Morwen real-canon-final-04: independent visual QA

Reviewer: independent, read-only. No repository files were modified. All crops are in /tmp/indep_f4/.
Coordinates are aligned-canvas pixels (1200x1600, anchor 600,1540) unless marked "source".
Hashes checked against MANIFEST.json and they match: back raw f3e64078…, front f9a0272c…, right b435dde0…, left a48ab1bc….
Front aligned = source translated, byte-identical on 100% of opaque pixels. Right is 99.0% identical (only the heel fix differs). Left was colour-matched (mean |dRGB| 30).
The raw-to-aligned back difference map (diff_raw_vs_aligned_back.png) shows a smooth global colour change only. There are no rectangular seams from the hair or leather box fixes, and no geometric change.

## 1. Identity of the new back: PASS
Crops: raw_vs_clean_checker.png, grid4.png, crop_skirt_garter.png, zoom_garters.png.
- Open centre slit: yes. The robe parts from about row 560 down and shows the pleated skirt (hem at about row 860, two gold hem lines at rows 832–845), the garter, both legs and both boots.
- No long centre cloth. At columns 565 and 635 the colour runs unbroken from skin (rows 862–904) to sock welt (910–922) to sock (928–1294) to boot (1298–1540). The only thing between the legs is a 1-px alpha-14 speck at (601,1202).
- Wide robe with long hems: robe lowest point is row 1480 on both sides (front is 1440–1443). Silhouette x 204–1005.
- Present: purple and gold, a purple flower with green leaves (on the character's right), one gold laurel tier following the upper band, a book-and-laurel crest centred on the upper back (about row 496), a leather bag on the right hip, and a strap from the left shoulder. Also a purple bob, ribbon and tip crystal.

## 2. Proportions (aligned): FAIL (two items over 3%)
Overall height to the head top cannot be measured in any view because the hat covers the head (hat tip not used). Distances below are measured from the ground (row 1540).

| feature | front | right | back | left | worst vs front |
|---|---|---|---|---|---|
| sock top row | 903 (637) | ~924 (616) | 907 (633) | ~918 (622) | right −3.3% (slanted thigh, borderline) |
| boot shaft top row | 1270 (270) | 1247–1283 slanted (257–293) | **1298 (242)** | **1294 (246)** | **back −10.4%, left −8.9%** |
| skirt hem (centre) | ~870 (670) | – | ~860 (680) | – | +1.5% |
| wrist / cuff bottom | ~792 | ~783 | ~788 | ~804 | <1.5% |
| fingertips | 878 (open hand) | – | 853–855 (curled) | – | pose difference |
| hand centre span (x) | 381 / 816 → **435** | – | 322 / 872 → **550** | – | **back +26%** |
| hat brim width | ~462 | ~487 | ~446 | – | −3.5% |
| silhouette at row 600 / 640 | 467 / 447 | – | 411 / 494 | – | different drape, not a clean shoulder measure (UNSURE) |

Crops: ruler_legs.png, ruler_torso.png, zoom_back_hand_L/R.png, zoom_front_hand_L.png, crop_boots.png.
- In the back view the arms hang at the outer edge of the robe silhouette (row 760: robe 323–875, hands 300–345 and 845–898). In the front view the robe flares about 50 px beyond each hand.
- Back hair reaches about row 435–445. Hair in the side views ends at about row 380, and the front side locks end at about rows 365–400. So the back hair is about 55–65 px longer and also looks fuller.

## 3. Ground contact: PASS (minor note)
- Front, row 1536: soles at x 528–593 and 608–671, centred at 599.5. Both soles reach row 1540.
- Back, row 1536: soles at x 551–591 and 607–648, centred at 599.5. The right heel reaches row 1540; the left heel's last opaque row is 1539 (1 px).
- Right: heel 517–563 and forefoot 601–678. Both reach row 1540.
- Left: forefoot reaches row 1540 (x 556–574), but the heel's last opaque row is 1538, so the heel floats by 2 px.

## 4. Design match across the 4 views: FAIL
Consistent:
- Flower on the character's right in all views. The left view correctly shows only the small hair flower.
- Laurel runs from front-right to the right side to the back-right of the band. None shows in the left view, which is consistent.
- Ribbon on the right side, ending around row 480 (front, right and back).
- Tip crystal in every view. The brim crystal under the flower shows in front and right only, which is plausible because it hangs at the front.
- Crest: two on the front capelet, one on each side capelet, one on the upper back.
- Capelet with tiers and a cuff with a white frill in every view.
- Bag on the right hip, strap from the left shoulder, compass/star emblem, matching size.
- Plaid insert at the front only (front, right and left show it at the front; the back is plain).
- Robe continuity: open front, back slit, side hems reaching rows 1480–1514.

Contradictions:
1. **Garter leg.** Front: one garter on the character's RIGHT thigh (viewer-left, x ≈550). Right view: garter on the near (right) leg. Left view: no garter on the left thigh. Back: one garter on the character's LEFT thigh (viewer-left, x ≈543, buckles at rows ~880–905). The back is the odd one; its garter looks mirrored. (zoom_garters.png)
2. **Boot shaft height.** Back (242 px) and left (246 px) against front (270) and right (257–293). Back and left are the odd ones. Back boots show a top buckle and an ankle-side buckle; having no laces is fine for a rear view.
3. **Arm spread.** Back hand span is +26% and the arms sit outside the robe silhouette, unlike the front. The back is the odd one.
4. **Hair.** The back bob is longer (about 60 px) and fuller, with inward-curled tubular strands and strong horizontal gloss bands. The front and side views show straight, blunt, matte strands. The back is the odd one. (zoom_hair.png)
5. **Gold embroidery motif.** The front and side robe panels carry circular sigils (a circle with a cross). The back panels carry thorn-branch "tree" motifs, plus thorn-vine circles on the brim. Same family, different motif; the back is the odd one (minor).
6. **Hat flower.** The back flower's petals are near white-pink; front and right are lilac-violet. One large flower in the back, against a large flower plus small flowers in the front (minor; the small ones could be hidden).

## 5. Colour and rendering: PASS_WITH_NOTES
Median Lab per material (aligned, alpha 255):
- Body purple: F (28.8, 30.3, −25.2), R (26.7, 28.2, −24.3), B (28.2, 29.4, −23.3), L (28.9, 29.0, −23.3). Matched.
- Bright lining: L 46.6–48.1, C 54–59, hue −36…−38° in all four views. Matched.
- Gold: L 81.0–82.4, b 34.6–37.5. Matched.
- Leather bag: **back L 44.6** against front 33.0 and right 27.8. The back bag is about 12–17 L lighter, pinker and smoother-glossy. (zoom_bags.png)
- Boots: back chroma about 29.8 (a 24, b −17.7) against front about 22.0 and right about 19.2. The back boots are more saturated and have a strong lacquer gloss.
- Hair: back median L 27.3 against front 21.9, and p90 L 83 against front 42. The back hair is lighter and more violet, with heavy specular highlights.
- Socks: back L 38.0, between front 32.3 and right 42.6. Acceptable.
- Line and texture density: interior Sobel mean is F 0.0596, R 0.0626, B 0.0597, L 0.0653. Similar.

Visual remainder: the back is more airbrushed and glossy, with thicker and brighter gold trims than the front and right. The left view now matches front and right well. The back matches in purple and gold but not in leather, boot or hair finish.

## 6. Transparency and edges: aligned PASS, raw NOTES
- **Raw back:** the background is alpha 0 but carries a non-zero RGB purple glow (max 207, mean 54/27/44), which shows up in any viewer that ignores alpha. There are 39,309 haze pixels at alpha 1–12, and 1,989 speck components under 50 px. 42 haze pixels touch the top border at row 0. **No pixel reaches alpha 255 (max 254)**, so the whole figure is about 0.4% see-through. No checkerboard and no white pixels.
- **Alpha-clean copy:** alpha below 13 is set to 0 with RGB zeroed. 4 isolated pixels remain (alpha 13–14, at source (668,231), (397,391), (637,423), (507,1161)). No border contact, bbox 110–911 × 6–1500, no white fringe. The body is still at alpha max 254.
- **Aligned (all four):** background alpha 0 and RGB 0, body 255. Only natural gaps inside the silhouette (between legs, arm–hair). No white edge pixels (right has 1). The dark ring is the drawn outline, not a black halo (zoom_edges2_w/k.png). No border contact or cropping: the back hat tip is at row 47, soles at row 1540. The back has one alpha-14 speck at (601,1202).

OVERALL: FAIL (strict). Purple and gold colour, ground, transparency and the identity of the back pass. The cross-view position rule (garter leg) and the over-3% proportion items fail. If the director explicitly accepts these as part of the fixed back design, the rating would become PASS_WITH_NOTES.

Remaining issues, ranked:
1. The back garter is on the character's left leg; front, right and left put it on the right leg (or show none on the left). [needs redraw] (a local edit on the back, or a decision to change the other three)
2. The back boot shaft is 10.4% shorter than the front (top at row 1298 against 1270), and the left is 8.9% shorter (row 1294). [needs redraw]
3. The back arms are spread +26% (hand span 550 against 435 px) and sit outside the robe silhouette. [needs redraw]
4. The back hair is about 60 px longer and fuller, in a different strand style. [needs redraw]; its lighter colour and gloss [fixable by position/colour]
5. The back bag leather is too light and pink (L 44.6 against 28–33). [fixable by position/colour]
6. The back boots are over-saturated and glossy (C ≈30 against ≈20). [fixable by position/colour]
7. The back hat flower petals are whiter than the lilac in front and right. [fixable by position/colour]
8. Gold motif: thorn-branch on the back against circular sigils on front and sides. [needs redraw] (minor)
9. Raw back: RGB glow under alpha 0, haze and specks, alpha max 254 (no full opacity). The clean copy still has alpha max 254 and 4 specks. [fixable by position/colour] (alpha cleanup; the aligned files are already clean)
10. The left heel floats 2 px (last opaque row 1538) and the back left heel 1 px. [fixable by position/colour]
