# Emma conversation portrait (ASSET-EMMA-01)

## Registered
- `img/portraits/emma/emma_normal.png` — the supplied normal portrait, **byte-identical** (1024x1536 RGBA, alpha 0..254), sha256 `f4dfd09d08e3bd333743f677afbe84e4e1771b295863e92a96a3b4c0904114b2`.
  The file I had was the chat-attachment copy of `優しい薬草使いの老婦人(2).png`; its size matches the spec (1024x1536). The original file itself was not available to compare.
- Registry entry `emma` in `js/field/talk-portrait.js`: crop `{x:90,y:0,w:880,h:880}` (head + shoulders, source 1024x1536), side right.
- Per-character expression ids: Emma uses `faces: normal, expression01..expression04`; Fiona/Lou keep the shared 8 ids unchanged. `ready: ['normal']` — an id without an image falls back to `normal` **without a request**. Unknown ids / Fiona-Lou ids (`smile`, `03` …) also give `normal` for Emma.
- Conversations: `char:'emma', face:'normal'` added to every Emma conversation in `talk-data.js` and `talk-data-quests.js`. Where Fiona speaks inside an Emma line (emma_closed / emma_open) that page shows Fiona's `normal` portrait, then Emma again. Text, choices, conditions, effects, ids and priorities are unchanged (verified by flattening old/new tables and comparing).

## NOT registered: expression01..04
Source: `四表情の優しいおばあさん_sprite.png`. Only a 2172x724 copy was available (spec says 2048x682; **no original found**). Findings on the copy:
- 4 cells (alpha rects, ~504x724): x0-494 / 534-1038 / 1078-1582 / 1622-2126, pitch 543; 2px opaque white seam lines at x=541-542, 1085-1086, 1629-1630 (may be a copy artifact).
- The cells are **not scaled copies of the normal portrait**: vertical scale 0.471 (=724/1536) but horizontal ~0.505; head tilt, glasses position/shape, brows and eye positions differ. Best affine alignment on the face area has ECC correlation only 0.33-0.39.
- `emma_expression_alignment_check.jpg` overlays each aligned cell on the master face at 50 %: eyes, glasses rims, nose and mouth are off by tens of pixels (double glasses). A face-only composite onto the master (the Fiona/Lou method) cannot be done without repainting. Cells are also ~47 % of the master resolution.
- Per the instruction ("do not register if the composite is unnatural; re-create"): **not registered**. Options: (a) deliver the four expressions again at master pose/resolution, (b) approve using the sheet cells as standalone portraits (pose jumps when switching, ~2x upscaling), (c) approve a repaint-style composite. Until then `expression01..04` resolve to `normal`.
- source copy of the expression sheet: docs/portraits/source/emma_expression_sheet_COPY_2172x724.png (sha256 in source/SHA256.txt) — a copy; spec says 2048x682, original not available.
