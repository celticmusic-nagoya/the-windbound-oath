# LIND-ECO-01 — prior history import (vegetation)

Imported 2026-11-16 by the ECO lane (read-only, via `gh api` contents of `feature/map-vegetation-master-01`, PR #337 head `e0a62a4b76c838a8c4c88b2f13a5d598c0d3b010`). Counts are carried, not reset (CAUSAL_RETRY v2 §6). Cross-branch ledger sync is NOT_IMPLEMENTED; this file carries the history explicitly.

## Sources read (SHA-256 of the fetched file bytes)
| File (PR #337) | SHA-256 |
| --- | --- |
| docs/production/MAP_VEG_01_SPEC.md | e0190699f4bd7ed2d0020a5ee3b034a0d17b6c312f8ea308c1765969549114d5 |
| docs/qa/MAP_VEG_01_CANDIDATE_A_REVIEW.md | c453de94998c60d56288d19435efdf996bd171fc3b308a88ee91b2f21c87d681 |
| tools/map_blender/map_veg_01_generate.py (candidate A) | 09c9425f3223234c2661e1c504e0a260a0e5dfdf4895ad51745cab8b79a11b36 |
| tools/map_blender/map_veg_01_generate_b.py (candidate B) | 6127dcc078e7224f1661ef629ed8911d0b994ff3a31e779cb999456036f71c5e |
| tools/map_blender/map_veg_01_manifest_qa.py | 39876cd86a2321cd19da1733b298654aaf15b4e5b2cef377c798aabf682a18d1 |

CI runs: candidate A render run 43810846659 (artifact 14200905243, head 8edc968); candidate B renders 43811405176 / 43812195250 (success, technical only). PR reviews/comments: none recorded on GitHub. The "grass failure ledger" of #337 consists of the candidate A review document; no separate JSON ledger exists on that branch.

## Recorded outcomes
- **Candidate A (grass_master_A)** — G2 **FAIL** (independent review 2026-11-16): blades legible at 768px but the three clumps read sparse and narrow, no layered mass, no distinctive silhouette; game-size readability unproven. Reviewer root cause: blades distributed evenly around a single centre; no layered broad/narrow blades, basal foliage or controlled overlap. Reviewer explicitly forbade "just more blades / new seed".
- **Candidate B (grass_master_B)** — rendered in CI, **no art review recorded**. Structurally it is candidate A's generator with a 62/38 split of blade parameters (wider, shorter "basal" blades + an `arch` term). Same placement algorithm, same single-centre sqrt-uniform disc, same one-object-per-blade, same flat single-colour materials.

## Method families — status for this lane
| ID | Family (as defined by its algorithm, not its name) | Prior failed attempts | Status for ECO |
| --- | --- | --- | --- |
| VEG-F1 | **Single-centre radial/disc scatter of independent per-blade mesh objects** (sqrt-uniform radius around one centroid, outward lean = azimuth ± jitter, flat per-material colour, one Blender object per blade). Includes A and B (B changes only per-blade parameters; per policy a parameter change is not a new family). | 1 G2 FAIL (A) + 1 unreviewed same-family variant (B) | **STOPPED — do not repeat.** Treated as exhausted: B adds no structural change, so a third build of it would be a forbidden parameter-tuning retry. |
| VEG-F1x | "Fix by increasing blade count / changing seed" | explicitly forbidden by reviewer | **STOPPED** |

## Causal distinction required of ECO grass (method family ECO-G1, new)
1. **Tiller-based architecture**: each clump = 3–7 off-centre tillers, each with its own lean vector and a fan of blades in a narrow cone (not a single radial disc).
2. **Length-dependent gravity droop + V-folded midrib cross-section**: long blades arch and droop, short ones stand; tips may fold.
3. **Height distribution skewed** (many short basal, few tall) **plus seed-head stems and dry/dead blades** at the base.
4. **Per-vertex colour gradient** (dark base → light/ochre tip, per-blade hue jitter) via colour attribute, instead of 4 flat materials, to give layered mass at 48/96 px.
5. One merged mesh per clump (instance-friendly), with `wind_weight` vertex attribute for the global wind channel.
Measurable hypothesis: at 96 px on ground the clump reads as a dense tuft with a lighter crown and darker core (non-uniform luminance across the silhouette), and the silhouette bounding box aspect differs per variant.

## Other prior lanes checked
#309 (Aidan asset ledger: Poly Haven CC0 textures, all architectural; no vegetation entries), #311/#323/#329/#331 (roof/architecture/masonry families F1–F8) — no vegetation method families. Their masonry families are not relevant to ECO and are not reused.
