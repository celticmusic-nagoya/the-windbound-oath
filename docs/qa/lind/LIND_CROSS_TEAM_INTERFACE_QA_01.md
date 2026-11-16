# LIND WORLD ↔ ROUTE ↔ HOME / BUILD / ECO interface and independent QA contract

Status: PREPARATORY CONTRACT ONLY. No model generated, no Blender run, no art approval.
Baseline: PR #351 at 415d4d5093fe94e95cd047f2aabdd621ddee9c1a; candidate D immutable; PR #350 deterministic pipeline unchanged.

## Findings requiring explicit integration work

- `tools/map_pipeline/tasks.json` still uses `readonly-candidate-partition-render-v1`, immutable candidate D, and enables only WORLD and ROUTE. This is appropriate for the evidence pipeline, but it **does not** execute the new `WORLD-GEO-02` / `ROUTE-SUPPORT-01` work orders in `tools/map_pipeline/geology_route_work_orders.json`.
- Do not overwrite `tasks.json` to force new work orders through the old extraction pipeline. Add a separately versioned production adapter and tests after Codex produces actual new geometry scripts/outputs; compare input SHA and source immutability.
- The production work-order file currently records ROUTE's WORLD interface as prose, not a machine-verifiable immutable interface SHA. No canonical meter scale is approved. Full spatial G1 remains BLOCKED.
- HOME, BUILD, ECO must not silently consume candidate-space units as meters, nor assume fixed positions from concept imagery.

## Proposed machine-verifiable interface (candidate, not adopted canon)

Each producing unit should export a separate JSON sidecar with:
- `schema_version`, `producer_unit`, `producer_commit`, `source_sha256`, `model_sha256`, `blender_version`, `coordinate_space` (e.g. `candidate-local-unscaled`), `unit_scale_status` (`UNAPPROVED` unless formally locked), `axes`, `origin_policy`, `up_axis`, `handedness`, `transform_matrix`, `interface_sha256`.
- Named anchor IDs with local 3D positions, normal and intended consumer, but mark coordinates `PROVISIONAL` until G1 formal placement/scale approval.
- Geometry boundary exports as separate meshes with immutable SHA and explicit ownership: terrain contact, bridge abutment face, road-junction boundary, foundation contact, river/waterline, vegetation exclusion region.
- Producer/consumer dependency graph; ROUTE must not append duplicate WORLD context geometry to final assembly.
- Recompute SHA from canonical serialized interface bytes, not manually copied text. Fail closed on mismatched hashes, missing anchors, ambiguous units or source-version changes.

## Independent QA: bounded sector first

WORLD geology:
1. Validate expected geometry objects, nonempty finite evaluated mesh, face areas, normal consistency, obvious self-intersections and material assignments; state limits of each detector.
2. Render overview, cliff detail, gameplay-size; compare actual images with approved source. A smooth banded cliff or sawtooth grass transition is G2 FAIL regardless of technical PASS.
3. Confirm no reintroduction of the exhausted A/B geology method by comparing generation algorithm and historical failure ledger.

ROUTE support:
1. Evaluate actual triangulated road/terrain/support geometry, not only sampled centerline/edges. Report unsupported span area, maximum and distribution of gaps, abutment intersection/overlap and joint continuity.
2. Measure slope, step, clearance and junction geometry; any threshold is **provisional** until approved. Existing 1,557 sample nonburial is regression evidence only.
3. Collision/navigation and Android/runtime remain NOT_RUN unless actually tested.

Cross-unit:
1. Require matching interface SHA, coordinate convention, explicit transform and input asset hashes.
2. Validate seams and non-overlap at contact boundaries; do not assert structural support from visual proximity alone.
3. Preserve deterministic artifacts, logs, images, SHA, versions, and failure ledger. After two effective same-cause/same-method failed attempts, stop rather than retry.
4. G1 full canon/metric: BLOCKED; G2: FAIL for existing candidate D / NOT_RUN for new work until independent image review; G3: only tested checks PASS; G4: NOT_RUN.

## Integration order and no-conflict rules

1. Codex WORLD/ROUTE continues PR #351 new production. This QA contract is isolated in its own Draft PR.
2. Claude HOME / BUILD / ECO may create standalone high-quality modular assets with **provisional** interface adapters; no canonical terrain placement, meters, map integration or replacement until shared interface is approved.
3. Once first WORLD/ROUTE actual renders and interfaces are available, run independent geometry/image QA and compare to these proposed acceptance criteria. Fix the contract against evidence, not guesses.
4. Only after successful bounded-sector QA should the approved production adapter link new geometry to the existing PR #350 deterministic renderer. Do not alter old evidence tasks to make the tests appear green.
5. Never merge main, publish, delete originals, or promote a candidate based on this document.
