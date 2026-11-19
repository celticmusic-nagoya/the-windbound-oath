# LIND PARALLEL WORLD PRODUCTION v1 — coordination design (NOT CANON)

Status: PRODUCTION PLAN; no external agent launched, director-approved world-map image adopted 2026-11-16; no canon overwritten. Coordinator: ChatGPT; producers: separate authorized Claude/Codex sessions; executor: GitHub Actions + Blender. Complements Draft PR #332 character team without altering its scope.

## Source-of-truth and protected interfaces
At every task start read main AGENTS.md and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md; read the **current main** private handoff repo's reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md, CANON_ADDENDUM.md, CANON_STATUS.md. Do not copy private lore verbatim into public repo. **NEW MASTER SOURCE PRIORITY (supersedes legacy map):** director-approved 2026-11-16 coastal world-map illustration, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620` (binary not yet committed); private handoff `reference/lore/WORLD_MAP_CANON_20261108.md`; formally approved event CGs and current story. See `LIND_3D_WORLD_MASTER_APPROVED_20261116.md` and `LIND_WORLD_REBUILD_SOURCE_PRIORITY_V1.md`. Legacy `リルド村RPGアセット全体マップ.png`, old 15 anchor pixel overlay, DOM field coordinates and screenshots are **excluded as layout authority**. CG/source provenance and SHA verification required before G1 PASS.

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
S0 register director-approved world-map PNG unchanged in GitHub, inventory approved event CG and scripts, reconcile adopted world geography and scene anchors; explicitly exclude old playable map geometry; no inferred positions. S1 lock reviewed L0 spatial/interface JSON and camera; **director approves** spatial contract. S2 WORLD and HOME in parallel, STORY read-only; ECO starts on locked terrain zones; BUILD starts after HOME interface, but its research can run now. S3 independent QA each package, no unverified PASS; S4 INTEGRATION assembles only compatible reviewed candidates, scene turntable and event shots; S5 runtime integration only after separate approval and Android QA. The full village is one coherent world, not a collage of unrelated isolated assets.

## Acceptance criteria
G1: map/CG/script/canon visual concordance; no private canon leakage.
G2: independent art review for proportions, silhouette, material coherence, lived-in details, composition, close-up and 48/96px.
G3: deterministic Blender run, source SHA unchanged, correct normals/UV/alpha, dimensions, render hashes, PNG evidence and resource limits.
G4: event and save compatibility, movement/door/collision/visibility, performance on Android; no game-code change before approval.
Any unknown source or unrun gate -> BLOCKED or NOT_RUN. CI PASS != G2. Two failures of same root cause and method family -> switch structurally, preserve ledger. No main merge, destructive deletion, accepted source overwrite or publication without explicit approval.

## Initial independently useful tasks
1. COORD+STORY: build a **read-only** provenance table of every village map, approved CG, event scene, script and event anchor, including status and SHA; separate canon from reference and draft.
2. WORLD: survey the director-approved 2026-11-16 world-map illustration, adopted geography and event CG terrain/water reference sheets; propose coordinates and elevation without locking them.
3. HOME: survey all accepted Aidan-home CG, house references, door/interior event shots, and prior failed building/masonry candidates; produce interface/spec and design QA rubric, no speculative art.
4. ECO: survey approved flora/crops and current grass failure ledger, then create candidate-only modular production plan.
5. INTEGRATION: stabilize isolated Blender technical render pipeline; do not claim real render PASS until logs and PNG are checked.

## Session handoff
Claude WORLD: "Read current main AGENTS.md, causal retry policy, private canon current main, and docs/production/LIND_PARALLEL_WORLD_TEAM_V1.md on Draft PR #338. Audit official village map and reference images. Work only on a dedicated candidate branch; propose L0 terrain/water anchors and cite source hashes. Do not infer unknown positions, merge main or adopt assets."
Claude HOME: "Same policies and team spec. Audit Aidan home official art, CG, event doors, prior masonry QA; create complete-quality architecture module contract and isolated candidate plan. Never substitute cube mockups for final art."
Codex STORY: "Same policies and team spec. Read-only audit village prologue scenes, CG references, event IDs, door/bridge/training triggers and save hooks. Output provenance matrix and spatial anchors with verified vs unresolved distinctions. Do not modify game logic."
Codex INTEGRATION: "Same policies and team spec. Verify AI render loop CI/Artifacts, maintain source hashes and safe numerical patching, define L0 import/scene assembly QA. No main merge, release or G2 self-approval."

## 2026-11-16 team audit
- COORD: source policy and spatial approvals; ensure original image is registered before distributing immutable source references.
- WORLD: new coastal/river geography and two separate cliffs; no old DOM terrain reuse.
- HOME: modular finished-quality architecture; independent of terrain while footprint not locked.
- BUILD: building material and scale interfaces from HOME; research can proceed before its G2 PASS.
- ECO: north farmland, southwest coastal vegetation, southeast forest; wind motion independent from water flow.
- STORY: explicit two-cliff event distinction; raid jump -> downstream landing; CG camera and scene IDs.
- INTEGRATION: Actions technical PASS is pipeline-only, not art or world model PASS; no legacy geometry as a new spatial source.
- QA: independent source, artistic, technical, Android/gameplay gates. No self-approval.
- All agent lanes remain **ASSIGNED_LOGICALLY_NOT_LAUNCHED** until independent sessions are actually connected and run.
