# Independent warning / boundary analysis — anatomical quad patches

Reviewer: `/root/body_art_qa`, separate AI reviewer, not geometry author. Date: 2026-11-17 UTC. **Read-only investigation: no geometry edited, no reference download/hash verification, no render rerun.** This is an AI technical/anatomical investigation, not human artist or device QA.

Machine-readable evidence: [INDEPENDENT_WARNING_ANALYSIS.json](INDEPENDENT_WARNING_ANALYSIS.json). The JSON includes all 15 new warning locations/vertex tuples and all confirmed source/candidate penetration face pairs, not just a net count.

## Inputs and definition

- Current stored mesh: `assets/candidates/morwen-rebuild-01/body-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend`, reopened with scripts disabled in Blender 4.3.2 to read its actual face connectivity and stored world coordinates.
- `body-local-v01/local-edit.npz`: frozen before coordinates (body-fit-v02), pre-cage rest coordinates, free/shoulder/leg/central-chest masks.
- Existing local before/after closeups and wire diagnostics, and the prior independent art review. No canonical reference state was reopened for a new SHA gate.

The old warning is `dot(n_rest, n_candidate) < 0`, where the normal is computed from the polygon's first three indexed vertices. Independently reproduced: **38 before, 36 after; 17 removed, 15 new**. This is a source-relative orientation diagnostic, not automatically a proof of inversion. Original pose, deformation, triangulation and normal rotation can all affect it.

## The 15 new flags are not knee flags or directly mixed-boundary faces

All 15 lie in the shoulder / side-thorax / axilla / proximal upper-arm transition. Seven have positive X and eight negative X. Their stored-after face centroids span approximately `|X|=.0529–.0747`, `Z=.7167–.7924` in normalized body coordinates. Their corresponding pre-cage Z range is `.6827–.7407`. None is on the knee patch.

Every flagged face has **four free vertices and zero protected central-chest vertices**. They are interior editable faces, not mixed free/fixed faces. A constrained-boundary influence can still propagate inward; calling them simply “boundary faces” would be inaccurate.

Angles below compare first-triangle normals. Area ratio uses that triangle, not the whole quad area. Values are rounded; full precision and the explicit vertices/centroids are in the JSON.

| Face ID (old/source topology) | Side | After centroid Z | Angle vs rest before → after | Local before→after turn | Area after/before | Largest adjacent-face dihedral after |
|---:|---|---:|---:|---:|---:|---:|
| 3176 | X+ | 0.792 | 22.2° → 99.2° | 78.5° | 1.052 | 56.1° |
| 3807 | X+ | 0.774 | 40.3° → 100.3° | 63.2° | 0.698 | 54.7° |
| 3810 | X+ | 0.761 | 6.9° → 102.1° | 104.8° | 0.382 | 74.0° |
| 3811 | X+ | 0.770 | 18.2° → 106.4° | 93.7° | 0.749 | 65.8° |
| 3859 | X+ | 0.717 | 21.1° → 97.6° | 85.3° | 0.945 | 118.8° |
| 4277 | X+ | 0.778 | 13.1° → 97.0° | 87.6° | 0.861 | 69.9° |
| 4278 | X+ | 0.780 | 11.4° → 92.1° | 81.3° | 0.533 | 64.6° |
| 10002 | X− | 0.746 | 20.4° → 110.8° | 99.5° | 0.247 | 166.1° |
| 10057 | X− | 0.774 | 86.8° → 98.8° | 18.6° | 0.785 | 46.8° |
| 10059 | X− | 0.755 | 6.1° → 97.0° | 98.6° | 0.156 | 100.2° |
| 10060 | X− | 0.763 | 6.4° → 119.1° | 120.2° | 0.235 | 68.9° |
| 10061 | X− | 0.771 | 5.0° → 122.5° | 118.2° | 0.321 | 61.6° |
| 10527 | X− | 0.778 | 19.3° → 115.6° | 100.2° | 0.640 | 62.3° |
| 10528 | X− | 0.780 | 22.6° → 94.1° | 78.0° | 0.632 | 50.0° |
| 10688 | X− | 0.785 | 12.8° → 97.8° | 87.3° | 0.803 | 75.0° |

### Cause classification

1. **Strong compression / fold evidence:** Faces 3810, 10002, 10059, 10060 and 10061 lose more than 60% of first-triangle area while rotating strongly. Face 10002 has area ratio about .247 and an adjacent dihedral about 166.1°; face 10059 has area ratio about .156 and an adjacent dihedral about 100.2°. These warrant an explicit folded-surface investigation rather than merely relabeling their normals.
2. **Large orientation migration with remaining area:** Several other faces rotate about 78–118° locally. Their normal flag is not a tiny floating-point threshold crossing. Even where the two triangles of a quad still point in broadly similar directions, the surrounding surface can double back or pass through another part of the axilla.
3. **Threshold-sensitive orientation case:** Face 10057 was already about 86.8° from rest and becomes about 98.8°, with only about 18.6° local turn. This illustrates why each >90° rest-relative flag cannot be treated as the same defect, and why deleting one flagged face cannot itself prove that a fold was repaired.

The code's bi-Laplacian objective has hard exterior pins and soft positional handles, but no orientation-preserving Jacobian constraint or collision barrier. A lower smoothness residual can therefore coexist with local surface compression, turning through a neighbouring sheet, and a deep axillary groove. That is the supported causal risk; this investigation does not infer an unknown rig or animation cause.

## New self-intersection baseline — actual penetrating geometry found

I added a separate local crossing screen instead of interpreting the rest-normal warning as collision evidence:

1. Build the saved mesh's loop triangles and a BVH with zero inflation.
2. Inspect candidate pairs touching at least one vertex of the editable mask, from different polygons. Exclude triangle pairs sharing a vertex ID from this particular strict-piercing screen to avoid counting their expected common contact.
3. For each remaining pair, test edges against the other triangle using an interior segment parameter and strict triangle-interior barycentric coordinates (normalized-coordinate epsilon `1e-9`). Coplanar/contact-only cases are classified separately, not silently declared clean.
4. Use the same saved-after triangulation for the before and after coordinates so a changed tessellation does not manufacture a count change. This controls comparison but does not certify all alternative quad triangulations.

| Distinct polygon pairs with confirmed strict noncoplanar piercing in this screen | Count |
|---|---:|
| Before local fairing (body-fit-v02 coordinates) | 106 |
| Current saved local-v01 coordinates | 59 |
| Newly introduced polygon pairs | 23 |
| Removed polygon pairs | 70 |

All BVH candidates in this tested subset confirmed strict penetration; there were no coplanar-only or unconfirmed candidates in that subset. `exact_non_coplanar_penetration_screen.after_pairs` in the JSON contains **all 59** current pairs; `before_pairs`, `new_pairs` and `resolved_pairs` retain the complete comparison.

**Static local collision screening is FAIL for the current source.** A drop from 106 to 59 is not clearance, and the 23 new pairs cannot be hidden by the 70 removed pairs. This is a conservative scoped finding, not a complete all-contact collision certificate: shared-vertex/edge folds, coplanar overlap and alternative triangulations still need their own tests. No source mesh was modified to run this investigation.

## Safe replacement boundaries and protected topology

Independent connectivity classification from the current face list gives:

| Current source-face / boundary class | Count |
|---|---:|
| Faces whose four vertices are free | 3,264 |
| Faces whose four vertices are fixed | 8,926 |
| Mixed free/fixed faces | 310 |
| Free/fixed crossing edges | 310 |
| Faces touching the 346-vertex central chest mask | 412 |
| Central-chest-touching faces that also touch a free vertex | 68 |

A shape-only pin on 9,080 vertices is weaker than preservation of their whole incident surfaces. To preserve the exterior's **shape and topology**, keep all 8,926 fixed faces and all 310 mixed faces (9,236 faces) with their original ordered vertex tuples. Freeze the **318 free vertices incident to those mixed faces** as an additional collar if those faces must also retain their exact geometry. To preserve only the entire central-chest incident surface requires freezing 68 adjacent free vertices, in addition to the existing 346 central vertices.

These are conservative preservation conditions, not a command to replace all 3,264 all-free faces. Select smaller shoulder/axilla and knee disks around the actual defects; do not remove a mixed protected face merely because one of its vertices is free. Boundaries must reference the current local-v01 source geometry, not silently revert to the pre-local or pre-cage shape.

The boundary of the full all-free-face region contains **314 boundary edges arranged in 11 closed, degree-two loops**, not just one clean annulus per shoulder/leg. The shoulder region includes small holes around pinned measurement extrema; the legs also have separate thigh and ankle loops. The JSON records loop sizes/centroids. Do not assume that two ring vertex counts can simply be zipped together. The author's narrower all-free dual-graph disk selections are a better starting point, provided the resulting boundary cycles and all defect/intersection coverage are recorded explicitly.

For a protected-boundary patch:

- Retain source IDs as attributes for surviving vertices and faces. Compare protected coordinates, ordered face tuples and adjacency by those source IDs; new element allocation must not obscure a protected-region change.
- Keep the ordered boundary cycle, its coordinates and edge incidence exactly. No T-junction, unwelded duplicate seam or unapproved boundary resampling.
- New interior topology may differ. Record deleted source faces, retained collar faces, new faces, and the patch-to-source correspondence separately.
- The original source reports zero open boundary edges and zero edges with more than two incident faces. A disk replacement must retain that global closed-surface property rather than turn a deleted warning region into a hole.

## Evaluation must survive old-face deletion

A warning is **not resolved** merely because its original face ID no longer exists. The following combined test is recommended for the candidate:

1. **Persistent geometric samples:** Freeze the old 15 face centroids plus several interior/edge-near samples per face, alongside samples from every current penetrating region. Preserve a patch correspondence (for example, the proposed harmonic-UV mapping) so each sample remains located on the rebuilt surface. Verify UV coverage, orientation and uniqueness; a sample that maps outside the new patch or onto multiple overlapping UV triangles is unresolved, not removed.
2. **Surface coverage and boundary continuity:** The sample regions must still have a continuous sheet with nonzero area. Missing faces, collapsed area, retreating the sheet out of the defect region or a new open seam cannot count as repair. Report patch coverage, its boundary conditions and static silhouettes before/after.
3. **Normals in anatomical context:** Recompute the old orientation diagnostic at tracked samples and record before/after vectors. Because pose can legitimately change a rest-relative normal, combine this with boundary-propagated outward orientation / a declared anatomical local frame and neighbouring-surface continuity; do not make the first-three-vertices diagnostic the sole truth.
4. **Real collision clearance:** Run broad-phase plus explicit triangle-triangle/contact tests on every rebuilt face against the whole body and the retained collar, not just on old IDs. Log spatial crossing segments/locations and source-patch labels as well as face IDs. Require no unresolved piercing/coplanar-area overlap in the changed region and no new contacts elsewhere. Report pre-existing out-of-scope contacts separately. Excluding all adjacent/shared-vertex pairs is insufficient by itself: folded adjacent interiors require a separate adjacency-aware test.
5. **Quad fold checks:** Test both diagonals, triangle area, projected bow-tie edges, signed local-chart Jacobians, nonplanarity/twist and adjacent-face dihedral across every new face and patch seam. A sum or average polygon normal can conceal a folded quad. Pre-register tolerances in normalized units and report worst locations, not only aggregate counts.
6. **Bending / flexion stress:** In addition to static fold tests, use explicitly documented temporary shoulder and knee bending poses (e.g. shoulder 0/15/30°, knee 0/15/30/60°) with stable pivot/weight definitions, then rerun collision and fold/area checks. A temporary geometric stress deformation is not a production rig; if no valid flexion test can be executed, mark that test NOT_RUN and do not certify deformation readiness.
7. **Independent visual QA:** Reopen the saved candidate and inspect matching shoulder/axilla/knee/shin close-ups and all body views. A smooth mathematical disk can still have the wrong deltoid, axillary depth, patella, calf or standing-line anatomy.

A candidate should not receive technical acceptance simply because it has fewer faces, fewer remembered IDs, fewer rest-normal flags, or a lower Laplacian energy. Its protected surface must remain intact and its new geometry must actually pass the coverage, collision and folding tests.

## Current decision / handoff

- Read-only warning localization and source-boundary analysis: completed.
- Current local-v01 static noncoplanar crossing screen: **FAIL** in the tested local region.
- Proposed quad-patch candidate: **NOT_RUN**; no candidate geometry was authored by this reviewer.
- Bending stress and full collision/quad-fold acceptance for the new candidate: **required, not yet run**.
- Whole-body G2 remains FAIL from the prior review. No adoption, source overwrite, merge or publication is authorized by this analysis.
