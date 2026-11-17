# Morwen realistic basemesh — four-view head visual review (2026-11-17)

## Scope and evidence
- Reference: unmodified low-glare 512×768 orthographic PNGs from https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44032196306
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44032196306/artifacts/14305024028
- Mesh: Blender Studio CC0 `GEO-body_female_realistic`; NOT an approved Morwen model.
- Review performed using crops from front, left, right, and back render PNGs, with no pixel retouching or geometry modifications.

## Visual observations
- Front: chin outline and neck junction visible; front facial structure, shoulders and upper torso can be evaluated visually.
- Left/right: underside of chin, jaw profile and neck transition are distinguishable in the raster images.
- Back: skull-to-neck and shoulder transitions visible; does not reveal anatomical chin.
- The low-glare shader resolves the prior overexposure sufficiently for this visual comparison.
- Visual visibility **does not identify exact 3D chin/head-top vertices or coordinates**. Do not infer numeric head counts or mark `reviewer_confirmed` from these crops.

## Gate and next productive task
- G3 image rendering: PASS (diagnostic only).
- G1 canonical Morwen matching: BLOCKED; G2 Morwen artistic quality: NOT_RUN; G4 game/runtime: NOT_RUN.
- Preserve original official references and basemesh hashes. A reviewed anatomical point must have 3D position, vertex or triangle evidence, and front/side confirmation.
- **Stop condition:** no further scanline-only iterations or guessed chin Z coordinates. Next task should establish a source-aligned canonical 3D silhouette specification and a *new isolated candidate* with visual G1/G2 comparison, while leaving canonical assets unchanged.
