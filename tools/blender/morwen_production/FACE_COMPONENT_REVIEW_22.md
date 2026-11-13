# MORWEN-FACE-22 — Component review from verified CI artifact

Source: GitHub Actions run 43425305773, artifact morwen-vroid-cc0-head-review, FACE_COMPONENT_INDEX.json.
Status: **MATERIAL-BASED CANDIDATE CLASSIFICATION ONLY**. No anatomical approval.

- Source Face: **2,054 vertices**, **34 disjoint connected components**. Complete, non-overlapping index coverage passed in CI.
- Component 0: **588 vertices**, material `F00_000_00_Face_00_SKIN` (1,064 faces). **Likely primary face skin**, unverified visually.
- Component 1: **102 vertices**, material `F00_000_00_FaceMouth_00_FACE` (128 faces). **Mouth-related candidate**, exact anatomical role unverified.
- Components 2–3: **75 vertices each**, `FaceEyeline` material (112 faces each). **Eye-line candidates**, side mapping unverified.
- Components 4–5: **75 vertices each**, `FaceEyelash` material (112 faces each). **Eyelash candidates**, side mapping unverified.
- Components 6–7: **62 vertices each**, `FaceMouth` material (96 faces each). **Mouth-related candidates**, unverified.
- Components 8–9: **61 vertices each**, `EyeIris` material (96 faces each). **Iris candidates**, side mapping unverified.
- Components 10–11: **61 vertices each**, `EyeHighlight` material (96 faces each). **Eye-highlight candidates**, side mapping unverified.

These IDs are specific to the source asset and indexing algorithm, not portable across models. Do not use these labels to deform mesh before visual verification. Source images, textures and mesh remain unchanged.

## Next QA / art actions
Render an **ID-colored diagnostic** (unique palette per component, front and oblique views) with a matching legend, preserving original topology and material assignments in source; identify left/right and overlapping facial islands visually. Then generate an edit mask that targets *only* verified skin/jaw components. Evaluate against manually annotated canonical landmarks, not generic percentage taper.
