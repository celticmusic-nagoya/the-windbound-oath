# AIDAN — CC0 scan asset shortlist / acquisition gate (2026-11-16)

## Verified public candidate sources
1. Poly Haven Rock Moss Set 01 — https://polyhaven.com/a/rock_moss_set_01 ; six weathered stone 3D models, 63k triangles across set, CC0. PRIMARY candidate for individually retopologized and art-directed master stones. Existing moss/dirt may be too strong for house corners: material separation and consistency review required.
2. Poly Haven Boulder 01 — https://polyhaven.com/a/boulder_01 ; weathered large boulder, ~124k triangles, CC0. Reference/secondary source only; poor natural mating faces.
3. Poly Haven Mossy Rock — https://polyhaven.com/a/mossy_rock ; texture, NOT a geometry model; CC0, candidate PBR only after silhouette approval.
License: https://polyhaven.com/license (all Poly Haven assets CC0).

## Acquisition status and non-destructive gates
- Source URL and license VERIFIED from publisher page. Asset bytes NOT_ACQUIRED: this execution environment could not resolve api.polyhaven.com DNS. No source archive, asset SHA256, model integrity, or Blender import has been verified.
- Do not claim imported/retopologized/PBR completed.
- On GitHub Actions with outbound access, use the publisher's documented API to resolve download files, choose lowest practical LOD and textures, log exact URLs, sizes, license and SHA256. Verify non-empty archive and model import; preserve raw source separately from derived candidate. If API unavailable, BLOCKED, never substitute a random model.
- Before art pass: inspect 6 meshes in clay and textured views, separate stone silhouettes, select 2-3 masters, create deliberately shaped bedding/mating faces; require collision/clearance and consistent joint thickness. Make corner arrangement manually art-directed before Geometry Nodes distribution. Bake maps and optimize triangles only after art pass. Render at intended game scale.
- Candidate assets must not overwrite canonical Aidan house or PR #323; no main merge or publish.
