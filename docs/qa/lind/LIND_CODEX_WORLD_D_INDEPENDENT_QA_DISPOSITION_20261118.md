# LIND WORLD candidate D — source-backed independent QA disposition (2026-11-18)

**Read-only integration assessment. Not official adoption.**

## Provenance
- Source branch: `feature/map-deterministic-pipeline-world-route-01` (Codex WORLD/ROUTE PR #346 line).
- Directly inspected: `docs/qa/lind/spatial-codex-independent/report.md`, `summary.json`, `docs/qa/lind/spatial-codex-world/PRODUCTION.md`, `attempt-ledger.json`.
- Candidate D source: `assets/candidates/lind-spatial-codex-01/world/candidate-d/world.blend`, SHA-256 **2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72** as recorded by independent reviewer. This audit has not independently downloaded/rehashed the binary.
- Approved CG SHA recorded in prior independent QA: `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.

## Verified from existing independent QA
- D actual-mesh BVH sampled left/center/right across four routes: **1557/1557 not buried**, 0 buried points. Candidate route grades <=25° (study-only threshold).
- Maximum road-to-support gap **0.444855 candidate units at east bridge**; no verified supporting structure, intersection, triangle-interior clearance, collision/navmesh or runtime walkability.
- Original terrain 58,081 vertices/57,600 faces, 27 meshes; independently rendered source geometry but no UV layers, production LOD or performance acceptance.
- **G2 FAIL**: smooth periodic cliff strata, sawtooth material edges, unfinished coast/shore, no production architecture or ecology. Geology heightfield family A and B each failed; **STOP that family**.
- Route C failed true surface burial at harbor and bridge; D switched to actual-mesh support sampling and removed sampled burial, but floating support gaps remain.
- The earlier Claude WORLD c01 is stopped and remains reference only; do not restart.

## Integration decision
- **Reuse candidate D as a measurable road/terrain technical study**, not as a final village mesh.
- **Do not place** packed CC0 `rock_face_01` or `boulder_01` as world-aligned geology until the continuous cliff structural design and world scale are approved.
- **New production technique needed:** authored nonperiodic jointed cliff macro geometry (scan-guided only where licenses and source match) with explicit structural rock fracture and erosion; road/bridge supports require continuous junction earthworks and engineered abutments rather than floating ribbons. Separate this from Codex-owned bridge Method C.
- Next concrete test: retrieve candidate D source .blend and actual render binary, rehash and reopen independently; measure route support and inspect G2 image against master CG before making any modifications. Avoid duplicating Codex WORLD lane work.

## Quality gates
G1 **BLOCKED** (metric/origin/camera and full spatial/event concordance).
G2 **FAIL** for current WORLD candidate D (existing independent reviewer).
G3 **PARTIAL**: sampled nonburial/grades PASS; full route support, UV, LOD, navmesh and game budgets NOT_RUN.
G4 **NOT_RUN** (game and Android).
No main merge, canon overwrite, publication or production asset change.
