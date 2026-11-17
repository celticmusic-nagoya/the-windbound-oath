# LIND PBR image loading: failure stop and diagnosis

## Evidence (immutable runs)
- Initial glTF import, PBR assertion FAIL: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44070509505
- Removed reload, logged texture datablocks, FAIL: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44071241434
- Switched to explicit verified dependency mapping and reload, FAIL: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44083451999
- The source asset provenance and independent three-way QA passed: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44069687005
- No PBR PNG was produced in any of these runs. Uploaded logs are **not** successful render evidence.

## Direct observations
- Blender 4.0.2 on ubuntu-24.04 imports geometry and material image nodes.
- For rock_face_01 the three imported images have names rock_face_01_diff, rock_face_01_nor_gl and rock_face_01_rough; dimensions are all 1024x1024.
- Explicit glTF URI resolution and SHA checks succeed for:
  - textures/rock_face_01_diff_1k.jpg SHA-256 41bd26ed2db1332b1ebb4b1326fd8af4d21f0f0eb57b8ea385033115c722cfdb
  - textures/rock_face_01_nor_gl_1k.jpg SHA-256 9a9d85b9a01f4e24fc9ceec8baf96c019f552bca69591ff544c7a725e28b1d97
  - textures/rock_face_01_arm_1k.jpg SHA-256 59128c79d207a50a69a38002986135ade3b19642d26158cec141eca41578c9ca
- After both importer resolution and explicit img.filepath + img.reload(), all three image datablocks have has_data=False despite their nonzero dimensions. **The cause is not established**. has_data may not by itself prove the image is unusable in a render; do not assume missing files without independent decoding.

## STOP
Stop repeating PBR render attempts against the same unverified Blender image-load assumption. This is not an approved production renderer and must not be treated as an accepted cliff asset. Existing geometry Workbench previews remain valid as geometry-only evidence.

## Next bounded independent diagnosis (not yet run)
1. On a verified downloaded dependency, use an external image decoder to validate JPEG header, dimensions, and full decode, recording SHA. Keep the original unchanged.
2. In Blender 4.0.2 create a tiny **standalone** diagnostic scene that loads a known verified JPEG with bpy.data.images.load(check_existing=False), records filepath, packed_file, size, has_data and pixels access behavior; render one small emission plane if warranted. Separate this from the glTF importer.
3. Only if standalone decode/render PASS, inspect glTF image node linkage and run a single production PBR render. If it fails, stop and choose an alternate material pipeline or Blender version after evidence-based diagnosis.
4. Keep timeouts, maximum 2 attempts per newly identified independent root cause, and artifacts with explicit PASS/FAIL/NOT_RUN.

## Gates
G1 BLOCKED (official terrain/camera/placement); G2 NOT_RUN (PBR art and full cliff); G3 source/geometry/Workbench PASS but PBR FAIL; G4 NOT_RUN. No main merge, deletion, official asset substitution or release.
