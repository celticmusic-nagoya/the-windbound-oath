# Phase 2 Delivery 2 QA (Claude self-check — not independent QA)

Source: `source/ref_sheet_v2.png` (1536×1024, ChatGPT new drawing, real alpha).
Processing: `tools/normalize_h01.py split` → `fit` (LANCZOS downscale into the FIT box, binary alpha, transparent RGB = 0, fragments <12 px removed, stand items on bottom row) → `tools/fireplace_layers.py`.

## Numeric (tools/accept_h01.py) — all PASS

| asset | canvas | scale from sheet | content box (x,y,w,h) | result |
|---|---|---|---|---|
| fireplace (composite) | 304×272 | 0.751 | 4,21,296,251 | PASS |
| fireplace_body | 304×272 | 0.751 | same | PASS |
| fireplace_fire | 304×272 | 0.751 | 103,145 → 218,246 | PASS |
| bed | 248×184 | 0.586 | 10,4,228,180 | PASS |
| bed_small | 224×168 | 0.590 | 20,8,183,160 | PASS |
| rug_green | 400×240 | 0.655 | 2,25,396,193 | PASS |
| window_wall | 128×152 | 0.562 | 2,4,123,144 | PASS |
| tapestry | 144×200 | 0.595 | 0,13,144,169 | PASS |
| spinning_wheel | 120×156 | 0.413 | 4,44,112,112 | PASS |

Fireplace registration: body + fire (alpha_composite) == composite, **0 differing pixels**.
Fire layer = lit drawing's opening interior (flames, logs, glow) restricted to the opening box; body = unlit drawing. The composite therefore uses the unlit drawing outside the opening.

## Visual (300%, `qa/delivery2/delivery2_x3_magenta.png`)
No white fringe, no background remnants, no cut edges, no text. Seam between body and fire is not visible.

## Render (browser-only interception, rilde_in_house_01; PC / Android landscape / portrait viewport emulation, not real device)
13/13 house_01 props loaded under the new IDs in all three viewports, 0 page errors. Small items (doormat, table, chair, stool, barrel, jar) are Delivery 1 candidates, shown only to fill the room.

- Beds now cover their colliders (Delivery 1 was ~70%).
- Fireplace, window and tapestry read correctly against Aidan / Fiona / Lou.
- Notes: rug is width-limited (content height 193 of 240 because the drawing is a flatter oval); spinning wheel content is 112×112 inside 120×156 (square drawing). Both are proportion-preserving; widen the drawing only if the director wants them to fill the box.

## Not done / not verified
- Real Android device: 未検証.
- Repair items (table white between legs, stool cut, jar shadow, chair grey line): not in this delivery.
- No change to main, maps, manifest or adopted assets. Approval pending for every candidate.
