# MORWEN REALISTIC CROSS-VIEW HEAD HYPOTHESIS QA — 2026-11-17

## Executed evidence
- Workflow: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44003685444 — SUCCESS
- Artifact ID: 14293199139; file `head_landmark_crossview_evidence.json`
- Source mesh: `GEO-body_female_realistic`; source hash unchanged = true
- 4 orthographic views, scanline y=77 (candidate crown), y=160 (candidate chin), sampled x=160..352 at 8-pixel increments (25 rays per scanline)
- The candidates are manual visual estimates from a prior render, NOT independently approved anatomical landmarks.

| View | y=77 hit count | y=160 hit count |
|---|---:|---:|
| front | 1/25 | 5/25 |
| back | 1/25 | 5/25 |
| left | 2/25 | 6/25 |
| right | 2/25 | 6/25 |

Hit sample Z: y=77 approx. 1.639806, y=160 approx. 1.418256 world units, across views. Consistency of Z is expected for the same orthographic scanline; it does not independently confirm anatomy. 4-view ray intersections demonstrate geometric occupancy only. The y=160 line may intersect chin, neck, or another surface depending on x.

## QA
- G1 canonical design/head ratio: BLOCKED
- G2 independent visual anatomical QA: NOT_RUN
- G3 raycast execution, source immutability, 4-view hit evidence: PASS
- G4 in-game/Android: NOT_RUN

## Decision
Do not adjust geometry based on the 7.40-head point estimate. Stop extending the same scanline/raycast method for chin identification without independent anatomical reference. Next useful production task is to produce a formally reviewable 7.75-head 4-view turnaround derived from the five canonical Morwen images, then design/rig the high-quality 3D model with art QA. This candidate remains unapproved.
