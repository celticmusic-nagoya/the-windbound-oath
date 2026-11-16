# LIND ↔ CHARACTER full-3D integration interface v0.1 (CANDIDATE)

**2026-11-16 | Proposed interface only | G1 BLOCKED, G2 NOT_RUN, G3 NOT_RUN, G4 NOT_RUN**

## Authority and supersession
- Director's later full-3D decision supersedes the former 2.8-head sprite / 2.5D map *future production targets*. Historical assets and existing runtime remain protected.
- Character-team source: `feature/morwen-fable-eval-01:docs/production/MAP_TEAM_FULL_3D_HANDOFF_20261116.md` and `CHARACTER_FIELD_SHARED_CONTRACT_20261116.md`.
- Read latest `main:AGENTS.md` and private canon main/addenda/status before canonical geography work.
- `HANDOFF.md` and `Blender.md` currently exist on the map feature branch, **not main**; do not falsely claim main has the shared contract.
- World visual reference SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620` is WORLD-only, not a metric source.

## Shared interface proposal — fields requiring cross-team approval
| Property | Proposal / status | Producer / reviewer |
| --- | --- | --- |
| Coordinate handedness, up axis, forward axis | UNDECIDED; candidate glTF-compatible Y-up export, Blender Z-up authoring, with explicit transforms | WORLD + CHARACTER + INTEGRATION |
| World unit scale, origin and geographic placement | BLOCKED; never infer meters from village painting or DOM pixels | WORLD + director |
| Character height and physical collision capsule | BLOCKED; measure from approved model and actual gameplay design | CHARACTER + INTEGRATION |
| Camera projection, FOV, framing and movement-relative facing | BLOCKED; preserve current camera behavior until 3D proposal is reviewed | WORLD + CHARACTER |
| Ground sample, foot bone/pivot and terrain normal | Candidate `ground_query(world_position) -> height, normal, surface_id`; no assumed values | WORLD provides, CHARACTER consumes |
| Root motion, movement authority and animation states | Candidate game logic owns movement, animation follows; SAVE stores gameplay state, not raw engine objects | INTEGRATION + CHARACTER |
| Shadow contact, directional light and color management | BLOCKED pending common render comparison; no baked/dynamic shadow double counting | WORLD + CHARACTER |
| Bridge/cliff/roof occlusion, navigation, collision | Explicit 3D depth test and gameplay collision agreement; river raid jump remains story-only | WORLD + INTEGRATION |
| Mesh/material exchange | glTF 2.0/GLB **candidate**, PBR metallic-roughness; validate Blender version/exporter compatibility | WORLD + CHARACTER |
| Android memory, GPU time, draw calls, LOD, texture limits | NOT_MEASURED; profile real Android Chrome before setting numeric limits | INTEGRATION + QA |

## Runtime architecture candidates (not yet selected)
| Option | Fit for current HTML/CSS/vanilla JS | Android Chrome risk | Decision |
| --- | --- | --- | --- |
| Three.js + WebGL2 | Lightweight incremental canvas and GLB loader; must implement field adapter, input, lighting and resource management | Device-specific shader/texture/thermal limits; benchmark | Candidate A |
| Babylon.js + WebGL2 | More integrated scene, animation, physics interfaces; larger engine migration surface | Load size and device performance must be measured | Candidate B |
| Custom WebGL2 | Minimal dependency but high engineering and QA burden for PBR, skinning, LOD, tooling | High implementation risk | Not preferred absent evidence |
| WebGPU-first | Modern features but uneven browser/device support and fallback requirements | Android support cannot be assumed | Research-only, not sole renderer |
| Offline Blender render + DOM | Good reversible fallback, preserves current runtime, **does not fulfill fully interactive real-time 3D target alone** | Lowest immediate migration risk; limited true 3D camera | Compatibility fallback only |

**Suggested test order:** isolate Three.js/WebGL2 and Babylon.js/WebGL2 behind a feature flag and compare actual Android Chrome performance and current game integration. No engine selected and no unverified performance claim.

## Non-destructive bridge architecture
1. New `field3d` renderer is a separate optional scene/canvas. Existing DOM field remains the default and rollback path.
2. An adapter consumes existing gameplay state, movement and JSON collision without rewriting SAVE/CONTINUE or story/battle code.
3. Map import and character GLB are independently hashed and validated; transforms are declared rather than silently applied.
4. Gameplay events remain source of truth. Rendering may interpolate positions but may not modify saved coordinates.
5. Test with a **limited technical integration scene**, not a fake final village or adopted character model. Do not ship that test as final art.
6. Enable feature flag only in isolated branch. Verify old SAVE loads, movement, collision, bridges, one-way story jump, camera, touch, reduced-motion behavior and Android before G4 PASS.

## Required machine-readable exchange fields
`schema_version`, `asset_id`, `lane`, `source_sha256`, `output_sha256`, `blender_version`, `exporter_version`, `axis_conversion`, `unit_scale_approved`, `world_origin_approved`, `ground_contact`, `root_motion_policy`, `camera_contract_id`, `lighting_contract_id`, `collision_contract_id`, `animation_state_map`, `performance_budget_id`, `qa_status`, `approval_evidence`.

All unapproved physical values must be null, not guessed defaults. G1–G4 are separate. Source-review Blender success is not world geometry or G2 art approval.

## Immediate cross-team questions
- CHARACTER: supply candidate GLB/rig orientation and measured foot/root bones, actual export version and source SHA; do not mark final until character G1 provenance conflict is resolved.
- WORLD: supply candidate camera/origin/ground-query and occlusion interface without pretending dimensions are approved.
- INTEGRATION: compare renderer candidates on isolated Android test and propose measurable budgets, preserving current SAVE and DOM runtime.
