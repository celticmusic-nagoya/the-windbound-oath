# ROUTE-MAT-01 / method C: curated stone geometry intake

**Status: BLOCKED — no approved sculpted geometry supplied.** This is a new source-geometry method, not a third tweak of failed block generators A/B. Keep old candidate PNG/.blend and source hashes unchanged.

## Input needed
- One genuinely hand-sculpted or rights-cleared photogrammetry/3D asset (GLB, OBJ, BLEND) with individual irregular stone geometry, plausible structural contact and a real masonry wall depth. Avoid flat wall-photo planes and procedural cuboid arrays.
- Sidecar JSON with **all** fields: `source_url`, `author`, `license`, `license_evidence_url`, `source_sha256` (lowercase SHA-256 of exact model bytes), `asset_status`: `candidate`.
- Record actual Ireland provenance separately if established; Ireland-inspired geometry must not be misrepresented as an Irish photograph or Irish stone sample. Source reference: https://nationalinventoryich.ccs.gov.ie/dry-stone-construction/ .
- External source assets require review of redistribution/derivative terms; CC0 materials from Poly Haven are separate **texture** candidates, not geometry.

## Reproducible intake
```bash
blender -b --factory-startup --python-exit-code 1 --python tools/map_blender/lind/route_mat_01/audit_curated_mesh.py -- --input candidate.glb --manifest candidate.json --report audit.json
```
Missing model/manifest => BLOCKED report, no false success. Audit checks hashes, required rights fields, mesh existence, boundaries and nonmanifold edges. Passing intake is **not** G2/G4 PASS. Inspect silhouette, stone contact, actual bridge structure and three clay renders separately, then compare the existing Codex material to CC0 photo-based PBR on **the same geometry**.

## Exit criteria
G1: canonical geometry/design alignment + source rights evidence. G2: independent clay-render review at close, 3/4 and gameplay scale. G3: no unintended open/nonmanifold mesh, correct UVs, textures, saved Blender reopen. G4: WebGL/Android frame time and visual regressions. Until all four PASS, do not adopt, merge to main or publish.
