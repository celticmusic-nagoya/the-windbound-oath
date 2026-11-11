# MORWEN-ASSET-74B — left walk ART-74B (art finishing of ART-74A)

Status: **CANDIDATE**. The technical self-QA passed. These checks have **not been run**: third-party art QA, the Android device check and approval of the master's far-side structure.
Not registered in the manifest, not used in production, and no files under `74A/`, the official right walk `72/` or `main` were changed.

## Changes (all made in the right-view reference; the 72 pipeline then animates and mirrors, so all 6 frames share one structure)
| FIX | Content |
|---|---|
| FIX-01 | Hat back where the flower and hair ribbons were removed. The single mixed fill used in 74A is replaced with a fill split into three zones: (1) BAND: the gold-patterned hat band is copied along its own direction (11,-7) and tapers to 5 px around the back; (2) CONE: the purple hat fabric is filled from fabric only, so no gold dots fall inside it; (3) BACK: the brim underside and back hair are filled from dark purple and hair only. Isolated pixels are then merged into their zone's majority colour. Only existing palette colours are used. Hat back: 293 px changed in the reference; near-black px in the hole area went from 24 to 13. |
| FIX-02 | Where the bag was removed: the pleat band (y78-83) is painted in full, which closes the 1 px transparent hole (left-view x52, y81). The mantle front edge (right-coords x41, y74-92) carries on with the existing gold mid tone (16 px). No bag, flower or ribbon was added, and existing gold was not removed. |
| FIX-03 | **Not changed, still UNVERIFIED**: the left shoulder decoration, the left earring, the left hand position and the far-side ribbon exposure (same as 74A). |
| FIX-04 | Rows ≥96 (legs, feet, stride) are identical to 74A and to the mirror of right 72. The ground row is 124 (96 px) and 61 (48 px) in every frame. Scale, palette and frame count match 72. Consecutive-frame change (F05→F00 included) is 74B `[4551,4042,1293,4534,4085,1422]` vs 74A `[4565,4049,1305,4548,4092,1434]` at 96 px, so the loop is unchanged. |

## QA (`QA_REPORT_74B.json`): technical_qa = PASS
- PNG RGBA, alpha only 0/255, transparent RGB = 0, one connected component, 96×128 / 48×64 × 6 frames.
- Pixels changed vs 74A, per frame: 96 px 315–325, 48 px 77–80. Changes outside the FIX zone (74A↔74B reference difference + 3 px motion reach): 0.
- Changes vs the DEV mirror outside the 74 edit zone: 0. Right-72 SHA values are recorded unchanged.
- Rebuilding from the repository (`--source ../74A/source_65B_F00`) gives byte-identical output.
- Art check: `COMPARE_ART-74A_vs_ART-74B.png` (96 ×2, 48 native/×3, F00 hat and waist at ×6) and `BACKGROUNDS_ART-74B.png` (light, dark and moss; 96 ×1/×3 and 48 ×1/×3). This check is self-QA only.

| F | 96×128 SHA-256 (first 12) | 48×64 |
|---|---|---|
| 00 | a148aa39bcc1 | a33e79da995a |
| 01 | 328100b0cff5 | 180c0842dde4 |
| 02 | 7625e234a808 | 1e4bd1d3e0eb |
| 03 | 3c40b7c2c9d0 | 7debbda0cd0b |
| 04 | 6db3480e82ac | 49f66cb5df9d |
| 05 | d208b35881a9 | a33fb5ec62c7 |

## Remaining
- Third-party art QA: NOT_RUN. Android device QA: NOT_RUN. Use `qa_preview_74B.html`, which compares 74A, 74B and right 72 and has a record form.
- FIX-03 items need confirmation from the master.
- At 48 px the hat back reads as the band wrapping round with a dark underside. Whether that reads well enough is for third-party QA to judge.

## Regeneration (run from this directory)
```
python3 build_morwen74b.py --source ../74A/source_65B_F00 --out <out>
python3 qa_morwen74b.py --art . --prev ../74A --dev <DEV ZIP dir> --right72 ../../morwen-right-walk/72 --repo <repo root>
python3 make_sheets74b.py --art . --prev ../74A --ground <repo>/img/field/moss/art
python3 make_qa_preview74b.py --art . --prev ../74A --right72 ../../morwen-right-walk/72 --ground <repo>/img/field/moss/art --out qa_preview_74B.html
```
