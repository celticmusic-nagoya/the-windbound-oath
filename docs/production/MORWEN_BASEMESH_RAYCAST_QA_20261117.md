# MORWEN BASEMESH RAYCAST QA — 2026-11-17

- Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43990885381 — SUCCESS
- Artifact ID: 14287627331
- Evidence: `raycast_surface_evidence.json`
- Method: BVH triangle intersection with fixed 512x768 orthographic diagnostic pixel grid (15 samples per view)
- Input Blender source SHA-256 checked unchanged by the script.

| Source | Front | Back | Left | Right | Total |
|---|---:|---:|---:|---:|---:|
| GEO-body_female_stylized | 6/15 | 6/15 | 4/15 | 4/15 | 20/60 |
| GEO-body_female_realistic | 9/15 | 9/15 | 5/15 | 5/15 | 28/60 |
| Combined | | | | | 48/120 |

Misses on fixed diagnostic pixels are not automatically failures: the rays may pass outside the mesh silhouette. This is not a full rendered-pixel correspondence QA. The hit positions do not identify the anatomical chin, neck, or head top.

## Gates
- G1 Canonical Morwen proportions: BLOCKED
- G2 Anatomical/artistic approval: NOT_RUN
- G3 Blender execution, raycast artifact, immutable source: PASS; independent projection calibration: NOT_RUN
- G4 Game integration and Android: NOT_RUN

## Next
Project silhouette/contour samples rather than arbitrary grid points, verify projection against image alpha and mesh, then review actual candidate anatomical marks before computing head ratios. Do not infer a chin from sparse hits.
