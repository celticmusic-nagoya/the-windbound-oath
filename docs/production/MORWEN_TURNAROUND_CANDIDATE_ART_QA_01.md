# MORWEN 3D turnaround candidate — independent visual review 01
Date: 2026-11-16
Status: FAIL as production-accurate 3D turnaround; retain as noncanonical visual candidate.

## Evidence
A newly generated composite character sheet was displayed in conversation after director approved a 7.5–8-head candidate. Source-of-truth is the five-image 2026-11-16 canonical set under `assets/canonical/morwen/2026-11-16/`. **The generated composite PNG is not yet stored in this PR**; QA is based on direct visual inspection of the displayed image, not on an image-diff or measured mesh. Do not claim source-file hash comparison for this generated image.

## Findings
- Overall recognizable design elements: purple bob, glasses, violet/gold hat and cape, academy uniform, bag and potion vials. **PARTIAL**, not certified exact.
- A `7.75 heads` label appears on the generated sheet but no pixel-calibrated head-to-height measurements were recorded. **BLOCKED** for numerical proportion verification.
- Front, side, back design details and accessory locations are not fully constrained by a shared geometric model. **FAIL** for production turnaround consistency; visual resemblance alone is insufficient.
- Garter must be anatomical right leg, continuous and rear-visible. It appears in views, but continuity and screen-left/screen-right under true orthographic orientation have not been geometrically established. **PARTIAL**.
- The composite includes a small Layer 0 depiction and proportion callouts, but is not a verified orthographic source with consistent landmarks. **FAIL** as a Blender modeling master.
- No Blender geometry, UV, rig, render, game integration or Android QA was performed.

## Quality gate status (new turnaround candidate)
G1 FAIL for production-master eligibility (exact source-detail fidelity and cross-view geometry not established).
G2 PARTIAL (attractive concept illustration; independent production-art approval NOT granted).
G3 NOT_RUN (no measured pixel geometry/alpha/camera validation).
G4 NOT_RUN.

## Method switch — next step
Do **not** repeat whole-sheet unconstrained image generation as the primary fix. Produce each orthographic view as a separate controlled candidate against the 2026-11-16 source, using common anatomical landmarks and measured head-height. Validate front/back/left/right cross-view features, right-leg garter, seams and accessories before assembling a single sheet. Preserve original images and this failed candidate as QA evidence; never promote without director approval.

No canonical files, game assets or main changed in this QA.
