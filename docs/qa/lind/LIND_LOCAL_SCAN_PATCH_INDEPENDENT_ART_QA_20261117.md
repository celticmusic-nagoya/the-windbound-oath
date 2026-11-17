# LIND local cliff scan patch — independent image QA (2026-11-17)

## Evidence
- [Actions run 44010858412](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44010858412): SUCCESS; [artifact 14295844015](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44010858412/artifacts/14295844015).
- Exact source glTF SHA-256: `645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11`.
- Real 1200×800 render `local_source_patch_pbr.png` SHA-256: `8a8211e4b98c9b23fc31547d238654e3cbbac0e4193516df19d0ef731df45736`; .blend SHA-256: `8c86b29c1d28c0aad0a5a07873ce40c5ff3b64b18c8d64819bd98151c5a7781a`.
- Selected elevated grid cell (4,-1), 86,764 original triangles, 45,269 vertices, 3,734 open boundary edges, zero >2-face nonmanifold edges. Original UV loop values retained. No bake, retopo or geometry optimization performed.

## Independent art inspection
- **PASS as a source-detail reference only:** actual scanned irregular fracture faces, cavities, shadowing and varied green/grey rock texture remain visibly present. The prior globally remeshed candidate had lost this detail.
- **FAIL as game-ready geometry:** raw rectangular selection perimeter, visibly dangling thin triangular shards at left/lower boundaries, unnatural abrupt termination, patch lacks soil/turf transition, grounding, collision and world integration. Large areas are dark and diffuse texture looks soft at close range. These defects are not to be hidden by a success CI status.
- Original source was not documented as an Irish quarry/photograph; Poly Haven CC0 asset is a material/reference source, not a verified Irish geographical record.

## Gate decisions
- G1 BLOCKED — no canonical world placement/metric scale approval.
- G2 PASS for source reference / FAIL for finished cliff asset.
- G3 PASS for original UV-preserving extraction, SHA and saved Blender; FAIL for production open boundary, collision and optimization.
- G4 NOT_RUN.

## Next independent implementation
1. Select **interior contiguous** rock patch away from the 3,734 open edges; identify which boundary loops must be blended into authored macro terrain.
2. Plan topology-aware **local** retopology preserving irregular silhouette and dominant fracture planes. Do not use the stopped global Voxel Remesh or brute-force Decimate.
3. UV allocate to visible patch area, bake normal and diffuse as necessary, compare source vs low-poly under identical near-field camera and neutral clay/PBR lighting.
4. Stop if first controlled local patch fails to retain geometry; diagnose before second attempt. Do not adopt or integrate before G1–G4.
