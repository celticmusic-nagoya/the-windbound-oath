# MORWEN BASEMESH HEAD SECTION REVIEW — 2026-11-17

## Provenance
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43989208722 (SUCCESS)
- Artifact ID: 14287071306; file: `head_section_evidence.json`
- Script: `tools/character_blender/analyze_basemesh_head_sections.py`
- Method: 80 uniform world-Z vertex-occupancy bands, **not** surface/plane intersections.
- Source: official Blender Studio Human Base Meshes v1.4.1 CC0; input .blend hash is recorded in the artifact JSON.
- No canonical Morwen assets or original .blend changed.

## Observations (candidate neck constriction, NOT anatomical chin)
| Mesh | Z min | Z max | candidate narrow X band center | band X span |
| --- | ---: | ---: | ---: | ---: |
| GEO-body_female_stylized | -0.003753 | 1.613162 | 1.320096 | 0.097747 |
| GEO-body_female_realistic | 0.002014 | 1.641334 | 1.426173 | 0.105941 |

These are local width minima in the upper-body region, not manually verified neck/chin landmarks. Head-to-body ratios must not be computed from these minima. Sparse vertex occupancy and shoulder/hair geometry can bias the measurements.

## Quality gates
- G1 Morwen canon-to-mesh fit: BLOCKED (approved 7.5–8-head 3D turnaround missing)
- G2 independent artistic anatomy QA: NOT_RUN
- G3 geometry sampling and artifact creation: PASS (CI success); anatomical identification: BLOCKED
- G4 in-game / Android: NOT_RUN

## Next
1. Use Blender BVH/raycast or exact triangle-plane intersection to measure actual surface geometry, with reproducible view transforms.
2. Cross-check chin/head candidate locations on actual orthographic renders and mark them **unreviewed** until independent review.
3. Only then measure 7.75-head target deviation; do not mutate the source meshes.
