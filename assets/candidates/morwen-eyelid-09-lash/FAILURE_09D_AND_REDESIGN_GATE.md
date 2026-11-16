# MORWEN EYELID-09D | Failed geometry and method stop

Evidence: GitHub Actions 43786299068, real Blender run, saved source SHA256 9bff525ea293886f0aafdc79509f57d761d4a22a5f52e2700decae05c84ea9c4.

| Candidate | Left cage BVH pairs | Right cage BVH pairs | Eye pairs | Gate |
|---|---:|---:|---:|---|
| 09 original world-up | 64 | 59 | 0 | FAIL |
| 09 surface-frame | 17 | 0 | 0 | FAIL |
| 09B normal continuity | 4 | 0 | 0 | FAIL |
| 09D nearest cage surface clearance | 5 | 0 | 0 | FAIL |

09C exact residual diagnosis of 09B: L00 faces 0,1 vs cage triangles 938,940, 4 triangle pairs.

09D modifies six vertices (three root cross-sections) with nearest-surface projection plus 0.45 mm normal displacement. It **increased** overlap from 4 to 5; do not claim success or retry with small clearance/normal changes. A nearest-point offset does not guarantee swept ribbon triangles remain outside a nonconvex or rapidly changing-normal cage. It also chooses outward direction from candidate displacement rather than verified cage winding; this can be wrong if a vertex is already inside. This is a plausible cause, not a demonstrated root cause.

## Required next method: topology-aware root construction

Stop surface-frame normal averaging and nearest-surface displacement variants. First build a read-only report for 09D exact overlapping faces, signed containment, local cage winding, and segment-to-surface swept clearance, with cross-section correspondence to the 09B 09C evidence. Only after evidence, choose a distinct attachment: a root patch whose vertices follow the cage triangle adjacency and whose ribbon starts on a validated outward side; test continuous faces rather than vertex-only clearance. No further geometry variants before this evidence is collected.

Blender runtime emitted 'No module named numpy' / numpy._core.multiarray failed to import on startup, yet geometry scripts and BVH results executed. Treat runtime dependency hygiene as an independent technical issue. Do not declare the entire Blender environment healthy based on a successful bpy call.

G1 BLOCKED (canonical binary verification); G2 NOT_RUN; G3 FAIL; G4 NOT_RUN. No official model replacement, merge or publication.
