# MORWEN-BLENDER-02 — independent numerical anatomy QA (partial)

Source: PR #246 commit `a45ca2815675a4d186f08624de8d0329a6ed730c`; `assets/candidates/morwen-blender-01/anchors_candidate.json`. Review is read-only. This is **not a completed visual/art QA**.

## Verified from source JSON
- Four facings, each with 12 anatomical anchor entries; 48/48 normalized x,y values in [0,1].
- Approximate projected segment lengths (pixels, rounded), calculated with image 384×1024 scaling:

| Facing | Upper arm L/R | Forearm L/R | Pelvis–knee L/R | Knee–ankle L/R |
|---|---|---|---|---|
| Front | 127/127 | 147/148 | 242/242 | 241/241 |
| Right | 132/132 | 149/149 | 240/240 | 241/241 |
| Back | 126/126 | 150/150 | 243/243 | 241/241 |
| Left | 132/132 | 149/149 | 240/240 | 241/241 |

These are 2D projected measurements; similar lengths are **not** evidence of correct anatomical depth, skin deformation or 3D proportions.

- Alpha bounding boxes: front [54,17,373,1004], right [93,16,314,1003], back [14,16,331,1002], left [63,16,281,1003].
- Measured ground row in source JSON: front 1003, right 1002, back 1001, left 1002; 2 px maximum spread.
- Occluded inferred points: right view anatomical L shoulder/elbow/wrist/knee/ankle (5); left view anatomical R shoulder/elbow/wrist/knee/ankle (5). These 10 points are **not visually measured**.

## Findings / gates
- **MAJOR / unresolved:** Ten occluded joint projections and 48px provisional half-depth must be verified against a coherent 3D construction. Do not claim 3D anatomical accuracy.
- **MAJOR / NOT_RUN:** Pixel-level visual comparison of actual four overlay PNGs and 4-view neutral proxy against source references; no independent visual approval.
- **NOT_RUN:** Independent Blender execution and mesh/weight deformation QA. PR #246's technical PASS is implementation self-QA only.
- **NOT_APPLICABLE:** Hairstyle, knee-high socks, asymmetrical costume and left-facing satchel/hat ornament/shoulder crest checks: the current neutral proxy does not contain finished costume/hair.
- **PASS / numerical-only:** No out-of-range anchor coordinates; projected segment lengths are broadly consistent and the source ground rows are within 2 px.

## Recommendation
Proceed with **MORWEN-BLENDER-03 as a candidate-only single 3D base**, with explicit depth uncertainty and four-view visual overlay gates. Require independent visual inspection before adoption or production use. Preserve source SHA, left/right anatomy, no mirrored asymmetric source art. No old asset deletion, merge, publication or formal adoption.

## Scope and evidence
This report is derived directly from the GitHub JSON and arithmetic checks performed by ChatGPT. The overlay images and .blend have **not** been visually inspected or executed in this QA pass. Do not relabel this report as a complete independent art/anatomy review.
