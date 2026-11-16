# LIND ChatGPT takeover — 2026-11-16

Status: WORK-IN-PROGRESS / NON-CANONICAL. No production asset approval.

## Source and boundaries
- Approved reference: PR #344, commit dc17dd4846f35ea1f5dea25168eec9ddb50a3838, `assets/sources/lind-world-20261116/original.png`.
- Expected source SHA-256: `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`.
- Spatial planning: PR #338; source review workflow successful at run #43848242090.
- Codex's unfinished WORLD lane is PR #346, branch `feature/lind-spatial-codex-01`. Do not alter it or claim its terrain complete.
- Existing Claude masonry and vegetation candidates are separate; do not overwrite.
- This branch is for isolated integration and QA coordination, not canonical replacement.

## Acceptance and dependency contract
1. WORLD provides independent terrain, water, road and story-marker collections. The western/northwestern ocean-facing cliff and the eastern river-raid cliff MUST be distinct. The southwest fishing inlet is distinct from the river. The southeast landing follows the one-way story jump.
2. HOME is a separately owned hero asset, not regenerated as a terrain primitive. WORLD may reserve a non-metric interface but must not bake HOME into terrain.
3. BUILD and ECO own their source geometry and materials. Integration may instance only verified assets, retaining provenance, version, and transforms. No geometry rewrite.
4. All world-space coordinates, scale, collision dimensions, navmesh and camera framing remain CANDIDATE until explicit metric approval. Never derive metric coordinates from illustration pixels or legacy DOM anchors.
5. Reference image SHA must be verified before build. Output artifacts must record Blender version, inputs, code commit, seed where applicable, render settings and SHA-256.
6. Technical QA must separately verify topology, object/collection ownership, source provenance, no unintended overwrites, water connectivity and directional story transitions. Art QA must inspect silhouette, material fidelity and final game display size. CI alone cannot pass G2.
7. G1 BLOCKED until current private canon and event CG align with actual geometry. G2 NOT_RUN until actual rendered terrain. G3 SOURCE_REVIEW_PASS only (not terrain geometry). G4 NOT_RUN until game integration and Android device test.

## Conflict prevention
- Never edit Codex PR #346 or Claude branches.
- Do not merge main, replace approved assets, delete old materials, or publish.
- Before taking over WORLD geometry, inspect Codex's latest branch and reuse valid work. A paused agent is not evidence of a failed build.
- If no complete WORLD geometry is available, document the missing deliverable; do not substitute the 11 semantic empties for a finished world.

## Next executable gate
1. Inspect PR #346 latest commit and workflow artifacts for actual mesh/render.
2. If no geometry, implement a separate world-build candidate on a fresh branch only after auditing its ownership, without changing this coordination branch's canonical reference.
3. Render and capture before/after plus automated technical tests, then perform independent art review.
