# MORWEN-ASSET-74D — official colours, short boots and knee socks (ART-74C 8-frame walk kept)

Status: **CANDIDATE**.
- Static QA: PASS.
- Third-party art QA: NOT_RUN.
- Android device QA: NOT_RUN.

Nothing here is registered in a manifest or used in production. 74A, 74B, 74C, the right walk 72, the official turnaround and `main` are unchanged.

## Contents
| Files | Content |
|---|---|
| `morwen_left_walk_8f_00..07_{96x128,48x64}.png` | **74D, first candidate.** 74C 8-frame walk with the fixes below |
| `morwen_left_walk_12f_00..11_*` | Same fixes on the same cycle (12-frame version of 74C) |
| `REFERENCE_left_side_74D_colour_right_coords.png`, `PART_MASKS_74D_right_coords.png` | Recoloured left-side reference and its part masks |
| `COMPARE_OFFICIAL_74C_74D.png` | 1. Official left vs 74C vs 74D |
| `ZOOM_HAT_HAIR_BOW_74C_74D.png` | 2. Hat / hair / bow, zoomed |
| `ZOOM_SKIRT_SOCK_BOOT_74C_74D.png` | 3. Skirt / knee socks / boots, zoomed, F00 and F02 |
| `NATIVE48_74C_vs_74D.png` | 4. 48×64 native and ×3, 8 frames, light / dark / moss backgrounds |
| `COMPARE_74C_vs_74D_8f.gif`, `morwen_left_walk_74D_{8f,12f}.gif` | 5. Walk GIFs |
| `PALETTE_OFFICIAL_74C_74D.png` | 6. Main palette: official vs 74C vs 74D, including sock / boot ramps and gold |
| `PALETTE_SPEC_MORWEN_74D.md/.json` | Common palette spec draft for all directions. Not applied to other directions yet |
| `qa_preview_74D.html` | Android / third-party QA page with a record form |

## FIX-01 Official colours (part by part, no global filter)
- The 74C reference was split into parts: hat, hair, collar bow, jacket/capelet, skirt, mantle and potions.
- Each part was mapped to the official left profile's OKLab statistics for that part:
  - lightness: quantile map;
  - chroma: official × 1.25, because sprite areas read duller than the painted sheet;
  - hue: official hue, keeping 35 % of the part's own variation.
- Gold uses one antique-gold ramp. Single-pixel gold specks inside cloth become cloth; trims and ornament lines stay.
- Skin, eyes, glasses, earring and white frills were not touched.

| Part (base cloth) | official L / C / h | 74C | 74D |
|---|---|---|---|
| Hat | .365 / .073 / 318 | .466 / .161 / 339 | .367 / .091 / 319 |
| Hair | .365 / .057 / 332 | .378 / .119 / 347 | .366 / .071 / 333 |
| Collar bow | .442 / .142 / 315 | .541 / .127 / 333 | .457 / .170 / 316 |
| Jacket | .379 / .070 / 317 | .317 / .108 / 340 | .379 / .088 / 319 |
| Skirt | .431 / .074 / 318 | .355 / .124 / 339 | .437 / .092 / 319 |
| Mantle | .370 / .104 / 314 | .511 / .177 / 343 | .380 / .130 / 317 |

Strong-magenta share of the sprite (C > .12, hue 330–10°): 25.0 % (74C) → 0.4 % (74D).

## FIX-02 Short boots
- The boot shaft now starts at 0.5 of knee→ankle, matching the official left profile. In 74C it started just above the knee.
- The cuff, lacing band, strap with buckle, heel and sole keep the 68 structure. Nothing new was added.
- At 96 px the boot occupies rows ≈102–124 and the sock rows ≈90–108.

## FIX-03 Knee socks
- The sock runs from the thigh welt (skin band and garter above it, unchanged) down into the boot cuff.
- Sock colour is lighter warm mauve (mid L .37, h 354); boot colour is darker purple-black leather (mid L .27, h 322). The difference is kept at 48 px (`NATIVE48_…`).
- The sock top is fixed on the thigh, so its height does not change during the walk.

## FIX-04 Motion protection
- 74C's gait, pelvis, arm and lag tables are reused unchanged, and the region masks are taken from the 74C reference, so layering is identical.
- Silhouette difference to 74C:
  - above the leg zone: **0 px** in every 8f and 12f frame;
  - inside it: at most 18 px (96 px), which is the sock and boot outline.
- The leg joints and ground contact are computed by the same code, so foot slide, ground rows (124 / 61), stride and cycle are the same as 74C.
- Loop seam (last→F00 change as a share of the mean frame change): 0.42 for 8f, 0.59 for 12f.
- 6f and the old 74A / 74B / 74C files are untouched.

## QA
| Gate | Result |
|---|---|
| Static QA (`QA_REPORT_74D.json`): format, alpha 0/255, transparent RGB 0, one component, ground rows, silhouette above the leg zone = 74C, colours closer to official for every part, magenta reduced, sock and boot present in every frame, loop seam | **PASS** |
| SHA-256 of all outputs | `SHA256SUMS_74D.txt` |
| SHA-256 of 74A / 74B / 74C / right 72 | Recorded and unchanged; this commit only adds `74D/` |
| Rebuild from the repository | Byte-identical |
| Third-party art QA (C-1..7, B-1..3, S-1..3, M-1..2, X-1 in `qa_preview_74D.html`) | **NOT_RUN** |
| Android device QA | **NOT_RUN** |

## Remaining / notes
- On dark backgrounds the deep purple hat and mantle edges are weaker than in 74C. Third-party QA should judge whether a lighter rim on the lit side is needed.
- The far leg and the 48 px boot keep the 68 detail level: lacing reads as a gold dot band.
- The common palette spec (`PALETTE_SPEC_MORWEN_74D.*`) is a draft. Right 72, back and front stay unchanged until approval.

## Regeneration (from this directory)
```
python3 build_morwen74d.py --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 --out <out>
python3 make_sheets74d.py --art . --c74 ../74C --ground <repo>/img/field/moss/art --official <official left PNG from main>
python3 make_qa_preview74d.py --art . --c74 ../74C --right72 ../../morwen-right-walk/72 --ground <repo>/img/field/moss/art --out qa_preview_74D.html
python3 qa_morwen74d.py --art . --c74 ../74C --b74 ../74B --a74 ../74A --right72 ../../morwen-right-walk/72 --official <official left PNG>
```
