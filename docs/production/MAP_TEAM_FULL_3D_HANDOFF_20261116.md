# MAP DEVELOPMENT HANDOFF — FULL 3D INTEGRATION — 2026-11-16

**To:** Map/world development chat (WORLD/HOME/BUILD/ECO/INTEGRATION).
**From:** Character asset development chat.
**Status:** HANDOFF / NON-CANONICAL; no map asset, scene or runtime modification.

## Director-approved change
The game's entire graphics presentation is to be renewed with high-quality 3D character AND 3D world/map assets. The former ~2.8-head field-sprite target and 2.5D map are no longer the desired final production direction. Existing assets, movement/collision JSON, SAVE and game behavior must remain intact until an approved and verified 3D migration. Do not treat this decision as approval of any particular Blender candidate, camera, metric scale, WebGL engine or 3D model.

## Authority / read order
1. Current `main:AGENTS.md`, `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md` and latest explicit director decisions.
2. Private canon main official bible/addenda/status (only if authorized; otherwise canon-dependent work BLOCKED).
3. Map branch `feature/lind-agent-blender-handoff-01`: `HANDOFF.md`, `Blender.md`, `docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md`, `docs/production/LIND_BROWSER_RENDERER_FEASIBILITY_20261116.md`, `docs/production/CHARACTER_ENVIRONMENT_SHARED_HANDOFF_20261116.md`.
4. Character branch `feature/morwen-fable-eval-01`: `docs/production/CHARACTER_FIELD_SHARED_CONTRACT_20261116.md`, `tools/character_blender/validate_character_world_bridge.py` and `test_character_world_bridge.py`.

## Ownership boundary
- MAP owns WORLD/HOME/BUILD/ECO 3D geometry, terrain, water, buildings, materials, environmental VFX, world reference hashes, scene metric approvals and world G1–G4.
- CHARACTER owns Morwen/Aidan/Fiona/other character canonical refs, geometry, rig, animations, render provenance and character G1–G4. Character production continues separately.
- INTEGRATION owns a jointly approved interface; neither lane may silently change the other's source, SHA, scene collection or QA verdict.
- Map source `assets/sources/lind-world-20261116/original.png`, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620` is **world-only**, never a character reference SHA.

## Cross-team contract to settle BEFORE game integration
1. World coordinates, origin, units, transform and character nominal height; **do not infer metric distances from illustration**.
2. Approved camera/projection and field framing, camera-relative facing mapping, movement state/animation mapping.
3. Ground height and character foot contact/pivot, terrain normals, shadow origin and lighting/color management.
4. Bridges, cliffs, roofs, vegetation and props: depth ordering, occlusion and collision/navmesh relationships.
5. Runtime renderer choice and asset exchange (e.g. glTF candidate), LOD/texture/memory budgets, Android Chrome profiling and fallback; **no renderer selected yet**.
6. Adapter to existing DOM movement, JSON height/collision, events, SAVE/CONTINUE, UI and touch controls via isolated feature flag. No direct replacement before G4.

## Reproducibility / QA
- Shared process: input SHA-256, source commit, Blender version, dependency pins, deterministic seed, camera/render settings, license metadata, output SHA, QA reports and cumulative failure ledger.
- Do not force Blender version equivalence: map baseline 4.0.2; Morwen technical lane `bpy==5.3.0`. Cross-version compatibility NOT_RUN.
- G1 canonical/provenance, G2 independent visual art, G3 technical Blender/runtime, G4 game/Android. All independently PASS before final adoption.
- Retry policy: two failed attempts of the **same root cause/method family** stop that method; diagnose and switch structurally, preserving cumulative history.
- Existing map Draft PRs and candidates must be inspected before any edits; do not overwrite them.

## Current verified scope / blockers
- Map source-review CI previously reported PASS for source-review only, **not finished world geometry**.
- Character branch has candidate-only Morwen four-view renderer and a fail-closed 3D bridge contract validator, wired into Draft PR #339; **new workflow run/artifact not confirmed**.
- Character G1 is BLOCKED due to unresolved provenance/precedence between main v5.61 reference JPEG SHA `47d58cbe...` and later 2026-11-16 five-file sheet SHA `d9730dad...`. Do not assume character art is ready for scene placement.
- Camera, physical scale, renderer, collision/occlusion adapter and Android budgets are NOT_APPROVED / NOT_RUN. No game integration or main merge.
- Existing 2.8-head and 2.5D designs remain historical/rollback sources, not current final art targets.

## Requested MAP-team next tasks
1. Audit the latest map branches, PRs, existing Blender scene/render artifacts and failure ledger. Identify authoritative world source and actual successful render evidence.
2. Prepare a **candidate** 3D world↔character interface proposal with explicit unresolved fields (do not fabricate meters, camera, renderer or performance).
3. Compare feasible browser 3D runtime architectures against the current DOM/JSON game and Android constraints; benchmark only in an isolated feature branch.
4. Return to character team the proposed coordinate/scale, projection, ground-contact/shadow, occlusion and animation-facing conventions for review. Record QA and evidence separately.

**Safety:** no existing official asset overwrite, destructive deletion, main merge or publication without explicit director approval. A handoff document does not initiate another AI session.
