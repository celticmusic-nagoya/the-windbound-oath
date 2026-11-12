# MORWEN-BLENDER-17 — independent visual QA

**Technical QA PASS / Artistic QA FAIL.**

Reviewed actual four-view PNGs from GitHub Actions run `43243019859`, artifact `13954384498`, commit `9074d7c033a2f57b6284a1138a852bd5c01c9193`.

## Observations

- All four clay renders exist and the connected mesh renders.
- Front silhouette remains a near-straight tube with angular shoulder truncation and abruptly stepped pelvis/waist transitions.
- Side views show excessive broad bulge with sharp, stacked ledges around the lower waist/pelvis; chest/back profile is not natural.
- Back view has visibly asymmetric shading and an apparent crease; this is not sufficient evidence of intentional anatomy.
- Ring heights were sorted to avoid the initial assertion failure, but this can scramble anatomical region ordering when source landmarks are close or inconsistent. Sorting is a technical workaround, **not** a validated anatomical solution.

## Decision

**FAIL — not approved as character art.** Avoid further blind tuning of ring radius numbers. Inspect exact anchor heights and ratios against four canonical reference silhouettes; define a monotonic anatomically meaningful z profile; fit smooth cubic profiles with explicit front/back and waist/pelvis landmarks. Use an unlit silhouette pass for geometry QA before clay lighting. Do not add limbs, clothing, or head yet. Preserve reference PNG hashes and keep PR draft. No merge/publication.
