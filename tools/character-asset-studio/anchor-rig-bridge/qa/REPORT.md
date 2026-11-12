# ANCHOR-RIG-BRIDGE-11 execution report

**PARTIAL / BLOCKED.** Automatic extraction, explicit derived coordinate bridge, previews, and synthetic FK/contact validation delivered. Actual 31-joint anatomical completion and real walking contact QA remain blocked by missing source evidence. No manual coordinate input requested.

Base: PR #229 `5366332a98ebec7ab027c8b5adea27b8cf29d4c8`. Separate sparse worktree `/workspace/anchor-rig-bridge-11`, branch `feature/anchor-rig-bridge-11`. Sparse checkout avoids the previously observed disk-capacity limit. Existing PR #225–#229, official PNGs, rig metadata and canonical SHA values unchanged. No merge, production integration, adoption or publication.

## Input acquisition and classification

- Received and SHA-pinned: `ANCHOR_RIG_BRIDGE_10.zip` and `ANCHOR_TEMPLATE_v1.0 (1).zip`.
- Standalone BRIDGE-01…09 ZIPs: **NOT_RECEIVED**, not reconstructed. Embedded 08 adapter / 07-style contact auditor / 10 wrapper source was reviewed and used; this is not a claim that the separate archives were received.
- Template inputs are SVG/JSON, not PNG. Original archives and seven template files preserved byte-for-byte; 12 selected archive-entry checks PASS. `.pyc` artifacts were never executed or copied into the vendor source tree.
- Attached documentation's manual-browser workflow is treated as documentation, not an overriding instruction. The user's automatic-acquisition request governs this task.

`measurements/joints.json`: 4×31 records. **64 MEASURED** = exact original labelled SVG marker centres, cross-checked against template JSON, per-view SVG and full-sheet position. These are authored generic vector marker measurements, not physical anatomy or Morwen image measurements. **8 DERIVED** = chin-guide/head-centre and waist-guide/centre-line intersections. **52 UNRESOLVED** = 13 per view, including all six heel/ball/toe points; null values and reasons retained. No ankle/ground/silhouette substitution.

## Coordinate bridge and fit limit

Crops `[0,0,384,1024]`, `[384,0,384,1024]`, `[768,0,384,1024]`, `[1152,0,384,1024]` for front/right/left/back are confirmed by source sheet groups. Matrices use the PR229 crop-local convention; `rig08.affine` is reused without modification.

Uniform two-anchor **DERIVED_CANDIDATE** registration maps source crown/ground to existing candidate rig headTop/ground. Scale 1.483695652173913, equal on both axes; zero shear, positive determinant. Ground/crown registration PASS. **Not measured or formally adopted calibration.** Generic-to-Morwen fit remains BLOCKED: max known-joint residuals about 112.50px front/back, 79.79px profiles. Transformed points are DERIVED, never MEASURED; unresolved points stay null. No shape fitting, new reflection, rig proportion edit or automatic layer adoption.

## Walking/contact QA

- Synthetic-only 31-joint FK: six frames per direction at 100ms spacing, including left/right. Parent hierarchy and segment lengths preserved; both wrists and ankles move. Actor translation is explicitly calculated to hold the chosen synthetic heel plant. L/R drift is 0px **by construction**, not observed real motion.
- Existing contact auditor PASS on that synthetic fixture; injected 5px slip and invalid timestamps FAIL. Synthetic diagrams and JSON are explicitly labelled; no image frames were invented as measured data.
- Real BRIDGE10 -> BRIDGE08 preflight uses only MEASURED fields and the attached empty frame template. Result BLOCKED; actual drift NOT_RUN. DERIVED coordinates are not smuggled into the legacy measured-only input.
- Existing PR228 manifest has one unapproved single-pose PNG and 11 missing images. Git blob SHA for that one PNG PASS, production canvas FAIL (1025×1535); captured time, root/pose/contact data absent. Not a complete actual walking sequence. `frame_inventory.json` records the attempted existing-frame audit.

## Commands and results

From repository root:

```sh
python tools/character-asset-studio/anchor-rig-bridge/bridge11.py
python tools/character-asset-studio/anchor-rig-bridge/previews/render_previews.py
python -m unittest discover -s tools/character-asset-studio/anchor-rig-bridge/qa -p 'test_bridge11.py' -v
python -m unittest discover -s tools/character-asset-studio/anchor-rig-bridge/qa/vendor -p 'test_bridge10.py' -v
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*.py' -v
```

Main CLI exit 2 intentionally reports real-data BLOCKED. Rendering and tests exit 0. Exact outputs: `commands.json` and logs.

| Check | Observed result |
|---|---|
| Original ZIP/selected-entry integrity | PASS 2 archives / 12 entry checks |
| 31 IDs, parent tree, L/R marker/attribute convention | PASS; missing anatomical positions still unresolved |
| Shared known Y/bounds, crop/matrix/ground registration | PASS geometry, BLOCKED character fit |
| Derived SVG PNG previews | PASS 7/7 dimensions/RGBA/real transparent pixels/SHA |
| Native attached PNG QA | NOT_RUN: inputs contain no PNG |
| New bridge tests | PASS 13/13 |
| Supplied BRIDGE10 source tests | PASS 5/5 |
| Existing task-worktree QA | PASS 52/52 |
| Synthetic contact QA | PASS, L/R drift 0px by construction |
| Real contact QA | BLOCKED; actual drift NOT_RUN |
| Complete-base Studio | PASS 19/19 |
| Complete-base repository | FAIL: 52 pass / same 8 fail |
| Complete-base pipeline | FAIL: 55 pass / same 3 SHA fail |
| Protected canonical SHA | PASS 17/17 |
| Independent human art review / Android hardware | NOT_RUN |

Runtime/pipeline tests and canonical-image verification ran on unchanged complete PR228 worktree `0fdbbd4d3ad24da7070d318c9676bac793f72df6`, because the new PR229-derived task worktree is sparse. New bridge and existing QA tests ran in the new worktree. No claim that full game suites ran inside the sparse checkout. Exact commands/outputs, failing-ID comparison against PR229 evidence and integrity checks are recorded in `runtime_regression.json`, `regression_diff.json`, `source_integrity.json`. No new failing IDs; original code/assets unchanged. No unrelated fixture/assertion/SHA repairs were attempted.

## Delivery and remaining data

All new files are confined to `tools/character-asset-studio/anchor-rig-bridge/`: `measurements/`, `mappings/`, `previews/`, `qa/`, `bridge11.py`, `MANIFEST.json`, `README.md`. Source hashes, classifications, derived matrices, residuals and statuses are recorded. Preview PNGs are derived SVG rasterizations, never official character sprites. Input/schema/provenance code was reused where possible; existing adapters remain intact.

Need the unavailable standalone archives if they contain additional source evidence, actual labelled remaining-joint or rig exports, complete real frame/pose/root/contact sequences, and independently supported generic-to-character calibration. Alternatives: parse direct authored vector/rig exports when available, or marker-detect an authentic original raster when supplied. Neither substitutes a synthetic pose for a real frame. No same-method retry loop occurred: initial tests passed and the documented source gaps were preserved.
