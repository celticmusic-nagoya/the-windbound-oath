# MORWEN-ASSET-74E — video-analysed walk on the ART-74D design

Status: **CANDIDATE**.

| Gate | Result |
|---|---|
| Video analysis | DONE — manual keypoints plus automatic silhouette series. MediaPipe pose model unavailable offline: BLOCKED (`VIDEO_ANALYSIS_74E.md`) |
| Static / technical QA | PASS |
| Third-party art QA | NOT_RUN |
| Android device QA | NOT_RUN |

74A–74D, the right walk 72, the official turnaround and `main` are unchanged. Nothing here is in a manifest or in production.

## Frames
| Files | Content |
|---|---|
| `morwen_left_walk_8f_00..07_{96x128,48x64}.png` | **First candidate**, 8 frames |
| `morwen_left_walk_12f_00..11_*` | Same cycle at 12 frames. Each frame is a pose on the video-measured curve, not an in-between of the 8f frames. Adds the explicit toe-off (F08), the late pre-swing toe contact (F07) and the reach before heel strike (F11) |
| `*_sheet_*.png`, `morwen_left_walk_74E_{8f,12f}.gif` | Sheets and GIFs |

Frame roles (near leg / far leg):

| 8f | t | near | far |
|---|---|---|---|
| F00 | 0 | heel strike | pre-swing (toe contact) |
| F01 | .125 | loading | late pre-swing (toe contact) |
| F02 | .25 | mid-stance | mid swing (passing) |
| F03 | .375 | terminal stance | terminal swing |
| F04 | .5 | pre-swing | heel strike |
| F05 | .625 | late pre-swing (toe contact) | loading |
| F06 | .75 | mid swing (passing) | mid-stance |
| F07 | .875 | terminal swing | terminal stance |

The 12f roles are in `build_meta_74e.json`, as are all per-frame values (ankle position, foot angle, lift, bob, arm, cloth).

## What changed from 74D (motion only; design kept)
| | 74D (= 74C motion) | 74E (video) |
|---|---|---|
| Stance / swing | 50 / 50 % | **66 / 34 %** (toe-off 0.66) |
| Double support | none | **16 %** each, back foot rolls on the toe |
| Heel strike | toe up 14° | **19°**, foot flat by 0.07 |
| Heel rise | gradual from 0.375 | **0.43** (−8°) → −28° (0.5) → −60° (toe-off) |
| Swing | lift up to 4 px | **1–3 px** clearance, foot hangs after toe-off, reaches forward before heel strike |
| Body low point | loading (1 px) | **heel strike + early loading** (1 px) |
| Arm | 1 px, −cos | **2 px**, opposite phase, leading by 0.06 cycle |
| Speed | 34 px/cycle | **41.6 px/cycle** (96 px); 8f and 12f identical |

## Design kept from 74D, plus minimal additions
- Same recolour, short boots and knee socks. The reference differs from 74D only in **36 rim pixels**.
- **Dark-background rim:**
  - Hat and mantle: the top and front silhouette pixels that were almost black use one deep purple (74, 39, 87).
  - Legs: the front and top outline pixels use the boot ramp's 3rd tone.
  - The shape does not change. `BACKGROUNDS_74D_vs_74E.png` shows meadow, moss forest, dark cave and night field; cave and night are darkened repository textures, i.e. simulated.
- **Pixel clean-up** (art level C):
  - Gold is snapped to the 3 shared golds.
  - Isolated pixels in the head, torso and skirt layers are removed, except in the face.
  - Mean colours per frame drop from 2848 to 2485 (96 px) and from 859 to 734 (48 px).
- The magenta share stays at 0.4 % (74C: 25 %).

## QA (`QA_REPORT_74E.json`, `SHA256SUMS_74E.txt`)
| Item | Result |
|---|---|
| Video evidence (JSON, keypoints, series, pose table) | Present — PASS |
| Format / alpha 0/255 / transparent RGB 0 / one component / ground rows 124 / 61 (8f and 12f) | PASS |
| Foot slide of the planted edge, world coordinates | 8f ≤ 0.80 px, 12f ≤ 0.53 px — PASS (< 1.5) |
| Cycle / speed | 8f = 12f = 41.6 px/cycle — PASS |
| Arm vs leg | Arm −2 at near heel strike, +2 at far heel strike — PASS |
| Pelvis / shoulder | Pelvis rotation ±0.6 px and swing-side drop 0.5 px (design values). Shoulder shown through the arm only |
| Cloth lag | Collar, cape, potions and hair 1/8 cycle after the body; mantle longer; skirt during loading |
| Loop seam (last→F00 vs the same transition half a cycle earlier) | 8f 1.00, 12f 1.01 — PASS |
| Colours not increased vs 74D; magenta not increased | PASS |
| SHA-256 of 74A / 74B / 74C / 74D / right 72 | Recorded and unchanged; the commit adds only `74E/` |
| Rebuild from the repository | Byte-identical |
| Third-party art QA (`qa_preview_74E.html`, V-1, W-1..8, A-1..4, X-1..2) | NOT_RUN |
| Android device QA | NOT_RUN |

## Comparison material
| # | File |
|---|---|
| 1 | `VIDEO_KEYPOSES_74E.png` (key poses; skeleton only), `VIDEO_SERIES_74E.png` (head / foot-spread series) |
| 2 | `VIDEO_vs_74E_POSES.png` (video pose ↔ 74E frame with values) |
| 3 | `COMPARE_74D_vs_74E_8f_synced.gif` |
| 4 | `COMPARE_74E_8f_vs_12f_synced.gif` |
| 5 | `COMPARE_OFFICIAL_74D_74E.png` |
| 6 | `BACKGROUNDS_74D_vs_74E.png` |
| 7 | `NATIVE48_74D_vs_74E.png` |

## Game playback (recorded separately from the video)
- The video cycle is 4.24 s of slow-motion time, so the real cadence is unknown.
- Recommended game cycle: **0.84 s** (8f ≈ 9.5 fps, 12f ≈ 14.3 fps). Ground speed is 41.6 px per cycle at 96 px (≈ 50 px/s), or 20.8 px per cycle at 48 px.

## Remaining
- Third-party art QA and Android device QA: NOT_RUN.
- Pelvis and shoulder rotation were not measurable from the 2D video, so the values are design values.
- Stride is limited by the 2.8-head leg length: ±0.26 leg lengths at contact versus ±0.40 in the video.
- Each 1 px body bob changes about 4000 px between frames; this was the same in 74C/74D.

## Regeneration (from this directory)
```
python3 build_morwen74e.py --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 --out <out>
python3 make_sheets74e.py --art . --d74 ../74D --repo <repo root> --official <official left PNG from main>
python3 make_qa_preview74e.py --art . --d74 ../74D --c74 ../74C --right72 ../../morwen-right-walk/72 --ground <repo>/img/field/moss/art --out qa_preview_74E.html
python3 qa_morwen74e.py --art . --d74 ../74D --c74 ../74C --b74 ../74B --a74 ../74A --right72 ../../morwen-right-walk/72
# video analysis (needs the video files, which are not committed): ffmpeg crop to the left half -> seg.py / analyze_v2.py / make_video_evidence.py --skeleton-only
```
