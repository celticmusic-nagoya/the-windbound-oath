# MORWEN-EYELID-07 structural audit / failed candidate

**NOT ADOPTED. Full closure is NOT fixed. No production integration or main merge.**

## Source and protection

- Parent work: PR #321 and #324. Latest diagnostic: Actions 43669203225, commit 2cf14ed899ebc078e64ed78080802aa04ace0194; artifact 14143099185, ZIP SHA256 a8997c37c76a47f5460691c77575ad6f29ff9d6fb98ca4f8c7ad8f894cebdd95.
- Full model reconstructed once with unchanged EYELID-05 builder under pinned Blender 5.3.0: [Actions 43671604592](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43671604592), artifact 14144696884. This reproduces the recorded failed baseline; it is not another transfer/pivot experiment. Model SHA256 e373361904443570609797a0daf099f212f22a88027a9b0c4a84cb805a15bdd2.
- **All mesh vertex counts and every stored Shape Key coordinate hash exactly match the latest diagnostic**, including Face's 58 keys: Basis, target_0 through target_55, MORWEN_DESIGN_NoseDepth. Rebuilt .blend file SHA differs due to serialization; geometry equivalence is checked separately.
- Original source file, all 58 key coordinates/order, UV coordinates unchanged after candidate evaluation. Modifier disabled: exact zero evaluated-coordinate difference against modifier-off across all 56 isolated targets. Key values are intentionally exercised in memory and restored; no input save.
- Four Layer 0 image hashes verified against manifest. Full v5.61 canonical binary remains unavailable; do not infer design conformity from this CC0 engineering baseline's hair/face/material appearance. No formal artwork or asset edited.
- Fresh extraction from the saved baseline exactly matches all latest vertex IDs, edge IDs and rounded world coordinates (`qa/ACTUAL_BASELINE_TOPOLOGY_07.json`). Both boundary graphs: 28 vertices, 28 edges, connected cycle. Source-authoring coordinate matches give R 1397 -> 1351, L 1264 -> 1207, with six-decimal rounding bound. Anatomical/art adoption remains pending. The candidate uses model-declared +Z superior and +Y anterior, not a reviewed universal eye calibration.

## Method and structural findings

Stopped historical families remain stopped: annulus topology, VRoid key transfer A1/A2, analytic pivot B1/B2. EYELID-06 additionally assumes 57 keys, contains literal backslash-n syntax defects, uses an inconsistent open-boundary selector and a Z-only 2D projection. It was neither imported, repaired to enable deformation, nor bypassed.

New family `DIRICHLET_HARMONIC_INDEPENDENT_LID_FIELDS`: solve upper and lower Dirichlet displacement fields independently on the actual patch graph, keep the outer displacement boundary fixed, carry matching wall/card vertices, apply four independent 0..1 controls with a Geometry Nodes modifier **after keys, before Armature**. Original keys remain byte-identical. The closure curve is the existing UNREVIEWED EYELID-06 proposal, source/calibration bound; it is not a new formal design. Controls are manual inspection controls; no automatic Blink/wink/Joy production binding is claimed.

Attempt 1 left expression cancellation tapered at the patch boundary, causing 38 Blink / 68 Blink+Joy flipped faces. Attempt 2 separates fixed displacement from expression cancellation across the patch and feathers cancellation over 6 mm of adjacent skin. This removes full-state flips and measured full-state eye exposure, but does not constrain intermediate Jacobians or contact between the unequal 16/14-column upper/lower margins. Independent interpolants and their walls intersect. A denser 33-sample correspondence table alone cannot create contact-compatible mesh topology.

**STOP this family after two FAILs.** No third parameter adjustment or regenerated closure was attempted. The installer now reads the cumulative ledger and refuses another build of this stopped family; no bypass is provided. Replays/renders inspect the already-built second candidate. Both trials are appended to the cumulative shared ledger; all previous entries remain intact.

## Actual QA

`qa/STRUCTURAL_QA_07.json` is the final expanded replay of attempt 2. Eye visibility uses 3,282 deterministic eye vertices/triangle centroids per direction and skin BVH occlusion. It is finite sampling, not a continuous guarantee. Socket rays are 25x25 per eye/view in the existing world-X/Z grid; profile grids are degenerate screen projections, so raw counts are diagnostics, not an area measure. Card/brow overlays are skipped for socket first hits. Proper triangle intersections use a BVH broad phase followed by strict interior noncoplanar segment/triangle tests; coplanar overlap and global/card collisions remain NOT_RUN.

| State | Flipped patch faces | Proper triangle crossing pairs | Socket backface first hits, summed over 2 eyes x 5 views |
|---|---:|---:|---:|
| Neutral | 0 | 0 | 0 |
| Blink | 0 | 124 | 0 |
| Wink L | 0 | 62 | 850 |
| Wink R | 0 | 62 | 850 |
| Joy | 0 | 124 | 0 |
| Blink+Joy | 0 | 124 | 2 |
| Half Blink | 2 | 2 | 2 |

Blink/Joy/Blink+Joy: zero measured eye-surface exposure from all five directions. Full Blink socket eye-first hits: zero. These sub-results do **not** overcome intersections, intermediate flips or wink socket failures. No degenerate patch faces detected. Unchanged UV coordinates alone are not a proof of all evaluated surface winding correctness.

35 actual Cycles CPU renders: seven states x front, left/right 45 degrees, left/right profile, 384x384, 12 samples, original materials, nonblack world background. See `REVIEW_SHEET_07.png` and `renders/`. These are engineering face closeups, not final game-size art composites. Codex inspected neutral/front, Blink/front, Blink/45, half-Blink/45: irregular lash seam and upper-lid shelf remain visible. No independent art PASS.

Python unit tests: 26 PASS; cumulative ledger validator tests: 5 PASS. (20 inherited splitter/capture tests including five repeated baseline cases; six solver/intersection tests). Complete render hashes are in the report; repository evidence hashes in `qa/ARTIFACT_SHA256.json`.

| Gate | Status |
|---|---|
| G1 | Protection checks PASS; full canon comparison BLOCKED |
| G2 | NOT_RUN; Claude independent art review pending |
| G3 | FAIL: intersections, half-Blink flips, wink socket backfaces; broader collision checks incomplete |
| G4 | NOT_RUN; no runtime integration/performance/Android tests |

## Next method and Claude handoff

Switch to `ARTIST_MULTI_STATE_CONTACT_CAGE`. This supplies explicit 25/50/75/100-percent shapes and contact-compatible seam/wall topology rather than one endpoint field interpolated through the known bad expression space. It may require a new candidate-only shared contact cage with matched seam segments, leaving the original Face and its 58 keys as a protected reference. Do not remesh or reindex the protected Face in place.

- `inspection/CANDIDATE_DISABLED_07.blend`: failed second trial, four controls zero on save. For inspection only. On Face, Geometry Nodes modifier `M07_HARMONIC_CANDIDATE` exposes R_upper/R_lower/L_upper/L_lower. Do not adopt or bind it to production expressions.
- `inspection/SCULPT_SETUP_07.blend`: separate authoring document. Original Face retains all 58 keys; four independent, unkeyed copies of neutral with nose-depth value 0.5 baked into the copies only. Names explicitly say UNAUTHORED. Only the 50-percent copy is visible in the viewport. Lid skin/wall vertex groups distinguish both sides. This is an authoring setup, not four completed sculpted targets.
- Claude: compare the 35 images and contact sheet; review neutral opening against Layer 0; assess closure line, fixed canthi, lash attachment, shelf, tangent continuity and profile thickness. Cite state/view filenames. Keep G2 NOT_RUN until independently reviewed; return FAIL/required changes rather than promoting zero eye rays to approval.
- Before executing the next deformation family: artist must author actual intermediate/contact targets and define a reviewed eye-local frame/seam. Then independently validate every intermediate state and Wink/Joy composition, source-bound anchors, self/coplanar/card intersections, UV winding, skin/eyeball clearance, zero socket backfaces and all 58 protected-key hashes. Render full-res and composited 128/64/32-px outputs. No new sculpt deformation trial has been executed yet; next-family status is NOT_RUN.

## Implementation and reproduction

Scripts: `tools/blender/morwen_production/eyelid_sculpt/`:

- `rebuild_baseline_07.py`: unchanged source rebuild, save and fingerprint.
- `structural_solver_07.py`: positive graph Laplacian and numeric modifier reference.
- `build_structural_candidate_07.py`: source-bound four-field diagnostic modifier, Blender 5.3 typed control API.
- `run_structural_qa_07.py`: candidate checks, preservation tests, disabled snapshot. **Stopped method; do not use for a third optimization trial.**
- `surface_checks_07.py`, `review_saved_candidate_07.py`: strict crossings, socket rays, replay and renders of existing candidate.
- `export_sculpt_handoff_07.py`: separate next-method authoring setup with source hash/protection assertion.
- `test_structural_solver_07.py`: exact boundaries, disconnected graph rejection, independent controls/identity, proper triangle crossings.

Python 3.13 + bpy 5.3.0; execution also used numpy 2.5.4, scipy 1.18.1, pillow 13.0.0. Blender 4.3 cannot read the newer .blend container; use 5.3. Source-download HTTP403 locally was resolved through the existing Actions download path; no verification bypass.

```sh
python -m unittest discover -s tools/blender/morwen_production/eyelid_sculpt -p 'test_*07.py' -v
python tools/blender/morwen_production/validate_shared_attempt_ledger.py tools/blender/morwen_production/_qa/morwen_shared_attempt_ledger.json
python tools/blender/morwen_production/eyelid_sculpt/review_saved_candidate_07.py --model assets/candidates/morwen-eyelid-07-structural/inspection/CANDIDATE_DISABLED_07.blend --qa assets/candidates/morwen-eyelid-07-structural/qa/STRUCTURAL_QA_07.json --out /tmp/new-m07-review --renders
```
