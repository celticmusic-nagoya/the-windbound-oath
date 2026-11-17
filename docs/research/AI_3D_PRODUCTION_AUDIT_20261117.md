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
