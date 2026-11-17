# LIND Cliff LOD25 — controlled artifact diagnosis (2026-11-17)

## Actual evidence
- PR #372; [Actions run 44004406983](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44004406983) completed SUCCESS.
- [Artifact 14293697347](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44004406983/artifacts/14293697347) contains source scan, 5 real 1200x800 PNGs, .blend, source SHA manifests, logs.
- Source glTF SHA-256: `645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11`; source 1,537,926 triangles; LOD25 384,480 triangles. Original source bytes unchanged.
- Five controlled renders: `01_full_pbr.png`, `02_lod25_pbr.png`, `03_lod25_pbr_without_normalmap.png`, `04_lod25_neutral_clay.png`, `05_full_neutral_clay.png`.

## Independent direct visual findings
- `02_lod25_pbr` has bright thin strokes on the right rock formation, including a visible curved/triangular stroke at the lower right, absent or much less prominent in the original `01_full_pbr`.
- `03_lod25_pbr_without_normalmap` **still shows the bright strokes**, at closely matching locations. Disabling the Principled BSDF Normal socket input does **not** remove the issue. Therefore the normal-map link **alone** is not a sufficient explanation or fix.
- Neutral clay `04` versus `05` shows broad geometric smoothing after reduction. The bright strokes are difficult to resolve reliably in the uniformly lit clay, so this experiment **does not prove** whether they originate from mesh gaps, UV interpolation/texture sampling, triangle overlap, or face/vertex normals.
- This is a reproducible close-up **G2 FAIL** for the 25% candidate. Do not infer a single precise root cause from these renders.

## Decision and anti-loop stop
- Existing raw Decimate .25 PBR candidate is **REJECTED for near-field formal adoption**. Source high-poly remains the reference.
- A parameter-only rerun of the same Decimate method is **not authorized as the next operation**. Two meaningful visual evaluations have found the same unresolved hairline issue (PR #371 and #372). Follow protocol: stop this approach and redesign the asset path.
- Next viable direction: geometry-aware retopology or curated scan patches on a separately authored continuous macro terrain, with seam-aware UV islands and **baked normal maps** from preserved high-poly; verify close-range PBR, topology, UV, LOD transitions, and actual world seam/collision. A narrow forensic test of actual face-edge/UV boundaries may be justified only if it has a clear diagnostic end condition and no repeat of prior renders.
- The source scan itself has open boundaries and disconnected geometric components; no candidate is an integrated game-ready cliff.

## QA
- G1 BLOCKED: official world alignment and scale not validated.
- G2 FAIL: LOD25 close-up bright hairline artifacts.
- G3 limited PASS: verified source download/hash, Blender render, .blend reopen. Game topology/collision/LOD transition NOT_RUN.
- G4 NOT_RUN: WebGL/Android not integrated.
- Main, formal CG, bridge PR #363, and official game assets untouched.
