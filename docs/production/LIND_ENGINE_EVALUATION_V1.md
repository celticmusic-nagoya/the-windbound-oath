# LIND-ENGINE-EVAL-01 — Blender / Unity / browser pipeline decision (candidate)

Status: EVALUATION ONLY. No engine migration approved. Existing HTML/CSS/JS runtime and official assets remain untouched.

## Production roles
- **Blender:** source of truth for modular geometry, UVs, PBR authoring, authored vegetation, source .blend, mesh/texture optimization and deterministic offline renders.
- **Unity (optional):** scene staging, lighting probes/baked GI, prefab/LOD/occlusion experiments, terrain painting and camera-consistent previews when these are measurably more efficient than Blender. Unity projects are disposable consumers of versioned source assets, not the canonical asset source.
- **Existing browser runtime:** current field camera/input/story/save, Android Chrome and final image/atlas integration. No forced WebGL runtime replacement.
- **Alternative engines:** evaluate only if a specific unmet need survives the Unity/Blender tests; avoid multiple parallel engines without measurable benefit.

## Evaluation gates
1. **Source parity:** import a representative high-quality Aidan house module with stable transforms, materials, normals, UVs, pivot/foot anchors and hashed input. Compare Unity staging output with Blender master at matched camera/lighting.
2. **Lookdev:** check natural environment composition, color management, shadow quality, vegetation instancing, water, terrain blending, baked texture seams, and weathered stone at full view and 48/96px final presentation size.
3. **Runtime path:** prove a practical export into existing HTML/CSS/JS 2.5D field without breaking door IDs, navigation, collisions, save or story flags. A Unity screenshot alone is not runtime integration.
4. **Android:** benchmark memory, download size, startup, frame pacing, touch interaction and device compatibility on real Android hardware. Do not assume Unity WebGL or embedded 3D outperforms the existing runtime.
5. **Reproducibility/cost:** record exact Unity Editor version, render pipeline, package versions, Blender version, seeds, asset hashes, licensing and CI requirements. Unity CI/editor licensing and runner feasibility must be confirmed before automation.
6. **Decision:** adopt Unity for staging only if it produces a clear measured gain in visual quality or total development effort without blocking source portability. Record PASS/FAIL/BLOCKED/NOT_RUN for G1–G4; keep visual G2 independent of CI.

## First limited test (after canonical layout audit)
- One **finished-quality** Aidan house exterior with a short road, terrain/stone edge, fence, two vegetation sets and a consistent light rig.
- Export a versioned glTF/FBX candidate plus manifest and SHA-256; retain the .blend master.
- Stage the exact same geometry in Unity using a pinned supported Editor and URP settings, and in Blender.
- Capture matched camera views, texture memory, build/asset footprint and Android-ready sprite/atlas export. Only then choose a scene-staging tool.

## Work division (logical roles, not claims of live external agents)
A: architecture/house modular assets. B: terrain/roads/water. C: ecology/foliage. D: lookdev/Unity staging. E: browser exporter and interaction anchors. F: independent QA and regression.
Each package has source inputs, hash manifests, output assets, QA evidence, and independent branch/Draft PR. No destructive merge.

## Current status
- G1 BLOCKED: official whole-village map image and current private canon not fully visually compared in this workflow.
- G2 NOT_RUN: no completed integrated scene render.
- G3 NOT_RUN: no Unity import or Unity Editor run; Blender assembler not executed.
- G4 NOT_RUN: no browser/Android integration test.
- Decision: **Blender primary; Unity candidate for scene assembly/lookdev only**. This is reversible and not an engine migration.
