# MORWEN-MESH-REUSE-DECISION-01 | Evidence-based gate before geometry edits

Date: 2026-11-14. Status: **PARTIAL / NO VISUAL APPROVAL**.

## Source inventory and findings
- Canonical Layer 0 four-view references: `tools/blender/production_mesh_08/references/` front/right/back/left. Keep distinct from final-costume target sheet.
- Target sheet: `docs/art/MORWEN_3D_TARGET_SHEET_20261113.md` (uploaded JPEG hash recorded, binary GitHub registration pending).
- VRoid CC0 candidate audits: `tools/blender/morwen_production/MESH_QA_01_FINDINGS.md` and `MESH_QA_02_COMPONENT_FINDINGS.md`. Body 7,797 vertices / 11,646 faces / 179 islands; Face 2,054 vertices / 3,158 faces / 34 islands; Icosphere 42 vertices / 80 faces / 1 island. 0 edges with >2 incident faces in audited meshes, but many boundary edges. This is topology evidence only.
- The largest Body island has 1,160 vertices; Face island 588 vertices. Component names, material roles and spatial assignments have not been confirmed. Small islands must **not** be deleted on size alone.
- Earlier local jaw-percentage tuning did not establish visual fidelity. Do not resume that method.

## Part-by-part disposition
| Part | Current evidence | Decision |
| --- | --- | --- |
| Body / Layer 0 | topology audit, four approved views; no calibrated rendered silhouette comparison | CONDITIONAL_REUSE_CANDIDATE; no adoption |
| Face / jaw / eyes | Face topology only, no measured landmark match to front/profile | REUSE_UNDETERMINED; STOP local percentage tweaking |
| Hair | no proven four-view clump geometry match | NEW_HIGH_FIDELITY_PARTS_REQUIRED, pending canonical comparison |
| Hat | detailed asymmetric target; no matching geometry proven | NEW_HIGH_FIDELITY_PARTS_REQUIRED |
| Costume / cape / skirt | layered purple-gold costume target; no matching geometry proven | NEW_HIGH_FIDELITY_PARTS_REQUIRED |
| Boots / stockings | knee-high socks canon; fit/UV/deformation not yet demonstrated | UNDETERMINED |
| Satchel / vials / insignia | detail and placement from target; canonical asymmetry must be checked | NEW_PARTS_AFTER_G1 |

## Mandatory diagnostic before reuse decision
1. Confirm Blender version, model source and license evidence, current blend/VRM paths and source hashes.
2. Generate **actual** orthographic front/right/back/left neutral-pose PNGs, same camera scale and root anchor, plus indexed mesh-island/material diagnostic.
3. Compare front/profile facial landmark locations (eyes, nose, mouth, chin, ear), face width/height and side silhouette. Record numerical confidence; do not infer absolute body measurements from stylized reference.
4. Overlay full-body silhouette and test deformation at final in-game pixel size.
5. Mark each part `REUSE`, `REBUILD`, or `BLOCKED` with evidence, not assumption.
6. Register attempts using the map team's canonical `schema_version:1` ledger at `tools/blender/morwen_production/_qa/morwen_attempt_ledger.json`; verified history only.

## Quality gates
G1: BLOCKED for final target-sheet binary registration and complete canonical cross-check.
G2: FAIL for previous candidate; new target fit NOT_RUN.
G3: PASS for existing mesh topology audit **only**, render/UV/rig unverified.
G4: NOT_RUN.

No approved source has been edited. No Blender render or device QA is claimed in this report.
