# LIND Coastal Cliff 04 — LOD study independent visual QA (2026-11-17)

## Actual reproducible evidence
- PR #370; Actions [run 43997465143](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43997465143), completed SUCCESS.
- [Artifact 14291130384](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43997465143/artifacts/14291130384) stores original official Poly Haven glTF/textures, full/LOD25/LOD10 clay PNGs, saved .blend, logs, `lod_qa.json` and SHA-256 receipts.
- Full source 1,537,926 triangles; LOD25 384,480 triangles and 206,423 vertices; LOD10 153,791 triangles and 86,537 vertices. Both LOD candidates have one UV layer. Exact source glTF SHA-256: `645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11`.
- CI passed source hashes, three PNG signatures/hashes, .blend signature/hash and reopening saved .blend. No world geometry or bridge files changed.

## Independent direct image inspection
Three real 1024×720 workbench images were downloaded and examined in original framing and a fixed crop (x=210..820, y=270..435), with equal-scale comparison.
- LOD25 visually preserves overall crest, fissure hierarchy and silhouette extremely closely to full source at this distant camera. Tiny rock roughness is somewhat smoother.
- LOD10 still retains macro silhouette and large fissures, but fine roughness and some small fracture edges soften. This does not establish close-up or game-size art quality.
- Important: cliff occupies only about 591×141 pixels of the 1024×720 image. Thus the small differences are **not sufficient** for final art or mobile LOD acceptance.
- Deterministic image differences (same camera/render setup, reference full): on pixels whose original RGB differs by >20 from background RGB 59, LOD25 mean absolute channel difference 2.016/255, 0.82% of foreground pixels have any channel difference >10; LOD10 3.601/255 and 5.94% respectively. These are image-space observations only, **not** perceptual scores, geometry Hausdorff distance or final-display QA.
- All three variants inherit the source's hard strip edges, open boundaries and incomplete cliff cap. Decimation cannot fix integration.

## Gates
G1 BLOCKED: approved LIND world placement/scale and CG comparison still incomplete.
G2 PARTIAL SOURCE-LOD VIEW PASS (distant silhouette only); **overall G2 BLOCKED** pending close-up, materials, final-scale and world seam review. No formal adoption.
G3 LOD BUILD/UV/HASH/REOPEN PASS; **overall G3 BLOCKED** pending topology, collision, LOD transitions, normals/tangents and performance budgets. The source itself has open geometric boundaries.
G4 NOT_RUN: no WebGL/Android integration or real-device testing.

## Recommendation
Retain full high-poly original as immutable production source; use LOD25 as the provisional **detail-preserving** geometry candidate, not an approved game asset. LOD10 may serve only as a farther-distance candidate if later screen-space tests pass. Next independent safe work is close-up and game-scale comparison with actual normal/PBR maps, and non-destructive surface placement against a separately approved macro terrain. No main merge or formal adoption.
