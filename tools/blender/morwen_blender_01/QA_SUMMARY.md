# MORWEN-BLENDER-01 QA

## Local technical self-QA: PASS

- Baseline main: `cab9aa52da653198a712bd986992adc03ea4bfe2`.
- Sources downloaded directly from GitHub: PR #239 `6374a9854e4b1e22fd7b180f656bf8f9b5f8f163`, PR #242 `27dee80c34a568ba6657cd6683dd707beabfbed7`. All 18 copied files SHA-256 verified; all 12 protected PNGs match the original manifest. `SOURCE_RECEIPT.json` records exact paths and hashes.
- 384×1024 four-view calibration: alpha>=128 grounding; shared pixel scale, no image resampling/mirroring. Height spread 1 px. Visible anchors are pixel-refined visual candidates, hidden profile anchors/depth remain inferred. Front anatomical L/R corrected from the rough source.
- 8 unit/schema tests PASS (status honesty, anatomical side/depth, hidden inference, source tamper rejection, NaN/aspect rejection, complete mapping). Python compilation and staged diff checks PASS.
- Actual local headless **Blender 4.3.2 / Cycles CPU** build PASS: four rigged neutral segmented blockouts, four 17-bone armatures, 16 parent links each, four packed reference planes, four native overlays and neutral overview. All bone endpoints project back to their source pixel candidates within 0.01 px; the overview camera contains every proxy bounding box.
- Saved .blend independently reopened in a second Blender process: 4 packed original image hashes match, 17-bone hierarchy/finite geometry/nonzero face areas/17 weight groups PASS. Each proxy has 2336 vertices; a real forearm rotation deforms the weighted mesh and restores to rest. `reload_qa.json` and `local_reload.log` contain actual results.
- `OUTPUT_MANIFEST.json` records .blend, preview and QA artifact SHA-256. No source overwrite, legacy deletion, runtime/production/scenario/site/other-character change. Existing AGENTS body retained verbatim below the task-specific priority note.

## GitHub Actions

Real workflow build/reload is pending at this initial implementation commit. Final run URL, tested commit, outcome and artifact link will be recorded in `CI_EVIDENCE.json` and the Draft PR after completion. A local PASS is not presented as an Actions PASS.

## Review and limits

This is a four-view **2.5D neutral blockout/rig candidate**, not one solved detailed 3D Morwen model, finished skin/topology/costume, IK or animation. Hidden-side anatomical positions and depth are not measured. Images remain REFERENCE_ONLY; result remains FUTURE_CANON_PENDING_APPROVAL. Technical PASS is not visual approval.

Initial Eevee rendering exposed EGL/cache restrictions and was replaced with reproducible CPU Cycles. The first neutral overview was cropped; its landscape orthographic span was corrected and an all-proxy camera-bounds assertion added before the final build. No repeated image regeneration or source edits were performed.

Claude independent visual review, human director approval and Android/device QA: **NOT_RUN**. Next task: independent anatomical/proportion review, then refine a coherent single 3D base and smooth skin. No main merge, adoption, site publication or game integration.
