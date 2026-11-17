# MORWEN HEAD-RATIO VISUAL CANDIDATES — 2026-11-17

## Evidence
- Original Blender diagnostic render artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43997425866 (artifact 14290617836)
- Render front view: 512 × 768, orthographic vertical scale 2.05 world units, both meshes source unchanged.
- Visual observations made from magnified front-view diagnostic PNGs; no source files edited.

## Unreviewed candidates (NOT canonical measurements)

| Mesh | Top pixel y | Chin underside pixel y | Head height approx. | Total mesh height | Approx. head count |
| --- | ---: | ---: | ---: | ---: | ---: |
| GEO-body_female_realistic | 77 | 160 | 0.22155 | 1.639320 | 7.40 |
| GEO-body_female_stylized | 81 | 187 | 0.28294 | 1.616915 | 5.72 |

Formula: head_height = (chin_y - top_y) * 2.05 / 768; ratio = world mesh height / head_height. Pixel candidates are **manual visual estimates**, NOT BVH-validated anatomical landmarks.

For illustration only, allowing ±6 pixels at *each* endpoint gives very broad possible ratios: realistic about 6.47–8.65, stylized about 5.13–6.44. These are sensitivity bounds, **not statistical confidence intervals**. Realistic is closer to the 7.75 target by point estimate, but is **not accepted** as the Morwen base mesh.

## Review gates
- G1 Canonical Morwen design: BLOCKED
- G2 Independent anatomy/art QA: NOT_RUN
- G3 Actual Blender render, source hash, raycast pipeline: PASS; chin landmark verification: BLOCKED
- G4 Game and Android: NOT_RUN

## Next
Cross-check the underside-of-chin point in front/side views using pixel-to-triangle raycasts, then obtain independent visual review. Recompute head-count only after chin and crown are validated. Do not deform or replace any canonical mesh from this candidate estimate.
