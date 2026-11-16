# LIND PARALLEL WORLD PRODUCTION v1 — coordination design (NOT CANON)

Status: PRODUCTION PLAN; no agent launched, no art adopted, no canon overwritten. Coordinator: ChatGPT; producers: separate authorized Claude/Codex sessions; executor: GitHub Actions + Blender. Complements Draft PR #332 character team without altering its scope.

## Source-of-truth and protected interfaces
At every task start read main AGENTS.md and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md; read the **current main** private handoff repo's reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md, CANON_ADDENDUM.md, CANON_STATUS.md. Do not copy private lore verbatim into public repo. Public canonical village map: docs/art/reference/lind/リルド村RPGアセット全体マップ.png SHA-256 83dd4ad1eb10103fdb7eb569e8b1b22cc92920d4c94d4eae85735125de87fe6c (inventory). Reference images, event CG, scripts, accepted art and current runtime event IDs require direct inspection; never infer exact coordinates or building shape from prose. Map visual comparison and source/scene provenance required before G1 PASS.

Verified village canon: agricultural/livestock settlement; central square, wind rune stone, well, inn, shop, elder home, Aidan home, dwellings, sheds/barns, cattle/pig/chicken buildings, wheat/vegetable/flower fields, apples, hay, river, bridge, waterfall, fishing; separate training ground east across river; wind hill north; elder home/waterfall northwest; farmland/livestock south-southeast. Wind moves vegetation/signs/laundry/leaves; wind-stop halts wind-driven motion but **not water flow**; birds respond. Event staging and existing prologue remain governed by the current canon and approved script.

## Architecture
L0 **spatial contract**: immutable map SHA; orientation, world origin, axes, unit scale, ground plane, elevations, camera type/ortho scale, output sizes, map-to-world transform, walkable nav boundaries, river/bridge crossing, anchor IDs for doors/events, collision, wind state, water state. Unknown values = null/BLOCKED; director reviews before locking. The 2200×1550 DOM field is an implementation prototype, NOT final village geometry.

L1 **landform**: connected terrain, banks, water, bridge footprint, cliffs, slopes and paths.
L2 **architecture**: Aidan home quality master and other village buildings; reusable walls/roofs/doors and trims, nonuniform hand-built silhouette, PBR and UV.
L3 **ecology and livelihood**: plants, fields, fences, livestock and movable props; modular variants under approved seed/LOD rules.
L4 **story and camera**: event CG/scene-to-location matrix, characters and staging, wind-stop and attack/escape routes, light/time-of-day; preserve script and SAVE/event anchors.
L5 **render/export**: unified Blender assembly, identical camera/lighting standards, PNG atlas/billboards if current HTML/JS runtime requires them; Unity only as optional lookdev comparison, not runtime migration.

## Team lanes (logical roles; not automatically running agents)
| Lane | Agent | Exclusive work package | Dependency |
| --- | --- | --- | --- |
| COORD | ChatGPT | reference index, source hashes, task DAG, review decisions, interface changes, no unilateral canon adoption | source access |
| WORLD | Claude session A | master terrain, waterways, bridge approach, elevation/collision contract | L0 spatial G1 |
| HOME | Claude session B | Aidan home finished-quality modular building, interior/exterior threshold, doors and storytelling details | official image/CG and L0 footprints |
| BUILD | Claude session C | inn, shop, elder home, residential/farm structures, architecture kit | HOME material/scale contract |
| ECO | Claude session D | trees, crops, grass, riverside plants, livestock/farm props, wind channels | L0 and WORLD interfaces |
| STORY | Codex session A + script reviewer | event CG mapping, script event IDs, NPC paths, wind-stop state, camera shots; read-only canon | script/CG audit |
| INTEGRATION | Codex session B | manifest validation, asset imports, scene assembly, render loop, HTML/JS event adapter candidate | versioned packages |
| QA | independent Codex or Claude session | G1/G2/G3/G4 evidence and regressions, no self-approval | per-lane outputs |

Sessions and paid API access are **not** created by this document. A single available agent may execute lanes sequentially; parallelism is bounded by available independent sessions.

## No-conflict branch and artifact contract
One lane -> one branch -> one Draft PR -> one immutable candidate package; no two agents edit the same source, main, shared spatial contract or accepted art. Suggested branches: feature/lind-world-01, feature/lind-home-01, feature/lind-buildings-01, feature/lind-ecology-01, feature/lind-story-staging-01, feature/lind-integration-01. **Do not create branches until assigned and current refs inspected.** Outputs under assets/candidates/LIND-<LANE>-<ID>/<candidate-id>/, scripts under tools/map_blender/lind/, evidence under docs/qa/lind/. Each package: task_id, branch, source refs+SHA, accepted-vs-reference-vs-candidate status, Blender version, scripts, seed, material/license inventory, coordinate transform version, camera settings, mesh/UV QA, 4-direction/close-up and final-size PNG, geometry/material budget, method-family attempt ledger, G1–G4.

## Dependency graph and release gates
S0 read official sources and images, inventory CG and scripts, reconcile current map vs scene anchors; no inferred positions. S1 lock reviewed L0 spatial/interface JSON and camera; **director approves** spatial contract. S2 WORLD and HOME in parallel, STORY read-only; ECO starts on locked terrain zones; BUILD starts after HOME interface, but its research can run now. S3 independent QA each package, no unverified PASS; S4 INTEGRATION assembles only compatible reviewed candidates, scene turntable and event shots; S5 runtime integration only after separate approval and Android QA. The full village is one coherent world, not a collage of unrelated isolated assets.

## Acceptance criteria
G1: map/CG/script/canon visual concordance; no private canon leakage.
G2: independent art review for proportions, silhouette, material coherence, lived-in details, composition, close-up and 48/96px.
G3: deterministic Blender run, source SHA unchanged, correct normals/UV/alpha, dimensions, render hashes, PNG evidence and resource limits.
G4: event and save compatibility, movement/door/collision/visibility, performance on Android; no game-code change before approval.
Any unknown source or unrun gate -> BLOCKED or NOT_RUN. CI PASS != G2. Two failures of same root cause and method family -> switch structurally, preserve ledger. No main merge, destructive deletion, accepted source overwrite or publication without explicit approval.

## Initial independently useful tasks
1. COORD+STORY: build a **read-only** provenance table of every village map, approved CG, event scene, script and event anchor, including status and SHA; separate canon from reference and draft.
2. WORLD: survey official map image and terrain/water reference sheets; propose coordinates and elevation without locking them.
3. HOME: survey all accepted Aidan-home CG, house references, door/interior event shots, and prior failed building/masonry candidates; produce interface/spec and design QA rubric, no speculative art.
4. ECO: survey approved flora/crops and current grass failure ledger, then create candidate-only modular production plan.
5. INTEGRATION: stabilize isolated Blender technical render pipeline; do not claim real render PASS until logs and PNG are checked.

## Session handoff
Claude WORLD: "Read current main AGENTS.md, causal retry policy, private canon current main, and docs/production/LIND_PARALLEL_WORLD_TEAM_V1.md on Draft PR #338. Audit official village map and reference images. Work only on a dedicated candidate branch; propose L0 terrain/water anchors and cite source hashes. Do not infer unknown positions, merge main or adopt assets."
Claude HOME: "Same policies and team spec. Audit Aidan home official art, CG, event doors, prior masonry QA; create complete-quality architecture module contract and isolated candidate plan. Never substitute cube mockups for final art."
Codex STORY: "Same policies and team spec. Read-only audit village prologue scenes, CG references, event IDs, door/bridge/training triggers and save hooks. Output provenance matrix and spatial anchors with verified vs unresolved distinctions. Do not modify game logic."
Codex INTEGRATION: "Same policies and team spec. Verify AI render loop CI/Artifacts, maintain source hashes and safe numerical patching, define L0 import/scene assembly QA. No main merge, release or G2 self-approval."
