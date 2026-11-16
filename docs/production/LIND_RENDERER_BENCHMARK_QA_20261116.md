# LIND renderer benchmark evidence and next quality gate — 2026-11-16

Status: TECHNICAL CANDIDATE ONLY. No renderer adoption, game integration, or official asset approval.

## Provenance
- Draft PR #349, benchmark commit `cbfb9f5fcec812a51b49b518de88e004f2d5054d`.
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43869438301
- Artifact: `lind-technical-glb` (run artifact ID 14227975336).
- Blender 4.0.2 on Ubuntu 24.04; headless Chromium; Three.js 0.170.0 and Babylon.js 7.40.3.
- Both engines loaded identical GLB SHA-256 `92e8805f051bdec96919fe0bac672cdd47a1af10eae9e30adcefa9eec3021839`.
- Scene: 100 meshes, 1,200 triangles; no skinned meshes or animation.

## Single-run observations (not a comparative performance verdict)
| Metric | Three.js | Babylon.js |
|---|---:|---:|
| Warmup | 3 s | 3 s |
| Measurement | 30 s | 30 s |
| Frames | 1801 | 1801 |
| Mean frame interval | 16.665963 ms | 16.666019 ms |
| P95 frame interval | 16.8 ms | 16.7 ms |
| GLB load time | 75.7 ms | 61.2 ms |
| Page errors | 0 | 0 |

**Important limitations:** requestAnimationFrame intervals near 16.67 ms indicate a browser frame-pacing ceiling, not equal GPU throughput. Engines are tested sequentially, not randomized, and only once; startup/cache effects and GPU driver are uncontrolled. The scene is too light to discriminate performance. Three.js reports 100 draw calls; Babylon draw-call stats are NULL and must not be compared. No Android device or actual approved production model has been tested. Browser load times are single samples, not statistically significant.

## Next reproducible tests (not yet executed)
1. Run >=5 repetitions per engine, alternating engine order; retain raw per-frame intervals and environment fingerprint (browser, viewport, devicePixelRatio, GPU renderer if available).
2. Include 3 workload tiers with **explicitly non-canonical** assets: baseline, high mesh/draw-call, and high material/texture cost; report triangle count, draw calls where comparable, GLB size and memory proxies.
3. Record dropped/long frames (e.g. >33.3 ms), P50/P95/P99, mean and actual elapsed duration; ensure timing excludes GLB load and warmup.
4. Validate on Android Chrome with approved reference geometry and touch/game UI. Keep existing DOM movement/collision/SAVE unchanged behind an isolated feature flag.
5. Before using production assets, reconcile latest official references and approvals. Do not derive scale or world meters from artwork.

## QA
- G1 BLOCKED: official 3D reference, metric/camera approvals and private canon reconciliation incomplete.
- G2 NOT_RUN: independent art review of production geometry.
- G3 PASS **only** for deterministic technical GLB export, integrity, headless import and 30 s render loop.
- G4 NOT_RUN: Android, gameplay, SAVE/collision regression, performance on actual assets.

This record is not a substitute for the source manifests, workflow logs or independent QA.

## Repeated run verification (2026-11-16)
- Commit `60a57ef596e93045aefb13066fd1f4149a22fed0`; CI https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43872820534 SUCCESS.
- 5 alternating-order runs per engine; 10/10 COMPLETED, each 1,801 frames in ~30.015 seconds, matching input GLB SHA-256, zero page errors.
- Mean frame intervals near 16.666 ms for both engines; this **does not resolve comparative GPU performance** due to browser frame pacing and low workload.
- CI artifact `lind-technical-glb` ID `14229550237`; previous CDN-dependent navigation timeouts were avoided by serving pinned local packages in CI. The standalone smoke workflow also passed: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43872820618.
- G3 PASS for repeated headless technical GLB render; G1 BLOCKED, G2 NOT_RUN, G4 NOT_RUN remain unchanged. High-load tiers NOT_RUN.

## High-load synthetic mesh-count tiers (2026-11-16)
- CI https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43874818839 SUCCESS, all three Blender export/browser jobs PASS. Source commit `4d01bd25068a1ae0fa5fabff72ea3a1d9db21f50`.
- 100 objects: Three mean 16.666 ms / p95 16.7 ms; Babylon mean 16.666 ms / p95 16.7 ms.
- 1,000 objects: Three mean 18.291 ms / p95 33.3 ms; Babylon mean 18.280 ms / p95 33.3 ms.
- 3,000 objects: Three mean 37.708 ms / p95 50.1 ms; Babylon mean 41.688 ms / p95 50.1 ms.
- Each tier has one 30-second measurement per engine; **not statistically sufficient to rank engines**. Synthetic cube geometry, headless Chromium SwiftShader, no production textures/animation or Android hardware. No formal renderer selection.
- Artifacts: `lind-highload-100` ID 14228864044, `lind-highload-1000` ID 14228704701, `lind-highload-3000` ID 14230261635.
- G3 PASS limited to CI technical GLB export/render; G1 BLOCKED, G2 NOT_RUN, G4 NOT_RUN. Next: repeated high-load runs and Android real-device measurement; protect main and production assets.
