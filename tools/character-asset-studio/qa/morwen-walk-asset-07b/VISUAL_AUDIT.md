# Source visual audit — Codex self-review, not director adoption

All four images were retrieved from GitHub blob API using the specified base commit and inspected at their native aspect ratios. Reference identity PASS 4/4 is an exact byte/SHA result. This audit describes the **user-requested HD v2 pixel originals**, not an adoption of any new candidate and not a global canon update. Older turnaround/chibi sprites were not used as image-generation references.

| Feature | Observed in requested originals / preservation instruction |
|---|---|
| Hair | Blunt purple bob with straight bangs; profile/back volume and dark purple highlights must remain consistent |
| Face | Gold-rim glasses, violet eyes, visible small ear flower and purple jewel earrings; do not transfer side visibility automatically |
| Hat | Oversized purple hat with drooping tip/pendant, gold piping and motifs; right side has large flower, leaf/ribbon assembly; left view shows different ornament occlusion |
| Costume | Purple/gold academy bodice, white high collar and cuffs, bow, book/laurel shoulder motif, long layered flared robe with detailed gold geometric symbols, purple pleated skirt |
| Legs/boots | Opaque dark-purple thigh-high stockings, visible asymmetric thigh strap/buckle where shown, short heeled lace-up boots with gold buckles and trim; preserve source silhouette |
| Asymmetry | Right view shows bag/diagonal strap and hat ribbons; left view differs and retains visible bottles/chain; no whole-image reflection |
| Proportions | Preserve original full-height silhouette and relative hat/head/torso/leg sizes; ratios were not independently measured here. HD track must not silently become an old chibi sprite |

The left source visibly includes a book emblem. Historical ART-74A's instruction to remove it applied to a different source. The selected v2 front/skirt and hat details also differ from some later prose policies. This task follows the user's four explicitly named images, preserves observed details, and records the discrepancy rather than silently changing the source.

## Native image / alpha limits

`SOURCE_DOWNLOAD.json` records sizes: front 1024×1536, left 1024×1535, right 1087×1446, back 1086×1448; all RGBA. These are not already a common 1200×1600 walk canvas. All have transparent outer pixels and partial-alpha subject/edge pixels (`ORIGINAL_ALPHA.json`). Keep original bytes, including alpha. Production binary-alpha rules apply to new derivatives only. No source cleanup/recompression was performed.

## Candidate attempts and observed deltas

### Attempt 1 — whole left six-frame sheet

Tool: `image_gen.imagegen`, transparency requested. References: downloaded left/front/right originals; the left image controlled direction/design and the other two explained asymmetric equipment. Requested a 3×2 sheet with contact/loading/passing and opposite lead legs, full costume preservation and transparent exterior.

Observed: 1536×1024 six-cell sheet, reduced detail scale, shortened/simplified cape/ornament relative to source, top/bottom pose-pair repetition and opposite lead not demonstrably distinct. It is not six independent target-size frames. Technical pixels: 1,211,922 fully transparent, 360,942 partial-alpha, zero fully opaque pixels, maximum alpha 254. **FAIL** the production canvas/binary-alpha and sequence-design gates. Retained under `rejected/`.

Correction to the first live commentary: the rendered dark/purple preview was initially described as an opaque background. Pixel inspection instead finds transparent outer pixels; that interpretation was wrong. The recorded failure is partial subject alpha and sheet/pose/design limitations. No background-removal operation was applied.

### Attempt 2 — changed method: single source-based lower-leg pose edit

Tool: `image_gen.imagegen`, transparency requested, only original left supplied. Protected hat/face/costume and asked for a local leg-pose change with an independently constructed far leg, instead of redrawing a whole sequence.

Observed: substantially closer full-body HD left pose, with additional visible far leg and costume close to source; output 1025×1535, not 1200×1600. Technical pixels: 994,754 fully transparent, 578,109 partial-alpha, 512 fully opaque. **FAIL** production canvas/binary-alpha gate. Actual anchor, anatomical mapping, pose/root transforms and contact coordinates unmeasured. Preserve as **UNAPPROVED CANDIDATE**, not an accepted F01 or exact protected-pixel edit. Independent design agreement remains NOT_RUN.

Two total attempts used; generation stopped. No right sheet is fabricated after the method fails. The structural limitation is unconstrained raster generation: exact canvas/alpha, protected-pixel detail, distinct gait states and anatomical correspondence cannot be assured from this process. No fake frames are made by mirroring, cropping the sheet, holding the original, or translating a static sprite.

## Alternatives / next deliverable

1. Layered artist/manual pass using the exact reference package, locked source regions, separate far-limb drawings and measured native anchors. Produce/review two opposing contact keys before completing all twelve.
2. Verified 2D part rig with actual authored gait/root data, independent left/right costume layers, controlled render canvas/binary alpha and producer-recorded contacts.

Reference-package integrity is PASS. Production design/asymmetry, 12-frame duplicate/loop checks, measured contacts, human adoption and Android remain NOT_RUN/BLOCKED. The two candidates do not establish a formal walk sequence or real-motion contact export.
