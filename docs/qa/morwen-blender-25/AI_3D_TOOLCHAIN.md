# MORWEN-BLENDER-25 | AI-assisted 3D toolchain policy

## Current MVP: adopt now
| Purpose | Software / language | Responsibility |
| --- | --- | --- |
| Parametric model, UV, rigs, render, export | Blender + Python (`bpy`, `bmesh`, `mathutils`) | Headless scripts generated/reviewed by ChatGPT and Claude |
| Geometry/manifest QA | Python 3, JSON, SHA-256, unittest | Repeatable reference locks, topology checks, metadata |
| CI/CD | GitHub Actions + YAML + shell | Build .blend, render contact sheet, validate and archive |
| Web/Android preview | HTML, CSS, TypeScript/JavaScript + Three.js | Candidate-only GLB viewer and orbit/lighting checks; do not replace existing game engine without audit |
| Exchange format | glTF 2.0 / GLB | Portable preview/export; inspect animation and materials compatibility |
| Source control | Git, GitHub Draft PR | Never overwrite reference PNGs, main merge only after approval |

## Conditional tools: evaluate against project constraints
- **Godot 4** (GDScript/C#): optional 3D preview and runtime test only; avoid engine migration before current game architecture audit.
- **Krita/GIMP**: hand retouching UV texture atlases, alpha and masks; scripts may use Python + Pillow.
- **Substance 3D Painter**: optional manual PBR authoring, commercial license and desktop needed; not required for MVP.
- **Material Maker**: optional procedural materials; evaluate compatibility and time cost.
- **MeshLab**: optional mesh diagnostics, never automatic replacement for animation retopology.
- **VRM tooling**: only if avatar/VTuber export is a project requirement, not a default dependency.
- **Node.js + npm**: existing web tooling, browser preview checks; no unnecessary new dependencies.
- **glTF Validator**: optional standardized validation when GLB export becomes part of CI.

## Execution policy
1. AI writes Blender Python and tests; GitHub Actions runs Blender headlessly. No claim of manual sculpt/texture work that was not actually performed.
2. Generate neutral clay renders: front, left, right, back, 3/4; verify actual PNGs and compare with locked canonical references before art approval.
3. Validate topology, winding, bounds, naming, export, SHA and Android-friendly geometry budget. A green CI is **not** art approval.
4. Store outputs as candidate-only CI artifacts; preserve official character asymmetry and all canonical source hashes.
5. Two unsuccessful similar iterations maximum; stop and diagnose topology/pipeline rather than blindly regenerate.
6. Production integration, publication and main merge require separate authorization.

## Source documentation
- Blender Python API: https://docs.blender.org/api/main/info_advanced_blender_as_bpy.html
- Blender glTF I/O: https://github.com/KhronosGroup/glTF-Blender-IO
- Khronos glTF 2.0 specification: https://registry.khronos.org/glTF/
- Godot 4 supported formats: https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html

## Next work
BLENDER-26: candidate-only five-view Blender render job and GLB export smoke test; first confirm existing model visuals, then decide whether sculpt + manual retopology is needed.
