# ROUTE-MAT-01 Method C — actual candidate and independent handoff

Status: **ACTUAL MODEL + THREE PNGS GENERATED; QUALITY FAILED. NOT ADOPTED.**
PR #363 baseline `42fc98f0300ebd4bf6d82db89ad4c4a6f60358e3`; main checked at `5365e5f799e8212544ec1ab439b844bf1a093e52`.

## Outputs and actual execution

`assets/candidates/route-mat-01/method-c-01/` contains the exact two original CC0 Poly Haven source BLEND files, API metadata, source/rights/reference SHA manifest, saved candidate `render/abutment.blend`, neutral clay `front.png`, `oblique.png`, `side.png` (1280×1024), saved-file mesh audit, independent art review and execution logs. All files are covered by `SHA256SUMS` at the route-mat-01 candidate root. `abutment.blend1` is retained from the pre-denoise-recovery save; it is not the reviewed final file.

55 model mesh objects, 44,712 audit triangles (QA ground excluded). Original full source files are unchanged; both source MD5s also match the provider manifest. **Initial model used both source LOD3 meshes**, disclosed explicitly. The downloaded BLENDs contain higher LODs, but the candidate must not be described as using them. No PBR/normal/height images were used. Half-arch bridge abutment section is a study, not complete bridge/game integration. Right/inner termination faces are declared cutaway surfaces. Coordinates and scale are study values only; canonical transform/footprint/origin remain null.

The strategy uses real volumetric scan meshes fitted to individually authored irregular joint domains and a radial springer chain. It does not import/reuse A/B code, cuboid stone arrays or image displacement. A/B failures remain inherited, not reset. The scan-domain cutting method nevertheless creates broad artificial planes and sharp facets; a different input alone did not solve the final art problem.

## QA actually run

- G1 **BLOCKED** overall. Approved CG and world-original bytes SHA verified and both images viewed. Latest main AGENTS matches branch. Latest private Bible/addendum/status were read through authenticated GitHub; private text is not copied. Source authors, original download URLs, CC0 asset license and redistribution/derivative permission checked. No Irish geographic provenance is claimed. Full metric/placement/design adoption is unapproved.
- G2 **FAIL**. Separate reviewer opened all three actual PNGs and the official CG; exact image/BLEND hashes and detailed findings are in `render/independent-art-review.json` and `INDEPENDENT_ART_QA.md`. Broad quarry cut planes, pointed facets, flat/unsupported-looking coping and unnatural bedding/foundation fail the high-quality target. A declared cutaway alone is not counted as a defect. No 48px/actual game-size acceptance was established.
- G3 **FAIL**. Blender 4.3.2 actually saved/reopened the file in a separate process. Per-object bounds, UV area/presence, volume, boundary/nonmanifold/degenerate checks and stone/core/BVH contact evidence saved. Three objects fail the initial mesh inspection; numerous stone-surface crossings require resolution. BVH crossings do not certify positive overlap volume, and core intersections are not structural engineering/load certification. Source/candidate files were read back and hashed.
- G4 **NOT_RUN**. No game/Android integration, collision/navmesh, runtime budget or device validation. Game code/assets untouched; this is a scope-diff check, not a runtime regression PASS.

First render stopped because the local Blender build lacks OpenImageDenoise. **Saved geometry was reused**, denoising disabled, and only rendering resumed. All three PNGs were then actually generated at 64 samples. This technical recovery is not an art revision.

## Failed corrective operations and stop

`method-c-02/BLOCKED.json` and logs preserve the unsuccessful LOD0 build and contact-fitting operation. No 02 BLEND/PNGs were produced or claimed. Explicit LOD0 selection still returned an empty `Far_F12` Exact Boolean result. Source LOD0 itself was closed/manifold with positive volume. A bounded update/depsgraph probe did not resolve it. Priority contact subtraction on the existing model then emptied `Near_F16`. **Stop this Exact scan-domain fitting approach** rather than relabeling or jittering it. These are technical failures, not unviewed G2 failures.

The saved 01 geometry is preserved unchanged. Current builder supports explicit recorded LOD3 selection and source SHA checking, but **a full reconstruction with the revised builder was not run or certified bit-identical**. Experimental LOD0 rebuild is explicitly blocked. The reliable reviewed deliverable is the saved BLEND; renderer and auditor operate on it without rebuilding. The contact fitter is retained as failed engineering evidence, not a release tool.

## Reopen/render/audit the actual saved candidate

Use Blender 4.3.2. Keep source and original render directories read-only; copy the candidate BLEND into a new scratch output directory before rerendering.

```sh
blender -b SCRATCH/abutment.blend --threads 6 --python-exit-code 1 --python tools/map_blender/lind/route_mat_01/render_curated.py -- SCRATCH
blender -b SCRATCH/abutment.blend --threads 2 --python-exit-code 1 --python tools/map_blender/lind/route_mat_01/audit_candidate.py -- SCRATCH
```

The auditor writes explicit FAIL/subset states; do not equate an executed audit or packaging CI success with QA acceptance. Workflow uploads already executed local outputs and evidence with 14-day retention; it does not claim a new Blender production run.

Next eligible production work: manual closed-mesh stone sculpt/retopology with independently designed bedding and through-bonds, or an appropriately licensed complete high-quality masonry scan. Review actual clay geometry before PBR. G1 metric approval is additionally needed before placement/adoption. No official asset changes, failed-candidate deletion, main merge, adoption or publication.

## GitHub evidence delivery

Executed packaging run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43989537216 . Actual 13,046,277-byte artifact: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43989537216/artifacts/14286882505 (14 days). Source commit `0af629c7536be36da48b17d448e60c75a44c27a6`. This successful run validates bytes/PNG headers and uploads executed outputs; G2/G3 remain FAIL.

Legacy A workflow was inadvertently triggered by its broad PR path filter on the first evidence push; run 43989536839 was cancelled during dependency installation; the Generate step was verified SKIPPED, so no old model was regenerated. A/B jobs are now explicitly skipped to enforce their stopped state without deleting recipes or history.
