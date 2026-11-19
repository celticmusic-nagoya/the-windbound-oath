# LIND new-world implementation handoff — ChatGPT lane (2026-11-16)

**Status:** NON-DESTRUCTIVE DESIGN PREPARATION; no new 3D world mesh claimed. Claude is temporarily unavailable. Avoid duplicating Claude WORLD/HOME/BUILD/ECO branch work or PR #345 repairs.

## Immutable inputs
- Director-approved PNG: `assets/sources/lind-world-20261116/original.png`, source commit `dc17dd4846f35ea1f5dea25168eec9ddb50a3838`, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`, registered in Draft PR #344.
- Private world geography: `the-windbound-oath-handoff/main/reference/lore/WORLD_MAP_CANON_20261108.md`; approved event CG provenance PR #340. Do not expose private lore text.
- PR #345 isolates legacy assembler, pins Actions Blender and repairs SAVE fixture. Do not reimplement these fixes.

## Spatial topology, not metric placement
- Center: village residential/storage hub.
- West/northwest: **Windward Cliffs** (sunset/stargazing), ocean-facing.
- Southwest: small fishing harbor/inlet.
- North: farmland and Dunvall road exit.
- East: north-to-south river, bridge and a **separate raid riverside cliff**.
- Southeast/downstream: landing -> Moss Forest -> ancient altar.
- The raid cliff and Windward Cliffs are different sites. The raid cliff to downstream landing is a **story transition**, not an ordinary walkable path.
- World coordinates, origin, unit scale, elevations, camera and final footprints remain `null/BLOCKED`. Illustrated scale bar is not a metric source. Do not use old 15 pixel anchors, DOM coordinates or legacy map assembler as a new-world spatial source.

## Concrete independent tasks available without Claude
1. **STORY / Codex**: read-only verify actual event CG view angles and camera transitions against the adopted image; report every evidence path, hash and unresolved camera axis. Never infer camera-space north from map illustration.
2. **INTEGRATION / Codex**: implement a standalone `new-world-topology` validator for named nodes, directed transitions, separate cliffs and null metric fields; use isolated tests, not game runtime changes. Keep PR #345 unchanged.
3. **COORD / ChatGPT**: reconcile Claude candidate branch outputs once pushed; verify they use the approved source SHA, material/scale contracts and no legacy coordinates. Create an issue list for G1 blockers rather than silently filling gaps.
4. **QA**: independently verify semantic graph, source hash, event IDs and existing SAVE regression tests. G2 art and G4 Android remain NOT_RUN until relevant actual assets/runtime exist.

## Production guardrails
- New scene is modular: terrain/coast/water, hero house, other buildings, ecology, story cameras and render/integration adapters. Final geometry requires real art QA; no cube mockups accepted as final.
- G1 source registration PASS; G1 full spatial/event concordance BLOCKED; G2/G3 new world NOT_RUN; G4 world/Android NOT_RUN.
- Do not merge main, replace adopted assets, publish or mark candidate art accepted. Keep Claude's branches and the #344/#345 PRs intact.
