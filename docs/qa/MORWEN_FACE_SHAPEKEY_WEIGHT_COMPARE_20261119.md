# Morwen recovered facial shape-key and weight comparison — 2026-11-19

Source: [Blender 5.2.4 Actions run 44521777298](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44521777298), successful; artifact 14528705636, SHA256 ZIP `76be5f06759d8e84ef960ea8ac9ba32107780ab337634ca793fb1fd2814483b1`. Directly compared both `structure.json` files.

| Region | shape-key position mismatches (#316 vs #318) | weight fingerprint | shared vertices across material regions |
|---|---:|---|---:|
| FaceMouth | 0/58 | MATCH | 0 |
| FaceEyeline | 58/58 | MATCH | 0 |
| FaceEyelash | 58/58 | MATCH | 0 |
| FaceBrow | 0/58 | MATCH | 0 |
| Face skin | 58/58 | DIFFERENT | 0 |
| EyeExtra | 58/58 | MATCH | 0 |
| MORWEN_Eyes procedural | 0/58 | MATCH | 0 |

The Shape Key fingerprints include Basis and all 57 other blocks. **Important:** the static base mesh topology/position/UV fingerprints for eyelash/eyeline match between scenes, but their Shape Key coordinates do not. This can arise from shape-key changes or reindexing and needs geometric evaluation. Do **not** claim deformation equivalence or G3 PASS.

Zero shared vertices across material regions in each mesh is a promising separation precondition, **not** proof that separation preserves shape keys, vertex groups, modifiers, material alpha, or animation.

Next step: create non-destructive *copies* of selected regions from PR #316, preserving 58 Shape Key blocks, original material, UV, weights, armature relationship, and local coordinates. Verify before/after exact evaluated geometry for neutral and representative blink/expression states; generate actual Blender comparison renders, then independent G2 QA against canonical Layer 0. Do not reuse PR #318 eyelid deformation (historical G3 FAIL).

G1 partial; structural fingerprint comparison PASS; new G2 NOT_RUN; deformation G3 NOT_RUN / prior lid G3 FAIL; G4 NOT_RUN. No charged APIs, new PR or main merge.
