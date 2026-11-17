# Morwen basemesh vertex evidence — verified GitHub Actions artifact

## Actual execution
- Workflow run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43981958536 — SUCCESS
- Artifact ID: 14284285452 (`morwen-basemesh-blender-geometry-inventory`)
- Evidence: `landmark_vertex_evidence.json` in artifact, plus 8 diagnostic PNGs and geometry inventory.
- Script: `tools/character_blender/export_basemesh_landmark_evidence.py`
- Original .blend SHA-256: `e5e9d30a7e6bb385fed21459dce68d1ad0d06e7bde4f9626696dbfda07cd541a`
- Artifact reports `PASS_GEOMETRY_EVIDENCE_ONLY` and `source_unchanged: true`.

## Actual recorded mesh data
| Object | Vertex count | World Z min | World Z max | Height | X translation |
|---|---:|---:|---:|---:|---:|
| GEO-body_female_stylized | 12502 | -0.003753 | 1.613162 | 1.616915 | +0.635978 |
| GEO-body_female_realistic | 10582 | +0.002014 | 1.641334 | 1.639320 | -1.340052 |

Both have 13 world-Z sampling bands (0.00 through 1.00), 12 indexed nearest vertices per band. These are **not** anatomically labeled or independently verified landmarks. The two meshes are translated along X relative to one another; a front-view comparison must normalize per-mesh position while keeping equal scale.

## Limits and next gate
- World bounds and band samples alone cannot identify skull top, chin, shoulder/acromion, waist, hip, crotch, knee, ankle or sole. In particular, bounding-box extremes are not substitutes for anatomical landmarks.
- Current anatomical landmark entries are null; reviewer_confirmed remains false. Do not calculate or claim actual 7.75-head compliance.
- Next: Blender-generated evidence overlays with world-Z grid, mesh object name, vertex-index probes, and full orthographic front/side/rear views; independent reviewer must identify landmark positions and supporting indices.
- G1 BLOCKED, G2 NOT_RUN, G3 source/geometry evidence PASS only, G4 NOT_RUN. No canonical asset changes, production selection, merge, or publication.
