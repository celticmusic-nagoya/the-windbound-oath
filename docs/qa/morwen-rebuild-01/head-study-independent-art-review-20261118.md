# MORWEN head-study independent visual review — 2026-11-18

Source: GitHub Actions run 44234611478, artifact 14396588515, four rendered files under `morwen-workspace/head-study-renders/`. Actual rendered mesh reviewed; not reference-only images.

## Gate decisions
- G1: BLOCKED for formal art matching; reference images are preserved, but no verified face-feature alignment or calibrated projections.
- G2: FAIL. Front face reads as a smooth egg-shaped volume with a narrow extruded nose, weak orbital anatomy, minimal eyelid/lip definition, absent ears, hair and glasses. Profiles show an abrupt beak-like nose and insufficient forehead–nose–mouth–chin transition. Back is featureless. These cannot be approved as a Morwen character head.
- G3: LIMITED_PASS for Blender 4.3.2 mesh generation, closed-quad topology test, saved/reopened .blend, and four renders. Deformation topology, UV, materials, rigging and game-ready geometry NOT_RUN.
- G4: NOT_RUN.

## Production decision
Reject this head as a production-quality asset; retain only as a technical surface-generation study. Do not repeat parameter tuning of the same ellipsoid-plus-Gaussian-bumps technique. Switch to artist-directed face sculpt with cranium, orbital rims, eyelids, cheek planes, nose bridge/alar wings, philtrum, mouth corners, ears and mandibular transitions, using the approved four-view visual references. Require visible four-view silhouette and 3/4 facial detail, then independent art QA before advancing to hair and accessories. Do not merge to main or overwrite canonical assets.

## Evidence
- Workflow: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44234611478
- Artifact ID: 14396588515
- Candidate script: `tools/morwen_rebuild01/build_head_surface_study.py`
- Candidate .blend: `morwen-workspace/MORWEN_HEAD_STUDY_UNAPPROVED.blend`
