# LIND-GEO-PHOTO-PBR-01: geometry-first Irish-landscape material pipeline

**Status:** Candidate pipeline only. This document does not claim a finished cliff mesh, acquired texture or rendered result. No approved asset replacement.

## Ownership and sequencing
- WORLD: produce genuinely different **authored geological cross-sections and joint-constrained cliff sculpt**; stop smooth-heightfield/periodic stripe methods after historical G2 FAIL. Build ocean cliff, separate eastern river cliff, waterline, turf cap and road-support geometry. Avoid overlapping Codex ROUTE-MAT-01 Method C masonry.
- INTEGRATION: verify map source/CG provenance and geography, unapproved metric scale, camera, road/nav boundaries. Never infer meters from the illustration.
- ART QA: inspect neutral clay geometry from close/three-quarter/gameplay camera before any texture masking. If clay silhouette/strata/contact fails, stop: textures cannot fix bad geometry.
- MATERIAL: only after geometry G2 clay review, collect rights-cleared **photo-derived PBR** texture sets. Prefer field-authentic Irish reference photos for visual guidance, not unlicensed direct projection. Poly Haven / ambientCG CC0 materials are candidates; verify actual item licenses, downloads and provenance per item. **CC0 does not establish Ireland capture location.**
- ENVIRONMENT: use triplanar/world-aligned projection on cliff faces where appropriate; UV for intentional strata, decals and authored localized detail; blend cliff rock, dirt, grass, moss and dampness using slope, height, curvature, ambient occlusion and hand-painted masks. Avoid obvious repeating tiling and abrupt grass/rock bands. Use albedo sRGB, roughness/normal Non-Color; normal maps require correct tangent convention. Preserve plausible scale, roughness and wet shoreline.
- DELIVERY: separate high-resolution Blender source and WebGL/Android texture/LOD variants; measure memory, compressed texture size and shader cost.

## Source evidence
Official world illustration `assets/sources/lind-world-20261116/original.png`, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`. Existing terrain PR #346 candidate D is **not** accepted geometry; 1,557 sampled route points unburied but unsupported bridge gap up to 0.444855 candidate units, G2 FAIL. Do not reuse its smooth periodic cliff geology as a new method.

Potential sources to verify, not yet acquired:
- Irish heritage craft reference: https://nationalinventoryich.ccs.gov.ie/dry-stone-construction/ (reference only; do not assume photos are licensed for reuse).
- Poly Haven CC0 photo-based materials: https://polyhaven.com/a/stone_wall and https://polyhaven.com/a/old_stone_wall (not necessarily Irish).
- ambientCG: https://ambientcg.com/ (verify exact asset and terms).

## Intake manifest schema
Place `manifest.json` next to texture files. Required:
```json
{
  "asset_status": "candidate",
  "source_url": "https://example.invalid/specific-asset",
  "author": "verified creator",
  "license": "verified rights",
  "license_evidence_url": "https://example.invalid/license",
  "capture_location_claim": "unknown",
  "textures": {
    "basecolor": {"path": "rock_basecolor.png", "sha256": "<sha256>", "color_space": "sRGB"},
    "roughness": {"path": "rock_roughness.png", "sha256": "<sha256>", "color_space": "Non-Color"},
    "normal": {"path": "rock_normal.png", "sha256": "<sha256>", "color_space": "Non-Color"}
  }
}
```
Optional normal channel; if `capture_location_claim` is `Ireland`, `ireland_provenance_evidence_url` is required. The above URLs and hashes are **schema examples**, not real licenses or actual acquired files.

Run `python3 tools/map_blender/lind/validate_photo_pbr_intake.py /path/to/manifest.json --report /tmp/pbr-intake.json`. It checks source metadata, traversal, SHA and color-space declarations; it does **not** validate legal enforceability, visual texture quality, normal-map convention, tileability or actual Blender shader wiring.

## Evidence gates
G1: canonical image/CG alignment and asset-specific source/rights/hash; currently BLOCKED for complete scene.
G2: clay geology PASS before photo-PBR, then independent final-display-size PBR blend art QA; NOT_RUN for new geometry.
G3: Blender saved .blend reopen, UV/triplanar correctness, roughness/normal colorspaces, masks, no texture seams, road support/junctions and rendered comparison; NOT_RUN.
G4: WebGL/Android render time, memory, texture loading, collision/SAVE regressions; NOT_RUN.
Stop after two same-root-cause failures; record method switch. No main merge, source overwrite, deletion or publication.
