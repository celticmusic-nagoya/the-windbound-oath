# LIND WebGL2 runtime benchmark protocol — phase 0

This isolated HTML page is a **native WebGL2 baseline**, not yet a Three.js vs Babylon.js comparison, GLB load test, full 3D map, or game integration. The page is intentionally independent of game boot, SAVE, field movement, assets, and external CDN dependencies.

## Execute
Open `tools/map_blender/runtime_benchmark/index.html` via a safe branch preview or downloaded local copy in Android Chrome. Tap **30秒測定**, keep the tab foregrounded, then copy JSON. Do not claim a device test without a recorded device/browser/version and output.

## Measurements
Records availability of WebGL2, vendor/renderer label, max texture size, viewport, device pixel ratio, context losses, elapsed time, average and p95 animation-frame intervals. Results are affected by display refresh, browser throttling, GPU drivers, temperature and other apps. The diagnostic draws one simple triangle, so **it does not predict real-world scene performance**. No automatic PASS threshold is defined.

## Next phases
1. Compare pinned Three.js and Babylon.js versions with identical licensed GLB, geometry count, textures, lights, animation, camera, resolution, warmup, and 30-second duration; record dependency licenses and SRI/hash.
2. Benchmark draw calls, frame times, GPU memory proxy, loading and skinning on Android Chrome. Obtain a director-approved minimum target device/budget before any G4 PASS.
3. Connect only through a feature-flagged adapter to existing game movement, collision, events and SAVE, with old field renderer as rollback. No main modification.
4. Independent G2 assessment on final-quality 3D village/character output. A technical triangle is not production art.

## QA state
G1 BLOCKED (world physical scale, camera and private canon reconciliation); G2 NOT_RUN; G3 NOT_RUN for Android benchmark; G4 NOT_RUN.

## Phase 1 engine-comparison candidate
- `tools/map_blender/runtime_benchmark/engine-compare.html` now contains independently selectable Three.js 0.170.0 and Babylon.js 7.40.3 runs, each rendering 100 shared box meshes, one directional and one ambient light, rotating for 30 seconds.
- This is a **technical-only, nonproduction** comparison. No GLB, textures, skinning, shadows, map geometry, SAVE adapter or mobile QA. Numeric metrics are not available until actual runs.
- Engine dependency URLs are pinned by version but not yet pinned by content hash. Browser CDN import and Android compatibility are NOT_RUN; network availability and CORS may block loads.
- Do not compare results unless the same device, browser, resolution, warmup and thermal state are recorded. Babylon and Three may internally batch/optimize differently; geometry equivalence is not a guarantee of equal GPU work.
- Run each engine twice, discard warmup, compare p95 frame time, mean frame time, context loss, loading failure and available render statistics. Actual engine adoption remains BLOCKED pending real GLB and game integration testing.

## Phase 2 local GLB handoff preflight (implemented, not executed)
- Open `tools/map_blender/runtime_benchmark/glb-inspect.html` in a secure context (HTTPS or localhost) on Android Chrome or PC. Choose a **local** `.glb` using the file picker; no file bytes are uploaded by the page.
- Inspect GLB magic/version/file size/chunk alignment, JSON glTF 2.0 metadata, bufferView and accessor references, mesh/node/material/texture/skin/animation counts, external URI declarations, and calculate SHA-256 with Web Crypto.
- `STRUCTURE_PASS` means **only basic container/reference checks**. It is NOT full glTF schema validation, semantic PBR QA, proof of GLB import into Three.js/Babylon.js, animation rig integrity, visual QA or game QA.
- External URIs, extensions, glTF semantics, geometry bounds and renderer compatibility need independent validation. The tool is not yet run on any actual candidate GLB.
- Report status: G1 BLOCKED, G2 NOT_RUN, G3 PARTIAL only for the checks actually performed, G4 NOT_RUN.
