# LIND scanned cliff voxel retopo / bake — independent QA (2026-11-17)

## Execution
- [GitHub Actions 44006786285](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44006786285): SUCCESS; [artifact 14295240652](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44006786285/artifacts/14295240652).
- Actual Blender 4.x: source scan 1,537,926 triangles; separate Voxel Remesh (.22 source units) + Shrinkwrap candidate 36,956 triangles; 1 UV layer, 1024x1024 tangent normal bake, 1200x800 render; .blend saved/reopened; hashes checked.
- Original glTF SHA-256 `645cadf494f60e247434451af6a88291d3be3019aa0973d635596810b0fe2d11` preserved.
- Render SHA `97081b531c163a1dbc5b818dc33e0547f3ba434f66d57c0561de33810f54b414`; baked normal SHA `95c66066d373a34a73cf3bc49e3d27e7402cafae48cd2ae621918e7e54876875`; .blend SHA `9d00e8e71a9d7a51bff99fac0757e0b399bb9a2a1c0db2354dedbfeaf5ff1468`.

## Independent actual image inspection — FAIL
- `voxel_retopo_baked_render.png`: nearly entire scene is flat grey; cliff appears only as scattered faint fragments, not a recognizable coherent high-quality cliff.
- `voxel_retopo_baked_normal.png`: largely flat purple, with sparse, tiny diamond-shaped baked patches and large unused atlas areas. Strong indication of inadequate UV texel occupancy for this mesh at 1024x1024.
- Cannot infer exact root cause of the missing rendered cliff solely from image: candidate geometry orientation, surface normals, remesh/shrinkwrap geometry, camera framing and/or backface handling require independent geometry diagnostics. The UV layout is demonstrably unsuitable for detail transfer.
- A successful Cycles bake operation and valid PNG **do not mean useful normal detail**.
- This is not a completed retopology, not an accepted material, not a world cliff.

## Gate decisions
- G1 BLOCKED — world CG scale/placement unverified.
- G2 FAIL — visible missing cliff and unusable normal atlas.
- G3 FAIL for intended topology/UV/bake visual acceptance; technical execution, file hashes, Blender save/reopen PASS only.
- G4 NOT_RUN.
- Preserve originals, do not integrate candidate. No main merge, canonical overwrite or publication.

## Next step / failure discipline
- Do **not** blindly rerun the same global Voxel Remesh + Smart UV Project + 1K atlas. First inspect candidate mesh bounding box, face orientation, UV island distribution and texel occupancy, source-to-target surface distance, and camera/frustum visibility. Only a targeted root-cause correction is allowed (max two meaningful trials), otherwise switch to **selected local scan patches + authored topology-aware retopology with managed UV islands and per-patch bake**.
- Keep Codex bridge PR #363 and all approved sources separate.
