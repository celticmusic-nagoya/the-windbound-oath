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

## Director correction — VRoid-derived anime base is NOT rejected (2026-11-20)

**Decision clarification:** Past G2 FAIL applies to the specific previous mesh/alteration methods and their insufficient design/measurement preparation, NOT to VRoid Studio or anime-styled VRoid-derived base meshes as a class. It is incorrect to disqualify VRoid because a prior attempt did not match the official Morwen design. An anime-styled VRoid base may be closer to the intended visual language than an unmodified realistic CC0 human base. No base selection is formally adopted by this clarification.

**Required fair comparison before selecting a base:**
1. Lock approved Layer 0 four-view reference, SHA-256, camera/projection assumptions and canonical design landmarks. Record measured vs estimated values separately.
2. Prepare a detailed 3D production blueprint with front/side/back/quarter silhouette, eye/socket and face proportions, hair volume/parting, neck/shoulder landmarks, asymmetric costume constraints, geometry targets and provisional local coordinates. Do not infer unobservable back-side topology from a single image.
3. Compare three independent candidates: (A) clean, legally reusable anime VRoid/VRM-derived base; (B) newly authored stylized sculpt; (C) unmodified licensed realistic CC0 base requiring stylization. Use matched cameras, lighting, normalized scale, clay renders and the same design/QA criteria. Do not assume realistic base is the default.
4. Score silhouette/landmark error, sculptability and topology, deformation/Shape Key preservation, facial expression rig compatibility, licensing, total correction time and final-size readability. Distinguish a base's potential from the previous modification method's failure. Keep past FAIL evidence, and avoid repeating stopped mesh-repair methods without a structural change.
5. Select the best supported method from actual geometry and independent art QA; record G1–G4 individually. If reference dimensions or candidate rights are missing, mark that subtask BLOCKED while proceeding with independent reference measurement and design work.

**Execution status:** direction corrected; blueprint and controlled candidate renders NOT_RUN; no VRoid candidate is approved or rejected by this note. Preserve the original VRoid/VRM files and previous candidate QA artifacts unchanged.
