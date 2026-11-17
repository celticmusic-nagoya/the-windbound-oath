# LIND existing WORLD/cliff candidate reuse audit — 2026-11-18

Status: **READ-ONLY TRIAGE; NO NEW TERRAIN OR APPROVAL**.

## Source evidence checked
- Branch comparison main → `feature/lind-world-01`: candidate `assets/candidates/LIND-WORLD-01/lind-world-terrain-c01/lind-world-terrain-c01.blend`, six renders and build manifest exist.
- Direct source: `feature/lind-world-01:docs/qa/lind/world/HANDOFF_TO_CODEX_20261117.md`. WORLD/Claude lane was **STOPPED**; Codex WORLD/ROUTE PR #346 and pipeline #350/#351 were identified as active. Do not resume this stopped lane.
- Direct source: `feature/lind-world-01:docs/production/LIND_SOURCE_SCENE_MATRIX_01.md`.
- Direct source: `feature/lind-cliff-scan-macro-reference-scene-01:.github/workflows/lind-macro-scan-reference.yml`. Existing comparison pipeline references source patch SHA `8c86b29c1d28c0aad0a5a07873ce40c5ff3b64b18c8d64819bd98151c5a7781a`, but explicitly renders **not world-aligned**.
- Direct source: `feature/lind-cliff-scan-macro-reference-scene-01:docs/production/LIND_VILLAGE_WORLD_INTEGRATION_PHASE1_20261117.md`.
- Current independently verified PBR source candidates: PR #415, Actions #44108000629, editable packed .blend files; geometry is **unplaced**.
- Proposed graph guardrails: PR #416, Actions #44109498760 **SUCCESS**, six negative controls. Source CG SHA `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.

## Candidate disposition
| Candidate | Evidence | Decision |
| --- | --- | --- |
| WORLD c01 .blend and six renders | Existing GitHub files; WORLD handoff documents visible heightfield seams, flat materials, underscaled cliffs, inaccurate river distance (130–230m vs CG ~50–70m), hidden river in raid camera; not compared to later master CG | **REFERENCE_ONLY / G2 FAIL by documented self-review; no independent visual QA** |
| Existing macro OBJ + scan patch | Workflow builds comparison PNG and verifies a fixed source patch SHA, but no world alignment | **REFERENCE_ONLY / no placement** |
| CC0 rock_face_01 and boulder_01 packed .blend | CI reopens meshes and packed textures; not terrain geometry | **REUSABLE_UNPLACED_COMPONENTS / G3 source packaging PASS** |
| Codex WORLD/ROUTE candidate D #346 | Referenced as active owner in handoff; source binary and final QA not inspected in this audit | **INSPECT_NEXT / NOT_RUN** |

## Safe next production gate
1. Inspect PR #346 and its artifacts/actual terrain renders, compare with the approved master CG and prior c01 known failures; do not reconstruct c01.
2. Resolve physical world scale, origin and camera through approved reference and character/WORLD interface; **no numeric coordinates may be inferred from illustration**.
3. Only after source review, decide whether scanned rock components can be authored as localized cliff surface inserts on an independently validated continuous terrain mesh.
4. Keep HOME, BUILD, ECO and ROUTE-MAT-01 Method C separate; no edits to those lanes.

## Gates
- **G1 BLOCKED**: official scale/origin/camera, private canon reconciliation, exact placement.
- **G2 NOT_RUN**: independent inspection of current Codex WORLD mesh; historical c01 self-review is negative.
- **G3 PASS limited**: packed CC0 component reopen and topology guardrails only; production WORLD G3 **NOT_RUN**.
- **G4 NOT_RUN**: runtime, collision, SAVE, Android.

No main merge, no official source replacement, no new terrain geometry, no publication.
