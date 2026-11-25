# TWO high-end 3D production policy v1.1 — Codex and all development agents

Status: DIRECTOR-APPROVED POLICY. Applies repository-wide after merge into main. Existing canon and later director instructions take precedence.

## Scope and target
- Build an explorable, original Celtic/Irish fantasy RPG with consistent high-end art direction. Genshin Impact (color and landscape), NTE (spatial staging), Arknights: Endfield (precision and materials), and NIKKE (character presentation) are quality references only; never copy their protected designs.
- Characters: face, hair, body, clothing, equipment, PBR, rig, animation and QA. Environment/map/architecture belong to a separate team; character agents must not duplicate them.
- The current approved move toward fully 3D is the production target. Protect currently shipped assets until the replacement passes all gates.

## Mandatory startup checks
1. Read current main AGENTS.md, latest official private lore Bible/addenda/status, applicable asset design manifests, source SHA, branch HEAD, open PRs, previous QA, failure ledger, and current handoffs. HANDOFF.md or Blender.md may be absent; record that rather than guessing.
2. Resolve source-of-truth hierarchy: latest explicit director adoption, private canonical documents and addenda, approved asset records, then candidates. A branch, an older prompt or an attractive generated image is not canon.
3. Lock original assets with SHA-256 and retain candidate/reference/experiment separation. Missing canonical source => G1 BLOCKED; do not infer replacements.
4. Assign ownership and avoid conflicts with parallel character and map teams.

## High-end asset execution
1. Define acceptance at intended final game display size, silhouette, dimensions, material response, rig and target hardware before modelling.
2. Compare techniques by artistic quality, repeatability, total effort, cost, license and WebGL/Android compatibility. Consult Blender official references, 3dnchu.com, legal libraries, reputable production breakdowns, GitHub and relevant research. Record citations/licenses; do not use unlicensed assets as official content.
3. Prefer actual art-directed sculpting, authored retopology, UV/PBR, baked textures, authored geometry, Geometry Nodes or legal existing assets as appropriate. Python/CI may automate reproducible work, but procedural primitives or successful scripts alone are not final art.
4. Produce modular character anatomy, face, hair, clothing, accessories; validate front/back/left/right and 3/4 views, occlusion, contact, deformation, motion and visual identity. Do not add noncanonical adornments.
5. Preserve a high-quality editable Blender master separately from optimized WebGL/Android deliverables. Store renders, provenance, SHA, geometry deltas, test outputs and regression comparisons.
6. Independent G2 art QA is distinct from CI/technical screening. A render is not proof of topology, rigging, or gameplay quality.

## Gated acceptance
- G1 canonical identity, reference registration, source hashes.
- G2 sculpt/material/character visual identity and detail.
- G3 topology, dimensions, UV, texture, rig, animation deformation, rendering.
- G4 game integration, performance, touch controls, Android real-device and regressions.
- Record PASS/FAIL/BLOCKED/NOT_RUN per gate; official adoption requires four PASS. Never conflate script execution, CI, render completion and art acceptance.

## Retry and safe autonomy
- Follow [Causal Retry v3](CAUSAL_RETRY_AND_METHOD_SWITCH_V3.md). After two failures with the same cause, reassess the evidence and continue only with a justified bounded correction or method switch. Preserve the cumulative attempt ledger and continue independent work.
- Work on dedicated branches and Draft PRs; do not overwrite canonical originals, delete destructively, merge main, or publish without explicit approval.
- Continue approved non-destructive work autonomously. Do not claim to have invoked an unavailable AI, editor, service, or test.
- Split independent tasks across ChatGPT (specification/independent QA), Codex (Blender/code/CI), optional Claude (review), GitHub Actions (execution/renders/technical QA), respecting actual capabilities and permissions. Use PRs and artifacts for handoffs.

## Current character handoff — Morwen
- Active SCULPT02: PR #407; active SCULPT03: Draft PR #417. Do not start from scratch.
- SCULPT02 editable source: assets/candidates/morwen-sculpt02/morwen_sculpt02_v02_UNAPPROVED.blend; SHA-256 90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b.
- Independent G2 FAIL: realistic face, small eyes, large nose/jaw and helmet-like thick bob. Two same-family Grab/volume corrections failed. SCULPT03 requires structural face quad retopology and rooted layered asymmetric bob.
- SCULPT03 workspace preparation script/CI are **not** finished retopology. Verify Actions execution and artifacts; then perform real geometry editing, 6+6 view renders, wireframes and independent QA.
- Preserve approved Morwen purple bob, glasses, outfit and original design; source check before any work. No environment or map implementation in this character task.

## Reporting contract
1. Files/specs/commits/PRs/actual implementation.
2. Completed QA, NOT_RUN/BLOCKED, regressions and provenance.
3. Next concrete task, actual automation results, blockers and unlock condition.
Prefer links to real .blend, renders and Artifacts over plans. No fabricated results.
