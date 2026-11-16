# LIND runtime renderer feasibility audit — 2026-11-16

STATUS: SOURCE-READ AUDIT; NO RUNTIME CODE MODIFIED.

## Verified source (main)
- `index.html`: game boot loads `js/field/field-movement.js`, `field-navigation.js`, `field-height.js`, `field-camera.js`, `field-collision.js`, CSS `style.css` and `lind-field-review.css`. This is evidence of an existing browser field runtime, not evidence that the production village is using Three.js or Unreal.
- `js/field/field-camera.js`: the world is transformed through DOM style `translate(...) scale(...)`; the renderer uses world/viewport bounding boxes and keeps gameplay movement/collision unscaled. QA scale controls are session-only.
- `js/field/field-height.js`: opt-in height levels for JSON-map runtime, pixel-based collision/visual rectangles, connectors, and overpasses. Existing map coordinate semantics must remain intact.

## Architecture decision
1. Treat the proposed Blender village as an OFFLINE authored 3D source until a dedicated runtime adapter is designed and approved.
2. Never assume UE5 Lumen, Nanite, World Partition, Three.js InstancedMesh or real-time PBR are supported by the existing browser field renderer.
3. Preferred initial integration path: Blender camera-matched rendered layers / baked lighting / sprite or texture atlases, delivered through existing DOM/CSS/JSON runtime after mapping compatibility tests.
4. Alternative interactive 3D path: separately benchmark WebGL/WebGPU renderer and bridge to existing movement, collision, SAVE, UI and accessibility. This requires explicit architectural approval and Android profiling before replacing the field renderer.
5. Do not infer Blender world meters from current pixel coordinates, illustration scale, or old DOM anchors. Define an explicit reversible projection/coordinate contract before integration.

## Proposed VFX compatibility matrix
| VFX | Offline Blender render | Existing DOM/CSS runtime | Real-time 3D renderer |
| --- | --- | --- | --- |
| Baked global illumination and ambient occlusion | FEASIBLE | Texture/layer delivery; integration unverified | Requires separate renderer |
| Grass/cloth wind | Author animation and flipbooks | CSS sprite animation candidate; unverified | Vertex animation if supported |
| River current, foam and reflections | Flow/foam textures and baked reflections | UV scrolling/layer animation candidate; unverified | Custom water shaders if supported |
| Fog, volumetric rays, sunset haze | Rendered atmosphere layers | Parallax/overlay candidate; unverified | Depth-based fog requires depth buffer |
| Smoke, fireflies, dust | Rendered flipbooks | DOM sprite/pooling candidate; unverified | GPU particles if supported |
| Dynamic day/night | Offline lighting variants | Layer/texture switching candidate; unverified | Dynamic lights require benchmark |
| Nanite/Lumen/World Partition | NOT APPLICABLE | NOT AVAILABLE | UE5-only implementation |

## Gates before runtime implementation
- G1: current canonical private lore and official map reference must be reconciled; all spatial metrics remain BLOCKED.
- G2: evaluate actual Blender render at gameplay display size; NOT_RUN.
- G3: validate pixel-to-world mapping, visual depth order, alpha, tile seams, animation, source hashes; NOT_RUN for new VFX.
- G4: profile Android Chrome (frame time, memory, initial payload, thermal, motion accessibility) and SAVE/collision regression; NOT_RUN.
- Keep current `main` unchanged; do not overwrite paused Codex PR #346, Claude candidate assets or approved materials.

## Next actionable task
Implement a *non-runtime* export specification and QA harness for Blender-to-browser layers in a separate branch, once actual WORLD meshes and approved camera framing exist. Do not create placeholder game art and call it production.
