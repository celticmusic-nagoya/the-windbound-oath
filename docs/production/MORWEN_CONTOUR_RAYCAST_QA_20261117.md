# MORWEN CONTOUR-DRIVEN BVH RAYCAST QA — 2026-11-17

## Executed evidence
- Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43997425866 (SUCCESS)
- Artifact ID: 14290617836
- Files: `render_contour_candidates.json`, `raycast_surface_evidence.json`
- Source: verified Blender Studio CC0 Human Base Meshes v1.4.1; diagnostic orthographic RGBA renders.
- Contours sampled at 8px vertical intervals, with three points per occupied scanline (left +2px, midpoint, right -2px), within upper-frame rows 72–256.

| Mesh | Front | Back | Left | Right | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stylized | 66/66 | 66/66 | 66/66 | 66/66 | 264/264 |
| Realistic | 69/69 | 69/69 | 69/69 | 69/69 | 276/276 |
| Total | | | | | 540/540 |

All 540 selected interior pixels raycast onto source mesh triangles. The sample set is selected from the render alpha, not an independent all-pixel projection accuracy test. The source image hashes are checked against the diagnostic manifest. The original source .blend SHA is checked unchanged. This evidence is **not** a head/chin landmark identification and cannot establish the 7.75-head target.

## Quality gates
- G1 official Morwen anatomy/design: BLOCKED
- G2 independent visual/anatomical QA: NOT_RUN
- G3 contour extraction and selected BVH intersections: PASS; pixel-to-surface depth correctness beyond hit/miss: NOT_RUN
- G4 game integration and Android: NOT_RUN

## Next
Compare projected silhouette with rendered alpha, identify candidate chin and head-top locations in both front and side views, then independently review those hypotheses. Do not label arbitrary scanline minima as anatomy.
