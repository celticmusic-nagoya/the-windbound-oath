# Morwen Blender 5.3 compatibility decision — 2026-11-19

Official Blender Foundation release: **Blender 5.3.0 released November 10, 2026**.
- https://www.blender.org/releases/5-3/
- https://www.blender.org/press/blender-5-3-release/
- https://www.blender.org/download/releases/5-3/

## Relevant changes
- EEVEE Material Lighting nodes may improve toon/NPR shading, but headless Linux/EGL and game-engine shader portability need independent testing.
- Cycles glass dispersion and anisotropic transmission can help eye/glasses look-development; not essential to initial clay sculpt.
- Multires Sculpt texture display, viewport and Geometry Nodes updates may be useful; evaluate on the same asset rather than claiming improved geometry.
- GPU DLSS denoising requires supported NVIDIA hardware/driver; do **not** assume available on GitHub-hosted CPU runners.
- 5.2 is LTS and current verified shared installation is **5.2.4**. Do not overwrite or replace the 5.2.4 installer.

## Adoption gates
1. First obtain real editable new head candidate and five actual PNGs using the pinned 5.2.4 baseline.
2. Create **isolated 5.3 trial** only after pinning official Linux binary URL and SHA256 from trusted release bytes; no mutable latest download. Keep versioned installation paths/cache separate.
3. Run same .blend on 5.2.4 and 5.3.0; compare mesh counts/positions, Shape Keys, materials, Python API compatibility, output hashes, render time and appearance, glTF roundtrip.
4. Preserve a 5.2.4-compatible original. **Do not save the only original in 5.3** or claim backwards compatibility without reopening.
5. If trial is faster/better and passes G1–G3 without regression, propose controlled migration; G4 WebGL/Android remains independent.

## Current status
- 5.3.0 official release VERIFIED via Blender Foundation.
- 5.3 installed: NOT_RUN.
- 5.3 headless Cycles / EEVEE: NOT_RUN.
- 5.3 compatibility / performance: NOT_RUN.
- Production default remains 5.2.4, no paid API.

## Actual GitHub Actions results (2026-11-20)
- Blender 5.3 isolated CPU Cycles smoke, save and reopen: **PASS**, run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44553193163, artifact 14544321964. This is a technical test monkey, **not** Morwen sculpt.
- Official Layer 0 four-view packed reference opened with Blender 5.3.0: **PASS**, run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44554802279, artifact 14545315896. Four verified PNG SHA values retained; 0 sculpt meshes.
- Decision: **Blender 5.3.0 GO for new, isolated Morwen authoring scenes**. Existing 5.2.4 source remains unchanged. Do not claim existing sculpt/rig/animation/glTF/Android migration PASS.
- HairHarpy actual GUI/Vulkan execution and export remain **NOT_RUN**. No hair asset or G2 art pass.
- Avoid repeating the proven version smoke or reference-only tests. Next useful action is a true authored facial sculpt with independent render/art QA, and separate HairHarpy graphical-capability check.
