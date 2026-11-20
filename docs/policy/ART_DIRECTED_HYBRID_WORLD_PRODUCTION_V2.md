# Art-Directed Hybrid World Production 2.0
Status: DIRECTOR APPROVED production policy, 2026-11-20. Applies to all AI agents and automations. Extends existing approved hybrid production; not canon, asset adoption or runtime release.

## Objective and scheduling
Complete an explorable, coherent high-end world rather than endlessly optimizing one mesh. Run Windwaiting Cliff, Rilde village and Moss forest in parallel after checking existing owners, PRs, assets, official CG and private canon. No region may block independent work in another. Keep one writer per file and existing owning PRs; avoid duplicate jobs/PRs. Park cliff local refinements (preserve E, C12 and rock repair candidates and QA) while evaluating full-scene composition; resume only targeted high-impact issues with evidence. Apply authoritative causal retry v3; do not reset history. Allocate Claude/Codex/ChatGPT/Gemini by demonstrated capability, not fixed assignment; Actions handles reproducible execution. No claim of agent activation without evidence.

## Production systems
- World layout: canonical landmarks, paths, encounter/exploration structure; provisional local origin, axes, scale and transforms documented. No guessed canonical dimensions. Separate provisional assembly from official placement.
- Terrain: heightfields for gentle slopes, meadows and distant terrain; sculpted/precise meshes for hero cliffs, overhangs, fractures. General cliffs use art-directed reusable rock modules and natural joins; distant cliffs use lightweight meshes/baked materials. Avoid uniform noise or repeated stone walls.
- Village: audit existing HOME/BUILD/ROUTE and furniture assets first; Aidan's home as proposed quality master, modular walls, beams, roofs, doors, windows, chimneys, bridges, fences and props according to official CG. Reuse modules with variation, not repeated identical buildings.
- Forest: reusable trees, understory, grass, ferns, moss, fallen wood and rocks; Geometry Nodes or equivalent slope/density/biome masks and deterministic seeds. Exclude roads, buildings, collision corridors. Initial 44 natural asset types (8 trees,10 shrubs/ferns,12 grass/flowers,6 moss/deadwood,8 rocks) are planning candidates, not quotas or canon; prioritize visible MVP needs.
- Water, lighting and VFX: compose complete scenes early, with matched game camera and art-directed palette; protect traversal and readability.
- Asset library: Blender Asset Browser or equivalent indexed reusable models, materials, pivots, scale, collision, LOD, provenance, license, source hash and approval status. Use CC0/appropriately licensed scans and PBR (e.g. Poly Haven, ambientCG) after individual license and style checks. Sculpt hero assets; evaluate trim sheets, atlases, instancing and glTF/GLB. Study Houdini procedural/modular world methods without requiring purchase or engine migration. Existing Blender/Actions first; use approved versions and pinned hashes. Validate runtime capabilities before adopting specific optimizations.

## Execution order
1. Inventory current main, private canon, approved CG, owning PRs/HEAD, assets/QA/failed methods. Reuse compatible outputs. Inventory must not become a repeated report-only task.
2. Establish shared asset library and minimal scene/export contracts, with a real reusable asset and render as proof.
3. Independently start village building kit/master, forest biome sample and cliff scene composition; each produces editable Blender source and actual renders. Different region work can proceed before cliff G2 passes.
4. Compose a provisional playable slice per region and connect only where canonical coordinate/route contracts permit. Check collision, slope, road/bridge joins, camera, traversal and existing game behavior early in a segregated test environment; do not replace shipped game.
5. Prioritize scene-level art QA at actual camera/display size; focus detailed sculpt effort on hero features and defects visible in gameplay.
6. Optimize measured WebGL/Android frame time, memory, draw calls, load and LOD; verify G1–G4 separately. No invented performance budgets; establish baseline and test on actual target devices.

## Quality and progress
Quality bar remains unchanged; scope can be reduced, not adopted asset quality. Track completed validated assets, reusable asset utilization, explorable area, scene art QA, runtime performance and total cost/time to acceptance; PR/CI/vertex count is not progress. Use matched cameras, actual models, independent structural/art QA and shared authenticated artifact ZIP with SHA manifest. No formal adoption until G1–G4 PASS and required explicit approval. Do not merge unfinished assets, alter canon, delete originals, publish or incur cost without approval. Unknown canon-dependent tasks BLOCKED, independent work continues. This later policy changes scheduling/production strategy only; authoritative retry v3 and safety gates stay intact.

## Immediate workstreams
Cliff: PR #421, verify current state, preserve E/C12/rock candidates, move to complete provisional scene evaluation instead of more isolated iterations.
Village and forest: identify existing owners/branches and reusable HOME/BUILD/ECO/ROUTE assets; start safe independent production on corresponding existing PRs. If none can safely own an independent stage, document reason before creating a new PR. Do not invent PR IDs or claim work has started.
