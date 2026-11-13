# AIDAN-HOME-PBR-INTAKE-PLAN-01

Status: EXISTING SHORTLIST REUSED / DOWNLOAD AND BLENDER APPLICATION NOT YET VERIFIED

## Canonical inputs (do not duplicate or overwrite)
- tools/map_blender/aidan_pbr_shortlist.json (six candidate records)
- tools/map_blender/aidan_external_asset_sources.json (Kenney verified reference, provider leads)
- tools/map_blender/verify_pbr_shortlist.py (metadata-only verification; not texture import)
- tools/map_blender/aidan_home_production_candidate.py (current render candidate)
- .github/workflows/aidan-home-render.yml (technical render pipeline)

## Priority and material use
1. stone_wall: Poly Haven medieval_blocks_05. Evaluate tile scale, UV mapping, normal/displacement and stone silhouettes.
2. timber: Poly Haven medieval_wood. Check grain alignment, roughness, hue and beam edge quality.
3. thatch: Poly Haven reed_roof_03, alternate thatch_roof_angled. Treat as texture only: a PBR map cannot replace the geometry of layered eaves, ridge and straw ends.
4. door_shutters: Poly Haven dark_wooden_planks. Adapt to separately modeled hinges, panels, frames and joins.
5. ground: ambientCG Ground111. Apply only after checking suitability and texture budget.

## No-regeneration strategy
Use existing provider metadata discovery and shortlist. Do not repeat broad catalog search. Check exact asset metadata and license before download. Prefer 1K/2K maps and reuse texture sets. Capture exact downloaded files, SHA-256, source URL, license evidence, map channels, dimensions and attribution conditions.

## Implementation acceptance gates
- G1: canonical appearance, dimensions, roof choice and licensing reviewed.
- G2: 5-view comparison at final display scale, silhouette and surface quality.
- G3: no missing maps/purple materials, valid UV, alpha, provenance, SHA, Blender reproducibility.
- G4: browser/Android memory, draw calls and visual quality.
- Never report G2 PASS based only on GitHub Actions SUCCESS.

## Immediate safe task
Verify source candidates and texture download APIs, then build a separate **candidate** material import module and render branch. Do not mutate canonical assets, merge main, publish or invoke paid AI APIs.
