# MAP-ASSET-RESEARCH-01 — Claude work packet

Status: ASSIGNED / NOT EXECUTED BY CLAUDE
Owner: Claude (manual/agent handoff; this document does not invoke Claude)
Baseline: current main AGENTS.md; verify current private canon before any lore-dependent design.

## Mission
Audit high-quality legal 3D/PBR source assets for Aidan's Home and the Rild village master style. Compare Kenney Fantasy Town Kit, Poly Haven, ambientCG, Quaternius and other verified sources. Prioritize architectural shape, topology, real stone construction, thatch, timber, door/window joinery and life props rather than primitive-only massing.

## Scope and deliverables
1. Read current main AGENTS.md, docs/design/FIELD_VISUAL_OVERHAUL_20261108.md and the current Aidan candidate branch and its PR #295. Do not copy candidate files blindly.
2. Confirm source URLs, exact asset identity, license, redistribution/modification rights, author/attribution, resolution, downloadable maps, dimensions and actual model suitability.
3. Inspect source meshes and materials; propose reusable modular architecture with a consistent coordinate system, anchors, UV/texel density and roof pitch.
4. Produce a ranked, evidence-based asset matrix with rejected candidates and provenance. Clearly distinguish VERIFIED / CANDIDATE / BLOCKED.
5. Define G1-G4 acceptance criteria and artistic QA reference shots at actual game scale.
6. Submit a separate Draft PR with documentation, manifests and reproducible source-processing scripts only. Do not overwrite adopted assets.

## Important blockers
The previously selected Poly Haven IDs were not yet confirmed as textures; ambientCG Ground111 returned HTTP 404 from the test endpoint. Verify before inclusion.
Do not use Pinterest imagery as a copied asset. Do not declare a rendered mesh production-ready without art QA.
Do not modify main, merge, publish, or replace canonical assets.
