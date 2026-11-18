# MORWEN Method B — independent visual rejection and method switch (2026-11-18)

Evidence: Actions run 44235548355; artifact 14397158572. Actual four-view Blender mesh renders reviewed, not merely CI success.

G1 BLOCKED: formal facial-feature matching remains uncalibrated.
G2 FAIL: frontal surface exhibits severe vertical crease artifacts and a collapsed nasal region; lateral views have an unnaturally flat, vertical posterior cutoff, disconnected-looking nose projection, no convincing eye/mouth/cheek planes. Does not resemble an approved Morwen sculpt.
G3 LIMITED_PASS: .blend generation, re-open, closed quad mesh and four renders. Retopology suitability, UV, rig, deformation NOT_RUN.
G4 NOT_RUN.

Method B is rejected for production use. The previous Method A (ellipsoid/Gaussian bump) was also rejected. Stop both procedural head-generation families. No further small coordinate/station edits under a renamed method. Next admissible route is an artist-directed sculpt from a legally verified, unmodified high-quality human head/base mesh (CC0 or license-compatible), or genuinely manual sculpt with explicit sculpt QA; verify topology, face aesthetics, and design fit. Do not claim finished Morwen assets from either failed method.

Sources:
- https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44235548355
- `tools/morwen_rebuild01/build_head_surface_study.py` (A)
- `tools/morwen_rebuild01/build_facial_planes_blockout.py` (B)
