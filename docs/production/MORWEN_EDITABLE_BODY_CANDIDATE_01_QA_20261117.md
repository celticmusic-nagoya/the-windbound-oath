# Morwen — editable body candidate 01 QA (2026-11-17)

## Actual generated assets
- GitHub Actions: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44036495955 (SUCCESS)
- Artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44036495955/artifacts/14307014394
- `morwen_body_candidate_01.blend` (13,162,990 bytes); SHA-256 `f2cc214226a163d636154224756dd1c8c47d4af4cf32b304fe0eb01a979a5c57`.
- `MORWEN_BODY_CANDIDATE_01_{front,back,left,right}.png`, each with SHA-256 in `candidate_manifest.json`.
- Source CC0 .blend SHA-256 `e5e9d30a7e6bb385fed21459dce68d1ad0d06e7bde4f9626696dbfda07cd541a` unchanged.
- Realistic original mesh 10,582 vertices; candidate 10,582 vertices, 10,580 moved. Editable mesh, not merely an image or primitive proxy.
- First-pass deformation parameters: shoulder X -0.055; waist X -0.065; hip X +0.012; leg X -0.015 (smooth regional influences).

## Evidence and gate
- G3: source hash, editable mesh generation, four diagnostic PNGs PASS; rig, UV/material preservation and game optimization NOT_RUN.
- G1: **BLOCKED**. Candidate is a mildly adjusted generic human basemesh, not a verified Morwen silhouette. Skull/chin/sole anatomical points unreviewed, 7.5–8 heads unverified, four canonical view alignment not calibrated.
- G2: **NOT_RUN** independent full-body artistic comparison. Candidate lacks official Morwen facial features, hair, costume, garter and other asymmetric design.
- G4: **NOT_RUN** Android/WebGL and regression checks.
- Production approval: false; no canonical file replacement, main merge or publication.

## Next safe gate
Perform side-by-side candidate-vs-source and candidate-vs-canonical comparison using *identical orthographic scale and pose where possible*. Quantify whether actual deformations materially improve the full-body silhouette; if not, stop micro-parameter tuning and redesign the deformation method from canonical shape constraints. Do not claim high-end finished geometry or start costume details prematurely.
