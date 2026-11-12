# SERENA-LAYER0-MASTER-01 — BLOCKED

## Source preserved

- Director attachment: `7824.png`.
- Source: `assets/characters/serena/layer0/source/7824.original.png` (original bytes, no processing).
- SHA-256: `c5f051bafe2a59cef9f8f4fcf647d7257749eee6ad0c5a31b359af2813d3595b`.
- PNG, 1536×1024, RGBA, 2,199,342 bytes. Source alpha range 0–254, 806,186 pixels already alpha0. The file is not an RGB/fully opaque PNG; complete background matte quality is not claimed.
- The input was supplied as formally adopted by the director. The registration task has an additional explicit stocking-side constraint; preserving the input approval does not waive that constraint.

## Blocking design mismatch

| View | Task requirement | Supplied original |
|---|---|---|
| Front | Stocking on screen-left (Serena's right leg) | Stocking on screen-right |
| Back | Stocking on screen-right (Serena's right leg) | Stocking on screen-left |

The gold-trimmed stocking and chain visibly follow the opposite leg. Pixel review probes at front (180,700)/(280,700), back (1270,700)/(1340,700) are recorded with their original RGBA values in MANIFEST.json. This is a source-image visual finding; pixel colors alone are not presented as a semantic classifier.

Background-only alpha editing cannot relocate the stocking. Moving it, mirroring the figures, or redrawing the character would alter the supplied approved design and exceeds this task's permitted background-only processing. No such edit was made.

## QA and delivery

- Source PNG metadata/SHA/byte-preservation: PASS.
- Source contains the four supplied views: PASS by visual inspection.
- Required right-leg asymmetry: FAIL; primary blocker.
- Background removal attempts: **0 / maximum 2**. Stopped at the input design gate; no pointless background retry can fix a character-side mismatch.
- Processed transparency/contour/fringe QA: NOT_RUN.
- `assets/characters/serena/layer0/serena_layer0_fourview_master.png`: **NOT CREATED / NOT REGISTERED**.
- Processed SHA: null, not fabricated from the unchanged original.
- Only the original, manifest, and this QA record are added. Existing Serena assets, Morwen/Fiona masters and rigs are untouched. No existing file overwrite/deletion, main merge, game integration or website publication.

The Draft PR preserves the source and the concrete blocker for review. Registration can resume from an approved input that matches the specified leg, or a separate explicit direction authorizing a character-design correction. No regeneration or character modification is attempted by this task.
