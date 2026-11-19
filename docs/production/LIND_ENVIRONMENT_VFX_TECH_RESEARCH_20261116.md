# LIND environment visual technology research — 2026-11-16

STATUS: RESEARCH / PROPOSED ONLY. Not a canon change, runtime feature, render completion, or art QA PASS.

## Source-backed observations
- Genshin Impact: multi-layer terrain art, color variation, vegetation diversity (GDC 2021 coverage: https://www.famitsu.com/news/202107/23228135.html); dynamic day/night, weather, ambient occlusion and volumetric fog (developer account: https://www.hoyolab.com/article/15499).
- NTE: Unreal Engine 5 Lumen, Nanite, procedural content generation, World Partition. These are engine-specific techniques, not directly available in the current browser game (https://www.unrealengine.com/developer-interviews/crafting-the-urban-open-world-of-nte-neverness-to-everness-with-ue5-across-pc-playstation-5-and-mobile?lang=ja).
- Arknights: Endfield: cross-platform production standards, customized Unity rendering, and visual coherence across devices (https://developer.apple.com/news/?id=cpt08xv8). Developer interview discusses terrain streaming, virtual textures and long-distance dynamic shadows (https://www.gamespress.com/es/Arknights-Endfield-Reimagined-An-In-depth-Interview-with-Light-Zhong-a).
- NIKKE: distinctive silhouette, dense detail, lighting/color/composition and staging. It is a staging/character-background reference, not an open-world field-geometry implementation reference (https://www.pocketgamer.com/goddess-of-victory-nikke/4th-anniversary-dev-team-interview/).

## Candidate adaptations for TWO (not implemented)
| Rank | Production technique | Blender/offline | Browser/runtime | Verification |
| --- | --- | --- | --- | --- |
| P0 | Hero-quality modular cliff, rock, masonry and cottage surfaces | Sculpt/Geometry Nodes + baked normal/AO/PBR maps | Existing map renderer-compatible textures or meshes, only after runtime audit | silhouette, material, close/far captures, source hashes |
| P0 | Layered terrain with biome transitions | Slope/height/mask-driven shader bake | Texture atlas / blended materials where supported | seams, tiling, mobile memory |
| P0 | Environment lighting art direction | Key/fill/rim, contact shadow, AO, color-managed bake | Baked lighting, optional minimal dynamic lights | day/night comparison, readability |
| P1 | Vegetation diversity and placement | Procedural scattering with deterministic seed and authored clusters | Instancing or baked layers if renderer supports it | draw calls, overdraw, collision |
| P1 | Water/river/coast VFX | Flow maps, foam masks, shoreline meshes | UV scroll / sprite sheets / shader only if supported | flow direction, seam, Android FPS |
| P1 | Atmosphere and wind | Fog layers, god-ray textures, foliage wind masks | Depth-aware lightweight overlay / parallax | depth legibility, reduced motion |
| P2 | Interactive event VFX | Authored flipbooks, particles, masks | Pooling and capped particles | low-end device thermal/fps |
| P2 | Streaming and LOD | Chunk partition, baked impostors | Visibility culling / LOD / progressive loading | load time, memory, popping |

Three.js InstancedMesh can reduce draw calls when applicable: https://threejs.org/docs/pages/InstancedMesh.html. Do not assume the existing game uses Three.js. Verify renderer first.

## VFX and art-direction targets for Lind
- Wind-facing western cliff: ocean spray, wind-driven grasses, low warm sun, distant haze; avoid visual noise that hides characters.
- Eastern river and raid cliff: directional current, waterfall/river foam where geography warrants, clear dramatic silhouette; story jump is one-way.
- Southwest fishing inlet: localized water glints, rope/cloth movement, subtle ambient activity.
- Central village: warm window light, chimney smoke, footsteps/dust, handmade materials, authored human-scale detail.
- North farms: wind movement, differentiated crop clusters, atmospheric depth.
- Southeast landing: coherent transition toward Moss Forest; no unapproved lore effects.

## Engineering and QA gates
1. Audit the existing renderer and Android performance before adopting any runtime shader or new engine dependency.
2. Separate source image/reference rights from redistributable textures/models. Never import proprietary assets from benchmark games.
3. Preserve official source SHA and private canon; visual reference is non-metric.
4. Use independent modular asset ownership (WORLD/HOME/BUILD/ECO); no overlapping edits with paused Codex PR #346.
5. Render with deterministic configuration; record Blender version, seed, source SHA, output SHA, camera settings and before/after.
6. G1 BLOCKED until approved spatial metric/placement; G2 NOT_RUN for new art; G3 NOT_RUN for proposed VFX; G4 NOT_RUN until Android device QA.
7. Performance thresholds (FPS, memory, download bytes, draw calls) must be measured and explicitly approved; do not invent budgets.

## Decision
Prioritize offline-quality geometry, material and lighting with runtime-efficient presentation. Do not migrate to UE5 or claim Lumen/Nanite availability. Use targeted technical proofs only for high-risk runtime features, and do not treat low-quality primitive scenes as final assets.
