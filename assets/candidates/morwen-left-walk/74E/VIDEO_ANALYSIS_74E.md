# MORWEN-ASSET-74E: video analysis report

**Result: DONE.** The attached files themselves were analysed; this is not a URL search. One full gait cycle was measured. The analysis is partly manual:
- MediaPipe 0.10.32 is installed, but it contains no pose model, and model files cannot be downloaded here (network off). Automatic pose estimation was therefore **BLOCKED**.
- Joints were annotated by hand on 9 frames, on a 3× zoomed grid (±3 px).
- Timing, head height and foot spread were measured automatically from the silhouette (OpenCV) on every frame.

## 1. Files (ffprobe)
| File | Format | Size | FPS | Duration | Use |
|---|---|---|---|---|---|
| `animation_reference_-_female_standard_walk_-_grid_overlay_360p.mp4` | H.264 | 640×360 | 25 (each picture shown twice → 12.5 unique) | 24.72 s / 618 frames | **PRIMARY.** Split screen: left = side view (faces right), right = front view; grid overlay; slow motion |
| `Long-Stride_Walk_Animation_Reference___Young_Adult_Female___Slow_Motion.mp4` | H.264 | 640×360 | 25 | 60.96 s / 1524 frames | Secondary. Side and front views; an exaggerated long stride with wide arm swing. Step ≈ 27 frames (silhouette foot spread). Used only to confirm the heel→toe roll, not for parameters (not an everyday walk) |
| `female_walk_720p.mp4` | H.264 | 1280×720 | 24 | 1.00 s / 24 frames | **Not used.** Front view only, 1 s, a 3D game character model; side-view joints cannot be observed |

The videos are not committed (third-party footage). The repository holds only derived data: keypoint JSON, the silhouette series, and skeleton drawings without video pixels.

## 2. Section used
- Side view, f134–f240 (one full cycle).
- The whole clip f60–f520 shows steady walking. The foot-spread maxima repeat every 52–56 frames (median 53 = one step).
- The subject is followed by the camera, so all positions are measured relative to the hip.

## 3. Phases (one leg; t = fraction of the cycle from its own heel strike)
| Event | Video frame | t |
|---|---|---|
| Heel strike, far leg A | f134 | 0 |
| Foot flat | ≈ f141 | 0.07 |
| Mid-stance | f154–f160 | 0.19–0.25 |
| Heel rise | ≈ f180 | 0.43 |
| Opposite heel strike (near leg B) | f187 | 0.50 |
| Toe-off (automatic: back foot leaves the ground) | f204 | 0.66 |
| Next heel strike | f240 | 1.00 |

- Stance **66 %**, swing **34 %**, double support **16 %** each.
- Cycle = 106 frames = 4.24 s of video time. This is slow motion, so the real-time cadence is unknown. Game playback time is therefore recorded separately (recommended 0.84 s).

## 4. Joints (manual, `ann_v2.json`; drawings in `VIDEO_KEYPOSES_74E.png`)
| t | Knee flexion | Foot angle (+ = toe up) | Ankle relative to hip (leg lengths) | Foot clearance |
|---|---|---|---|---|
| 0 (heel strike) | ≈0° (straight) | +19…+24° | +0.40…+0.41 | 0 |
| 0.07–0.38 (stance) | ≈0–8° (within annotation error) | 0° | +0.34 → −0.24, linear | 0 |
| 0.43 | ≈5° | −15° | −0.32 | 0 |
| 0.50 | ≈6° | −24…−31° | −0.45…−0.51 | 0 (toe) |
| 0.57 / 0.62 | 2° / 33° | −44° / −75° | −0.51 / −0.55 | 0 (toe) |
| 0.69 (initial swing) | 40° | foot hangs (−105°) | −0.38 | 12 px |
| 0.75 (mid swing) | 69° | −54° | −0.25 | 7 px |
| 0.81 | 55° | −26° | −0.01 | 5 px |
| 0.88 (terminal swing) | 27° | +9° | +0.26 | 3 px |
| 0.93 (reach) | 11° | +24° | +0.41 | 2 px |

Other measurements:
- **Step length** (heel to heel): 0.87 leg lengths.
- **Head:**
  - It moves 11 px over a 283 px body height (3.9 %).
  - It is lowest from heel strike through loading (about 0–0.15 of each step) and highest at mid-stance (automatic series, `VIDEO_SERIES_74E.png`).
  - The front-view head top gives the same timing.
- **Arms:**
  - The wrist moves about ±0.27–0.34 leg lengths relative to the hip, opposite to the leg on the same side.
  - The arm reaches its back extreme about 0.06 cycle before that side's heel strike.
- **Posture:**
  - The trunk is upright (shoulder over hip at mid-stance) and the head is steady.
  - Side-view arm swing is small at mid-stance: both hands pass near the hip.
- **Pelvis and shoulder rotation** (side-to-side tilt and rotation) cannot be resolved in the 2D side view, and the automatic front-view measurement was too noisy (shorts and legs mix in the silhouette). Both are therefore **estimates**: the 74E values for them are design values.

## 5. Mapping onto Morwen (`build_morwen74e.py`, `VIDEO_vs_74E_POSES.png`)
- **Sprite leg:** hip→ankle is 31 px at 96 px.
  - Stride uses the video reach × **0.78** (restraint).
  - The 2.8-head legs (thigh 15 + shin 17 px) can barely reach ±0.33 leg lengths. After the pivot correction, which keeps the planted heel or toe on the same spot, heel strike sits at +0.26 L and toe-off at −0.27 L.
- **Timing taken from the video:**
  - Stance 66 % and toe-off at t 0.66.
  - Heel strike with the toe up 19°, then foot flat, heel rise from 0.43, and −28 / −45 / −60° through pre-swing.
  - Swing ankle path and foot angles at 0.69 / 0.75 / 0.81 / 0.88 / 0.93.
  - Low foot clearance (1–3 px at 96 px).
  - Body lowest at heel strike and loading.
  - Arm opposite to the leg, leading by 0.06 cycle.
  - Cloth follows the body 1/8 cycle later.
- **Deliberately reduced:**
  - Head bob is 1 px (0.8 % of height; video 3.9 %), because steady head movement was required.
  - Arm swing is 2 px at the hand (video ±0.29 L), because the capelet covers the upper arm and the swing must stay restrained.
  - The foot hang in early swing is clamped at −70° (video −105°) so the pixel foot stays readable.
- **Not taken from the video:** body shape, proportions and costume. The official design is kept.
