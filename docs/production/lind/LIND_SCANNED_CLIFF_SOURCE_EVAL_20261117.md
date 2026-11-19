# LIND — Reference-led scanned-cliff source evaluation (2026-11-17)

## Why change
PR #367 planar Voronoi and PR #368 continuous sinusoidal procedural cliff both **G2 FAIL** on actual three-view renders. The smooth heightfield/striped-rock family was already exhausted in PR #346. No third variation of those methods.

## Candidate 1: Poly Haven Coastal Cliff 04 (priority)
- Official asset: https://polyhaven.com/a/coastal_cliff_04
- Publisher: Poly Haven; author credits: Rico Cilliers (cleanup), Rob Tuytel (photography/processing).
- Published license declaration: CC0; https://polyhaven.com/license
- Source offers 1K–8K, Blender/glTF/FBX/USD, AO, diffuse, normal, roughness. Published size ~86.8m wide and ~3 million triangles at full detail. This is **not** a confirmed Ireland photograph or a source for approved LIND dimensions.
- Intake: download only 1K/2K source as **candidate** in isolated CI temp directory; record exact original URL, declared checksum if available, computed SHA-256, license snapshot URL, asset version and triangle count. Do not commit binary scans to main. Generate clay and textured comparison and retain optimized game copy separately.
- Primary test: does the source show fractured scarps, non-periodic natural erosion, convincing soil–rock connection, and appropriate cliff silhouette after non-destructive composition? Compare to approved CG. If not, reject; do not make this an accepted world asset merely because it is scanned.

## Candidate 2: Poly Haven Coastal Cliff 02
- Official: https://polyhaven.com/a/coastal_cliff_02
- Source listing identifies weathered seaside cliff, crevices and grassy top, CC0. Independently verify official license/version/author at intake before download. Alternative if #04 mismatches LIND geography.

## Candidate surface only: Poly Haven Rock 3
- https://polyhaven.com/a/rock_3
- CC0 declared; rock/lichen diffuse, normal, roughness/displacement. **Not a geometry substitute**.

## Actual Irish geology references (reference only)
- Geological Survey Ireland, Old Head of Kinsale report: https://gsi.geodata.gov.ie/downloads/Geoheritage/Reports/CK069_Cork_CGS_Old_Head_of_Kinsale.pdf — photographs of folded shale/sandstone and coastal fracture exposures.
- Geological Survey Ireland, Dun na Mo report: https://gsi.geodata.gov.ie/downloads/Geoheritage/Reports/MO051_Dun_na_Mo_Oirreas.pdf — metadolerite/psammite contacts, quartz vein and coastal outcrop.
- Geological images are **reference only**; do not assume texture reuse rights without a verified license. The Poly Haven asset is not asserted to be photographed in Ireland.

## Geometry and QA contract
1. Verify official source URL, CC0 claim and binary SHA before any integration; unknown provenance => BLOCKED.
2. Preserve scanned high-detail mesh as unmodified original and create a distinct edited candidate. Align world footprint only after approved scale/coordinate anchors are known.
3. Compare clay front/oblique/top and game-size crops to approved LIND CG, explicitly reject repetition, straight cuts, stretched scans, or abrupt turf seam.
4. Test high-poly source, 40k-triangle-ish game LOD and PBR maps separately; verify texture color spaces and UVs, seams, topology, overhang and collision.
5. Independent G1–G4: no promotion without all PASS. WebGL and Android NOT_RUN.
6. Avoid Codex bridge PR #363 and protected original sources. No main merge, publication or approved-asset replacement.

## Current state
Research and candidate provenance specification only; no 3D scan downloaded, no scan Blender render, no new artistic QA. Previous PR #368 G2 FAIL remains unchanged.
