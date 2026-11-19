# FULL3D-INTERFACE-v3.4 — CHARACTER ↔ MAP ↔ INTEGRATION

## 2026-11-19 interpretation — independent production vs integration
This document is a **historical candidate cross-team integration contract**, not an independent-asset production gate. Following the director-approved 2026-11-18 provisional-local-coordinate policy, CHARACTER and MAP may create editable Blender assets and render/QA them using documented provisional local origin, axes, scale and transforms. `BLOCKED_UNAPPROVED` and null fields in this candidate contract apply to **approved shared world metrics, scene placement, joint camera/ground interfaces and game integration**, not to the independent asset's internal provisional modeling coordinates. Do not misrepresent provisional values as approved world values, or change the candidate schema to bypass validation. Use the current shared Blender 5.2.4 infrastructure where applicable; the older 4.0.2/5.3.0 notes below are historical evidence, not current prescribed versions. G1–G4 all PASS is required for formal integrated adoption; independent G2/G3 can progress while G4 is NOT_RUN.

**Status: CANDIDATE / NON-CANONICAL / CONTRACT-ONLY.** No 3D renderer, camera, metric scale, character design, world geometry, engine, or budget is approved by this document. Do not infer approval from a passing schema or CI.

## Source reconciliation (read-only, 2026-11-17)
- Current main `AGENTS.md` and `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`.
- `feature/morwen-fable-eval-01:docs/production/CHARACTER_FIELD_SHARED_CONTRACT_20261116.md`.
- `feature/lind-agent-blender-handoff-01:HANDOFF.md`, `Blender.md`, `docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md`, `docs/production/CHARACTER_ENVIRONMENT_SHARED_HANDOFF_20261116.md`, `docs/production/LIND_BROWSER_RENDERER_FEASIBILITY_20261116.md`.
- Later director approval: high-quality full-3D character and world art is the final production direction. Existing 2D runtime remains protected as a rollback baseline until verified migration.

## Ownership and non-overlap
| Lane | Owns | Must not change |
| --- | --- | --- |
| CHARACTER | canonical character source provenance, geometry, rigs, animation, exported character candidates | MAP source, environment collections, scene metrics |
| WORLD/HOME/BUILD/ECO | terrain, houses, other buildings, ecology, water and their own Blender collections | CHARACTER design or rig, unrelated lane collections |
| INTEGRATION | proposed scene/coordinate/export/runtime interface, compatibility adapter, combined QA | canonical source, either lane's production geometry without approval |
| INDEPENDENT QA | source/art/technical/game gate evidence | falsely elevate candidates to approved art |

## Contract decision register
| Field | Current state | Required evidence / decision |
| --- | --- | --- |
| World origin, axes and units | BLOCKED_UNAPPROVED | joint CHARACTER+MAP decision, Blender transform evidence |
| Character nominal height, proportions | DESIGN TARGET 7.5–8 heads, not metric | character-specific canonical reference and director-approved measurements |
| Camera projection, field framing, facing map | BLOCKED_UNAPPROVED | comparative candidate captures, approved framing and input mapping |
| Foot pivot, ground height, terrain normal | BLOCKED_UNAPPROVED | measured contact and slope tests |
| Shadow/light/color management | BLOCKED_UNAPPROVED | shared render settings and cross-scene visual tests |
| Bridges/cliffs/roofs occlusion, collision/nav | BLOCKED_UNAPPROVED | explicit topology and runtime mapping |
| Exchange format, renderer/engine, fallback | NOT_DECIDED | isolated WebGL/Android feasibility benchmarks; no engine assumed |
| LOD, texture, draw calls, memory, load budgets | NOT_DECIDED | actual Android Chrome measurements |
| SAVE/CONTINUE, events, touch and accessibility | EXISTING BASELINE PROTECTED | feature-flagged adapter regression tests |

**Important:** The map `LIND_BLENDER_SCENE_INTERFACE_V1.md` intentionally keeps `local_origin`, `bounding_box_m`, `world_transform`, `elevation_reference` null pending metric approval. Do not populate them from illustration pixels. Its proposed collection IDs are not automatically canonical. Map source SHA `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620` is WORLD-only. Character v5.61 reference SHA `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638` and later five-file sheet SHA `d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b` differ; authority reconciliation is G1 BLOCKED.

## Candidate manifest interface (schema proposal, not executable validation)
Each team exports a separately versioned manifest with:
- `contract_version`, `lane`, `asset_id`, `status` (reference/candidate/approved), `source_commit`, `source_hashes`, `output_hashes`, `license_provenance`;
- `blender_version`, `dependencies`, `generator_version`, `seed`, `camera_settings`, `render_settings`;
- `local_origin`, `world_transform`, `bounds`, `projection_id`, `ground_contact`, `shadow_anchor`, `occlusion_contract`, `collision_contract`, `animation_state_map`, `runtime_budget_ref` (null until measured/approved);
- `dependencies_on_lanes`, `qa_gates` (G1/G2/G3/G4: PASS/FAIL/BLOCKED/NOT_RUN), `evidence_paths`, `attempt_ledger_ref`.

This proposed interface must be reconciled with existing validators before implementation; do not silently change `docs/production/LIND_BLENDER_SCENE_INTERFACE_V1.md` or existing manifest schemas.

## Quality gates and exit criteria
1. **G1:** actual canonical bytes/approval and map provenance, plus explicit approved spatial/camera decisions. Currently BLOCKED for cross-team integration.
2. **G2:** independent final-display-size visual review of real character/world renders. NOT_RUN for combined 3D scene.
3. **G3:** pinned Blender build and reopened .blend, object/material integrity, actual render SHA, repeatability, adapter tests. NOT_RUN for combined scene. Map CI 4.0.2 and character bpy 5.3.0 are separate; cross-version parity NOT_RUN.
4. **G4:** game integration and Android device profiling including movement, collision, SAVE, UI, performance and fallback. NOT_RUN.
5. No formal adoption until all four PASS. Two same-root-cause/same-method-family failures stop that family only; preserve ledger and switch method based on a causal hypothesis.

## Next safe tasks (not performed by this document)
1. Jointly review decision register with CHARACTER/MAP; record explicit approvals rather than guessing values.
2. Prepare isolated non-runtime schema/negative tests for null-unapproved values, provenance, cross-lane ownership and SHA validation.
3. Benchmark candidate 3D runtime against current DOM/JSON field system in a separate feature flag before selecting renderer.
4. Capture independent visual and Android QA evidence when actual 3D assets and approved framing exist.

**No GitHub Actions run, Blender execution, render, game modification, or independent QA is claimed here.**
