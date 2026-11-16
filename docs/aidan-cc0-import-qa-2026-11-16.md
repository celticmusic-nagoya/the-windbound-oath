# AIDAN CC0 stone Blender import QA — 2026-11-16

Evidence: GitHub Actions run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43784300747 ; Blender 4.0.2; artifact aidan-cc0-import-audit (id 14189104613). Source Poly Haven rock_moss_set_01_8k.blend, pinned SHA-256 23d6220c6c7613c4d7006d902ac99acebc7e7859f1368ba6dc0ae4123551cdc6. License CC0 https://polyhaven.com/license.

| Mesh | Triangles | Boundary edges | Nonmanifold edges | Dimensions (Blender units) |
|---|---:|---:|---:|---|
| rock01 | 11000 | 0 | 0 | 2.23763,3.36880,1.47270 |
| rock02 | 10996 | 0 | 0 | 2.65538,3.26372,1.26199 |
| rock03 | 5000 | 0 | 0 | 2.10858,2.07959,1.09969 |
| rock04 | 10589 | 18 | 27 | 2.12763,1.96474,1.76832 |
| rock05 | 16548 | 0 | 0 | 1.81732,2.99866,1.20545 |
| rock06 | 8994 | 0 | 0 | 2.12598,2.75730,1.26185 |

Total 63127 triangles. Imported geometry is verified; art suitability is not. Topology audit only covers nonmanifold/boundary counts, not self-intersections, UVs, scale or actual stone fitting. rock04 requires repair or exclusion. rock03 and rock06 are first inspection candidates due to relatively low triangle counts, not art-approved selections. G1 BLOCKED (house canon dimensions), G2 NOT_RUN, G3 PARTIAL_PASS, G4 NOT_RUN.

Next: render isolated rock03/06 clay silhouettes, inspect stone proportions and natural shape at final 48px, and decide whether either can be adapted into individually hand-fitted corner master stones. No geometry modifications until source suitability review. Do not merge or replace official assets.
