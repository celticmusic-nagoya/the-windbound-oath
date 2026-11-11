# Morwen real-canon-final-04 — independent QA of FIX-01 / FIX-02 (independent reviewer)

Scope: front `aligned/morwen_front_aligned.png` (master) vs `fix01/morwen_{right,back,left}_fix01.png`; FIX-02 material (no PNG candidate). Repository files were not modified. All crops are in `/tmp/indep_fix02/`. Rows were read on 1:1 canvas coordinates (1200x1600, anchor 600,1540), using 2–3.4x zoom with 10 px ticks. Visual readings are ±3 px unless noted.

## 1. Upper-body landmarks, front vs back fix01 — FAIL (confirmed: back upper body is ~48–57 px low)

| Landmark | Front | Back fix01 | Back − front | Author's figures (F/B/Δ) |
|---|---|---|---|---|
| Hat crown top (tip excluded; alpha top matches) | 34 | 48 | **+14** | 35/45/+10 |
| Hat brim lowest point | ~345 | ~365 | **+20** | 325/345/+20 |
| Hair tip lowest point | ~367 (side locks) | **~424** | **+57** | 370/445/+75 |
| Neck/shoulder line (capelet top at shoulders) | ~384 | ~432 (collar ~420) | **+48** | 385/440/+55 |
| Capelet layer-1 bottom (lowest, near centre) | ~537 | ~591 | **+54** | 545/598/+53 |
| Chest/waist | vest bottom ~650–665 | hidden under capelet/robe | n/a | same |
| Cuff bottom (frill) | ~792 | ~788 | **−4** | 775/775/0 |
| Skirt hem (pleat tips) | ~866 | ~861 | −5 | 868/862/−6 |
| Sock top | ~903 | ~907 | +4 | 905/908/+3 |
| Boot top (fix01) | 1270 | ~1271 | +1 | 1270/1270/0 |
| Sole | 1540 | 1540 | 0 | same |

- What moves: hat +14/+20 (a little), hair/neck/shoulders/capelet +48 to +57 (a lot). What does not: cuffs, skirt hem, sock top, boots, sole (all within ±5).
- Effect: from the back, the shoulder-to-cuff length is ~356 px against ~407 px in the front (**−51 px, −12.5 %**). Brim to hair tip is ~58 px against ~22 px, so the back hair is ~35–40 px longer relative to the hat. Crown to shoulder is ~384 px against ~351 px.
- Correction to the author's JSON: the back hair tip is at about **424, not 445**. The lowest hair pixels sit just over the collar (crop `back_hairtip.png`). The author's +75 overstates hair shortening by ~20 px; about +57 is right. The shoulder figure is +48 rather than +55. The other figures agree within ~5 px.
- Crops: `fb_hat.png`, `fb_crown.png`, `fb_brim.png`, `fb_neck.png`, `fb_shoulder.png`, `front_shoulder.png`, `back_hairtip.png`, `fb_cape1.png`, `fb_cuffL.png`, `fb_cuffR.png`, `fb_cuff_skirt.png`, `fb_hem.png`, `upper4.png`, `full4.png`.

## 2. Local non-generative fix feasibility — BLOCKED (author's BLOCKED is justified; the mask/spec is correct in intent but not sufficient)

Pure move/stretch cannot give a seamless result:
1. **Hair**: to lift the capelet ~48 px, the hair has to end at ~375–385 (≈40–50 px shorter). Compressing the 365–424 band by about 3x would squash the strands. A "cut the middle and shift the tips up" splice is in principle possible for vertical strands. However, the bob's rounded side contour and the nape/collar under it would still need repainting.
2. **Hat ribbon conflict (not addressed in spec)**: the hat's long purple ribbon tails hang over the right shoulder and capelet, rows ~280–520 at x ~700–830. About **1,900 ribbon-coloured px lie inside the orange (move-up) mask**. Moving orange would tear the ribbon away from the hat. Keeping the ribbon in place leaves capelet pixels behind it that do not exist. The spec says the ribbon is outside the mask, which is wrong (`mask_outline_back.png`).
3. **Bag conflict**: the cyan band (rows 600–774) contains the bag top, flap and buckle (bag ≈ 690–890) and the strap buckle. The spec says to redraw cyan but also says to protect the bag. These contradict each other. The bag must be translated as a protected layer, and the strap re-routed: a diagonal strap that crosses a stretch boundary gets a slope kink.
4. **Arms/robe band**: lengthening ~48 px over the visible upper sleeve and robe (≈650–705 above the cuff band) is about +30 % or more if stretched. That deforms the cuff gold bands, the thorn embroidery and capelet layer 2, which sits inside cyan, and the spec gives no instruction for it. This needs redrawing, not stretching.
5. **Hat residual**: the spec leaves the hat +14 (crown) / +20 (brim) low. If the director requires the back upper body to match the front exactly, the hat also needs ~14 px lift with the hair under it. The spec does not decide this.
6. Mask quality: magenta is a per-pixel hair mask with many holes (glossy highlights excluded, see `mask_outline_back.png`), and its x extent is 448–700 (spec says 400–700). Painting only the magenta pixels would leave orphan highlight fragments, so it should be a filled region. Hair-shortening targets should be re-based on 424, not 445. The shoulder lift should be about 48 px rather than 55.

Verdict: redrawing is required (shorter back hair with new nape/collar, longer upper arms and sleeves, capelet top behind the ribbon). Local moves alone are not enough. BLOCKED is the correct status. The spec should be revised for items 2–6 before it is handed to an artist or an inpaint step.

## 3. Arms vs robe layering, 4 views — front/right/left PASS; back UNSURE (design decision needed)

- Front: hands come out of the frilled cuffs naturally. The arms hang in front of the open cloak's inner side, with the robe flaring ~60 px outside the arms (silhouette at row 750: 327–864). PASS.
- Right/left fix01: the sleeve emerges from under the capelet and the arm hangs in front of the robe, which falls behind the body. Hands are natural. PASS (`side_arms.png`).
- Back fix01: hands and cuffs are natural. However, the sleeves (rows ~650–790) are drawn **on top of** the robe's outer surface at its silhouette edge, and below the hand the robe flare passes behind the hand (`back_armL.png`, `fb_arms.png`). The front and sides read as a sleeveless cloak hanging behind the arms. A cloak like that, seen from the back, would cover the arms wherever they overlap. The only single-garment explanation for all 4 views is an outer robe with **side arm slits hidden under capelet layer 2** (~650), so the arms pass outside the robe below the capelet. That structure is not drawn or documented anywhere. This is not a failure for arm spread. It is an occlusion-order question for the director: accept "arm slits under capelet" as canon, or repaint the back so the robe hem edge covers the sleeve's inner edge.
- Anatomy: back shoulder-to-wrist is 12.5 % short versus the front (see §1). This is a real anatomy mismatch, caused by the low shoulders.

## 4. FIX-01 boots regression — PASS

- Boot top: front 1270, right ~1270, back ~1271, left ~1271.
- Upper strap: front ~1308–1342, right ~1305–1333, back ~1304–1336, left ~1305–1333. Consistent within ~5 px (`boots4.png`).
- Sock enters the boot cleanly in all views.
- Pixel diff, pre-fix aligned vs fix01, rows ≥ 1440:
  - Right: 0 px changed.
  - Back: 109 px changed, max Δ 5 (dark-gold colour class).
  - Left: 96 px changed, max Δ 8.
  - Alpha changed in rows ≥ 1440: 0 in all three.
  - Heel and sole geometry are unchanged.
- Geometry edits are confined to the boot boxes. Outside them only colour-class changes occur: back max Δ 8, left max Δ 21 from the skin/gold fine-tune, with no alpha change.
- At 3x (`boots_back_prepost.png`, `boots_left_prepost.png`, `boots_right_prepost.png`): no seams, no doubled outlines and no smearing. One minor note: the left boot's lace X pitch is ~20 % taller in the stretched zone than below 1440. It is hard to see at game scale.

## 5. Colour and alpha — PASS_WITH_NOTES

Median Lab values by class:

| View | Purple L/C | Gold L/C | Skin L/b | Leather L/C |
|---|---|---|---|---|
| Front | 23.8 / 33.3 | 80.1 / 38.3 | 88.6 / 8.3 | 32.2 / 21.5 |
| Right | 21.7 / 31.4 | 80.6 / 35.6 | 87.0 / 9.5 | 31.9 / 21.3 |
| Back | 25.5 / 34.9 | 81.7 / 35.9 | 84.1 / 5.7 | 33.5 / 23.2 |
| Left | 23.7 / 30.7 | 81.5 / 36.7 | 87.5 / 7.0 | 31.4 / 21.4 |

- All classes are within ΔE ≈ 2–4, except **back skin**, which is ΔE ≈ 5 darker and cooler than the front. FIX-01 did not touch back skin (identical to pre-fix). This is a minor note.
- Alpha:
  - Background is fully alpha 0.
  - α=0 px with non-zero RGB: back 2, left 1. Harmless.
  - No light halos: the semi-transparent edge pixels are darker than the solid edge (mean L 62–78), with 13 light semi-alpha px on left.
  - Faint α>0 pixels more than 4 px from solid: back 0, right 98, left 137 (front has 86 for comparison). These are wispy hair-strand tips at rows 339–395 that are part of the artwork, plus one α=60 px at left (796,1483). There is no haze.

## OVERALL (4-direction unification): **BLOCKED**

FIX-01 boots pass. The back upper-body height requirement, the director's top-priority item, is not met: shoulders/capelet are +48 to +54 px low, hair is +57 px low, and the arms are 12.5 % short. No FIX-02 candidate exists, and the fix needs redrawing beyond non-generative local editing.

Ranked remaining issues:
1. Back shoulders/capelet ~48–54 px low and back arms 12.5 % short versus the front. Needs a redraw of hair tips/nape, a capelet lift, and longer upper sleeves (§1, §2).
2. FIX-02 spec errors that must be fixed before handing it off:
   - The hat ribbon is inside the orange move mask.
   - The bag is inside the cyan redraw band while also listed as protected.
   - Hair numbers are based on 445 instead of ~424.
   - The magenta mask has holes.
   - No rule for capelet layer 2 or the strap path.
3. Back sleeve/robe occlusion order is unexplained by the front/side garment structure. The director should decide between hidden side arm slits and a repaint (§3).
4. The back hat stays +14/+20 px low after the planned fix. The director should decide whether this is acceptable.
5. Back skin is ~ΔE 5 darker/cooler than the front (minor).
6. Left boot lace pitch is slightly elongated in the stretched zone (cosmetic).
