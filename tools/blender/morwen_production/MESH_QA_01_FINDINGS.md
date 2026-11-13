# MORWEN-MESH-QA-01 — Verified Blender topology measurements

Source: GitHub Actions run 43439652209, SHA 24d0bae5ded98e05fb6c03ef340557eaba641ac2, artifact `morwen-vroid-cc0-head-review/MESH_TOPOLOGY_AUDIT.json`.

| Mesh | Vertices | Faces | Connected vertex components | Boundary edges | Edges with >2 incident faces |
|---|---:|---:|---:|---:|---:|
| Body | 7797 | 11646 | 179 | 3594 | 0 |
| Face | 2054 | 3158 | 34 | 892 | 0 |
| Icosphere | 42 | 80 | 1 | 0 | 0 |
| Total | 9893 | 14884 | 214 | 4486 | 0 |

## Interpretation
- All figures are **measured topology**, not proof of artistic fidelity or production readiness.
- Many connected components can be legitimate detached eyes, mouth, clothing, accessories or import primitives; component counts alone do not establish defects.
- Boundary edges can be legitimate open surfaces; investigate their spatial placement and intended seams before closing any mesh.
- The imported `Icosphere` is **not confirmed** to be a production character part. Do not delete or modify it without source attribution.
- This audit does **not** prove manifold watertightness: boundary edges exist, despite zero edges incident to more than two faces.
- The 3D source is an isolated candidate. No canonical Morwen geometry has been altered.

## Next step
Create a per-component diagnostic report for Body (largest connected islands, material hints, spatial bounds), then classify intended detached pieces versus suspicious fragments. Do not indiscriminately merge or decimate parts.

G1 canonical images preserved; G2 not approved; G3 topology audit PASS; G4 not run.
