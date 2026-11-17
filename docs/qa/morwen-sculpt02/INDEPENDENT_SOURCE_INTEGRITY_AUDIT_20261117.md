# Independent source integrity and geometry-change audit — 2026-11-17

## Recovered original
GitHub Actions run 44076487693, source artifact 14325870825. Downloaded ZIP and read actual `morwen_sculpt02_v02_UNAPPROVED.blend` bytes in an independent inspection runtime.

- Actual SHA-256: `90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b`.
- Matches the artifact's `SHA256SUMS` and PR #407 report: **PASS**.
- `geometry_difference.json` was extracted and read; the metadata supports 1,067 face vertices changed, max displacement 0.0030108392319740194, RMS 0.0002765988621792047. This is metadata confirmation, **not** an independent vertex-by-vertex mesh comparison.
- `face_topology_changed: false`. Thus the old realistic facial topology was **not retopologized**; minor GUI strokes cannot be treated as the requested anime facial reconstruction.
- Hair inventory in metadata: 8 rendered masses, 1 hidden rejected crown bridge. Only the occipital mass (65 vertices) and left face framing sweep (83 vertices) report GUI brush edits; other rendered hair masses were authored as geometry without GUI brush strokes. Distinguish authored geometry from brush-sculpted geometry.
- Reported `head_count: 7.749997013650178`, a geometry ratio rather than a visual QA pass.
- `PR399_baseline_active_shape_unchanged: true` in metadata, **not independently proven** without reading both Blender scenes.

## Decisions
- Existing .blend is a verified recoverable source candidate; do not overwrite.
- New next-stage face **must change topology and orbital/jaw planes**, not repeat the unchanged-topology local-Grab family (two art failures).
- Hair needs redesigned rooted surfaces, taper and inter-layer spacing, not more thickness offsets on the same 8 shells.
- Use legacy VRoid facial topology and expression shape keys as *reference only* until independent transfer compatibility checks; #318 eyelid deformation remains rejected.

## Gates
- Source archive SHA: PASS.
- Direct Blender open / topology inventory / vertex-level diff: NOT_RUN in this independent audit.
- G1 BLOCKED; G2 FAIL (separate independent image review); G3 PASS_TECHNICAL_SCREEN per CI, complete G3 NOT_RUN; G4 NOT_RUN.
- No merge, deletion, replacement or publication.
