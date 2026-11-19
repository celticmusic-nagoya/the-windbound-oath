# LIND cliff — independent visual comparison QA (2026-11-17)

## Evidence
- Render workflow: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44032388671
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44032388671/artifacts/14305812720
- Image: `macro_vs_scan_side_by_side.png`
- Image SHA-256: `a6c031e49fa18f5ef5e66730f0ab5bc9251bea0fb9851cde65abed231e3fdd1c`
- Scan .blend SHA-256: `8c86b29c1d28c0aad0a5a07873ce40c5ff3b64b18c8d64819bd98151c5a7781a`
- Macro: 4,288 polygons. Scan reference: 86,764 polygons.
- Comparison only: scale and translation are visualization aids, **not world registration**.

## Independent visual findings
- **Macro FAIL (G2)**: upper surface is planar; wave pattern visibly periodic and mechanically generated; lateral faces terminate abruptly; no eroded soil/grass interface.
- **Scan rock detail PASS as reference only**: irregular fracture paths, mixed-size protrusions and coherent rocky visual relief; scan's rectangular crop and open edges prevent use as a finished cliff.
- **Integration NOT_RUN**: no physical join, projection, trim/transition, UV bake, LOD, collision or in-game scene. Workbench display does not validate PBR.
- **G1 BLOCKED**: official physical scale, positions and camera not approved. Keep west ocean cliff distinct from east river cliff.
- **G3 PASS for isolated OBJ import/render and PNG SHA only**; full production mesh G3 NOT_RUN.
- **G4 NOT_RUN**.

## Method decision and exit criteria
Do not rerun the periodic macro surface or whole-mesh voxel/decimate approaches. Next geometry method must start with a **connected, independently designed natural silhouette** and preserve source-scan detail through local surface dressing. Before expensive generation, require:
1. Source-to-world transforms explicitly marked as unknown until canon is approved.
2. Scan remains reference/dressing; collision must derive from independently validated macro geometry.
3. Proposed scan region boundary has a designed taper/transition, not a rectangular raw crop.
4. Geometry QA checks connected components, edge orientation, signed volume, degeneracy, and UV occupancy; image QA checks 3 angles at game-scale preview.
5. If the new method fails twice for the same root cause, stop and redesign; no repetitive parameter tuning.

**Status:** no new production geometry in this QA-only change; no canonical files modified.
