# LIND village world integration plan 01 — non-destructive Phase 1

**Status: DESIGN CANDIDATE / NOT A WORLD MESH.** Owner: ChatGPT INTEGRATION lane. WORLD terrain owner remains separate. No runtime/approved source changes.

## Verified source hierarchy
- Current main AGENTS.md and docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md.
- Map branch HANDOFF.md / Blender.md and docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md.
- Immutable world illustration assets/sources/lind-world-20261116/original.png, SHA-256 abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620.
- docs/production/lind-new-world-topology.v1.json is **proposed**; semantic routes not approved.
- Official lore lives in private handoff repo and must be verified before canon-dependent placement.

## Phase 1: geography and spatial integration, without placeholder art
1. WORLD: audit existing WORLD PR #346 and actual source geometry/artifacts before starting any terrain generation. Preserve all existing world candidates.
2. INTEGRATION: freeze a semantic region list from verified graph only; do not infer geographic distances from illustration. Existing geography distinctions: western/northwestern ocean cliff; separate eastern river raid cliff; southwest fishing inlet; northern farmland/road to Dunvall; southeast downstream landing. The east cliff -> downstream landing transition is a **directed story jump, not walkable navigation**. East training area placement remains REVIEW_REQUIRED.
3. HOME: existing Aidan house is independently authored; its footprint, scene transform and approval are **unresolved**. Do not reconstruct or resize without source QA.
4. BUILD: bridge masonry is Codex-owned in separate ROUTE-MAT-01 Method C lane; do not edit, regenerate or merge its files here.
5. ECO: vegetation, ground cover and water effects depend on WORLD exclusion masks and actual terrain. Avoid placing vegetation into paths, buildings, river and story clearances.
6. CHARACTER: request shared height/foot pivot/camera-facing and shadow/occlusion interface from character team; no automatic world scale derived from character illustration.

## Spatial contract decision table
| Field | Current value | Gate to resolve |
| --- | --- | --- |
| world unit/meters | null / BLOCKED | approved physical scale and reference measurement |
| scene origin | null / BLOCKED | map + character integration agreement |
| world transform / bounding boxes | null / BLOCKED | actual terrain and approved scale |
| house footprint | null / BLOCKED | approved HOME model and scene scale |
| camera projection and framing | null / BLOCKED | joint map/character camera decision |
| character nominal height | null / BLOCKED | character team reference/approval |
| terrain ground contact | null / BLOCKED | WORLD mesh and character pivot |
| bridge and cliff occlusion | not validated | actual meshes and depth tests |
| runtime renderer | not selected | separate WebGL/DOM feasibility benchmark |
| Android budget | not measured | device profiling |

## Candidate collection boundaries
- LIND_TERRAIN (WORLD); LIND_WATER (WORLD/ECO); LIND_ROADS (WORLD)
- LIND_HERO_HOME (HOME); LIND_BUILDINGS (BUILD); LIND_ECOLOGY (ECO)
- LIND_STORY_MARKERS (INTEGRATION)
These are interface proposals, not completed objects or adopted coordinates. Each lane provides immutable input hashes, provenance, local transform null until approved, exclusions, and reproducible output manifest.

## Work sequencing / non-overlap
**Now, independently of Codex:** validate source hash and semantic topology; inventory existing world meshes, source CG, Draft PRs, CI and failure ledger; record blocked coordinate decisions. Do not start primitive terrain blockout as final art.

**After metric and source reconciliation:** build terrain and river/water corridor in WORLD, with actual authored terrain shape, navigable land, riverbank, ocean cliff and inlet, while HOME/BUILD/ECO retain separate collections. Then perform clay 3-view art QA before applying PBR and vegetation. Existing bridge Method C can later be linked as candidate, never copied into this lane.

**After camera/renderer agreement:** choose Blender-authored offline layers vs measured real-time 3D renderer; implement an isolated adapter with existing DOM movement/JSON collision/SAVE untouched until G4.

## QA
G1 BLOCKED: private canon and scale/footprint/camera reconciliation.
G2 NOT_RUN: actual village geometry and independent final-display-size art review.
G3 NOT_RUN: production terrain, UV, navmesh/occlusion and full scene reopen; source-review CI does not qualify.
G4 NOT_RUN: browser integration, collision, SAVE and Android performance.
Stop after two ineffective same-root-cause attempts; switch actual mechanism, preserve evidence. No main merge, destructive cleanup or publication.
