# 歩行/停止/正面/背後 納品 (2026-10-11, aidan_fiona_walk.zip)
元ファイルは名前を付け替えて原寸保管(1312x1199 RGBA。fiona_back のみ 1024x1536)。実装は tools/field/install_hero_frames.py で正規化。
| 方向 | Aidan | Fiona |
|---|---|---|
| right walk(4) / idle | side_a,b,c,d / side_c | side_a,b,c,d / side_c |
| left | right の左右反転 | right の左右反転 |
| down walk(4) / idle | front_walk,front_idle,front_walk,front_idle / front_idle | front_walk,front_idle,… / front_idle |
| up walk(4) / idle | back_a,b,a,b / back_a | back のみ → 4コマ同一 / back |
未使用: aidan_side_e, aidan_front34_walk, fiona_side_e, fiona_left34。
不足(次回納品の希望): 各方向の専用 idle、左向き専用、正面/背後の歩行コマ、Fiona 背後の歩行。
