# LIND failed voxel candidate — measured root-cause triage (2026-11-17)

## Reproducible evidence
- [Actions run 44008259693](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44008259693): SUCCESS.
- [Artifact 14294834826](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44008259693/artifacts/14294834826) contains `voxel_rootcause_metrics.json` and `inspection.log`.
- Exact saved Blender source from prior run #44006786285 SHA-verified before inspection; no geometry rebuild, rerender, rebake or original source changes.

## Actual metrics (Blender 4.0.2)
| Metric | Scan source | Failed voxel candidate |
|---|---:|---:|
| Triangles | 1,537,926 | 36,956 |
| Vertices | 789,032 | 22,630 |
| Total face area (source units²) | 2,598.930884 | 114.309814 |
| Degenerate faces (<1e-10 area) | 0 | 16 |
| Mean local polygon normal Z | 0.500875 | -0.002069 |
| UV layers | 1 | 1 |
| Camera projected x bounds | 0.17465..0.83053 | 0.17577..0.82423 |
| Camera projected y bounds | 0.37258..0.62484 | 0.37800..0.62200 |

- Candidate surface area ratio is `114.309814 / 2598.930884 = 0.04398` (95.60% less), **not a valid preservation of the source surface**.
- Candidate UV occupied 72/65,536 cells of a 256×256 atlas = **0.10986328125%**; summed UV triangle area 0.00127193. A 1024px bake is effectively unusable at this occupancy.
- Candidate-to-source nearest-surface fit (3,233 deterministic samples): mean 0.00199995, p95 0.00200088, max 0.00200312. **Small nearest-point distance does not imply retained topology, face area or shape**: the collapsed candidate may lie close to some portion of the source.
- Both object bounding boxes project inside the camera image, so a wholly off-screen camera is not the primary explanation. The long scan occupies only about 65% image width and 24% height; this is not a valid close-up art camera.
- The face-normal Z shift and 16 degenerate faces support **major topology/orientation changes**, but do not alone prove whether the remesh's solidification, open-boundary behavior or subsequent projection caused the loss.

## Decision
- **G1 BLOCKED**, official world scale/placement not established.
- **G2 FAIL**, visible cliff and normal-map quality not retained.
- **G3 FAIL for candidate structural/UV integrity**; read-only inspection pipeline and SHA validation PASS.
- **G4 NOT_RUN**.
- **STOP global Voxel Remesh + Smart UV Project + 1K atlas on this open scan**. Do not blindly alter voxel size or retry the same global method. Evidence suggests the open scan is unsuitable for volumetric reconstruction without deliberate boundary closure.
- Next independent candidate should operate on a selected **localized contiguous high-poly scan patch**, retaining open surface character, with topology-aware patch retopology and UV island packing. Bake high-poly detail to an appropriately allocated patch texture, then compare with source at identical close-up camera. Preserve the publisher scan and the source's CC0 license metadata.
- This report is diagnostic evidence only, not an implemented new cliff. No canonical/main/bridge edits.
