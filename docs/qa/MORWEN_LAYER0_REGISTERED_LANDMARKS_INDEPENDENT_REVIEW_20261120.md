# Independent QA — Morwen Layer 0 registered 2D landmarks (2026-11-20)

**Owner:** existing Draft PR #427. **Reviewed HEAD:** `ab33d50814db1993bd1f84b5b1ad24c0e683b67b`. **Scope:** independently inspect actual registered overlay PNGs and metadata; no model/sculpt changes or canon adoption.

## Verified evidence
- Successful GitHub Actions run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44682957999
- Exact artifact inspected: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44682957999/artifacts/14605242741
- Inspected files: `registered/{front,right,back,left}_landmarks.png`, `registered/registered_landmarks.json`, `reference_verification.json`, `four_view_contact_sheet.png`; source manifest `tools/morwen_authored_sculpt/layer0_landmarks_v1.json`.
- Original reference bytes pass all 4 source SHA-256 comparisons. JSON annotation SHA256 in artifact: `8f20b39f01d96dfffbcd8b2232254ee8e491f2390e2ddd7528213e1bb064c22f`.
- Source image size 384×1024; registered silhouettes use alpha-bounds height and an **estimated** per-view horizontal stance anchor, not calibrated 3D cameras.

## Independent counting and layout checks
| View | Defined labels | Coordinate-bearing | Visible | Partial | Estimated | Occluded | Estimated stance center x |
|---|---:|---:|---:|---:|---:|---:|---:|
| Front | 17 | 16 | 11 | 2 | 3 | 1 | 213 |
| Right | 15 | 12 | 10 | 0 | 2 | 3 | 202 |
| Back | 14 | 8 | 5 | 1 | 2 | 6 | 171 |
| Left | 15 | 10 | 8 | 0 | 2 | 5 | 198 |
| **Total** | **61** | **46** | **34** | **3** | **9** | **15** | — |

- The **46-point** claim means 46 coordinate-bearing landmarks; 15 additional entries intentionally express occlusion. Not all 46 are pixel-exact: 9 are labeled visually estimated and 3 partially visible.
- Visual inspection of all four overlay PNGs found the sampled facial and buckle markers placed near the named features. No obvious full-image flip or wrong view ordering in overlays.
- Right/left profile eye height is y=122 on both; nose-tip y=137 on both; chin y=177 on both. Front eye y=124/125, nose y=143, chin y=180. This is **2D consistency evidence only**, not a calibrated 3D reconstruction.

## Qualified issues — DO NOT treat as passes for anatomical reconstruction
1. **Front ears:** front partially visible ear labels y=143/144 versus both profile ears y=125 (approx. 18–19 px difference before view registration). The views may locate different ear subfeatures, be illustrated with small pose differences, or include hair occlusion. Flag `ANATOMICAL_CORRESPONDENCE_NEEDS_REVIEW`; do not triangulate ear depth from these labels or silently change coordinates.
2. **Shoulder and neck:** all neck/shoulder anchor locations are estimated or partial. Their uncertainty radii cannot establish joints/bones, and shoulder location is not a mesh topology constraint without independent anatomical review.
3. **Horizontal origin:** stance centers front 213, right 202, back 171, left 198 are manually estimated. Image x-center and any model bone axis cannot be equated; registration is suitable for comparisons only with its assumptions disclosed.
4. **Projection and absolute scale:** original art is not a calibrated 4-camera dataset. No verified 3D depth, absolute body scale, camera lens/angle, mesh topology, UV, rig or morphs can be inferred from the 2D coordinates alone.
5. **Costume asymmetry:** side buckle labels on left are occluded and must not be mirrored. The visible front/right/back placements are image-space observations only.

## Gate decision and next bounded actions
- Source image SHA/metadata and landmark overlay **technical QA PASS**. This independent review is **not** an independent G1 source adoption decision or G2 art acceptance.
- **G1 PARTIAL**: four source SHAs and 46 coordinate-bearing markers verified, but correspondence of front ear labels, shoulder/neck anchors, and orthographic projection/scale remain uncalibrated.
- **G2 NOT_RUN**: no real matched editable A/B/C candidates with independent art review.
- **G3 NOT_RUN**: no accepted Morwen geometry, topology, UV, weights, morphs or actual render QA.
- **G4 NOT_RUN**: no game integration or Android testing.
- Next: review anatomical correspondence of front ears without inventing hidden anatomy; inventory exact model file hashes, licenses and editability for A=VRoid/VRM, B=art-directed sculpt, C=verified CC0 comparator. Compare only **available lawful real candidates** at normalized scale with matched cameras/clay lighting and quantifiable masks; missing candidates stay BLOCKED.
- Do not repeat the successful reference/VRM fixture Actions, or restart failed slab/voxel geometry methods. No new PR/main merge/canon replacement.
