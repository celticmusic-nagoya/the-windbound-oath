# LIND-SPATIAL-01 — first implementation checkpoint

## Actual work
- Dedicated branch and Draft PR #338. Main and existing accepted assets untouched.
- Spatial masterplan: docs/production/LIND_SPATIAL_MASTERPLAN_V1.md.
- Blender scene assembly tool: tools/map_blender/lind_spatial_assemble.py. Imports separately authored .blend modules, verifies their optional SHA-256, and organizes layers into one master scene with a common orthographic camera. No monolithic auto-generated village.
- Canon-locked input template: docs/production/lind-spatial-layout.template.json. It is deliberately BLOCKED, with no invented coordinates or camera.
- Current map source hash is taken from docs/art/reference/lind/inventory.json. Actual visual review of the map image and latest private canon must occur before switching the layout to PASS.

## Next production tasks (independent work packages)
1. G1: inspect whole-village official map PNG and approved architecture, verify all regions, topography and anchor positions. Build source-backed layout JSON and camera contract.
2. S1: validate scene assembler with an isolated verified layout and Blender CI; preserve every input hash and log.
3. S2: complete Aidan's house + road + fence + garden + trees + grass + terrain + lighting as one finished-quality spatial slice. Separate modular geometry by material and structural function. Do not reuse G2-failed stone/grass candidates as approved assets.
4. Independent G2: overall scene, close-up and 48/96px final-scale renders. Then G3 and G4 Android game checks.
5. Expand by verified zone/chunk; do not merge to main until director approval.

## Gate status
G1 BLOCKED (canonical layout and exact camera not visually verified this run).
G2 NOT_RUN. G3 NOT_RUN (script saved, not executed in Blender). G4 NOT_RUN.
Do not report a Blender scene, render, agent execution or playable map as completed.
