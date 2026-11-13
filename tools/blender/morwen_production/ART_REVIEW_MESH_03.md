# MORWEN-MESH-03 — independent visual art review

Status: **G2 FAIL**, reference comparison incomplete. Review of five renders from Actions run 43392444119.

## Observed failures
1. **Face silhouette:** elongated capsule/egg rather than approved youthful anime-styled cheeks and tapered chin.
2. **Facial construction:** eyes, nose and lips visibly float on top of a continuous featureless capsule; no integrated orbital/nasolabial topology.
3. **Hair:** evenly spaced vertical tube-like locks and helmet-shaped back. Fails the approved soft, layered violet bob silhouette.
4. **Eyes and glasses:** disproportionately exposed eyes and geometric rims; lack anatomical integration and controlled lens clearance.
5. **Camera/framing:** head occupies a small portion of 512px frame; use a consistent tighter orthographic crop and a separate in-game-size check.

## Root cause and change of method
The two consecutive Blender modeling attempts (`build_head_review.py`, `build_face_detail_review.py`) share the same primitive/cross-section approach and both failed G2. **Do not run a third variant of this approach.**

Use reference-guided sculpting or a licensed, deformation-ready human/anime base mesh followed by manual sculpt + retopology. Verify licensing and source before importing. Blender Python is appropriate for scene assembly, UV/materials, orthographic reference alignment, render and structural QA—not for asserting a finished face from unreviewed parametric anatomy.

## New production acceptance requirements
- Four canonical Layer 0 image hashes pass; supplemental 1536x1024 design sheet used only for visual details.
- Face has continuous quad loops around eyes, mouth, cheeks, nose and jaw. Separate eyes and glasses are allowed; the face itself cannot be a featureless capsule.
- Head shape, chin, cheeks, nose bridge, ears, bangs and bob silhouette match official references in front, profile, back and 3/4.
- Five 512px+ Blender render views with head filling at least 65% of image height, plus 96px/128px downscale.
- An independent human art review must approve G2. Scripts cannot declare aesthetic PASS.
- Right-only garter: anatomical +X, front screen left, back screen right; no mirrored left garter in later costume stages.
- Do not replace `MORWEN_MASTER_APPROVED.blend`, modify official PNGs, merge to main or publish.

## Status
G1: PARTIAL (references identified, geometry not matched)
G2: FAIL (visual evidence)
G3: PASS for previous render execution, **not** for production mesh
G4: NOT_RUN
