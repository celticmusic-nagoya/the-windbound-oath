# MORWEN-ASSET-74C — left walk: official-left design check + 8-frame (and 12-frame) elegant walk candidate

Status: **CANDIDATE**.
- Technical self-QA: PASS.
- Third-party art QA: NOT_RUN.
- Android device QA: NOT_RUN.
- Video analysis: BLOCKED (see `VIDEO_ANALYSIS_74C.md`).

Nothing here is registered in a manifest or used in production. 74A, 74B, the official right walk 72 and `main` are unchanged. The 8-frame version is a candidate and does **not** replace the 6-frame spec.

## Variants (all 96×128 and 48×64, RGBA, mirrored left)
| Files | Content |
|---|---|
| `morwen_left_walk_8f_00..07_*` | **First candidate.** 74C design + new 8-frame walk |
| `morwen_left_walk_12f_00..11_*` | The same cycle sampled at 12 frames: same stride and same speed per cycle. F00 is byte-identical to 8f F00 |
| `morwen_left_walk_6f_00..05_*` | 74B motion + 74C design only. Use this if the design fix is adopted without the 8-frame motion |

## 1. Official design check (official left profile `assets/official/characters/morwen/turnaround/` on main, SHA-256 `d858c428…`; `OFFICIAL_LEFT_vs_74B_74C.png`)
| Item | Official left | 74B | 74C |
|---|---|---|---|
| Bag | not visible | none | none — PASS |
| Hat flower / ribbons | none | none | none — PASS |
| **Hat-tip jewel** (gold bead + purple drop) | **none** | present | **removed (61 px)** — PASS |
| Shoulder crest | none | none | none — PASS |
| **Cross-body strap** | **not visible** | re-routed strap drawn by 74A | **removed (12 px, refilled from the bodice)** — PASS |
| Left earring | gold + purple drop | gold + purple drop | same. **Now verified** (was UNVERIFIED in 74A/74B) — PASS |
| Glasses, short bob with bangs, hat shape and band, cuff frill, potions + chain at the front waist | present | present | present — PASS |
| Hand position | arm down, hand at the thigh / skirt | hand at hip / skirt level | same (1 px swing) — PASS at sprite scale |
| Knee socks | thigh-high, skin band, garter | kept (68 structure) | kept — PASS (not tights) |
| Hair colour | dark purple-brown | mauve (same as right 72) | unchanged — **mismatch shared with right 72**; needs a joint palette decision, not fixed here |
| Neck bow | purple bow | pink/white collar ribbon (same as right 72) | unchanged — shared with right 72, open |
| Proportions | realistic | 2.8-head field sprite | unchanged (field spec 2.8–3.0 heads) — N/A |

The official website shows only the front image on its page (1 of 4), so the repository turnaround was used.

## 2. Motion (8f / 12f; `build_meta_74c.json`)
The walk is one cycle written as a function of phase. 8f and 12f sample the same cycle, so adding frames does not change speed. Speed is 34 px per cycle at 96 px, i.e. 4.25 px/frame (8f) and 2.83 px/frame (12f); 74B is 36 px per cycle. Play both with the same cycle time (QA page default 0.72 s).

- **Feet**
  - Key poses: heel strike, loading, mid-stance, heel rise, toe-off, initial swing, passing, reaching.
  - Stride is slightly shorter than 74B and foot lift is low (max 4 px).
  - In the tilted stance frames the ankle is shifted so the planted foot rolls over a fixed heel or toe point (pivot correction).
  - Foot slide (planted edge, world coordinates): 8f ≤ 0.75 px, 12f ≤ 1.17 px (quantisation at a fractional speed), 74B 3.0 px.
- **Pelvis**
  - ±0.6 px rotation: the hip of the forward leg moves forward.
  - 0.5 px drop on the swing side.
  - Both are sub-pixel and show only in the leg geometry.
- **Head and hat**
  - The body bobs 1 px on the loading frames only: 2/8 frames, versus 2/6 in 74B.
  - The hat-top row moves 1 px in 25% of the cycle (74B: 33%).
- **Arm**
  - The near arm swings 1 px, opposite to the near leg, anchored at the elbow.
  - Shoulder counter-rotation is not visible at this scale without redrawing the capelet. It is expressed by the arm only.
- **Lag** (cloth and hair follow the body by 1/8 cycle):
  - collar ribbon, cape front, potions and hair tips: 1 px;
  - mantle: 2 px trailing, held longer;
  - skirt hem: 1 px.
- **Loop**: the last→F00 change is 0.41 of the mean frame change (8f) and 0.58 (12f). No jump.

Body line and silhouette are not redrawn. Morwen's body shape and head ratio stay as in the official design (AGENTS: 17-year-old character, never sexualise). Grace comes only from posture, steady head, small arm swing, smooth weight shift, foot roll and cloth lag.

## 3. Technical QA (`QA_REPORT_74C.json`, `SHA256SUMS_74C.txt`): PASS
- All 6f, 8f and 12f frames: RGBA, alpha only 0/255, transparent RGB = 0, one connected component. Ground row is 124 (96 px) and 61 (48 px) in every frame.
- 6f design-only vs 74B: 74–75 px (96) and 16–20 px (48) changed, 0 outside the design-edit zone.
- 8f and 12f speed per cycle are identical.
- SHA-256 values of 74A, 74B and right 72 are recorded unchanged; this commit touches only `74C/`.
- Rebuilding from the repository (`--source ../74A/source_65B_F00`) gives byte-identical output.

## 4. Art QA (third party): NOT_RUN
Use `qa_preview_74C.html`. It compares 74B/74C (6, 8, 12 frames), uses the same cycle time for all, offers a ground-scroll view for foot slide, 48 native / ×3, light, dark and moss backgrounds, and a record form that exports JSON. It covers items D-1..3, M-1..7, A-1..6 (body line, proportions, standing→walk, linked motion, cloth, elegance vs practicality) and X-1.

Self-check images: `COMPARE_74B_6f_vs_74C_8f_12f.png`, `COMPARE_74B6f_74C8f_74C12f_synced.gif` (with moving ground marks), `morwen_left_walk_74C_{6f,8f,12f}.gif`, `BACKGROUNDS_74C_8f.png`, `OFFICIAL_LEFT_vs_74B_74C.png`.

## Remaining
- Video analysis: BLOCKED. A video file or frame sequence plus usage confirmation is needed.
- Third-party art QA and Android device QA: NOT_RUN.
- Hair colour and neck bow differ from the official turnaround in both directions (shared with right 72). This needs a separate decision.
- If 8f is adopted, the field code must play the walk with a cycle time instead of a fixed 6-frame index, at 34 px per cycle. Not implemented here.

## Regeneration (from this directory)
```
python3 build_morwen74c.py --source ../74A/source_65B_F00 --out <out>
python3 make_sheets74c.py --art . --b74 ../74B --ground <repo>/img/field/moss/art --official <official left PNG from main>
python3 make_qa_preview74c.py --art . --b74 ../74B --right72 ../../morwen-right-walk/72 --ground <repo>/img/field/moss/art --out qa_preview_74C.html
python3 qa_morwen74c.py --art . --b74 ../74B --a74 ../74A --right72 ../../morwen-right-walk/72
```
