# AIDAN-MASONRY-05 | Independent audit handoff (candidate only)

## Evidence and scope
- Draft PR #323, branch `feature/aidan-architecture-v3-01`
- GitHub Actions successful run 43664998326; artifact 14141413717, `aidan-masonry-candidate-qa` (3 PNG views, .blend, manifest, log)
- Source: `tools/map_blender/aidan_production_masonry_v1.py`
- Renderer: `tools/map_blender/aidan_production_masonry_render_v1.py`
- Existing QA validates Blender run, stone count, door/window intrusion, three PNG hashes. **This does not prove visual quality, watertight corners, accurate openings, or canonical design compliance.**

## Claude: independent art and architecture audit (read-only)
Review actual artifact images at full and game-view sizes, plus canonical Aidan's House design in repository. Inspect front/right/game27 views, stone silhouette, mortar, door and window surround, corner quoins, visual scale, course bonding, gable/eaves fit, material variation and Celtic medieval hand-built character. Give G1–G4 verdicts with concrete evidence, severity P0/P1/P2, exact file/line or image region, and minimal quality-first fixes. Do not assert PASS based solely on workflow success. Do not change files or approve art.

## Codex: independent Blender geometry and CI audit (read-only)
Inspect source, generated .blend and manifest. Check:
1. Window and door vertical boundaries: current code excludes entire intersecting rows; test 1.12m and 2.47m window and 2.20m door against actual stone bounds, not just absence of intrusion.
2. Corner continuity: corner gaps, wall overlap, and alternating quoin bonding; compare actual world-space bounds.
3. `_intervals` sliver suppression (`bb-aa < .07`) can create missing stones; detect every uncovered wall interval outside openings.
4. Backing mortar material is created but not used; check transparent gaps and whether backing would occlude openings.
5. Geometry currently consists of bevelled cube primitives; assess production-quality irregular hand-dressed stone faces, normals, mesh counts and rendering performance.
6. The 27-degree camera and scene measurements vs canonical model, and whether QA assertions actually catch regressions.
Return a reproducible test matrix, precise fix recommendations, and G1–G4 statuses. No changes to canon, main, existing approved assets or PR merge.

## Approval gates
- G1 canonical source and dimensions verified.
- G2 independent visual QA PASS (not yet).
- G3 structural and rendering QA PASS, including newly discovered boundary issues.
- G4 actual game display, scale and performance PASS.
Until all pass, status is **CANDIDATE_NOT_ART_APPROVED**.
