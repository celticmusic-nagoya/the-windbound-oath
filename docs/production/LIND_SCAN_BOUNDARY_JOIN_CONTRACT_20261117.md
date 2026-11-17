# LIND scan-led cliff: measured boundary-to-terrain join contract (2026-11-17)

## Evidence
- Diagnostic SUCCESS: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44037688057
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44037688057/artifacts/14307772675
- Exact diagnostic PNG SHA-256: `31d878b6c4f8b6cc85326b475076b18fa30672811e96a32100d7eb5e395bcaab`
- Exact scan-led source blend SHA-256: `37a95b7bfe2580159d5a27125c8388c06e048c30a585fb191b627704e513006a`
- One closed boundary loop: 462 edges / 462 vertices, 0 endpoints, 0 junctions, length 22.97307 source units; 96 boundary vertices in the lowest 20% of its Z range.
- Workbench inspection: real fractured rock surface; exposed long lower edge, abrupt crop and visible thin spur. Neither visual quality nor collision can be inferred from topology PASS alone.

## Architectural decision
A boundary loop does not prove that this is a natural terrain edge. Do not simply cap it with a planar polygon or stretch the entire boundary down into a flat extrusion. Instead use it as a **measured source attachment constraint**:
1. Preserve original scan geometry, publisher UV and texture/material assignments in a read-only collection.
2. Compute an ordered boundary loop from the verified degree-two graph, retain exact vertex positions and source hashes.
3. Author a **separate rock-transition shell** with local, geology-directed buttresses and overlap under the scan edge. The overlap must not be exposed as a visible dark seam or cause z-fighting.
4. Add **soil/turf transition** only where the surface actually approaches a top shelf; never cover exposed rock cracks indiscriminately.
5. Maintain separate authored terrain support and simplified oriented manifold collision mesh. Scan mesh is render-only.
6. Generate front, oblique and overhead PBR renders with consistent world-space camera definitions for *comparison*, not unapproved canonical camera.
7. Run seam/normal/nonmanifold/UV/material QA and inspect final WebGL and Android display sizes.

## Fail-closed acceptance
- A boundary graph with >1 component, endpoints or branch vertices is a BLOCKED input; do not bridge arbitrary islands.
- If measured scan-to-support gaps exceed the locally authored join tolerance, report FAIL, do not hide with shader tricks.
- If top shelf or base placement cannot be established from official map spec, G1 stays BLOCKED.
- Do not use blind ring erosion, global decimate, voxel remesh or periodic loft. These methods already failed independent G2.
- The scan-led rock source remains **reference-only** until a coherent join and independent G1–G4 PASS.

## Status
G1 BLOCKED; G2 FAIL for completed cliff (rock-detail reference PASS); G3 PASS for boundary graph and read-only render only; G4 NOT_RUN. No new terrain geometry in this contract; no main merge, publication or canonical asset modification.
