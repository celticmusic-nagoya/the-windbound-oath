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
