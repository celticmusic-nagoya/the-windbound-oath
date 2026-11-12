# BLENDER-31 | Render environment failure analysis

Status: BLOCKED — stop retries after two failed attempts.

## Evidence
- GitHub Actions run 43330825170: FAIL. A source edit inserted literal `\\n` sequences, causing a Python syntax error before rendering.
- GitHub Actions run 43331252072: FAIL. Preflight and build PASS; render failed with `RuntimeError: Error: Build without OpenImageDenoiser`.
- BLENDER-01 regression PASS on both attempts.
- No five-view art QA is justified by these runs.

## Structural cause
The Ubuntu-packaged Blender runtime lacks the OpenImageDenoiser feature requested by the active render configuration. Preflight currently checks module presence but not render-time feature compatibility. A second, independent defect in the initial patch was fixed before the second run.

## Alternative approach (NOT YET RUN)
1. Separate source-code syntax checks from Blender runtime QA.
2. Prefer EEVEE CPU/headless-compatible render for silhouette/framing QA, or explicitly disable Cycles denoising for all view layers and compositor nodes before a single controlled run.
3. Add a small preflight smoke render that tests the chosen engine and fails before the five-view batch.
4. Keep image QA as a separate step requiring RGBA silhouette, transparent background, margins, and human visual review.
5. Avoid changing anatomy or approving art until actual five-view images are inspected.

No production assets, canonical references, main branch, or published site changed.
