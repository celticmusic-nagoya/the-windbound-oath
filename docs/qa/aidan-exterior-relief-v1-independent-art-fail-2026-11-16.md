# Aidan exterior-only relief v1 — independent image review (2026-11-16)

Run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43789139055
Artifact: aidan-exterior-relief-gate-v1 (14191223024)
Commit: 6aa6b7231d2727617fe06130f3c2e9d745b80607

## Verified
- Workflow succeeded. Blender completed, 3 main renders + one 48x48 PNG exist and PNG header/dimensions validated.
- Three evaluated meshes: 0 boundary edges and 0 nonmanifold edges each, per generated audit.
- Actual artifact was downloaded and visually inspected, including three-quarter/front/top views and 48px.
- G3: PASS for this bounded watertightness/render gate. Exact interpenetration, contact normals and full exterior-surface preservation require independent checks (NOT_RUN).
- G2: **FAIL**. Image retains unmistakable rectangular block silhouettes; microrelief looks like low-frequency noise, not weathered individual stones. Top plane is flat and smooth; at 48px natural stone character is absent. This is not production-ready architecture.
- G1: BLOCKED pending authoritative house dimensional master; G4: NOT_RUN.

## Root cause and method decision
The procedural exterior-only noise method cannot solve silhouette and composition quality, even if its manifold/CI checks pass. Stop cosmetic parameter tweaking of the same block-based method. Preserve exact shared bearing as technical baseline, switch to independently authored scan-derived organic stone shells or properly fitted sculpted stone units with non-destructive exact mating interfaces. Require 48px art review before accepting any new art candidate. Never represent this technical model as completed CC0 scan-derived masonry.
