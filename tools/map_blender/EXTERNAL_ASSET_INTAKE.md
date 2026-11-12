# External map asset intake — Rilde village (2026-11-13)
Status: RESEARCH ONLY. No third-party assets imported or approved. No change to canonical map.

## Sources
1. Kenney Nature Kit: https://kenney.nl/assets/nature-kit
   - Official pack page: CC0; 330 nature objects. Intended use: distant trees, rocks, grass prototyping. Style and scale require comparison.
2. Poly Haven: https://polyhaven.com/license
   - Official site: CC0 for its downloadable HDRIs, textures, and models. Intended use: ground/stone/wood PBR and outdoor HDRI, with texture baking into a stylized palette.
3. Quaternius Medieval Village MegaKit: https://quaternius.com/packs/medievalvillagemegakit.html
   - Candidate only. License MUST be reviewed per pack and download date. Quaternius license page was updated 2026-08-28 to Quaternius Asset License (QAL) v1.0; prohibits redistributing raw assets. Older third-party catalogs describing Quaternius as CC0 may be stale. Do NOT import into public GitHub or include raw assets in downloadable source/ZIP without explicit rights verification.
   - Official license: https://quaternius.com/license.html

## Safe integration policy
- Download from official source; record asset URL, author, pack, download date, license URL, version, SHA256, and redistribution allowance.
- Use external models as modular *reference and candidate* only. Preserve original in a separately tracked, license-compliant location. Do not commit third-party source assets to public repo if redistribution is restricted.
- No copying proprietary game maps, screenshots, or meshes.
- Keep visual consistency: geometry silhouette, world-unit scale, palette, texture density, ground contact and lighting.
- Blender + Python automation for importing verified CC0 GLB/FBX, instancing prefabs and deterministic placement. Geometry Nodes for vegetation; glTF export only after runtime benchmarks.
- Gate: 25–30 degree field camera, 390px Android legibility, geometry collision, event camera fire occlusion, no map-canon drift, performance and SHA checks.

## First experiments
A. Compare 3-5 Kenney Nature Kit assets against existing Rilde landscape in a separate candidate scene.
B. Evaluate Poly Haven HDRI/stone/wood materials baked into stylized textures; no automatic runtime addition.
C. Quaternius medieval architecture: visual reference until individual pack license and distribution terms verified.

MAP22 remains under CI / art review. Do not claim this plan is a completed asset import.
