# MORWEN FIX-03 masks and spec R3: independent visual QA

Reviewer: independent Claude subagent. I did not make this material and changed no repository files. Evidence is in `/tmp/indep_fix03_r3/`.

Method:
- Parsed EDIT_MASK_FIX03.png per colour: purity, alpha, overlaps, unassigned pixels, connected components and per-column bounds (`an.py`, `comps.py`).
- Made 3–10x crops, each with the original plus mask boundaries (red) next to a 50% mask overlay (`crop.py`).
- Overlaid the derived revealed file on the base image.
- Cross-read REBUILD_SPEC R3, layers.json and the generator.

## Global checks
- 8 pure colours. 0 non-pure pixels and 0 mask pixels on alpha=0. Labels are exclusive.
- **Unassigned subject pixels above 790: 0. PASS** (verified independently).
- **Strap: 1 component, 5,943 px, bbox 513–680 × 451–708. PASS.**

## C3 (capelet top, collar, star, hair front/back): **FAIL (minor; core items fixed)**
- Fixed:
  - There is no 455/456 cut anymore.
  - The hair/capelet boundary is the 10-point polyline at y 421–428.
  - Emblem gold in hair: 0. The collar and top star are fully orange (emb_top.png).
  - Hair-over-capelet is defined in spec §2.9 and in JSON priority.
- Defects:
  - **(a) Hair in the capelet layer.** The polyline is almost horizontal (±3 px over 345 px) and does not follow the strand tips. Hair-tip wisps fall into capelet_move at x≈458–501, y≈424–435 (wispL.png, tips1.png) and at x≈665–707, y≈421–435 (tips2.png, capR_top.png). After the 48 px move they land at y≈376–387, at or below the new tip line (370–380). Stray hair fragments on the collar are likely.
  - **(b) Capelet in the hat layer.** A 106 px capelet fabric highlight at 715–727 × 482–501 is labelled hat_move. It would move 16 px with the ribbon instead of 48 px (ribcap.png).
  - **(c) Stray specks.** About 25 tiny orange specks (≈40 px) remain along the ribbon edge at x 734–778, y 401–492. This is R2 item 9, still partly open.

## C4 (tier-1 lower edge, tier-2 sides): **PASS (minor note)**
- The boundary follows the gold hem curve across the centre and both scallops. There is no 597 straight line, and the strap crossing is interpolated cleanly (hemL/hemC/hemR.png).
- The tier-2 tops at the sides are now cyan (cyan starts at row 560; per-column cap max at the sides is 560–590).
- Note: the per-column "lowest gold" method leaves vertical step cuts through the tier-1 curl lining at x≈383–401 (band comp 131 px, 560–585), x≈452–456, x≈745 and x≈797–807 (74 px, 570–589). The moved piece will have short vertical edges at the curl ends. Fix this during redraw or trace the curls.

## C5 (cuffs, frills, hands): **FAIL (major)**
- **The inner side is still a straight polygon edge,** not the alpha shape (cuffLz.png, cuffRz.png, cuffL.png, cuffR.png):
  - Left: (386,704)→(322,856).
  - Right: (824,~720)→(878,856).
- This edge cuts diagonally through the cuff band. The inner ≈30–40% of each cuff, with its gold piping and part of the frill, is cyan (redraw), not white:
  - Left: ≈x 360–388 at 715–790.
  - Right: ≈x 808–840 at 715–790.
- Below 790, the inner frill/hand sliver on the right (≈838–852 × 790–802) is unlabelled. It would stay in place while the rest of the hand moves.
- On the left, the white layer's top-right corner (≈368–388 × 703–722) takes in dark sleeve fabric above the cuff opening.
- The cuff top band (700–728) is included on the outer side only.
- Consequence: moving the white region 11 px inward would overlap the cut-off cuff remnant left in cyan, which would double the piping and frill. The y790 exception numbers in JSON and spec (753 / 2,659 px) and the orange derived area are computed from this wrong mask, so they are not valid.
- The JSON note "robe excluded by polygons traced along the robe edge" does not match the pixels: the polygon edge is not the robe edge.

## C8 (slit protect): **FAIL (moderate)**
- Good: for most rows the blue follows the inner edges of the two gold trims, and the large left robe embroidery motif is cyan, not protected (slit.png, slitBL.png).
- Straight clips remain:
  - Rows ≈755–790 left edge: x = 553, 548, 545, 542 at y 760/770/780/790. This is exactly the PS polygon line (594,628)→(542,790), and exposed skirt between the trim and that line is cyan (slitBL.png).
  - The top is a horizontal cut at y=648, so the opening under the buckle at 640–648 is cyan.
- Robe trim inside the protect layer:
  - An 81 px blue sliver at 576–590 × 648–686 is the purple stripe inside the left trim.
  - ≈244 px of the right robe trim's embroidery stripe at 612–635 × 650–700 is blue (slitBR.png).

## Bag: **FAIL (minor)**
- The bag is fully covered.
- Leaks onto the robe:
  - ≈785 green px at 640–668 × 715–790 are mostly the right robe trim's embroidery stripe beside the bag (bag.png, slitBR.png).
  - A 43 px green comp at 763–783 × 679–696 lies on the lower edge of the tier-2 gold band (bagtop.png).
- The R2 leak at 735–762 × 668–700 was removed by an axis-aligned rectangle. That leaves a straight vertical cut at x=735 and a horizontal cut at y=700, which clip the handle's outer edge into cyan (bagtop.png).
- Below 790, ≈768 px of skirt hem stripes are green. This is harmless because they are protected anyway, but the labelling is wrong.

## Derived revealed areas: **PARTIAL**
Totals: red 20,840 (rows 401–598), blue 10,855, green 1,490, orange 2,659 (derived_ov.png).
- Plausible: the red vacated band, including the strap-hole shadow along the strap, and the green capelet under the ribbon.
- Blue under the brim includes brim edges and the crystal over transparent background. 5,918 of 10,855 px are in the hair x-range. The background part should become alpha 0, not be repainted, and the file does not separate these cases.
- Orange (cuff uncovered) is invalid until C5 is fixed.

## SPEC R3
- Resolved:
  - y790 rule replaced by a cuff/hand-only exception with counts (§2.8).
  - y455/456 replaced by a traced boundary with hair over capelet (§2.9).
  - Director decisions recorded: limited moves with redraw of revealed areas and no warp or anisotropic scaling (§4.1); bob width redesign (§1); arm fine-tune with an obligation to record the amount (§1, JSON rules).
- Remaining defects:
  1. §3 table, said to be the overlap order from the top (黄, マゼンタ, 茶, **オレンジ**, 白, 緑, 青, 水色), contradicts layers.json and the generator (hat > hair > strap > cuff > bag > slit > **capelet** > band).
  2. §2.4 and §3 still say cyan covers rows 549–789. The actual cyan is 560–789, and the vacated area is a separate traced derived area (rows 401–598), not a 549–597 band. This is the R2 item 6 mismatch, still open.
  3. §3 states that the cuffs, slit and capelet top/bottom were rebuilt along real contours rather than straight lines or rectangles, and the cuff entry claims robe pixels are excluded. Both claims are false for the cuff inner edges and the slit bottom-left and top.
  4. The §2.8 exception counts (753 / 2,659) derive from the faulty cuff mask.

## Verdicts
- C3: FAIL (minor)
- C4: PASS (minor note)
- C5: FAIL (major)
- C8: FAIL
- Unassigned = 0: PASS
- Strap: PASS
- Bag: FAIL (minor)
- Derived: PARTIAL
- **MASKS (R3): FAIL**
- **SPEC (R3): FAIL** (the decisions are recorded and both conflicts are resolved in principle, but the text is inconsistent with the pixels and JSON)

## Required corrections
1. **C5:** Rebuild cuff_hand_move from the silhouette, for example by flood-filling from cuff/frill/hand seeds bounded by the dark outline and the robe's diagonal edge line, with no straight polygon clip. Include the full cuff width with all piping, the full frill, the full hand including below 790, and the 700–728 top band. Exclude the sleeve fabric above the cuff. Then recompute the y790 exception counts and the orange derived area.
2. **C8:** Replace the PS polygon clip at rows ≈755–790 and the y=648 top cut with the trim-bounded fill down to 790 and up to the real apex under the buckle. Remove the trim stripes from blue: 576–590 × 648–686, and 612–635 × 650–700.
3. **C3:** Trace the strand tips so that the wisps at 458–501 and 665–707 (y 421–435) go to hair. Move the 106 px capelet highlight at 715–727 × 482–501 from hat to capelet. Remove the ≈40 px of orange specks along the ribbon edge.
4. **Bag:** Remove the robe trim pixels at 640–668 × 715–790 and 763–783 × 679–696. Replace the 735/700 rectangle cut with the handle contour.
5. **Derived:** Split the brim-revealed area into "repaint hair" and "becomes alpha 0".
6. *(Recommended)* Trace the tier-1 curl linings instead of using vertical step cuts.
7. **Spec:**
   - Fix the §3 order table to match the JSON.
   - Update §2.4/§3 cyan rows to 560–789 and reference the derived vacated area.
   - Correct the §3 contour claims.
   - Update the §2.8 counts after item 1.
8. Re-run independent mask/spec QA.

Evidence: emb_top, tips1, tips2, wispL, capL_top, capR_top, ribcap, hemL, hemC, hemR, cuffL, cuffR, cuffLz, cuffRz, slit, slitTop, slitBL, slitBR, bag, bagtop, derived_ov (.png); scripts an.py, comps.py, crop.py.
