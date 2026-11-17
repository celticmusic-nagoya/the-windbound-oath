# MORWEN SCULPT02 — independent .blend binary container inspection

Source: GitHub Actions run 44076487693, source Artifact 14325870825, `morwen_sculpt02_v02_UNAPPROVED.blend`. Independently downloaded, opened ZIP and inspected the real binary bytes **without bpy**.

- Compressed .blend size: 29,066,567 bytes.
- SHA-256: `90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b` — matches saved canonical candidate hash.
- Compression: Zstandard frame (initial bytes `28 b5 2f fd`); decompressed size 44,346,172 bytes.
- Blender header after decompression: `BLENDER-v403`, 64-bit little-endian Blender 4.03 binary format.
- Parsed the actual BHead stream (24-byte header, 64-bit pointer) to `ENDB` with **no truncation or overflow**. 89,153 blocks; final offset equals decompressed file size.
- Block-code inventory includes **57 `ME` mesh datablocks, 77 `OB` object datablocks, 11 `KE` shape-key datablocks, 9 `MA` material datablocks, 8 `IM` image datablocks, 7 `CA` camera datablocks**. These are *stored datablock counts*, not visible/rendered mesh counts or independently verified armatures.
- The artifact's `geometry_difference.json` reports face 1,067 edited vertices, unchanged topology, 8 visible hair meshes. These claims remain **metadata-only** until Blender-level inspection.
- **Limitations:** binary container parsing does not evaluate mesh topology, UVs, vertex deformation, hair/scalp intersections, rig quality, material appearance or canonical design matching. A valid container is not proof of a usable model. Blender GUI re-open was reported by the production agent but not repeated in this audit.

Result: **PASS** source hash and binary-container structural integrity. **NOT_RUN** bpy mesh-level inventory, full G3 and G4. Existing independent G2 **FAIL** remains.

No source mutation, regeneration, main merge, deletion or publication.
