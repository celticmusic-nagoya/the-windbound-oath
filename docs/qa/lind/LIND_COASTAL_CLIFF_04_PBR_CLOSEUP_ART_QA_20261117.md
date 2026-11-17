# LIND — Coastal Cliff 04 PBR close-up independent QA (2026-11-17)

## Verified execution
- PR #371; Actions [43999516441](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43999516441) completed SUCCESS (all steps).
- [Artifact 14291293325](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43999516441/artifacts/14291293325), original glTF/textures, Blender source, 1200×800 full and LOD25 PBR PNGs, source SHA manifest, logs.
- Blender 4.0.2; source 1,537,926 triangles; 25% LOD 384,480 triangles; both UV layer count 1; source glTF SHA `645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11`. File SHA/signatures and Blender reopen passed.
- Fixed diagnostic camera: [-1,-24,11] looking toward [-5,-4,4.4], orthographic scale 11. Area lights 4500W/2500W, world strength 0.8. This is **not** the accepted game camera.

## Direct independent image inspection
- Both images show plausible real scanned rock texture and broken surfaces; PBR illumination is improved compared with the earlier dark distant PBR study.
- At identical framing, LOD25 closely retains broad shape and color; however **fine bright hairline seams/triangular streaks appear on the right rock surface in LOD25**, not comparably visible in full. This is a real image-space artifact and a G2 issue for close-range use.
- The main face remains somewhat soft in 1K material preview; higher-resolution normal/PBR, actual game camera and display-size inspection remain NOT_RUN.
- Numerical diagnostic over all 1200×800 pixels: full vs LOD25 mean absolute RGB channel difference 1.398/255; 0.049% of pixels differ by >30 in any RGB channel. **These low aggregate metrics hide localized bright seam defects** and must not be used to declare art PASS.
- Both source and LOD inherit open scan boundaries; neither is a watertight integrated world cliff. No Irish capture provenance claimed.

## QA and failure policy
- G1 BLOCKED (approved CG, placement, scale not aligned).
- G2 FAIL for **LOD25 near-field acceptance** because of visible fine bright seams; overall integrated map G2 also NOT_PASS.
- G3 PASS limited to verified download/import/LOD build/PBR render/hash/reopen. G3 collision, normals/tangent preservation, self-intersection, topology, mesh LOD transitions and WebGL remain NOT_RUN.
- G4 NOT_RUN.
- Root cause is not proven; likely UV seam/tangent/normal or decimation topology interaction. **Do not claim the specific cause without targeted tests**. Stop blind Decimate parameter sweeps. The prior clay distant view alone was insufficient.
- Next allowed technical investigation: one targeted, controlled comparison of unmodified original vs LOD25 with (A) geometry-only normals, (B) original normal map disabled, and (C) PBR material, isolating whether streaks are mesh gaps or tangent/normal shading. If not resolved in two meaningful attempts, switch to topology-aware retopology/baked maps rather than repeat same modifier.

## Source safety
Original glTF and publisher textures unchanged. No official map CG, bridge PR #363, main, published game, or formally adopted asset changed.
