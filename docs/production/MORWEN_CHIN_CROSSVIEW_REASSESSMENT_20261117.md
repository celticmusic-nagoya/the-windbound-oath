# MORWEN REALISTIC CHIN CROSS-VIEW REASSESSMENT — 2026-11-17

## Source and method
- Source: GitHub Actions https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43997425866 artifact 14290617836.
- Actual RGBA PNGs: GEO-body_female_realistic_front.png, _left.png, _right.png.
- Actual raycast evidence: raycast_surface_evidence.json (world-space BVH intersections).
- No mesh deformation, no canonical asset edits, no approved landmarks.
- 512x768 orthographic renders, vertical ortho scale 2.05.

## Measured pixel rows and world Z
| Pixel y | World Z | Observation |
|---:|---:|---|
| 144 | 1.460964 | visually near underside of chin; UNREVIEWED |
| 152 | 1.439610 | chin-to-neck transition candidate |
| 160 | 1.418256 | neck region, NOT chin |
| 168 | 1.396902 | neck region |

World Z values correspond to center pixel BVH hits on front view, and height mapping is shared across views. The left/right renders show that the earlier y=160 chin estimate was too low.

## Head count sensitivity and correction
- Earlier visual guess: top y=77, chin y=160 => 7.40 heads, **withdrawn as an anatomical assessment** because y=160 falls in the neck.
- Alternative UNREVIEWED chin y=144, top y=77 => 1.639320 / ((144-77)*2.05/768) = approximately 9.16 heads.
- The alternative is not an approved measurement; the true chin underside may lie between sample rows. No automatic head-count correction should be applied.

## QA
- G1 official 7.5–8 head Morwen turnaround: BLOCKED
- G2 independent anatomical/art review: NOT_RUN
- G3 actual source image, alpha scanlines, raycast coordinate correspondence: PASS; landmark validity: BLOCKED
- G4 in-game/Android: NOT_RUN

## Next
Confirm anatomical chin point against front and profile source geometry, then independently review; assess whole-body proportions before any high-quality 3D Morwen sculpt. Do not claim Realistic is closest to target without verified landmarks.
