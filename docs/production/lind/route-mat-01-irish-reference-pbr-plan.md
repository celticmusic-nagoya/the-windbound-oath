# ROUTE-MAT-01 — Irish masonry reference and PBR candidate plan (non-adopted)

Status: RESEARCH / DESIGN CANDIDATE. Issue #359; PR #360 source images; PR #361 bounded failed methods A/B. No canonical asset, approved placement, or main changes.

## Source hierarchy
1. Official project CG, maps and SHA-verified geometry specifications (must prevail).
2. Ireland National Inventory of Intangible Cultural Heritage: https://nationalinventoryich.ccs.gov.ie/dry-stone-construction/ — dry-stone craft, regional geology, irregular stones, stable interlock, bridges and arches. **REFERENCE ONLY**; no photographic reuse permission inferred.
3. Poly Haven Stone Wall: https://polyhaven.com/a/stone_wall — third-party CC0 photographic PBR candidate, maps include diffuse/roughness/normal/displacement. **Not necessarily Irish-sourced.**
4. Poly Haven Old Stone Wall: https://polyhaven.com/a/old_stone_wall — alternative CC0 photographic PBR candidate, not necessarily Irish-sourced.
5. Codex original image pair from PR #360: candidate reference SHA and license in its manifest. This remains the control material.

## Construction decisions (proposal, not canon)
- Build a genuinely connected abutment with load-bearing wall depth and a plausible stone bond, NOT detached rounded boxes or rectangular automatic facing. Sculpt or hand-place a limited set of unique silhouette masters; do not loop the same failed procedural shape generator.
- Irish dry-stone craft is one reference, but **do not assert the canonical bridge is mortarless**. Choose dry stone or lime mortar only after checking official bridge CG and approved design.
- Establish bridge foundation, abutment-wall contact, parapet/road connections and drainage in geometry before surface detail.
- At the limited patch stage use **neutral clay** to independently approve stone silhouette, physical contacts, joints and gameplay-scale readability before UV/PBR. If geometry FAILs, stop: textures cannot conceal structural errors.
- After geometry approval, assign separate, non-repeating UV islands and compare three materials on identical geometry and fixed lighting: (A) existing Codex pair, (B) Poly Haven Stone Wall CC0, (C) Poly Haven Old Stone Wall CC0. External maps must be separately downloaded, source/license/author/URL/version/hash recorded, and explicitly designated candidate; never overwrite Codex originals.
- Prefer photographed PBR maps for microdetail and weathering; avoid using photographic wall patterns to simulate nonexistent geometry or embedding fixed lighting/shadows. Normal/height must be assessed against real mesh relief; use 2K first, optimize for WebGL/Android only after quality check.
- Localize moss, wetness, dirt, runoff and ground contact with masks based on geometry and environment; avoid uniform green overlays.
- Assess at closeup, 3/4 view, 48px game-distance and Android budget. Preserve unchanged cameras for material A/B/C comparisons.

## QA and stop conditions
G1: official CG dimensions/placement, SHA, rights and candidate labels; BLOCKED for unverified metrics.
G2: independent comparison of actual clay and textured renders, no repetitive silhouettes/black chasms/artificial tile repetition; NOT_RUN.
G3: watertightness, intersections, support contact, UV seams, color space, roughness scalar, saved .blend reopen, reproducible hashes; NOT_RUN for new approach.
G4: game integration and Android performance; NOT_RUN.
Do not re-run failed A/B generators as 'new attempts'. A new method must have demonstrably different source geometry and objective exit criteria. No merge, formal adoption or publication.
