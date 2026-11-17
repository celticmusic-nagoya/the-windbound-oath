# TWO AI-assisted 3D production: evidence-first audit (2026-11-17)

Status: RESEARCH / NOT APPROVED FOR PRODUCTION. No canon, asset, CI, game or deployment modifications.

## Verified baseline
- Read main AGENTS.md on 2026-11-17. It requires canon protection, SHA preservation, causal retry v2 and G1-G4.
- main-root HANDOFF.md and Blender.md returned 404; this does **not** establish absence elsewhere.
- main AGENTS.md contains historical 2D guidance. The newer full-3D decision must be reconciled against authoritative handoff and latest main before implementing.
- Private lore source is NOT verified in this audit. All lore/design-dependent work is BLOCKED pending source verification.
- No current Actions, artifact contents, existing PR inventory, or production render was verified in this audit.

## Research leads (evaluate, not automatically adopt)
1. Blender official manual: https://docs.blender.org/manual/en/latest/ — geometry nodes, mesh, UV, animation, rendering.
2. Khronos glTF: https://www.khronos.org/gltf/ — asset interchange and validation.
3. Three.js docs: https://threejs.org/docs/ — browser 3D integration, rendering and performance.
4. Epic PCG docs: https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-in-unreal-engine — procedural world design reference; **not** an engine migration decision.
5. https://3dnchu.com/ — discovery only; confirm primary sources, version compatibility and licenses.
6. AI 3D services (Meshy, Tripo, Hunyuan3D): evaluate outputs, license, privacy, cost, topology and reproducibility; no automatic canon adoption.

## Acceptance matrix
| Stage | Deliverable | Exit condition |
|---|---|---|
| Inventory | main HEAD, relevant branches/PRs, canonical files and SHA256, CI workflow and failure ledger | all source references verified, conflicts documented |
| Tool feasibility | reproducible Blender version, scripts, input manifest, licensing ledger | headless render and saved blend reopen; reproducible output |
| Art feasibility | one approved representative character part and one environment piece | G1 canon match, independent G2 art review, G3 geometry/UV/material verification |
| Runtime feasibility | optimized GLB and test scene | G4 WebGL and Android measurements incl. FPS, memory, load time, visual regression |
| Automation | read-only audit and scoped non-destructive CI in Draft PR | evidence artifacts, timeout/retry budget, immutable inputs, no self-merging |

## Production method
Official 2D/turnaround references -> visual specification -> AI candidate or licensed base mesh (as appropriate) -> controlled sculpt/retopo -> UV/PBR -> rig/animation where relevant -> master blend -> optimized glTF/GLB -> independent art and technical QA -> runtime QA.

Keep master/high-poly and runtime assets separate. A rendered PNG alone cannot prove 3D quality. Reject unlicensed inputs and unidentified provenance. Avoid primitive-only final assets. For same defect/method, stop after two failed substantive attempts and document a structurally different approach.

## Parallel ownership
- Character: face/hair/costume/rig; own paths only.
- Environment: building/stone/terrain/vegetation; own paths only.
- Runtime: GLB loader, lighting, controls and Android performance; own paths only.
- Independent QA: read-only review of all streams.
Integrate through non-overlapping branches and Draft PRs. Do not assert agents or CI are running unless execution is observed.

## Gates (current)
G1 BLOCKED (private canon and full-3D authority not verified); G2 NOT_RUN; G3 NOT_RUN; G4 NOT_RUN.

## Next safe execution
1. Locate current full-3D handoff, canonical source, current HEAD and existing PRs/workflows.
2. Record SHA256 for authoritative inputs; reconcile historical 2D instructions.
3. Inspect latest character/environment failures to choose *one* bounded technique experiment each.
4. Build read-only CI audit and run with artifacts; only then enable narrowly scoped generation on a Draft PR.
5. No main merge, canon replacement, destructive deletion or publication without explicit approval.

## Follow-up evidence: source-level environment audit (2026-11-17)

Verified by reading the **actual branch files**, not by assuming a workflow ran:

- `feature/morwen-fable-eval-01:docs/production/MAP_TEAM_FULL_3D_HANDOFF_20261116.md` (blob `9e9064c4504673f05beb08b5852ed8271a80a932`): director-approved full-3D final direction; old 2.8-head/2.5D presentation retained only as legacy/rollback until verified migration. The handoff itself is NON-CANONICAL and does not approve camera, scale or renderer.
- `feature/lind-agent-blender-handoff-01:HANDOFF.md` (blob `0ae037b1c742392cb133c3f923be12623e62085c`) and `Blender.md` (blob `cf2caa26bf609e5d0ccc02b04b19fee3159572a3`) were FOUND. Their main-root 404s were branch/path differences, not evidence of deletion.
- Map Blender CI base specified as Ubuntu 24.04 + Blender 4.0.2; cited source-review run `43848242090`. This is **documented historical evidence**, not an independently fetched run/artifact in this audit. Source-review creates semantic placeholders, NOT completed world meshes.
- Map world reference: `assets/sources/lind-world-20261116/original.png` at pinned commit `dc17dd4846f35ea1f5dea25168eec9ddb50a3838`; declared SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`. Binary hash was **not** independently recomputed here.
- `docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md` (blob `70ca60f6d1410f5932d0c444036aaf490ca25266`) defines distinct WORLD/HOME/BUILD/ECO collections and null physical metrics until approval. Never turn the semantic graph into invented world coordinates.
- `docs/production/LIND_BROWSER_RENDERER_FEASIBILITY_20261116.md` (blob `ee213c4ca96877da5d4ddc91a1683e8cb7f4b599`) finds existing DOM camera/JSON collision. Offline Blender rendered layers are an initial compatibility candidate; interactive 3D requires an isolated WebGL/WebGPU benchmark and architectural approval.
- Main `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md` (blob `ae4edc35a4250dbb08cab9ea8187cbee357d764a`) confirms two failures per *same defect/method family*, with structural method switching, not project-wide termination.
- Map/character Blender version mismatch is documented (map 4.0.2, character lane bpy 5.3.0); cross-version compatibility NOT_RUN.
- Existing PR #344, #345, #346, #339 are referenced by handoffs; their live state and artifacts have not been checked. Do not overwrite them.

### Resulting implementation decision
**Do not deploy a new renderer or modify existing game movement.** First verify reference bytes, private canon and current PR/CI state. Then produce a non-runtime export contract and negative tests in this research branch, with no invented dimensions. The initial browser rendering choice is still OPEN: baked layers vs genuine 3D must be benchmarked against Android device constraints.

### Updated gates
G1 BLOCKED (private canon + reference binary + metric/camera approval); G2 NOT_RUN; G3 NOT_RUN for actual production geometry (source-review evidence documented); G4 NOT_RUN. No real Blender render or Android execution in this follow-up.
