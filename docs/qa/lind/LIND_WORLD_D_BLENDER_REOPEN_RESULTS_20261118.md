# WORLD candidate D — independent Blender reopen results 2026-11-18

Source: GitHub Actions run 44140823556, artifact 14354487092 (`lind-world-d-blender-reopen-qa`). The downloaded artifact was opened and `scene.json` and `geometry.json` directly inspected after successful CI.

- Blender version: **4.0.2**; opened immutable `world-d.blend` after verifying SHA-256 `2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72`.
- Objects: **32**, of which **27 are meshes**.
- Packed original PNG: **1536×1024**, 3,586,379 bytes, SHA-256 `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620`; **PASS**.
- Geometry: **27 mesh reports**, **0 nonfinite vertices**, **0 zero-area faces**; **PASS** for these narrow structural tests.
- UV layers across all meshes: **0**; texture/UV game readiness **NOT_RUN / not established**.
- Prior independent WORLD candidate D QA: **1557/1557** sampled road points not buried, but maximum unsupported road gap **0.444855 candidate units**. Do not claim road support, walkability, collision or Android pass.
- G1 full spatial/camera/scale: **BLOCKED**.
- G2 finished geology/environment: **FAIL** (previous independent review; no new final-art render produced).
- G3 source SHA/Blender reopen/finite geometry: **PASS**; UV/material/game-asset readiness, navmesh and road support **NOT_RUN**.
- G4: **NOT_RUN**.

Next: inspect the existing render and decide a structurally distinct cliff/road-support technique without repeating the twice-failed periodic heightfield geology. Keep character team and Method C masonry ownership separate. No source edits, main merge or publication.
