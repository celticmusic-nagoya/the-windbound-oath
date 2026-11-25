# RILDE-HERO-ROOF-01 — high-fidelity component-first production
Status: DIRECTOR APPROVED WORKFLOW / ART ASSET CANDIDATE
Previous MAP23 greybox generator remains only for spatial QA; it is NOT the starting point for production-quality modeling.

## Master lock (not negotiable without explicit approval)
- Canonical Rilde: western Irish/Celtic-inspired farming/fishing village; warm hand-built materials; red-brown roofs.
- Hero target: Aidan's home. Existing accepted house design/official images override any procedural dimensions or palette here.
- Preserve non-symmetric features, component anchor points, geometry scale, and the adopted master canvas.
- Reference: Pinterest pins and professional environment-art examples are visual/technique research only, not meshes/textures to copy. Existing connected Pinterest boards currently do not contain a dedicated Rilde background reference board.

## Layer tree
00_MASTER: design refs, dimensions, roof angle, color palette, material scale, origins and anchors.
01_ROOF_CORE: rafters, battens, roof sheathing, ridge support, eave fascia.
02_ROOF_TILE_MASTER: ONE hand-made high-poly slate/clay tile with physically visible thickness, curved lip, edge chipping, surface roughness.
03_ROOF_TILE_VARIANTS: controlled tile geometry variants from the approved master, deterministic seeds, no obvious tiling.
04_ROOF_ASSEMBLY: rows, overlap, offsets, ridge caps, valley, gable and eave endings.
05_ROOF_DETAIL: moss in crevices, patina, flashing, rain wear; not before silhouette approval.
06_MATERIALS: high-poly bake source, game LOD mesh, UVs, normals, AO, roughness, trim sheets.
07_LIGHTING: fixed close-up studio camera, orthographic game camera, neutral light and sunset light.
08_QA: original-vs-variant comparisons, seams, scale, silhouette, clipping, transparency, 390px legibility, GPU/memory cost.

## Gates (no automatic downgrade)
A. Single tile close-up image accepted; no roof assembly before approval.
B. Tile array passes seams, intersection and rhythm QA.
C. Roof structure passes reference alignment, asymmetry, silhouette and lighting.
D. House parts assembled only after individual modules pass.
E. Runtime optimization happens on a duplicate via baking/LOD, not by simplifying the master.

## Implementation
Generator: tools/map_blender/hero_roof_01_tile.py
Outputs in CI: roof_tile_hero_closeup.png, roof_tile_hero.blend, roof_tile_hero_manifest.json.
No source third-party mesh or texture used. This is a first independent high-detail component candidate; it must not be called final quality until visually reviewed.
