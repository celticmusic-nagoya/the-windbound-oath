# MORWEN-ASSET-74F — 12-frame elegant-walk refinement (candidates B and C)

Status: **CANDIDATE**.

| Gate | Result |
|---|---|
| Technical QA | PASS |
| Self art QA | Done (this file) |
| Third-party art QA | NOT_RUN |
| Android device QA | NOT_RUN |

- Recommended candidate: **74F-C**. Adoption is the director's decision.
- Base: ART-74E 12f (commit 1300991f). The reference image is the 74E reference unchanged: same colours, short boots, knee socks and rim, no added ornaments.
- 74A–74E, the right walk 72, the official turnaround and `main` are unchanged.

## Candidates (12 frames, 96×128 and 48×64, same 840 ms cycle and 41.6 px/cycle as 74E)
| | Content |
|---|---|
| A | **74E** (unchanged reference: `../74E/morwen_left_walk_12f_*`) |
| B `74FB` | Phase offsets only: pelvis, chest and head levels; pelvis fore-aft movement; capelet counter-motion |
| C `74FC` | B, plus the toe push held through F08, separate cloth phases per part, and the hand/cuff 0.5 frame behind the forearm |

Frame roles, levels and offsets are in `FRAME_DESIGN_TABLE_74F.png` and `build_meta_74f.json`; phase offsets per part are in `PHASE_REPORT_74F.md`.

### How the body levels are drawn
- One per-row offset map is applied to all upper layers, so the layers never separate:
  - head ≤ row 50;
  - neck ramp (rows 50–58);
  - chest;
  - waist ramp (rows 78–86);
  - pelvis and skirt.
- The legs use the same pelvis level for the hip joint.
- One row is stretched or dropped only inside the neck and waist bands, so no gaps appear.
- When the pelvis rises, the rear pleat panel extends upwards by the same row.

## What changed from 74E and what each change does
| Change (amount at 96 px / 48 px) | B | C | Effect (self art QA) |
|---|---|---|---|
| Pelvis level: down at heel strike and loading, neutral, up at mid-stance (−1…+1 px / 0…1 px). Video phase from 74E (see below) | ✓ | ✓ | The weight drop and rise read in the hips and the skirt; the skirt compresses when loaded |
| Chest follows the pelvis 1 frame later | ✓ | ✓ | The trunk no longer moves as one block with the hips |
| Head moves only when the chest has been down for 2 frames (0.5-frame posture correction) | ✓ | ✓ | The hat top moves in **2/12** frames (74E: 4/12); the face and glasses stay steady |
| Pelvis forward 1 px at mid / terminal stance (push), hips and skirt hem (0–1 px at 48) | ✓ | ✓ | A gentle forward drive over the support leg |
| Capelet (shoulder) counter-motion −1 px, 1 frame after the pelvis | ✓ | ✓ | Small shoulder/hip counter-motion at the capelet edge |
| Toe stays on the ground through F08 (toe-off at t 0.675) | | ✓ | "Push to the end with the toe" |
| Hand and cuff 0.5 frame behind the forearm; the arm still leads the legs by 0.06 cycle as in 74E | | ✓ | Softer wrist |
| Collar 1 frame, potions 1 frame, hair 1.5 frames, mantle 2 frames (longer); skirt hem 1 frame after the pelvis | | ✓ | Cloth parts no longer move on the same frame; free ends trail the attached parts |

### Video phase vs the director's table
- The proposed table puts the pelvis low at F01–F02 and high at F04–F05.
- The 74E video measurement puts the body lowest at heel strike and loading (t 0–0.15) and highest at mid-stance (t 0.25–0.35).
- Following the instruction to prefer measured values, the table was moved **one frame earlier**: pelvis +1 (low) at F00–F01, 0 at F02, −1 (high) at F03–F04, 0 at F05, then the same for F06–F11.
- The shape of the table (2 frames low, 1 neutral, 2 high, 1 neutral) is kept.

## Technical QA (`QA_REPORT_74F.json`, `SHA256SUMS_74F.txt`)
| Item | 74E | 74F-B | 74F-C |
|---|---|---|---|
| Format, alpha 0/255, transparent RGB 0, one component, 12 frames, ground rows 124 / 61 | PASS | PASS | PASS |
| Foot slide (planted edge, world px) | 0.53 | 0.53 | 0.53 — PASS (< 1.5) |
| Speed per cycle (96 px) / cycle | 41.6 / 840 ms | 41.6 / 840 ms | 41.6 / 840 ms |
| Loop F11→F00 vs largest other transition | 4200 / 4147 | 2051 / 4161 | 2072 / 4218 — PASS (no jump) |
| Mean changed px between frames (96) | 1843 | 2276 | 2302 (motion spread over more frames) |
| Enclosed transparent holes (max per frame) | 2 | 2 | 2 (only the natural gap between the thighs) |
| Colours per frame (96 / 48) | 2488 / 735 | 2477 / 731 | 2475 / 735 |
| Gold pixel count variation over the cycle (CV, 96 / 48) | .009 / .035 | .017 / .040 | .022 / .048 — PASS (< 1.5 × 74E + .01) |
| Isolated 1 px pixels (mean per frame, 96) | 18.6 | 19.5 | 20.5 (slightly up; row stretching) |
| Rebuild from the repository | – | Byte-identical | Byte-identical |
| SHA-256 of 74A–74E and right 72 | Recorded and unchanged | | |

**Game speed check (FAIL as a match, needs a decision).**
- The field movement nominal speed is 300 world px/s (`js/field/morwen-field-dev.js` on the #213 branch, `FieldMovement` 5 px/frame at 60 Hz). 48×64 art is drawn 1:1 in world px.
- At the art's own speed (20.8 px/cycle at 48 px, 840 ms) she covers about 25 px/s.
- At 300 px/s with an 840 ms cycle the planted foot would slide about 19 px per frame. The current DEV follower (#213: 225 px per 6-frame cycle) also slides.
- Matching the art requires either distance-driven playback with a longer world stride (accepting the slide, as most field sprites do) or a much slower field walk speed. This is a game-design decision; the art is not changed here.

## Self art QA (not third-party)
- **Official design, proportions and colours:** identical to 74E (same reference), confirmed in `COMPARE_OFFICIAL_74E_74FB_74FC.png`.
- **B:**
  - The hips and skirt carry the weight shift, and the head is steadier than in 74E.
  - On the one rising frame per step, the chest/waist compression is visible as a 1-row change in the waist band. This was checked: no gap appears.
- **C:**
  - The different cloth phases remove the "everything moves on the same frame" stiffness, and the F08 toe push makes the push-off easier to read.
  - Gold flicker is slightly higher than in B (mantle and hair move on more frames) but stays within the limit.
- **At 48 px:**
  - Pelvis and chest offsets reduce to 0–1 px.
  - The legs' front/back order and the boot/sock boundary stay readable (`NATIVE48_74E_74FB_74FC_x1.gif` / `_x3.gif`).
- **Dark backgrounds:** same rim as 74E (`BACKGROUNDS_74FC.png`).

## Recommendation
- **74F-C**:
  - It keeps every 74E measurement: slide, cycle, speed, toe-off share and the arm lead.
  - It adds the requested layered timing (pelvis → chest → shoulder → head; cloth per part), a steadier head (2/12 frames) and the toe push.
  - Its seam change is about half that of 74E.
- Choose B if the third-party QA finds C's cloth motion too busy.

## Why 12 frames rather than 8
- 12 frames separate toe contact (F07), toe-off (F08) and the reach before heel strike (F11). These moments fall between 8-frame samples.
- The two-frame low and high holds of the pelvis need 12 frames to show without 1 px jitter.
- The half-frame and one-frame lags (hand, chest, collar) only exist on a 12-frame grid.

## Remaining
- Third-party art QA and Android device QA: NOT_RUN.
- Game-speed mismatch (above): needs a director decision.
- Isolated-pixel count and gold variation rise slightly in B and C because of the row stretching.
- Pelvis and shoulder rotation remain design values (not measurable in the 2D video).

## Files
- Candidate frames:
  - `morwen_left_walk_74FB_12f_NN_{96x128,48x64}.png`
  - `morwen_left_walk_74FC_12f_NN_*.png`
  - sheets and single GIFs
- `COMPARE_74E_74FB_74FC_synced.gif`, `NATIVE48_74E_74FB_74FC_x1.gif` / `_x3.gif`
- `FRAME_DESIGN_TABLE_74F.png`, `PHASE_REPORT_74F.md`, `QA_REPORT_74F.json`, `SHA256SUMS_74F.txt`
- `COMPARE_OFFICIAL_74E_74FB_74FC.png`, `BACKGROUNDS_74FC.png`, `qa_preview_74F.html`

## Regeneration (from this directory)
```
python3 build_morwen74f.py --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 --out <out>
python3 make_sheets74f.py --art . --e74 ../74E --repo <repo root> --official <official left PNG from main>
python3 make_qa_preview74f.py --art . --e74 ../74E --ground <repo>/img/field/moss/art --out qa_preview_74F.html
python3 qa_morwen74f.py --art . --e74 ../74E --d74 ../74D --c74 ../74C --b74 ../74B --a74 ../74A --right72 ../../morwen-right-walk/72
```
