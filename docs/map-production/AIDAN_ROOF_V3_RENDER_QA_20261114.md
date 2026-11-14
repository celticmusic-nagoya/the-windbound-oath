# AIDAN-ROOF-03 | V3 rendered image independent QA

Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43531151846
Artifact: aidan-roof-vertex-first-v3-qa (14087477203), ZIP SHA256 26b078753098cb12dd3e59635c362c88ecc950b0e852261fd410c36d4af5e7c8.
Source commit: 0bb6a6c1d86aedaaf446d38c1736586f9a150eeb.

## Findings from actual game_27deg.png
- G1 PARTIAL: blue-gray slate retained, but roof is standalone, house structure not yet represented.
- G2 FAIL for formal art adoption: v3 has distinct offset slate shapes and clearly reads as individual roof tiles, a substantial improvement over v1 flat banding. However the tile variation looks too regular/repeated, ridge and verge transitions are thin, and right gable reveals a very dark unfinished substrate. No stone weathering or integrated house body; no UV/PBR.
- G3 PASS for isolated pipeline: static checks, Blender render, 5 PNG hashes, .blend, artifact upload passed in run #13. Manifold/UV and mesh budgets remain NOT_RUN.
- G4 NOT_RUN: final 290px/384px in-game legibility, Android runtime and collision not tested.

## Next phase
Avoid third round of superficial slate edge edits. Move to structural whole-house cage and integrated materials with proper UV. Compare at 290px before any G2 approval. Existing approved village CG and main remain unchanged.
