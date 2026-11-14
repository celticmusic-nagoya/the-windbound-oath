# AIDAN ROOF V2 — Independent image review (2026-11-14)

## Evidence
- GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43521547500
- Artifact: aidan-roof-vertex-first-v2-qa, ID 14084085301, SHA-256 archive digest 2f7bc572f72e75b4e658583eb8bc498545a20a94bd25ce72a13d094d1e20424f
- Renderer: tools/map_blender/aidan_roof_render_v2.py; builder: tools/map_blender/aidan_roof_vertex_first_v2.py; seed 1311
- Five views: game_27deg/front/rear/left/right. Blender .blend and manifest uploaded.

## Gate decisions
- G1: PARTIAL. Blue-gray slate direction respected; house dimensions, entrance and full exterior remain candidate.
- G2: **FAIL for formal adoption**. Visual inspection of game_27deg.png shows distinguishable slate courses and staggered joints, an improvement over v1. However tiles remain uniformly rectangular with flat surface, ridge/end caps and edge termination are not authored, no PBR/weathering, and there is no integrated cottage silhouette. Do not claim finished art.
- G3: PASS for isolated render pipeline only (five nonempty PNGs, SHA-256 checks, .blend existence). UV/manifold/normal and high-detail budgets NOT_RUN.
- G4: NOT_RUN (no game integration, mobile QA or performance test).

## Next geometry production, without repeating failed approaches
1. Preserve 8 architectural roof cage corners, add rafter/gable/ridge controls and roof edge trims; audit watertightness and contact.
2. Author 3–5 deliberate slate silhouette families (edge chips, taper, gentle camber, variable thickness), distributed with seeded constraints. Do not add random vertices uniformly or per-tile gratuitous subdivision.
3. Add non-repeating ridge caps and eave drainage termination. PBR CC0 source and SHA must be pinned before using.
4. Render clay/PBR at 27° and final 290px/384px; compare with protected approved village CG. Only pass G2 after independent visual QA.

No main merge, no runtime change, no approved CG replacement.
