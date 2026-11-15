# MORWEN-EYELID-08: independent 50% contact cage

**DISABLED / NOT ADOPTED.** Base: PR #325, ea14c1f281d475e4eccff2c12cebe62b69b9ccaf. This delivers a static 50% candidate, implementation, failed QA evidence and Claude review images. It does not resolve full Blink/wink animation or claim formal art approval.

## Source audit and protection (G1)

- Reviewed SCULPT_SETUP_07.blend, the complete seven-state/five-view contact sheet (35 images) and raw EYELID-07 QA. Prior Dirichlet family remains stopped; no old displacement, cancellation, pivot or key transfer was executed.
- Source file SHA256: a30b05af5369864578aea85b72f6c8e5100630d2ceb638c8a9a52add6e5defd7. The original Face has 1,972 vertices and **58 unchanged keys**: Basis, target_0..55, MORWEN_DESIGN_NoseDepth.
- Fresh source extraction exactly matched the saved EYELID-07 graph: 28 vertices/28 edges per eye, one connected cycle. Source-coordinate anchors R 1397 -> 1351; L 1264 -> 1207. These are source-authoring correspondences, **not formally approved anatomy**.
- Source Face was never remeshed, reindexed, given a modifier or deformed. Only its visibility changes in separate saved review documents. The unkeyed attachment-preview object is a disposable copy; removing its old patch faces and attaching its cards does not edit Face.
- Delivery reopens both source and candidate and compares a full protected signature: vertices/IDs, edges, polygon connectivity/material indices, smooth flags, object transform, UV coordinates, all key coordinates/names/order/relative keys/values/sliders/mutes, elm_patch and modifier inventory. Result: exact equality; signature `1a796bb8f22473f0f9a4d274a8b3719f0bd5a63aa8627878889cb86ed6d335c6`. The 58-key hashes also remain identical to the latest diagnostic supplied with PR #325.
- Full canonical v5.61 binary comparison remains BLOCKED. These are engineering baseline renders; no hair/costume redesign or formal asset replacement.

## Contact-cage specification

Two independent objects: `M08_R_CONTACT_CAGE_050` and `M08_L_CONTACT_CAGE_050`. Their topology and vertex numbers belong only to the new cages. Source Face remains intact as the hidden reference during review and the visible reference in the disabled delivery.

Upper/lower source chains are split at the bounded, uniquely matched source canthi. A shared longitudinal parameter set includes 33 uniform samples plus every original upper/lower/attachment knot. Both margins therefore refer to the same contact-guide columns. At 50%, their X/Z separation is exactly half of the neutral opening at matching parameters; **visible iris/sclera inside the half aperture is intentional**. Medial/lateral front vertices stay fixed. There is no central upper/lower contact at 50%; only the two canthi meet. The existing UNREVIEWED EYELID-06 curve supplies a source/calibration-bound guide, not an adopted closure design.

Each cage has one explicit opening loop (148 vertices) and an exact attachment loop (18 source boundary vertices). A constrained planar straight-line graph (PSLG) triangulates the concave attachment minus the opening, with hard boundary segments and a hole seed. Interior points use a 3-mm grid. Triangle `pYQ` prohibits boundary Steiner splits. This replaces the failed ruled quad connections, not a retuned Dirichlet field or polar zipper construction.

The final half surface is an explicit static target, not an interpolation of old Blink keys. It is a single-valued Y(x,z) graph. Front winding points anterior (+Y); rear winding is reversed. Rear vertices lie 0.6 mm behind the front along model anterior Y. Oriented side faces close the opening and attachment boundaries, giving a connected genus-one volume with Euler characteristic zero and no boundary/nonmanifold edges. **0.6 mm is anterior thickness, not uniform normal thickness**: measured minimum normal projection is only 0.0174 mm R / 0.0229 mm L near steep corners. This requires further thickness/art review before adoption.

New cage UVs use an independent affine fit to the source skin chart; tiny independent wall charts avoid zero-area UVs. Source UVs remain untouched. The fitted chart produces visible skin-colour/texture transitions in the candidate, requiring art review.

The second PSLG trial adds linear eye-obstacle inequalities at vertices of every overlapping projected cage/eye-triangle polygon. Rear skin must stay at least 0.2 mm anterior to the recorded eye surface. The 18 attachment vertices and two canthi per side remain locked; free front vertices can move anterior by at most 3 mm. Actual maximum moves: R 1.0292 mm, L 1.9967 mm. Infeasible constraints abort rather than moving protected anchors. X/Z aperture is unchanged.

Cards are registered on the disposable preview only. A bounded anterior lift enforces 0.1-mm clearance at the originally penetrating opaque samples (141 constraints, maximum vertex lift 1.3718 mm). This is insufficient: moving a card triangle can move additional opaque texels through the cage. No third adjustment was made after the second PSLG failure.

## Executed attempts and QA (G3)

| Trial | Structural result | Failure / action |
|---|---|---|
| M08-CONTACT-01 | Closed ruled quad shell, exact half aperture | Self-crossings R13/L6, attachment crossings R106/L114, bad normal/UV directions, five backface rays. Retired ruled connectivity; switched to constrained PSLG. |
| M08-PSLG-01 | Zero cage self/attachment crossings, normal/UV faults and socket backfaces | Cage/eye crossings R15/L23; opaque card samples inside shell R70/L71. Added explicit obstacle and preview-card constraints once. |
| M08-PSLG-02 | Cage, attachment and eye crossing checks zero; no socket backfaces | **Opaque card samples still inside R45/L23. FAIL; STOP family after two failures.** |

All previous attempt-ledger entries are preserved, with three EYELID-08 entries appended. `build_contact_pslg_08.py` now refuses a third build based on the cumulative ledger. Read-only inspection/rerender of the saved candidate remains available. No validation-bypass flag exists.

Final static cage checks:

| Measurement | R | L |
|---|---:|---:|
| Cage vertices / polygons | 672 / 1178 | 674 / 1182 |
| Boundary/nonmanifold edges; inconsistent directions | 0 / 0 | 0 / 0 |
| Degenerate triangles; non-anterior front normals | 0 / 0 | 0 / 0 |
| Self crossings, including positive-area coplanar overlap | 0 | 0 |
| Cage/attachment-preview skin crossings | 0 | 0 |
| Cage/eyeball crossings, including coplanar overlap | 0 | 0 |
| UV orientation disagreements; zero-area UV triangles | 0 / 0 | 0 / 0 |
| Opaque card samples inside closed shell | **45** | **23** |

Intersection checks use triangle BVH broad phase and strict interior noncoplanar crossings plus coplanar polygon clipping. Shared boundary contacts are permitted; positive-area overlaps fail. Eye clearance inequalities are a geometric piecewise-linear constraint; measured cage/eye crossings confirm the final stored mesh. Alpha-card collision uses 2,753 accepted samples, 15 barycentric points per card triangle with alpha >= 0.5, classified against closed-shell winding number. No unclassified card materials. This is **finite sampling**, not a continuous alpha-surface proof; even these finite checks FAIL.

Socket QA: 33x33 camera-plane orthographic rays per eye/view, 10,890 rays over front, +/-45 degrees and both profiles. Unlike EYELID-07's world-X/Z profile grid, these are not degenerate screen grids. Zero first-hit backfaces in all five directions. Source Face/templates are explicitly excluded; inspected geometry is preview skin, cages and original eyes. Alpha cards are skipped for socket occlusion. Background misses and expected half-aperture eye hits remain in JSON.

The cage Basis is already 50%: zero flips against Basis is **not a tested neutral-to-half animation**. Static normal orientation is tested separately. Full closure, 0..100 interpolation, Joy composition, full wink, rig/Armature binding, continuous lash collision, final game-size appearance and performance/Android remain NOT_RUN.

16 unit tests PASS: closed graphs, malformed/disconnected loops, shared knot preservation, concave-boundary/hole coverage and exact segments, manifold shell orientation, crossing/coplanar contacts, eye-clearance feasibility and rejection of locked infeasible anchors; card failures overriding partial geometry results.

## Delivery and Claude independent art QA (G2)

- `inspection/CONTACT_CAGE_DISABLED_08.blend`: original Face visible; cages and preview hidden from viewport/render, `enabled_for_production=false`. For review only, hide Face and show `M08_ATTACHMENT_PREVIEW_ONLY` plus both cage objects. Do not enable the four old UNAUTHORED M07 sculpt templates.
- `renders/half_050_front.png`, `half_050_q3L.png`, `half_050_q3R.png`, `half_050_left.png`, `half_050_right.png`: actual Cycles CPU, 384x384, 12 samples, nonblack world background. `REVIEW_SHEET_08.png` combines them. Codex inspected front, right-45 and left-profile. These are not Claude review results or final-size game composites.
- `qa/CONTACT_CAGE_DESIGN_08.json`: guide/contact columns, source IDs, topology, thickness, obstacle constraints and preview-card lift.
- **Authoritative outcome:** `qa/CONTACT_CAGE_COMPLETE_QA_08.json`. Raw geometry report alone is partial; delivery collision findings set the complete result to FAIL.
- `attempts/`: immutable first ruled guide/QA and first PSLG geometry/collision evidence. Original 35 EYELID-07 renders remain in PR #325 unchanged.

Claude should assess half-aperture shape, canthal tangents, shelf/creases, upper/lower volume, lash attachment and lift, source-aligned eye proportions, skin-chart transition and profile thickness. Cite image filename and eye side. Return required changes; do not infer G2 PASS from zero skin/eye intersection. No message has been sent to Claude and no independent review has been performed.

| Gate | Result |
|---|---|
| G1 | Protected source checks PASS; full canonical comparison BLOCKED |
| G2 | NOT_RUN; independent art review pending |
| G3 | **FAIL**: residual opaque card penetration; static cage subchecks pass |
| G4 | NOT_RUN; no game integration, animation binding or device test |

Next structurally different work: triangle-attached lash geometry authored against the contact surface, with continuous alpha-aware clearance and explicit silhouette approval, rather than another per-vertex sample-lift iteration. The static cage can serve as a disabled geometric reference. Authoring/validating that new lash topology is not completed in this task.

## Implementation

`tools/blender/morwen_production/eyelid_contact/` contains separate geometry, PSLG construction, bounded obstacle solver, preview-card clearance, triangle QA, protected-source verification, report combination and unit tests. The retired ruled builder is kept for provenance and source-guide extraction; it is not the final candidate. All executable modelling is Blender/Python; nothing is registered in the game.

Runtime used: Python 3.13, bpy 5.3.0, numpy 2.5.4, scipy 1.18.1, pillow 13.0.0, Triangle 20250106. Use Blender 5.3 to read the saved file.

```sh
python -m unittest discover -s tools/blender/morwen_production/eyelid_contact -p 'test_*08.py' -v
python tools/blender/morwen_production/eyelid_contact/qa_contact_cage_08.py --candidate assets/candidates/morwen-eyelid-08-contact/inspection/CONTACT_CAGE_DISABLED_08.blend --design assets/candidates/morwen-eyelid-08-contact/qa/CONTACT_CAGE_DESIGN_08.json --out /tmp/new-m08-review --renders
python tools/blender/morwen_production/eyelid_contact/verify_delivery_08.py --source assets/candidates/morwen-eyelid-07-structural/inspection/SCULPT_SETUP_07.blend --candidate /tmp/new-m08-review/CONTACT_CAGE_DISABLED_08.blend --out /tmp/new-m08-review/DELIVERY_VERIFICATION_08.json
python tools/blender/morwen_production/eyelid_contact/combine_qa_08.py /tmp/new-m08-review/CONTACT_CAGE_QA_08.json /tmp/new-m08-review/DELIVERY_VERIFICATION_08.json /tmp/new-m08-review/COMPLETE_QA_08.json
```
