# MORWEN FIX-03 Step 1: independent visual QA (base body, FIX-02 masks, REBUILD_SPEC_FIX03)

Reviewer: independent Claude subagent. I did not produce the material under review. No repository files were changed. All evidence is in `/tmp/indep_fix03/`.
Method: I opened the source PNGs at native resolution with 10/25 px grids and the spec markers drawn on top (`mk.py`), read joint centres by eye, took alpha-silhouette row scans for boots and soles, and analysed the mask with connected components, hole filling and unassigned-pixel counts (`ov.py`, `an.py`, `an2.py`). Coordinates use the 1200x1600 canvas (y down).

---

## 1. Gate 1: base body landmarks

### 1a. Front (master)
| Joint | Spec | My reading | Verdict | Crop |
|---|---|---|---|---|
| eye 255 / chin 322 | (600,255)/(600,322) | same | PASS | up_front.png |
| crown 180 (under hat) | 180, low | 180–188. The anime rule "eyes slightly below mid-head" gives 181–188 | PASS (low confidence is correct) | up_front.png |
| neck base | 395 | 390–395 | PASS | up_front.png |
| shoulders | (480,420)/(720,420) | The marker sits about 10–15 px inside the capelet's top-outer contour. The capelet surface over the shoulder is at y≈405. The joint centre is about 20–25 px below the acromion surface, so I read (≈487,430)/(≈713,430). Confidence medium-low | UNSURE. Correction ≈ +10 y, +7 x (at the threshold) | shoulder_front_back_zoom.png |
| elbows | (410,605)/(790,605) | Hidden under capelet tier 2. The sleeve emerges at x≈395–440 around y 690. I read about (415±10, 605–625). The marker is plausible, but confidence should be **low**, not medium | PASS (lower the confidence) | front_armR_zoom.png |
| wrists | (398,795)/(802,795) | (≈403,797) | PASS | front_armR_zoom.png |
| waist | 655 | belt/vest hem 640–665 | PASS | up_front.png |
| hips | (552/648,770), low | Hidden. Thigh centres at y 900 are about 100 px apart and knees are 87 apart, so the hip joints extrapolate to about 105–115 apart. Hip row is plausible between 770 and 800 (wrist level 795) | PASS with note: hip width is better at ≈110 (±7 per side) | low_front.png |
| knees | (555/642,1100) | 1100±15. The calf peak is about 1180–1200 | PASS | legs_4dir.png |
| ankles | (560/640,1470) | Boot-shaft centres at y 1300 are 564/630. The ankle x values were taken from the toe-flared soles. Better: (≈564,1468)/(≈632,1468) | PASS (<10 px) | legs_4dir.png |
| contacts | 560/640 @1540 | soles at y 1538: 534–587 / 614–667 | PASS | alpha scan |

Proportions: head height = chin 322 − crown ≈180 = **≈142 px**. Stature from crown to sole = 1360 px, about **9.6 heads** including a boot heel of about 50 px (about 9.2 heads without it). That is a stylised fashion proportion, but it is the approved front art, so I accept it as the turnaround target. The field-sprite 2.8–3.0 head rule is a separate later stage.
The thigh:shank ratio of 330:370 (0.89) is within stylisation. Real joint-to-joint lengths are close to 1:1, so this does not block.
Arm: upper arm 198 and forearm 190 (ratio 1.04). Anatomy would put the forearm shorter (about 1.25:1). The front elbow is hidden, so this can't be confirmed. Treat the 198:190 split as a low-confidence reading, not a design constant.

### 1b. Back (fix01)
| Joint | Spec | My reading | Verdict |
|---|---|---|---|
| crown | 200, low | Plausible (about 15–20 px below front, consistent with the hat offset) | PASS (low) |
| neck base | (600,445), low | **This is the capelet collar / hair-end contour, not the neck.** Anatomically the neck base should be front 395 + head offset ≈15, giving **≈(600,410±15)**. So the reported +50 "neck" delta is a garment delta. The anatomical delta is about +15 | **FAIL: correct to ≈410** (up_back.png, m_hair_ribbon.png) |
| shoulders | (470/730,470) | The marker is about 15–20 px under the capelet contour (contour ≈450), the same convention as the front. With a consistent joint rule: about (478,475)/(722,475). The front→back delta of ≈+45–50 is real | PASS (delta confirmed) | shoulder_front_back_zoom.png |
| elbows | (400/800,640), low | Plausible | PASS (low) | back_armL_zoom.png, m_left.png |
| wrists | (345/855,795) | (≈350,800) | PASS |
| hips | copied from front | Hidden. No independent evidence | UNSURE (low; state that it was copied) |
| knees 1100 / ankles 1470 / contacts 571,628 | — | Boot shafts at y 1300: 565/634, matching front 564/630 within 4 px. Contacts are the narrower rear heel blocks | PASS |

### 1c. Right side (fix01): several high-confidence readings are wrong
| Joint | Spec | My reading | Error |
|---|---|---|---|
| eye/chin | (655,250)/(650,320) | same | PASS |
| neck base | (615,395) | (≈605,390) | PASS |
| shoulder_near | (610,440) | The capelet surface over the shoulder is y≈395–400, so the joint is **≈(600,425–432)** | ≈−10 y (UNSURE) |
| elbow_near | (625,620) | Sleeve axis at x≈593 between y 715 and the cuff, so **≈(595,615)** | **−30 x** |
| **wrist_near** | **(680,795), "high"** | The marker sits on the **belt chain**. The real wrist / cuff end is at **(≈600,798)** | **−80 x: FAIL** (right_arm_zoom.png) |
| hip_near | (615,770) | Plausible | low |
| **knee_near** | (630,1095) | The marker is on the **shin (front) contour**. The leg spans about 548–640 at y 1100, so the joint centre is **≈(593,1100)** | **−37 x** (side_legs.png) |
| **ankle_near** | (600,1470) | The boot shaft at y 1400 is 532–615 and the heel block is 517–569, so **≈(573,1465)** | **−27 x** |
| contacts | heel 543 / forefoot 625 | heel 521–559, forefoot ball ≈630–637 | PASS |

### 1d. Left side (fix01)
| Joint | Spec | My reading | Error |
|---|---|---|---|
| eye/chin | (545,262)/(550,330) | The x of the eye marker is on the glasses rim. The pupil is at x≈580. Rows are OK. This whole view is drawn **about 8 px lower** than the front (chin 330 vs 322) | x: note |
| shoulder_near | (600,450) | Capelet surface ≈395–400, so the joint is **≈(612,433–440)** | ≈−12 y (UNSURE) |
| elbow_near | (590,625) | Cuff/sleeve axis at x≈612, so **≈(615,625)** | **+25 x** |
| wrist_near | (600,800) | The frill ends at about 825, so the wrist is **≈(605,820)** | **+20 y** (left_arm_zoom.png) |
| **knee_near** | (580,1095) | On the shin contour. The leg spans about 566–655, so **≈(610,1100)** | **+30 x** |
| **ankle_near** | (600,1470) | Shaft 592–674, heel 641–682, so **≈(630,1465)** | **+30 x** |
| contacts | forefoot 558 / heel 664 | 536–591 / 651–667 | PASS |

Check on my corrections: with them, the right and left views become mirror-consistent. Knee: right −7, left −10 relative to the ankle-to-forefoot direction. Ankle: 27–28 px behind the sole midpoint in both. The spec values are not mirror-consistent (knee +30 forward in the right view, +20 in the left).

### 1e. Answers to the specific questions
- **Legs consistent within ~5 px?** Rows (y) for knee, ankle and sole: yes, within about 5 px. Front/back ankle x: within about 4–8 px, using boot-shaft centres. **Side-view x positions: no.** Knees and ankles were placed on the shin contour, 25–37 px off the joint centre. The finding "legs agree across all four views within ~5 px" is only true for rows.
- **Side shoulder 440–450 vs front 420:** the main cause is **a reading error, not perspective and not anatomy.** The capelet surface over the shoulder is at y≈395–405 in the front, right and left views, so the drawn shoulders agree within about 10 px. The front joint was read about 10 px too high (near the surface). The side joints were read about 10 px too deep. The left view adds a real offset of about 8 px (the whole head is lower). This is an orthographic turnaround, so there is no perspective component. **Unified target: shoulder joint row ≈430±8, shoulder surface / capelet top ≈384–405.**
- **Back shoulder 470:** the +45–50 drop of the back capelet/shoulder relative to the front is confirmed. If the target row stays at 420 while the back is read with a 20 px-deep convention, the rebuilt capelet will ride about 10–20 px too high. Define one convention (joint = surface + 20–25 px).
- **Hidden hips:** they cannot be verified. Keep them low confidence, record the hip spacing as ≈110, and state that the back and side values were copied or derived.
- **Crown under hat:** 180–188 is plausible. Record it as a range.
- **Head width (missing from the spec):** the back bob at its widest is ≈450–730 (≈280 px). The front hair at the same level is ≈477–720 (≈243 px), so the back is about 15% wider (hairwidth_strips.png, head_front_back.png). Add skull width / hair-mass width to the base body record and decide whether the back bob volume should be narrowed during the hair redraw. (UNSURE: the ribbon occludes the right edge.)
- **Internal consistency of the target (important):** the rebuild spec puts back shoulders at (475,420)/(725,420), keeps wrists at (345,795)/(855,795), and keeps the front arm length 198+190=388. The straight-line shoulder→wrist distance is **397 px, which is more than 388**, so the arm cannot reach without being stretched about 2.5%. With the corrected joint row of about 430, the distance is about 389 px: geometrically possible, but the arm is **fully locked straight**, with no elbow bend. That contradicts "natural" arms and the slight bend in the front view. One of these has to change: (a) bring the back wrists about 10–15 px inward or up, (b) accept a straight arm explicitly, or (c) re-measure front arm length (the front elbow is hidden).

### Gate 1 verdict: PASS_WITH_CORRECTIONS
The base body **cannot be frozen as delivered.** The front-derived target rows are broadly plausible. However, one "high" landmark is 80 px off, the side knee and ankle x are systematically off, the back neck base is a garment reading, and the target arm geometry is infeasible as specified. After the corrections in §5 (items 1–6) and a re-check, it can go to the director as a freeze candidate.

---

## 2. Can the base body be frozen as a candidate?
**Not yet.** Required first: corrections 1–6 in §5. The overlay and cross-view diagram should then be regenerated and re-checked.

---

## 3. FIX-02 revised masks (`fix02/EDIT_MASK_back_upper_body.png`): revalidation
Pixel totals match the FIX-02 spec: magenta 21,274; orange 43,968; cyan 76,298; yellow 11,799; green 24,284; brown 10,564.

| Layer | Claim | Result | Evidence |
|---|---|---|---|
| Magenta hair 360–450, filled | Filled without highlight holes | **Mostly.** 1 component, 9 tiny unassigned holes (15 px, max 6 px). **Gap:** hair strands at x≈700–720, rows 360–405, between the magenta edge (x=700) and the ribbon are unassigned (≈690 px opaque in x 700–720). The 360 px top cut also leaves the hair just under the brim unassigned. After the hat moves up 14–20 px, those rows (≈345–360) need hair, and no layer covers them | unassigned_hair.png, m_hair_ribbon.png |
| Orange capelet tier 1 + emblem + shoulders, move-only | Rigid move up about 48 px | **FAIL.** The orange layer has **219 holes (2,293 px)**. **All of them are assigned to brown.** The emblem laurel outlines, book shading and the dark parts of the tier-1 gold trim are labelled "strap". Moving orange alone would leave pieces of the emblem and trim behind, and re-routing brown would repaint them. At the sides (x≈385–450, rows ≈560–597), orange also contains the **top of capelet tier 2 / sleeve**, and there is a hard horizontal cut at 597/598, so tier 2 is split between the move and redraw layers. The ≈48-row band that the move vacates (old rows ≈550–597) is **not assigned to any redraw layer** | brown_stray.png, m_orange.png, m_strap.png |
| Yellow ribbon protect | No ribbon in orange | **PASS for that claim.** Only anti-aliased fringe remains (16 ribbon-coloured px in orange at x≥680). It is not a hat layer: the hat body, flower and green leaves are not in any layer | ribbon_vs_orange.png |
| Green bag protect | Bag fully green | Bag fully covered: **PASS.** **Leaks:** green also takes capelet tier-2 hem and robe above the bag handle (≈725–810, 652–700), which must move or be redrawn. It also takes skirt hem trim below the bag (≈637–690, 812–850) and a robe fold left of the bag (≈637–665, 705–750). The strap's lower end and its bag hardware are green, which is acceptable | m_bag.png |
| Brown strap re-route | Strap only | **FAIL.** **257 components.** The main component includes the strap plus a large blob of tier-1 gold trim where the strap crosses it (≈495–615, 545–590) and robe/slit fold pixels (≈580–640, 600–700). There are 2,567 stray px: 2,236 in emblem/trim inside orange and 331 in robe embroidery inside cyan (≈470–495, 665–700). The strap above row 448 (to the shoulder) sits in magenta | brown_stray.png, m_strap.png, m_left.png |
| Cyan tier 2 + arms + robe band 598–789 | Redraw | Covers tier 2, sleeves and the robe band. **However:** (1) **cuffs, frills and buttons (≈700–790) are inside the redraw zone**, but the spec says cuffs are preserved, so they need a protect layer; (2) the **central rear slit above row 790** is inside the redraw band, but the director says protect the slit; (3) the hard bottom cut at 789 sits against the protected heel-level robe tails, and no seam or feather rule is given; (4) it contains a 246 px hole that is brown (robe embroidery mislabelled) | m_left.png, m_strap.png, mask_outline_full.png |

**Fit with REBUILD_SPEC_FIX03 (hat now moves 14–20 px):** the mask set does not support it. There is no hat/flower/leaf/laurel move layer, and no "upper hair under the brim" layer. The yellow ribbon moves with the hat by about 15 px while orange moves by about 48 px, so the capelet region under the ribbon (never drawn, occluded) must be painted, and no layer marks it. The layer order (hat move → hair redraw → capelet move → tier-2/arms redraw → strap) is not defined.

### MASKS: FAIL

---

## 4. REBUILD_SPEC_FIX03.md vs the director decisions
| Item | Status |
|---|---|
| Robe edges overlap sleeves naturally; no invented hidden slits (§2.5) | Present: OK |
| Hat/stature aligned to front, hat not distorted (§2.1) | Present: OK. But no mask layer exists for the hat, and nothing covers the hair revealed under the brim (see §3) |
| FIX-01 boots as approved baseline (§2.7) | Present. Missing: "subject to final visual regression" |
| Insignia (§2.3), bag and strap buckle (§2.6), green leaves and gold laurel (§2.1), rear garter ornaments, slit, robe tails (§2.7) | Present. **But the slit is protected only "below row 790", while the slit extends above 790 into the cyan redraw band**: contradiction |
| **Plain-base skirt with the check detail on character-right only** | **Missing.** §2.7 says only "スカート" |
| Dramatic side robe tails at heel level | Only "ローブの裾". Needs an explicit statement that the length and flare at heel level must not change, and a seam rule at row 790 |
| Shoulder joints (475,420)/(725,420) | **Wrong.** They use the front surface-level reading (≈420) instead of the joint (≈430). They don't match the stated 240 px target spacing (they give 250). Combined with fixed wrists and the 198:190 ratio, **the arm cannot reach** (397 > 388 px). Replace with values from the corrected, locked base body |
| Neck/nape | Hair redraw mentions the nape, but there is no neck-base target. Use ≈395 (front) after the head move. The current back 445 is a collar contour |
| Decision 1 "no simple translation" | Orange (capelet) and hat are "move-only" translations. Get explicit director acknowledgement that a layer translation positioned from the locked base body is allowed, as opposed to whole-upper-body translation |
| Cuffs and hands preserved, no robe/sleeve intersection (execution packet) | Only "consistent with front". No protect layer for cuffs, hands or frills |
| Capelet painted under the ribbon after the differential move; vacated band after orange moves; hair under the raised brim | **Missing** |
| Back skin colour match (nape and hands), alpha=0 outside subject, deliverables (PROCESSING_FIX03.json, MANIFEST SHA-256, 4-view comparison, base-body overlay of the candidate) | **Missing** from this spec. They are in the execution packet but should be referenced |
| Back hair volume/width vs front (≈15% wider) | Not addressed |
| Spec §3 refers to `QA_REPORT_FIX03.md` | The file does not exist yet. The mask revalidation is still owed, and this report gives FAIL |

### SPEC: FAIL
The spec is not sufficient as written: it has a geometric infeasibility, a contradiction on the slit, missing skirt-check and cuff protection, and missing instructions for the hat layer and revealed areas.

---

## 5. Ranked required corrections
1. **Fix the right-view wrist_near:** (680,795) → **(≈600,798)**. It is on the belt chain, and it is marked "high". Recompute the right limb lengths.
2. **Fix the side knee and ankle x to joint centres, not shin contours:** right knee (≈593,1100), ankle (≈573,1465); left knee (≈610,1100), ankle (≈630,1465). Side elbows: right (≈595,615), left (≈615,625). Left wrist (≈605,820), and record the left view's +8 px whole-figure offset.
3. **Define one shoulder-joint convention (joint ≈20–25 px under the acromion/capelet surface)** and restate the target shoulder joint row as **≈430±8** (front ≈(487,430)/(713,430)). Explain that the side offset is a reading error plus ≈8 px left-view drawing offset, not perspective. Keep the capelet top target at 384.
4. **Back neck_base 445 → ≈410 (anatomical).** Label 445 as the collar/hair contour. The garment delta is +50; the anatomical delta is about +15.
5. **Resolve the arm geometry:** with fixed wrists (345/855,795) and front arm length 388, a 420 shoulder is infeasible and 430 forces a locked-straight arm. Decide between moving the wrists in or up about 10–15 px, explicitly accepting a straight arm, or re-measuring the front elbow (lower its confidence to "low").
6. Add hip spacing ≈110 (low), the crown range 180–188, head and hair widths (front ≈243, back ≈280 → decision needed), and mark the back and side hips as copied/derived.
7. **Rebuild the masks:** remove all brown pixels from emblem, trim and robe (strap = one clean component). Fill the orange holes with orange. Take the green leaks out of capelet tier 2 and the skirt trim. Extend magenta to x≈720 and up to the brim.
8. **Add the missing layers:** hat + flower + leaves + laurel + ribbon move layer; upper hair under the brim; "vacated after orange move" redraw zone; capelet under the ribbon; cuff/frill/hand protect; slit protect above 790; a feather or seam rule at the 597/598 and 789/790 cuts. Define the layer order.
9. **Spec text:** add the character-right-only skirt check; protect the whole slit (including above 790) and the heel-level side robe tails explicitly; add the FIX-01 boot regression condition, skin colour match, alpha=0 and the deliverables list. Get the director to acknowledge the layer translations under decision 1.
10. Regenerate BASE_BODY_OVERLAY_4DIR / CROSS_VIEW after the corrections. Then run independent QA again before asking the director to freeze.

Evidence files (`/tmp/indep_fix03/`): up_{front,right,back,left}.png, low_{...}.png, legs_4dir.png, side_legs.png, right_arm_zoom.png, left_arm_zoom.png, front_armR_zoom.png, back_armL_zoom.png, shoulder_front_back_zoom.png, head_front_back.png, hairwidth_strips.png, mask_outline_full.png, m_hair_ribbon.png, m_orange.png, m_strap.png, m_left.png, m_bag.png, brown_stray.png, unassigned_hair.png, ribbon_vs_orange.png; scripts mk.py, ov.py, an.py, an2.py.

**GATE1 BASE BODY: PASS_WITH_CORRECTIONS** (not freezable until corrections 1–6 are applied and re-checked)
**MASKS: FAIL**
**SPEC: FAIL**
