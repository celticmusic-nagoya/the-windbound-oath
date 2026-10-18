# Fiona / Lou conversation portraits (8 expressions each)

Assets: `img/portraits/{fiona,lou}/{fiona,lou}_{normal,smile,angry,sad,surprised,worried,determined,relieved}.png` (16 RGBA PNGs, original resolution, canvas = master size: Fiona 1024x1536, Lou 1312x1199).

## Expression IDs
01 normal / 02 smile / 03 angry / 04 sad / 05 surprised / 06 worried / 07 determined / 08 relieved.
Set 1 (01-04: TL,TR,BL,BR) = `*_sheet_attach4/6`, set 2 (05-08) = `*_sheet_attach3/5`. **The set assignment is inferred from the sheet contents** (see SOURCE_SHA256.txt for the six originals, which are not stored here); swapping sets is a one-line change in `tools/portraits/mos.py` (`SRC`).

## Method (no regeneration, no AI repainting)
`normal` = the master, byte-identical. Other expressions: master + only eyes/brows/lids/iris, mouth (and a minimal cheek for Fiona relieved, soft blush for Lou smile/relieved) from the sheet cell. Cell->master alignment: SIFT+RANSAC similarity, refined by ECC (affine) on stable skin/outline contexts, one Lanczos resample; polygon masks, sigma 1.2 feather, skin-ring colour offset (clipped +-10). Everything else is the master's pixels. Scripts: `tools/portraits/` (`warp_char.py` -> `compose.py` -> `verify.py`).

## Verification (`docs/portraits/verify.json`)
All 16: RGBA, same size as master, alpha channel identical to the master (Lou wings' translucency and Fiona's alpha kept), RGB of alpha-0 pixels identical, **0 changed pixels outside the dilated edit polygons**. Changed area: Fiona x506-654,y244-375; Lou x665-871,y357-496 (face only; staff/crystal/hair ornaments/dress/wings/butterflies untouched).

## 要確認 (needs art-direction check)
Lou's sheet cells are ~2.1x smaller than the master (Fiona ~1.3x), so Lou's open-eye faces are softer and the iris is drawn in a different style (no ring/3 highlights as in the master): **lou_angry, lou_sad, lou_surprised, lou_worried, lou_determined = 要確認** (composited cleanly, no seam, but style differs from `lou_normal`). `lou_smile` / `lou_relieved` (closed eyes) and all Fiona faces looked natural at 3x zoom (`face_preview_*.png`: normal + 7 composites).

## Dialogue integration
`js/field/talk-portrait.js` (registry + display), small hooks in `js/field/field-talk.js`, CSS at the end of `css/style.css`. Scenario data (explicit, nothing is inferred from speaker names, existing conversations unchanged):
```js
{id:'x', lines:[{char:'fiona', face:'smile', pages:[ 'フィオナ「やあ。」', {speaker:'フィオナ', text:'「えっ？」', face:'surprised'}, {speaker:'ルー', text:'「ふふ」', char:'lou', face:'smile'}, {speaker:'', text:'（…）', char:null} ]}]}
```
`char`/`face` on the conversation = defaults (face applies to page 1); a page without `char` keeps the previous page's character (`null` hides); missing/unknown `face` -> `normal` (also accepts "01".."08"); image load failure -> `normal` -> no portrait (dialogue continues); unknown character -> no portrait. Hidden when the conversation ends, in battle mode, and whenever `body.dialogueOpen` is absent. The portrait sits just above `#msg` (measured, so phone/tablet/PC all work), `pointer-events:none`. Only the images a conversation uses are preloaded.
Tests: `tests/moss/m30_talk_portrait.py`.
