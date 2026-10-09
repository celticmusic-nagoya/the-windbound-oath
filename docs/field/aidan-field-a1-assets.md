# Aidan A1 standalone field asset checkpoint

Reference received: `aidan-fiona-lou.zip`. Full unchanged reference is archived under `docs/art/reference/characters/`; no sheet crops. Written one back-carried two-handed 誓いの剣 rule overrides the two handheld weapons drawn in the source.

20 accepted individual PNGs: 4 IDLE + 16 WALK. All1536×1024 RGBA, actual alpha0 pixels79.4–83.5%, visible content does not touch any edge. Individual images and light/dark composites visually checked: one sword/hilt/sheath per image, empty hands, no extra limbs or major omissions, no black/white/checker matte. Battle art unchanged.

Production PNGs are copied byte-for-byte from individual imagegen outputs. Foot padding is registered in the DEV field asset manifest, not cropped or painted away. The four contact sheets are QA previews only, never source sprites.

| File | RGBA | Fully transparent pixels | Alpha0 % | Sword count | Visual QA |
|---|---|---:|---:|---:|---|
| `aidan_idle_down.png` | yes | 1304729 | 82.95 | 1 | PASS |
| `aidan_idle_left.png` | yes | 1273601 | 80.97 | 1 | PASS |
| `aidan_idle_right.png` | yes | 1268546 | 80.65 | 1 | PASS |
| `aidan_idle_up.png` | yes | 1289330 | 81.97 | 1 | PASS |
| `aidan_walk_down_01.png` | yes | 1313479 | 83.51 | 1 | PASS |
| `aidan_walk_down_02.png` | yes | 1310632 | 83.33 | 1 | PASS |
| `aidan_walk_down_03.png` | yes | 1280441 | 81.41 | 1 | PASS |
| `aidan_walk_down_04.png` | yes | 1309091 | 83.23 | 1 | PASS |
| `aidan_walk_left_01.png` | yes | 1258055 | 79.98 | 1 | PASS |
| `aidan_walk_left_02.png` | yes | 1281886 | 81.50 | 1 | PASS |
| `aidan_walk_left_03.png` | yes | 1249087 | 79.41 | 1 | PASS |
| `aidan_walk_left_04.png` | yes | 1278445 | 81.28 | 1 | PASS |
| `aidan_walk_right_01.png` | yes | 1267521 | 80.59 | 1 | PASS |
| `aidan_walk_right_02.png` | yes | 1289090 | 81.96 | 1 | PASS |
| `aidan_walk_right_03.png` | yes | 1263393 | 80.32 | 1 | PASS |
| `aidan_walk_right_04.png` | yes | 1286044 | 81.76 | 1 | PASS |
| `aidan_walk_up_01.png` | yes | 1298434 | 82.55 | 1 | PASS |
| `aidan_walk_up_02.png` | yes | 1254646 | 79.77 | 1 | PASS |
| `aidan_walk_up_03.png` | yes | 1290439 | 82.04 | 1 | PASS |
| `aidan_walk_up_04.png` | yes | 1275295 | 81.08 | 1 | PASS |

Warnings: four-frame simple walk; small embroidery/cloak detail differences remain for PLAYER QA. Functional animation/placement/navigation and final Battle regression are recorded separately in the implementation/final checkpoints.
