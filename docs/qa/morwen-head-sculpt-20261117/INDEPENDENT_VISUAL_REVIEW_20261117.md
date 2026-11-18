# Morwen head study — independent visual review (2026-11-17)

**Input:** GitHub Actions run 44064066566, Artifact 14319881962, inspected `head_contact_sheet.png` showing front, back, character-left, character-right and two 3/4 head views. This is an independent review of the delivered candidate render, not a claim that the canonical images have been overlaid pixel-for-pixel.

**Overall: G2 FAIL.** Candidate remains UNAPPROVED. The technical geometry and measured 7.749997 head count reported in PR #399 are not independently re-measured here; technical status remains as reported by its existing QA, not elevated.

## Directly observed defects
1. Face identity: realistic adult facial planes, narrow eye opening, pronounced nose/philtrum and lower face do not communicate the approved anime-stylized Morwen identity. Major silhouette/plane redesign required, not another tiny numerical fit.
2. Front fringe: regularly repeated wedge-shaped panels with nearly equal widths and level ends. Mechanical segmentation, lacks layered sweep and intentionally varied grouping.
3. Back bob: evenly spaced thick pointed shell plates and smooth dome produce helmet-like silhouette. Requires art-directed sculpted locks, organic overlap and irregular length/curvature.
4. Profiles: chin/nose contour and head-hair mass feel realistic and blocky rather than character-directed. Ear/temple/hair occlusion needs reference-specific planning.
5. Glasses: gold circular frames present in all relevant views and can be retained as a modular technical candidate; fit, support at ears/nose, and character identity not yet art-approved.
6. Body/costume are out of this head close-up review. No statement about clothing completion.

## Corrective method — structurally different from failed attempts
- **Stop** automated face-fit parameter tweaking and radially/evenly generated hair plates; these have already failed twice.
- Establish front/profile reference overlays with calibrated camera scale and named anatomical landmarks. Use the actual approved design-sheet JPEG and four Layer0 images, with SHA verification; do not promote an earlier AI-generated turnaround.
- Sculpt the base facial surface with art-directed local mesh editing/brush strokes or equivalent high-quality sculpt workflow. Retain existing CC0 topology where feasible; avoid the previously rejected annulus/zipper eyelid construction.
- Sculpt/retopo the bob as a **small number of intentionally designed, asymmetric, overlapping broad hair masses**, followed by secondary locks; ensure back silhouette reads as continuous hair rather than an evenly segmented shell.
- First deliver one improved face front + side + 3/4, and hair front + back + side, with a contact sheet at real in-game display scale. Independent review before extending details.
- Existing technical candidate and its hashes are immutable evidence; new work in a separate candidate branch/Draft PR. No main merge, canon replacement, deletion or publication.

## Gate status
G1 BLOCKED (candidate fidelity not demonstrated); G2 FAIL (independent visual review); G3 PASS_TECHNICAL_SCREEN **as reported in PR #399**, not a full rig/UV/animation pass; G4 NOT_RUN.

## Completion requirement for next stage
Editable sculpt-ready .blend, materially different facial planes and non-repeating bob topology, 6-view review PNGs, source SHA evidence, reproducible render, explicit independent visual decision. A prompt or instructions alone do not count as implemented geometry.
