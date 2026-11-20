# MORWEN — candidate readiness and first real matched-render gate (2026-11-20)

Status: **EXECUTION GATE / NO CANDIDATE ADOPTED**. Existing owner Draft PR #427. Baseline HEAD `ac2297aee2ef6530cd60a9b30b4da211d0ca0a62`.

## Verified source inventory — do not confuse tool smoke with actual character
| Arm | Exact available evidence | Editable Morwen comparison input | Gate |
|---|---|---|---|
| A — anime VRoid/VRM | Blender 5.3 VRM Add-on 4.10.5 fixture import/export/reimport and CPU Cycles render PASS, run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44678376702 | No licensed, real **anime human base** model for Morwen located in this audit; fixture is not a usable Morwen base | **BLOCKED** pending actual source, license, SHA, topology |
| B — authored stylized sculpt | Existing PR #427 head studies and rendered candidates; known flat-slab/voxel G2 FAIL | No independently G2-acceptable editable sculpt verified; failed geometry not to be silently recycled | **BLOCKED** pending actual new sculpt method |
| C — Blender Studio Human Base Meshes v1.4.1 | Exact ZIP SHA256 `811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515`; Blender 5.3 direct audit run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44630228845 | `STYLIZED_Head` 4,410 vertices/4,408 faces; `STYLIZED_Body_Female.001` 13,020 vertices/12,894 faces; editable source verified; license statement for exact bundle **not yet independently preserved** | **TECHNICALLY READY / LICENSE BLOCKED FOR REDISTRIBUTION** |
| Excluded older MakeHuman OBJ | Blender import run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44550645526; 154 connected components and long-haired dressed figure | Not a neutral sculpt base, source suitability G2 FAIL | **REJECTED** |

## Required inputs and exact first executable task
1. **Do not rerun** successful VRM fixture, Blender installer, MakeHuman import, source ZIP audit or reference extraction.
2. Inspect `tools/morwen_authored_sculpt/layer0_landmarks_v1.json` and artifact https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44682957999/artifacts/14605242741: **46 actual coordinates**, 15 occluded entries; all measurements are 2D and manually annotated. Independent review `docs/qa/MORWEN_LAYER0_REGISTERED_LANDMARKS_INDEPENDENT_REVIEW_20261120.md` flags front/profile ear correspondence and estimated shoulders.
3. Codex: verify the official bundle's exact redistribution terms (official source only), reacquire the **pinned** ZIP by SHA, load only the actual stylized head and female body in Blender 5.3, **without any destructive sculpt edits**, render front/right/back/left and 3/4 with fixed neutral clay, Cycles CPU, a common normalized height, and export editable `.blend`, exact mesh counts/transforms, source hashes, and QA JSON. Keep it a *source-only comparator*, not a Morwen candidate acceptance. Stop if rights cannot be verified.
4. Codex: implement comparison against **registered 2D reference** only when silhouette segmentation/subject registration are reproducible. Use registered landmark confidence and occlusion to avoid treating missing 3D anatomical keypoints as measured data. If a mesh does not contain the complete figure or has incompatible source poses, flag `NOT_COMPARABLE`, never fill missing anatomy with invented geometry.
5. A and B remain **BLOCKED** until exact real editable inputs, licenses and SHA are verified. Do not manufacture generic spheres or proxy face grids to claim three-way comparison. No G2 PASS until independent review of real renders.
6. Outputs in the existing PR's Actions Artifact: actual `.blend`, four/five-view PNGs, wireframe, mesh inventory JSON, `source_manifest.json`, `qa.json`, per-file SHA256; retain immutable original provenance and no auto-adoption.

## Completion/stop criteria
- **Technical PASS**: pinned source SHA, documented lawful use, exact Blender 5.3 mesh objects, saved/reopened .blend, reproducible neutral renders, camera/render settings recorded, artifact present.
- **Stop/BLOCKED**: license ambiguity, wrong object identity, inconsistent source SHA, missing geometry, repeated identical render failures or failure to reopen.
- **G1 PARTIAL** (official reference hash and registered 2D coordinates PASS, camera calibration and candidate visual matching NOT_RUN); **G2 NOT_RUN**; **G3 NOT_RUN** for accepted Morwen geometry; **G4 NOT_RUN**.
- Never merge main, replace canon, publish or open a new PR for this task.
