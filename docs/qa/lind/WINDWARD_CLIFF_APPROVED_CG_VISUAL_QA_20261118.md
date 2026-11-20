# WINDWARD CLIFFS — approved CG direct visual QA, 2026-11-18

Status: **FIVE ORIGINALS HASH VERIFIED; DIRECT IMAGE REVIEW COMPLETE; NO 3D ASSET**.

## Execution evidence
- GitHub Actions `Windward Approved CG Source QA` run **44207247008**: completed SUCCESS.
- Artifact **14384491322**, `windward-approved-cg-source-qa` (ZIP 1,434,346 bytes; workflow artifact digest `sha256:cd4797fb2b05f707cb1bfa1a2bc5ece38bbb909af526b72d4418ec7a68588370`).
- Extracted `windward-cg-source-verification.json` from actual artifact: **5/5 PASS** for expected vs actual SHA-256 and byte count; Pillow decoded and verified images; contact sheet generated.
- Five original resolutions: sunset background **1672×941**, sunset two-character back **1671×941**, seated stars **1672×941**, standing stars **1671×941**, dialogue-only night **1672×941**.
- Approved per-file SHA source: `docs/art/approved-rilde-story-20261107.json`; do not change originals or republish CG on public site.

## Direct contact-sheet visual review
- Sunset background: foreground **large deciduous tree on left** framing sky; **white flowers and windswept grassy rim**; beyond, a **long near-horizontal plateau cliff with a near-vertical exposed rock face** and irregular descending secondary sea stacks; ocean and low sun on **right**. Avoid inventing a circular rock mesa, continuous rounded ramp, or random stepped procedural terraces.
- Sunset two-character rear view: both seated on grassy near-edge foreground, plateau/cliff behind, ocean and right-side low sun. Keep the **seating surface broad enough and free of blocking rocks**; do not turn this into a sheer ledge under their feet.
- Seated stargazing: same broad grass-and-flower foreground and left tree canopy, exposed cliff face behind the characters, ocean below. Starfield/Milky Way does not change geological geometry.
- Standing stargazing: same left tree, flowered grassy promontory and **low ocean horizon**; characters stand upright. Do not make the foreground slope so steep that standing is implausible.
- Dialogue-only night: prominent left tree, grassy foreground with flowers, distant irregular rocky headland/shoreline, ocean on right. Night view has a **wider sky allocation** and cliff mass lower in frame than sunset. Event CGs are **different compositions, not pixel-aligned orthographic views**; no exact 3D camera transforms can be inferred from them alone.
- Across all five: cliff silhouette is **a broad, relatively flat-topped eroded headland** with near-vertical fractured faces, asymmetrical recesses, sparse grass on upper soil, low rocky shore/sea stacks; foreground is playable turf and coastal flowers. Rock erosion should be sculpted and art-directed, not made from repeated box stones or a single heightfield.

## Design constraints / source-derived vs proposals
**Source-derived observations** above describe the contact sheet only; they do **not** specify exact rock strata orientation, geological material, world-space scale, camera lens, cliff height, player collider or navigable path. Such values remain proposals requiring G1 approval.

**Production recommendation**: build a modular focal cliff as authored/sculpted masses with UV/PBR, a separate grassy headland transition, and a left-tree/flower foreground framing layer. The tree and flowers are art requirements in the event composition, but their precise positions must be approved with camera and metric contract. Keep cliff and village invisible to each other per current approved story constraint. Use night/sunset comparison at final game display size.

## Gate record
- **G1 CG source integrity PASS (five originals)**.
- **G1 exact 3D metric, camera, physical placement BLOCKED**; full G1 remains BLOCKED.
- **G2 CG visual source inspection PASS**; **G2 new 3D sculpt NOT_RUN**.
- **G3/G4 new asset NOT_RUN**.
- Prior world candidate D's art FAIL does not transfer to this unproduced new sculpt.

## Next executable action
Create a distinct **editable Blender sculpt candidate** in the WORLD-owned lane using these five originals as non-destructive references. Before final placement, obtain explicit metric/camera contract; do not promote candidate as canonical. Require multiple-view wireframes and sunset/night CG comparisons and independent G2.
