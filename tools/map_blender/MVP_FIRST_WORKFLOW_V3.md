# MVP-FIRST BLENDER WORKFLOW v3.0 (proposal)

Status: PROPOSED. Does not supersede approved character sheets, canonical map topology, event CGs or asset originals. Scope: provisional Morwen and initial map prototypes only.

## Priority
Deliver a playable provisional character and a one-screen test map before production-grade mesh or art refinement. A provisional PASS never authorizes replacing canonical art.

## Four rules
1. **Blockout/reuse first:** Use primitives or licensed base meshes with provenance recorded. No manual vertex-by-vertex sculpting during MVP. Produce a render and in-game provisional placement within one workday when the existing runtime supports it.
2. **Phase-gated QA:** Phase 1 provisional PASS = visible head, torso, limbs, four identifiable views, distinguishable palette, and valid export. For maps = five or fewer prototype modules, traversable test screen, correct collision/occlusion and topology constraints. Phase 2 art QA only after actual walking/battle or traversal works. Technical failures remain failures, never relabel as art PASS.
3. **Small modular maps:** One ground tile, one wall/step module, two or three landmark modules. Instance them into one test screen. Avoid full-scene re-sculpting.
4. **Timebox:** Each task 30 minutes (maximum 60). At the deadline export, render or place the current candidate, record defects and move on. Two similar failed attempts maximum; switch approach rather than retry.

## 30-minute first task: Morwen blockout
- 00–05: Locate the approved Morwen reference and an existing Layer 0/base mesh; protect originals. If missing, use Blender primitives.
- 05–15: Assemble head, torso, two arms, two legs; coarse proportions and 3–5 color regions only. Do not sculpt anatomy or accessories.
- 15–22: Orthographic front/back/left/right captures with stable ground anchor; export a temporary GLB or PNG as supported by the game.
- 22–27: Place provisional model in a noncanonical test screen (or export for immediate placement if runtime adapter absent).
- 27–30: Record visible silhouette, facing, scale, and export status. Mark unverified items NOT_RUN. Stop at 30 minutes.

## Next 30-minute task: one-screen map
- 00–10: Build/reuse ground, wall/step, tree, rock, landmark (5 modules).
- 10–20: Instance modules on a one-screen grid consistent with MAP21 topology; never replace production map.
- 20–25: Place provisional player; test camera, collision, visibility.
- 25–30: Capture desktop/mobile-size previews, record PASS/FAIL/NOT_RUN, stop.

## Release gates
- Prototype PASS: technically usable and identifiable in-game; art differences documented, not blocking.
- Production PASS: canonical design, event CG parity, visual polish, runtime regressions and mobile QA verified independently.
- Never auto-merge or publish. Preserve originals, SHA checks and approved asymmetry.
