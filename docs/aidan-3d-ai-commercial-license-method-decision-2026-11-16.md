# 3D production method decision — commercial rights + zero-cost compute (2026-11-16)

**Scope:** THE WINDBOUND OATH, especially Aidan's house; **status:** approved non-destructive candidate-only research. No inference run or official asset adoption.

## Verified sources and license separation

| Method | License evidence | Rights / constraints | Production gate |
|---|---|---|---|
| Blender authoring + script / Geometry Nodes | https://www.blender.org/about/license/ | Tool is free; output rights depend on *inputs*, assets, fonts, plugins and other third-party data, not automatically 100% owned/zero-risk | **Primary** for architectural geometry, fitted joints and verified 2.5D render |
| Poly Haven scanned rocks / PBR | https://polyhaven.com/license | CC0, retain URL / SHA / audit evidence | **Primary** for reference/surface and selectively for nonstructural details |
| TripoSR (local/open model, distinct from Tripo Web service) | https://github.com/VAST-AI-Research/TripoSR/blob/main/LICENSE ; https://huggingface.co/stabilityai/TripoSR | MIT code and checkpoint; reference-input permissions remain necessary. README says ~6 GB VRAM for one image. MIT notices retained with redistributed code | **Conditional** for complex independent decorations or character blocking, never bypass canon / G2 |
| InstantMesh | https://github.com/TencentARC/InstantMesh/blob/main/LICENSE ; https://huggingface.co/TencentARC/InstantMesh | Apache-2.0 repo and weights listing; inspect dependency and source-input rights for exact run | **Conditional** for single-image 3D reconstruction, GPU required |
| Microsoft TRELLIS | https://github.com/microsoft/TRELLIS | Main MIT; project explicitly lists separately licensed components (diffoctreerast and modified Flexicubes), so complete dependency/license audit required | **HOLD** until environment and dependency audit |
| Meshy Free hosted Web | https://help.meshy.ai/en/articles/15696428-what-is-included-on-the-free-plan | **CC BY 4.0 permits commercial use with Meshy credit**; currently 10 free downloads/month of Meshy 6 Lite; no free-tier API. Do not confuse with NC | **Conditional**; only assets with source terms / attribution retained |
| Tripo AI Free hosted Web | https://www.tripo3d.ai/help/privacy-policy/how-to-use-tripo-models-commercially | Service says free tier does **not** grant commercial use, unlike MIT open-source TripoSR | **EXCLUDE** outputs from commercial assets |
| Google Colab free GPU | https://research.google.com/colaboratory/faq.html | GPU access not guaranteed; use limits change, not unattended CI | **Optional manual research**, never project-critical unattended nightly build |
| Patch.gg | https://patch.gg/terms | Each library item has distinct license; default Patch works cannot simply leave Patch without authorization | **Reference-only** unless item explicitly licensed for reuse outside service |

**Important distinctions:** MIT/Apache software licenses are not necessarily the license of uploaded 2D input images or hosted services. Human editing does not magically eliminate provenance / copyright risk or guarantee exclusive copyright. Procedural code may still embody a protected third-party design. Preserve provenance and treat uncertain sources as BLOCKED.

## Engineering choice (2026-11-16)
1. Keep standard free GitHub Actions CPU Blender as canonical reproducible render/QA baseline. It can run Blender (already verified) but does **not** provide guaranteed NVIDIA GPU for TripoSR/InstantMesh. Never mark image-to-3D generation RUN when it has not run.
2. Architecture: source-photogrammetry → select scanned master → edit bedding/corner mating surfaces independently → game-resolution G2 → optimize triangles/UV/material → G3 and G4. Avoid the already failed cubic randomization/facet/ring family.
3. Complex objects/characters: only when a formally approved source image is available, evaluate TripoSR then InstantMesh on a *single isolated* candidate, using available GPU/Colab as an optional user-initiated run. Store model+code hashes, inference settings, seed, input hash, model revision, dependency licenses, source attribution, and GLB/OBJ outputs. Compare with direct Blender work in **quality / repeatability / full labor** rather than images alone.
4. Three.js/Babylon.js are presentation/runtime options, not an obligatory new engine. Avoid moving an existing 2.5D browser game to a different renderer simply to use 3D meshes; prefer rendering 3D to existing sprites/backdrops until actual runtime architecture and performance are confirmed.
5. All candidate outputs live off canonical paths, no merges / publishing without explicit permission. G1 canon reference unavailable => BLOCKED. Code/CI success is not G2 art pass.

## Observed CC0 stone silhouette test
Workflow https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43784760144 succeeded; 6 images generated (3 directions x 2 scanned rocks). Source pinned hash 23d6220c6c7613c4d7006d902ac99acebc7e7859f1368ba6dc0ae4123551cdc6.
- **rock03:** rounded planar/slab-like; naturally relatively flat, but too smooth and wide for a focal irregular corner quoin. NOT_APPROVED as corner master; possible ancillary foundation/plinth surface after art direction.
- **rock06:** convincing natural irregularity but projecting spiky edges and sloped irregular faces; poor bedding/mating without original redesign. NOT_APPROVED as drop-in quoin; useful reference/raw input for carved pieces and organic accents.
- These source rocks are *not yet* a successful masonry composition. Their licenses and mesh imports pass; stone-fitting and independent art G2 remain NOT_RUN / NOT_APPROVED.
- A 48x48 comparative thumbnail was made from the isolated render frames for **illustrative size evaluation only**, not a screenshot in the actual game.

## Quality gates
- G1 **BLOCKED** exact official Aidan house dimensions/canon not cross-checked.
- G2 **NOT_RUN for assembled masonry**; individual stone visual audit indicates direct placement unsuitable.
- G3 **PARTIAL_PASS** source import and render pipeline, but collision/fit, LOD/UV/baking not tested.
- G4 **NOT_RUN** Android in-game QA.

Next concrete work: manually art-directed corner module with authentic dressed bedding surfaces (not procedural cubes) and measured joints; use rock06 as sculpt/normal reference where CC0. A generated single-image 3D mesh will only be trialed if an approved input image and GPU capacity are available.
